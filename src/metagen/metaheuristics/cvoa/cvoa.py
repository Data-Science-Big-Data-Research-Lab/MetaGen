"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import copy
import logging
import math
import random
import threading
from datetime import timedelta
from time import time
from typing import Callable, Set, List, NamedTuple, Tuple
from concurrent.futures.thread import ThreadPoolExecutor



from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.framework.solution.bounds import SolutionClass
from metagen.metaheuristics.base import Metaheuristic


class StrainProperties(NamedTuple):
    strain_id: str = "Strain#1"
    pandemic_duration: int = 10
    spreading_rate: int = 5
    min_superspreading_rate: int = 6
    max_superspreading_rate: int = 15
    social_distancing: int = 7
    p_isolation: float = 0.5
    p_travel: float = 0.1
    p_re_infection: float = 0.001
    p_superspreader: float = 0.1
    p_die: float = 0.05


IndividualState = NamedTuple("IndividualState", [("recovered", bool), ("dead", bool), ("isolated", bool)])

class PandemicState:
    def __init__(self, initial_individual:Solution):
        # Lock fot multi-threading safety access to the shared structures.
        self.lock = threading.Lock()
        self.recovered:Set[Solution] = set()
        self.deaths:Set[Solution] = set()
        self.isolated:Set[Solution] = set()
        self.best_individual_found:bool = False
        self.best_individual:Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        with self.lock:
            result: IndividualState = IndividualState(False, False, False)
            if individual in self.recovered:
                result = result._replace(recovered=True)
            if individual in self.deaths:
                result = result._replace(dead=True)
            if individual in self.isolated:
                result = result._replace(isolated=True)
            return result

    # Recovered
    def get_recovered_len(self) -> int:
        with self.lock:
            return len(self.recovered)

    def get_infected_again(self, individual:Solution) -> None:
        with self.lock:
            self.recovered.remove(individual)

    # Deaths
    def update_deaths(self, individuals:Set[Solution])-> None:
        with self.lock:
            self.deaths.update(individuals)

    # Recovered and Deaths
    def update_recovered_with_deaths(self)-> None:
        with self.lock:
            self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual:Solution)-> None:
        with self.lock:
            if individual not in self.deaths:
                self.recovered.add(individual)

    # Isolated
    def isolate_individual_conditional_state(self, individual:Solution, conditional_state:IndividualState) -> None:
        with self.lock:
            current_state:IndividualState = self.get_individual_state(individual)
            if current_state == conditional_state:
                self.isolated.add(individual)

    # Best Individual
    def update_best_individual(self, individual:Solution) -> None:
        with self.lock:
            self.best_individual_found = True
            self.best_individual = individual

    def get_best_individual(self) -> Solution:
        with self.lock:
            return self.best_individual

    def get_pandemic_report(self):
        with self.lock:
            return {
                "recovered": len(self.recovered),
                 "deaths": len(self.deaths),
                 "isolated": len(self.isolated),
                "best_individual": self.best_individual
            }



class CVOA(Metaheuristic):
    """

    This class implements the *CVOA* algorithm. It uses the :py:class:`~metagen.framework.Solution` class as an
    abstraction of an individual for the meta-heuristic.

    It solves an optimization problem defined by a :py:class:`~metagen.framework.Domain` object and an
    implementation of a fitness function.

    By instantiate :py:class:`~metagen.metaheuristics.CVOA` object, i.e. a strain, the configuration parameters must be provided.

    This class supports multiple strain execution by means of multy-threading. Each strain
    (:py:class:`~metagen.metaheuristics.CVOA` object) will execute its *CVOA* algorithm (:py:meth:`~metagen.metaheuristics.CVOA.cvoa`)
    in a thread and, finally, the best :py:class:`~metagen.framework.Solution` (i.e. the best fitness function
    is obtained).

    To launch a multi-strain execution, this module provides the :py:meth:`~metagen.metaheuristics.cvoa_launcher`
    method.

    :param strain_id: The strain name
    :param pandemic_duration: The pandemic duration, defaults to 10
    :param spreading_rate: The spreading rate, defaults to 6
    :param min_super_spreading_rate: The minimum super spreading rate, defaults to 6
    :param max_super_spreading_rate: The maximum super spreading rate, defaults to 15
    :param social_distancing: The distancing stablished between the individuals, defaults to 10
    :param p_isolation: The probability of an individual being isolated, defaults to 0.7
    :param p_travel: The probability that an individual will travel, defaults to 0.1
    :param p_re_infection: The probability of an individual being re-infected, defaults to 0.0014
    :param p_superspreader: The probability of an individual being a super-spreader, defaults to 0.1
    :param p_die: The probability that an individual will die, defaults to 0.05
    :param verbose: The verbosity option, defaults to True
    :type strain_id: str
    :type pandemic_duration: int
    :type spreading_rate: int
    :type min_super_spreading_rate: int
    :type max_super_spreading_rate: int
    :type social_distancing: int
    :type p_isolation: float
    :type p_travel: float
    :type p_re_infection: float
    :type p_superspreader: float
    :type p_die: float
    :type verbose: bool


    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import CVOA, cvoa_launcher
        domain = Domain()
        multithread = True

        domain.defineInteger(0, 1)

        fitness_function = ...

        if multithread: # For multiple thread excecution

            CVOA.initialize_pandemic(domain, fitness_function)
            strain1 = CVOA("Strain1", pandemic_duration=100)
            strain2 = CVOA("Strain2",  pandemic_duration=100)
            ...

            strains = [strain1, strain2, ...]
            optimal_solution = cvoa_launcher(strains)
        else: # For individual thread excecution

            CVOA.initialize_pandemic(domain, fitness_function)
            search = CVOA(pandemic_duration=100)
            optimal_solution = search.run()
    """

    def __init__(self, global_state, domain, fitness_function, strain_properties:StrainProperties = StrainProperties(), verbose=True, update_isolated=False,
                 log_dir="logs/CVOA"):

        # 1. Initialize the base class.
        super().__init__(domain, fitness_function, log_dir=log_dir)

        # 2. The Pandemic global state and strain properties.
        self.global_state = global_state
        self.strain_properties: StrainProperties = strain_properties

        # 3. Auxiliary strain control variables.
        self.verbosity = print if verbose else lambda *a, **k: None
        self.update_isolated: bool = update_isolated
        self.solution_type: type[SolutionClass] = self.domain.get_connector().get_type(self.domain.get_core())

        # 4. Strain control flow variables.

        # 4.1. Logical condition to ctrl the epidemic (main iteration).
        # If True, the iteration continues. When there are no infected individuals, the epidemic finishes.
        self.epidemic:bool = True

        # 4.2. The current iteration. The iteration counter will be initially set to 0.
        self.time: int = 0

        # 4.3. The best solution found by the strain.
        self.best_solution: Solution | None = None
        self.best_founded: bool = False

        # 4.4. The best strain-specific death individual will initially be the worst solution.
        self.best_dead = self.solution_type(self.domain, connector=self.domain.get_connector())

        # 4.5. The worst strain-specific superspreader individual will initially be the best solution.
        self.worst_superspreader = self.solution_type(self.domain, connector=self.domain.get_connector())

        # 5. Main strain sets: infected, superspreaders, infected superspreaders and deaths.
        self.infected:Set[Solution] = set()
        self.superspreaders:Set[Solution] = set()
        self.infected_superspreaders:Set[Solution] = set()
        self.dead:Set[Solution] = set()


    def initialize(self) -> None:

        # 1. Yield the patient zero (pz).
        pz:Solution = self.solution_type(self.domain, connector=self.domain.get_connector())
        pz.evaluate(self.fitness_function)
        self.verbosity(f'[{self.strain_properties.strain_id}, {threading.get_ident()}] Patient zero: {pz}')

        # 2. Add the patient zero to the strain-specific infected set.
        self.infected.add(pz)
        self.infected_superspreaders.add(pz)

        # 3. The best strain-specific individual will initially be the patient zero.
        self.best_solution = pz


    def iterate(self) -> None:

        # 1. Spreading the disease.
        self.propagate_disease()

        # 2. Stop if no new infected individuals.
        if not self.infected:
            self.epidemic = False
            self.verbosity(f'[{self.strain_properties.strain_id}, {threading.get_ident()}] No new infected individuals at {self.time}')

        # 3. Update the elapsed pandemic time.
        self.time += 1

        # 4. Update the base properties.
        self.current_iteration = self.time
        self.current_solutions = self.infected

    def stopping_criterion(self) -> bool:

        # When the strain is stopped?

        # First condition: When there are no infected individuals
        first_condition:bool = self.epidemic == False

        # Second condition: When the pandemic duration has been reached
        second_condition:bool = self.time > self.strain_properties.pandemic_duration

        # Third condition: When the best individual has been found and the time is greater than 1
        third_condition = self.best_founded and self.time > 1

        return first_condition or second_condition or third_condition

    def post_execution(self) -> None:
        self.verbosity(f'[{self.strain_properties.strain_id}, {threading.get_ident()}] Converged after {self.time} iterations with best individual: {self.best_solution}')
        super().post_execution()

    def propagate_disease(self) -> None:
        """ It spreads the disease through the individuals of the population.
        """

        # 1. Initialize the new infected population set
        new_infected_population:Set[Solution] = set()

        # 2. Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        self.update_pandemic_global_state()

        # 3. For each infected individual in the strain:
        for individual in self.infected:

            # ** 3.1. Determine the travel distance and the number of infections **
            n_infected, travel_distance = self.compute_n_infected_travel_distance(individual)

            # ** 3.2. Infect the new individuals. **
            new_infected_population = self.infect_individuals(individual, travel_distance, n_infected)

        # 4. Then, add the best individual of the strain to the next population.
        new_infected_population.add(self.best_solution)

        self.verbosity(f'[{self.strain_properties.strain_id}, {threading.get_ident()}] Iteration #{self.time} - {self.r0_report(len(new_infected_population))}'
                       f'- Best strain individual: {self.best_solution} , Best global individual: {self.global_state.get_best_individual()} ')


        # 5. Update the infected strain population for the next iteration
        self.infected.clear()
        self.infected.update(new_infected_population)


    def compute_n_infected_travel_distance(self, individual: Solution) -> Tuple[int, int]:

        # ** 1. Determine the number of infections. **
        if individual in self.superspreaders:
            # If the current individual is superspreader the number of infected ones will be in
            # (MIN_SUPERSPREADING_RATE, MAX_SUPERSPREADING_RATE)
            n_infected = random.randint(self.strain_properties.min_superspreading_rate,
                                        self.strain_properties.max_superspreading_rate)
        else:
            # If the current individual is common the number of infected ones will be in
            # (0, MAX_SUPERSPREADING_RATE)
            n_infected = random.randint(0, self.strain_properties.spreading_rate)
            # n_infected = random.randint(0, self.__MAX_SUPERSPREADING_RATE)

        # ** 2. Determine the travel distance. **
        if random.random() < self.strain_properties.p_travel:
            # If the current individual is a traveler, the travel distance will be in
            # (0, number of variable defined in the problem)
            travel_distance = random.randint(0, len(self.domain.get_core().variable_list()))
        else:
            # Otherwise the travel distance will be 1.
            travel_distance = 1

        return n_infected, travel_distance


    def infect_individuals(self, carrier_individual: Solution, travel_distance: int, n_infected:int) -> Set[Solution]:

        infected_population:Set[Solution] = set()

        for _ in range(0, n_infected):

            # If the current disease time is not affected by the SOCIAL DISTANCING policy, the current
            # individual infects another with a travel distance (using infect), and it is added
            # to the newly infected population.
            if self.time < self.strain_properties.social_distancing:
                new_infected_individual = self.infect(carrier_individual, travel_distance)
                self.update_new_infected_population(infected_population, new_infected_individual)

            # After SOCIAL_DISTANCING iterations (when the SOCIAL DISTANCING policy is applied),
            # the current individual infects another with a travel distance of one (using infect) then,
            # the newly infected individual can be isolated or not.
            else:
                new_infected_individual = self.infect(carrier_individual, 1)
                if random.random() < self.strain_properties.p_isolation:
                    self.update_new_infected_population(infected_population, new_infected_individual)
                else:
                    # If the new individual is isolated, and update_isolated is true, this is sent to the
                    # Isolated population.
                    if self.update_isolated:
                        self.global_state.isolate_individual_conditional_state.remote(new_infected_individual,
                                                                                          IndividualState(True, True,
                                                                                                          True))
        return infected_population


    def update_new_infected_population(self, new_infected_population: Set[Solution],
                                       new_infected_individual: Solution) -> None:
        """ It updates the next infected population with a new infected individual.

        :param new_infected_population: The population of the next iteration.
        :param new_infected_individual: The new infected individual that will be inserted into the netx iteration set.
        :type new_infected_population: set of :py:class:`~metagen.framework.Solution`
        :type new_infected_individual: :py:class:`~metagen.framework.Solution`
        """

        # Get the global individual state.
        individual_state: IndividualState = self.global_state.get_individual_state(new_infected_individual)

        # If the new individual is not in global death and recovered sets, then insert it in the next population.
        if not individual_state.dead and not individual_state.recovered:
            new_infected_population.add(new_infected_individual)

        # If the new individual is in the global recovered set, then check if it can be reinfected with
        # p_reinfection. If it can be reinfected, insert it into the new population and remove it from the global
        # recovered set.
        elif individual_state.recovered:
            if random.random() < self.strain_properties.p_re_infection:
                new_infected_population.add(new_infected_individual)
                self.global_state.get_infected_again(new_infected_individual)


    def r0_report(self, new_infections: int) -> str:
        recovered = self.global_state.get_recovered_len()
        r0 = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "\tNew infected = " + str(new_infections) + ", Recovered = " + str(recovered) + ", R0 = " + str(r0)
        return report

    def infect(self, individual: Solution, travel_distance:int) -> Solution:
        """ The individual infects another one located at a specific distance from it.

        :returns: The newly infected individual.
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        infected = copy.deepcopy(individual)
        infected.mutate(travel_distance)
        infected.evaluate(self.fitness_function)
        return infected


    def update_pandemic_global_state(self) -> None:
        """ It updates the specific strain death and superspreader's sets and the global death and recovered sets.
        """

        # A percentage, p_superspreader, of the infected individuals in the strain (infected) will be superspreaders.
        number_of_super_spreaders = math.ceil(self.strain_properties.p_superspreader * len(self.infected))

        # A percentage, p_die, of the infected individuals in the strain (infected) will die.
        number_of_deaths = math.ceil(self.strain_properties.p_die * len(self.infected))

        # If there are at least two infected individuals in the strain:
        # TODO: lo cambio a >= 1 (!=1 puede lanzar excepción)
        if len(self.infected) >= 1:

            # For each infected individual:
            for individual in self.infected:

                # Insert the current individual into superspreader set; if the insertion was successful, decrement
                # the superspreader's counter.
                if self.insert_into_set_strain(self.superspreaders, individual, number_of_super_spreaders, "s"):
                    number_of_super_spreaders -= 1

                # Update the recovered and death sets.
                if self.update_recovered_death_strain(individual, number_of_deaths):
                    number_of_deaths -= 1

                # If the current individual is better than the current global one, a new global best individual is
                # found, and its global variable is updated.
                if individual.get_fitness() < self.global_state.get_best_individual().get_fitness():
                    self.global_state.update_best_individual(individual)
                    self.best_founded = True
                    self.verbosity(f'[{self.strain_properties.strain_id}] New global best individual found at {self.time}! ({individual})')

                # If the current individual is better than the current strain one, a new strain the best individual is
                # found, and its variable is updated.
                if individual.get_fitness() < self.best_solution.get_fitness():
                    self.best_solution = individual

            # Update the global death set with the strain death set.
            self.global_state.update_deaths(self.dead)

        # Remove the global dead individuals from the global recovered set.
        self.global_state.update_recovered_with_deaths()

    def update_recovered_death_strain(self, to_insert: Solution, remaining:int) -> bool:
        """ It updates the specific strain death set and the global recovered set.

        :param to_insert: The individual that has to be inserted in the death set.
        :param remaining: The number of individuals remaining to be added in the death set.
        :type to_insert: :py:class:`~metagen.framework.Solution`
        :type remaining: int
        :returns: True, if the individual has been successfully inserted in the death set; otherwise False.
        :rtype: bool
        """

        # Insert the current individual into death set; if the insertion was successful, the dead variable
        # will be set to True; otherwise False.
        dead = self.insert_into_set_strain(self.dead, to_insert, remaining, 'd')

        # If the current individual is not dead, it is added to the recovered set.
        if not dead:
            self.global_state.recover_if_not_dead(to_insert)

        return dead

    # TODO: Método muy chungo, tocar lo menos posible
    def insert_into_set_strain(self, bag: Set[Solution], to_insert:Solution, remaining:int, ty:str) -> bool:
        """ Insert an individual in the strain sets (death or superspreader).

        :param bag: The set where the individual has to be inserted.
        :param to_insert: The individual that has to be inserted.
        :param remaining: The number of individuals remaining to be added in the set.
        :param ty: The set where the individual will be inserted ('s' if it is the superspreader set, 'd' if it is the
        death set.
        :type bag: set of :py:class:`~metagen.framework.Solution`
        :type to_insert: :py:class:`~metagen.framework.Solution`
        :type remaining: int
        :type ty: str
        :returns: True, if the individual has been successfully inserted; otherwise False
        :rtype: bool
        """

        # Initialization of the returned value.
        inserted = False

        # If there are still individuals to be added to the set:
        if remaining > 0:
            # The individual is inserted and the returned value is True.
            bag.add(to_insert)
            inserted = True

            # The worst superspreader individual (in the case of an insertion in the superspreader set) or the best
            # death individual (in the case of an insertion in the death set) are updated considering the previous
            # insertion. That is for the efficient updating of strain sets.
            if ty == 's':
                if to_insert > self.worst_superspreader:
                    self.worst_superspreader = to_insert
            elif ty == 'd':
                if to_insert < self.best_dead:
                    self.best_dead = to_insert

        # If there are no individuals left to add to the set:
        else:

            # If the current individual is worse than the worst in the superspreader set, the current individual
            # replaces the worst. This operation ensures that the worst new individual will be a superspreader.
            # This action adds more diversification to the metaheuristic.
            if ty == 's':
                if to_insert > self.worst_superspreader:
                    if self.worst_superspreader in bag:
                        bag.remove(self.worst_superspreader)
                    bag.add(to_insert)
                    inserted = True
                    self.worst_superspreader = to_insert

            # If the current individual is better than the best in the death set, the current individual
            # replaces the best. This operation ensures that the best new individual will be death.
            # This action adds more diversification to the metaheuristic.
            elif ty == 'd':
                if to_insert < self.best_dead:
                    logging.debug("bag: %s", str(bag))
                    logging.debug("__bestDeadIndividualStrain: %s",
                                  str(self.best_dead))
                    logging.debug("contains?: %s", str(
                        self.best_dead in bag))

                    bag.remove(self.best_dead)
                    bag.add(to_insert)
                    inserted = True
                    self.best_dead = to_insert

        return inserted


    def __str__(self):
        """ String representation of a :py:class:`~metagen.metaheuristics.CVOA` object (a strain).
        """
        res = ""
        res += self.strain_properties.strain_id + "\n"
        res += "Max time = " + str(self.strain_properties.pandemic_duration) + "\n"
        res += "Infected strain = " + str(self.infected) + "\n"
        res += "Super spreader strain = " + \
               str(self.superspreaders) + "\n"
        res += "Death strain = " + str(self.dead) + "\n"
        res += "MAX_SPREAD = " + str(self.strain_properties.spreading_rate) + "\n"
        res += "MIN_SUPERSPREAD = " + \
               str(self.strain_properties.min_superspreading_rate) + "\n"
        res += "MAX_SUPERSPREAD = " + \
               str(self.strain_properties.max_superspreading_rate) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.strain_properties.social_distancing) + "\n"
        res += "P_ISOLATION = " + str(self.strain_properties.p_isolation) + "\n"
        res += "P_TRAVEL = " + str(self.strain_properties.p_travel) + "\n"
        res += "P_REINFECTION = " + str(self.strain_properties.p_re_infection) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.strain_properties.p_superspreader) + "\n"
        res += "DEATH_PERC = " + str(self.strain_properties.p_die) + "\n"
        return res



def run_strain(global_state, domain:Domain, fitness_function: Callable[[Solution],float], strain_properties:StrainProperties,
               verbose:bool=True, update_isolated:bool=False, log_dir:str="logs/CVOA") -> Solution:
    strain = CVOA(global_state, domain,fitness_function, strain_properties, verbose, update_isolated, log_dir)
    return strain.run()



def cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                  verbose: bool = True, update_isolated: bool = False, log_dir: str = "logs/CVOA") -> Solution:


    # Initialize the global state
    solution_type: type[SolutionClass] = domain.get_connector().get_type(domain.get_core())
    global_state = PandemicState(solution_type(domain, connector=domain.get_connector()))

    t1 = time()
    with ThreadPoolExecutor(max_workers=len(strains)) as executor:
        futures = {strain.strain_id: executor.submit(run_strain, global_state, domain, fitness_function, strain, verbose, update_isolated, log_dir) for strain in strains}
    t2 = time()

    print("\n********** Results by strain **********")
    for strain_id, future in futures.items():
        print("[" + strain_id + "] Best individual: " + str(future.result()))

    print("\n********** Best result **********")
    best_solution = global_state.get_best_individual()
    print("Best individual: " + str(best_solution))

    print("\n********** Pandemic report **********")
    print("Pandemic report: " + str(global_state.get_pandemic_report()))

    print("\n********** Performance **********")
    print("Execution time: " + str(timedelta(milliseconds=t2 - t1)))


    return best_solution
