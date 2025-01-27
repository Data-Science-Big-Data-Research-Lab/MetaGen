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
from datetime import timedelta
from time import time
from typing import Callable, Set, List, Type, NamedTuple, Tuple

import ray

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.framework.solution.bounds import SolutionClass
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.distributed_tools import IndividualState, PandemicState, StrainProperties, \
    distributed_cvoa_new_infected_population


class DistributedCVOA(Metaheuristic):
    """
    Distributed Coronavirus Optimization Algorithm (CVOA) for optimization problems.

    This class implements a distributed version of the CVOA algorithm which models the spread
    of a virus in a population to solve optimization problems. It uses Ray for distributed
    computing and supports multiple virus strains running in parallel.

    The algorithm models:
    - Infection spread between solutions
    - Super-spreader events
    - Social distancing effects
    - Recovery and death of solutions
    - Travel between different regions of the search space

    :param global_state: The global state of the pandemic
    :type global_state: PandemicState
    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties defining the virus strain behavior
    :type strain_properties: StrainProperties
    :param verbose: Verbosity option, defaults to True
    :type verbose: bool, optional
    :param update_isolated: Whether to update isolated solutions, defaults to False
    :type update_isolated: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/DCVOA"
    :type log_dir: str, optional

    :ivar strain_properties: Properties of the virus strain
    :vartype strain_properties: StrainProperties
    :ivar global_state: Distributed state tracking pandemic progression
    :vartype global_state: PandemicState
    :ivar superspreaders: Set of solutions identified as superspreaders
    :vartype superspreaders: Set[Solution]
    :ivar time: Current iteration in the pandemic simulation
    :vartype time: int

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics.cvoa import DistributedCVOA, StrainProperties
        
        # Define the problem domain
        domain = Domain()
        domain.defineInteger(0, 1)
        
        # Define the fitness function
        fitness_function = ...

        # Configure virus strain properties
        strain = StrainProperties(
            strain_id="Strain1",
            pandemic_duration=100,
            spreading_rate=6,
            min_superspreading_rate=6,
            max_superspreading_rate=15,
            social_distancing=10,
            p_isolation=0.7,
            p_travel=0.1,
            p_re_infection=0.0014,
            p_superspreader=0.1,
            p_die=0.05
        )

        # Create and run the algorithm
        algorithm = DistributedCVOA(global_state, domain, fitness_function, strain_properties=strain)
        optimal_solution = algorithm.run()
    """

    def __init__(self, global_state, domain: Domain, fitness_function: Callable[[Solution], float],
                 strain_properties: StrainProperties = StrainProperties(), verbose=True, update_isolated=False,
                 log_dir="logs/DCVOA"):

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
        self.epidemic: bool = True

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
        self.infected: Set[Solution] = set()
        self.superspreaders: Set[Solution] = set()
        self.infected_superspreaders: Set[Solution] = set()
        self.dead: Set[Solution] = set()


    def initialize(self) -> None:
        """
        Initialize the pandemic simulation with a random solution.

        Creates an initial population of solutions and identifies potential superspreaders
        based on the strain properties.

        :return: None
        """

        # 1. Yield the patient zero (pz).
        pz: Solution = self.solution_type(self.domain, connector=self.domain.get_connector())
        pz.evaluate(self.fitness_function)
        self.verbosity(f'[{self.strain_properties.strain_id}] Patient zero: {pz}')

        # 2. Add the patient zero to the strain-specific infected set.
        self.infected.add(pz)
        self.infected_superspreaders.add(pz)

        # 3. The best strain-specific individual will initially be the patient zero.
        self.best_solution = pz


    def iterate(self) -> None:
        """
        Execute one iteration of the pandemic simulation.

        In each iteration:
        1. New infections are spread through the population
        2. Some solutions may recover or die
        3. Superspreader events may occur
        4. Solutions may travel to new regions

        :return: None
        """

        # 1. Spreading the disease.
        self.propagate_disease()

        # 2. Stop if no new infected individuals.
        if not self.infected:
            self.epidemic = False
            self.verbosity(f'[{self.strain_properties.strain_id}] No new infected individuals at {self.time}')

        # 3. Update the elapsed pandemic time.
        self.time += 1

        # 4. Update the base properties.
        self.current_iteration = self.time
        self.current_solutions = self.infected


    def stopping_criterion(self) -> bool:
        """
        Check if the pandemic simulation should stop.

        The simulation stops when the current time reaches the pandemic duration
        specified in the strain properties.

        :return: True if the pandemic duration is reached, False otherwise
        :rtype: bool
        """

        # When the strain is stopped?

        # First condition: When there are no infected individuals
        first_condition: bool = self.epidemic == False

        # Second condition: When the pandemic duration has been reached
        second_condition: bool = self.time > self.strain_properties.pandemic_duration

        # Third condition: When the best individual has been found and the time is greater than 1
        third_condition = self.best_founded and self.time > 1

        return first_condition or second_condition or third_condition


    def post_execution(self) -> None:
        """
        Post-execution processing.

        :return: None
        """
        self.verbosity(f'[{self.strain_properties.strain_id}] Converged after {self.time} iterations with best individual: {self.best_solution}')
        super().post_execution()


    def propagate_disease(self) -> None:
        """
        Spread the disease through the individuals of the population.

        :return: None
        """

        # 1. Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        self.update_pandemic_global_state()

        # 2. Initialize the new infected population distributed.
        new_infected_population = distributed_cvoa_new_infected_population(self.global_state, self.domain, self.fitness_function, self.strain_properties,
                                                                           self.infected, self.superspreaders, self.time, self.update_isolated)

        # 3. Then, add the best individual of the strain to the next population.
        new_infected_population.add(self.best_solution)

        self.verbosity(f'[{self.strain_properties.strain_id}] Iteration #{self.time} - {self.r0_report(len(new_infected_population))}'
                       f'- Best strain individual: {self.best_solution} , Best global individual: {ray.get(self.global_state.get_best_individual.remote())} ')

        # 5. Update the infected strain population for the next iteration
        self.infected.clear()
        self.infected.update(new_infected_population)


    def compute_n_infected_travel_distance(self, individual: Solution) -> Tuple[int, int]:
        """
        Compute the number of infected individuals and travel distance for a given solution.

        :param individual: The solution to compute the number of infected individuals and travel distance for
        :type individual: Solution
        :return: A tuple containing the number of infected individuals and travel distance
        :rtype: Tuple[int, int]
        """

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
            # n_infected = rs.randint(0, self.__MAX_SUPERSPREADING_RATE)

        # ** 2. Determine the travel distance. **
        if random.random() < self.strain_properties.p_travel:
            # If the current individual is a traveler, the travel distance will be in
            # (0, number of variable defined in the problem)
            travel_distance = random.randint(0, len(self.domain.get_core().variable_list()))
        else:
            # Otherwise the travel distance will be 1.
            travel_distance = 1

        return n_infected, travel_distance


    def infect_individuals(self, carrier_individual: Solution, travel_distance: int, n_infected: int) -> Set[Solution]:
        """
        Infect new individuals based on the carrier individual and travel distance.

        :param carrier_individual: The individual that will infect new individuals
        :type carrier_individual: Solution
        :param travel_distance: The distance that the new individuals will be infected
        :type travel_distance: int
        :param n_infected: The number of new individuals to infect
        :type n_infected: int
        :return: A set of newly infected individuals
        :rtype: Set[Solution]
        """

        infected_population: Set[Solution] = set()

        for _ in range(0, n_infected):

            # If the current disease time is not affected by the social_distancing policy, the current
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
                        ray.remote(
                            self.global_state.isolate_individual_conditional_state.remote(new_infected_individual,
                                                                                          IndividualState(True, True,
                                                                                                          True)))


        return infected_population


    def update_new_infected_population(self, new_infected_population: Set[Solution],
                                       new_infected_individual: Solution) -> None:
        """
        Update the newly infected population with a new individual.

        :param new_infected_population: The newly infected population
        :type new_infected_population: Set[Solution]
        :param new_infected_individual: The new individual to add to the population
        :type new_infected_individual: Solution
        :return: None
        """

        # Get the global individual state.
        individual_state: IndividualState = ray.get(
            self.global_state.get_individual_state.remote(new_infected_individual))

        # If the new individual is not in global death and recovered sets, then insert it in the next population.
        if not individual_state.dead and not individual_state.recovered:
            new_infected_population.add(new_infected_individual)

        # If the new individual is in the global recovered set, then check if it can be reinfected with
        # p_reinfection. If it can be reinfected, insert it into the new population and remove it from the global
        # recovered set.
        elif individual_state.recovered:
            if random.random() < self.strain_properties.p_re_infection:
                new_infected_population.add(new_infected_individual)
                ray.get(self.global_state.get_infected_again.remote(new_infected_individual))


    def r0_report(self, new_infections: int) -> str:
        """
        Generate a report on the current R0 value.

        :param new_infections: The number of new infections
        :type new_infections: int
        :return: A string report on the current R0 value
        :rtype: str
        """

        recovered = ray.get(self.global_state.get_recovered_len.remote())
        r0 = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "\tNew infected = " + str(new_infections) + ", Recovered = " + str(recovered) + ", R0 = " + str(r0)
        return report


    def infect(self, individual: Solution, travel_distance: int) -> Solution:
        """
        Infect a new individual based on the given individual and travel distance.

        :param individual: The individual that will infect a new individual
        :type individual: Solution
        :param travel_distance: The distance that the new individual will be infected
        :type travel_distance: int
        :return: The newly infected individual
        :rtype: Solution
        """

        infected = copy.deepcopy(individual)
        infected.mutate(travel_distance)
        infected.evaluate(self.fitness_function)
        return infected


    def update_pandemic_global_state(self) -> None:
        """
        Update the pandemic global state.

        :return: None
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
                if individual.get_fitness() < ray.get(self.global_state.get_best_individual.remote()).get_fitness():
                    ray.get(self.global_state.update_best_individual.remote(individual))
                    self.best_founded = True
                    self.verbosity(f'[{self.strain_properties.strain_id}] New global best individual found at {self.time}! ({individual})')

                # If the current individual is better than the current strain one, a new strain the best individual is
                # found, and its variable is updated.
                if individual.get_fitness() < self.best_solution.get_fitness():
                    self.best_solution = individual

            # Update the global death set with the strain death set.
            ray.get(self.global_state.update_deaths.remote(self.dead))

        # Remove the global dead individuals from the global recovered set.
        ray.get(self.global_state.update_recovered_with_deaths.remote())


    def update_recovered_death_strain(self, to_insert: Solution, remaining: int) -> bool:
        """
        Update the recovered and death sets for the strain.

        :param to_insert: The individual to insert into the recovered or death set
        :type to_insert: Solution
        :param remaining: The number of individuals remaining to insert
        :type remaining: int
        :return: True if the individual was inserted, False otherwise
        :rtype: bool
        """

        # Insert the current individual into death set; if the insertion was successful, the dead variable
        # will be set to True; otherwise False.
        dead = self.insert_into_set_strain(self.dead, to_insert, remaining, 'd')

        # If the current individual is not dead, it is added to the recovered set.
        if not dead:
            ray.get(self.global_state.recover_if_not_dead.remote(to_insert))

        return dead


    # TODO: Método muy chungo, tocar lo menos posible
    def insert_into_set_strain(self, bag: Set[Solution], to_insert: Solution, remaining: int, ty: str) -> bool:
        """
        Insert an individual into a set for the strain.

        :param bag: The set to insert the individual into
        :type bag: Set[Solution]
        :param to_insert: The individual to insert
        :type to_insert: Solution
        :param remaining: The number of individuals remaining to insert
        :type remaining: int
        :param ty: The type of set to insert into ('s' for superspreaders, 'd' for deaths)
        :type ty: str
        :return: True if the individual was inserted, False otherwise
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


    def post_iteration(self) -> None:
        """
        Post-iteration processing.

        :return: None
        """
        super().post_iteration()
        print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('DCVOA/Population Size',
                               len(self.current_solutions),
                               self.current_iteration)


    def __str__(self):
        """
        String representation of a DistributedCVOA object.

        :return: A string representation of the object
        :rtype: str
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


@ray.remote
def run_strain(global_state, domain: Domain, fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
               verbose: bool = True, update_isolated: bool = False, log_dir: str = "logs/CVOA") -> Solution:
    """
    Run a strain of the Distributed CVOA algorithm.

    :param global_state: The global state of the pandemic
    :type global_state: PandemicState
    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties defining the virus strain behavior
    :type strain_properties: StrainProperties
    :param verbose: Verbosity option, defaults to True
    :type verbose: bool, optional
    :param update_isolated: Whether to update isolated solutions, defaults to False
    :type update_isolated: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/CVOA"
    :type log_dir: str, optional
    :return: The best solution found by the strain
    :rtype: Solution
    """

    strain = DistributedCVOA(global_state, domain, fitness_function, strain_properties, verbose, update_isolated, log_dir)
    return strain.run()


def cvoa_launcher(strains: List[StrainProperties], domain: Domain, fitness_function: Callable[[Solution], float],
                  verbose: bool = True, update_isolated: bool = False, log_dir: str = "logs/DCVOA") -> Solution:
    """
    Launch the Distributed CVOA algorithm with multiple strains.

    :param strains: List of strain properties
    :type strains: List[StrainProperties]
    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param verbose: Verbosity option, defaults to True
    :type verbose: bool, optional
    :param update_isolated: Whether to update isolated solutions, defaults to False
    :type update_isolated: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/DCVOA"
    :type log_dir: str, optional
    :return: The best solution found by the algorithm
    :rtype: Solution
    """

    # Initialize Ray
    if not ray.is_initialized():
        ray.init()

    # Initialize the global state
    solution_type: type[SolutionClass] = domain.get_connector().get_type(domain.get_core())
    global_state = PandemicState.remote(solution_type(domain, connector=domain.get_connector()))

    t1 = time()
    futures = [run_strain.remote(global_state, domain, fitness_function, strain_properties, verbose, update_isolated, log_dir) for strain_properties in strains]
    results = ray.get(futures)
    t2 = time()

    print("\n********** Results by strain **********")
    i = 0
    for result in results:
        print("[" + strains[i].strain_id + "] Best individual: " + str(result))
        i += 1

    print("\n********** Best result **********")
    best_solution = ray.get(global_state.get_best_individual.remote())
    print("Best individual: " + str(best_solution))

    print("\n********** Pandemic report **********")
    print("Pandemic report: " + str(ray.get(global_state.get_pandemic_report.remote())))

    print("\n********** Performance **********")
    print("Execution time: " + str(timedelta(milliseconds=t2 - t1)))

    return best_solution
