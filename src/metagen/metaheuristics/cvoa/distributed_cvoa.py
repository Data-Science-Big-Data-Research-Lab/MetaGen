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
from typing import Callable, Set, List, Type

import ray
from ray.types import ObjectRef

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.framework.solution.bounds import SolutionClass
from metagen.metaheuristics.base import Metaheuristic


@ray.remote
class GlobalState:
    def __init__(self):
        self.recovered:Set[Solution] = set()
        self.deaths:Set[Solution] = set()
        self.isolated:Set[Solution] = set()
        self.best_individual_found:bool = False
        self.best_individual:Solution|None = None

    # Recovered

    def get_recovered_len(self) -> int:
        return len(self.recovered)

    def update_recovered(self, individual:Solution) -> None:
        self.recovered.add(individual)


    def different_uptade_recovered(self, individuals:Set[Solution]) -> None:
        self.recovered.difference_update(individuals)


    # Deaths
    def update_deaths(self, individuals:Set[Solution])-> None:
        self.deaths.update(individuals)

    def is_dead(self, individual:Solution) -> bool:
        return individual in self.deaths


    # Recovered and Deaths
    def update_recovered_with_deaths(self)-> None:
        self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual:Solution)-> None:
        if individual not in self.deaths:
            self.recovered.add(individual)


    # Isolated

    def update_isolated(self, individual:Solution)-> None:
        self.isolated.add(individual)

    def update_best_individual(self, individual:Solution) -> None:
        self.best_individual = individual

    def get_best_individual(self) -> Solution:
        return self.best_individual

    def is_best_individual_found(self) -> bool:
        return self.best_individual_found

    def update_best_individual_found(self, value:bool) -> None:
        self.best_individual_found = value


    def get_pandemic_report(self):
        return {
            "recovered": len(self.recovered),
            "deaths": len(self.deaths),
            "isolated": len(self.isolated),
            "best_individual": self.best_individual
        }


class DistributedCVOA(Metaheuristic):
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


    # If true, the isolated set is updated.
    __update_isolated: bool | None = None
    # If true show log messages.
    __verbosity: Callable[[str], None] | None = None

    def __init__(self, global_state, domain, fitness_function, strain_id="Strain 1", pandemic_duration=10, spreading_rate=5,
                 min_super_spreading_rate=6,
                 max_super_spreading_rate=15, social_distancing=7, p_isolation=0.5, p_travel=0.1,
                 p_re_infection=0.001, p_superspreader=0.1, p_die=0.05, verbose=True, update_isolated=False,
                 log_dir="logs/CVOA"):
        """ The constructor of the :py:class:`~metagen.metaheuristics.CVOA` class. It set the specific properties
        of a strain.
        """

        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.global_state = global_state

        # The best individual is initialized to the worst solution and the best individual condition
        # is initialized to false. It is a standard search scheme.
        DistributedCVOA.__update_isolated = update_isolated

        solution_type: type[SolutionClass] = domain.get_connector().get_type(domain.get_core())
        DistributedCVOA.__bestIndividual = solution_type(domain, connector=domain.get_connector())

        # Properties set by arguments.
        self.__strainID = strain_id
        self.__pandemic_duration = pandemic_duration
        self.__SPREADING_RATE = spreading_rate
        self.__MIN_SUPERSPREADING_RATE = min_super_spreading_rate
        self.__MAX_SUPERSPREADING_RATE = max_super_spreading_rate
        self.__SOCIAL_DISTANCING = social_distancing
        self.__P_ISOLATION = p_isolation
        self.__P_TRAVEL = p_travel
        self.__P_REINFECTION = p_re_infection
        self.__P_SUPERSPREADER = p_superspreader
        self.__P_DIE = p_die

        # Main strain sets: infected, superspreaders, infected superspreaders and deaths.
        self.__infectedStrain:Set[Solution] = set()
        self.__superSpreaderStrain:Set[Solution] = set()
        self.__infected_strain_super_spreader_strain:Set[Solution] = set()
        self.__deathStrain:Set[Solution] = set()

        # Other specific properties:
        # Iteration counter.
        self.__time = None
        self.solution_type: type[SolutionClass] = self.domain.get_connector().get_type(self.domain.get_core())
        # Best strain individual. It is initialized to the worst solution.
        self.best_solution = self.solution_type(self.domain, connector=self.domain.get_connector())

        # Best dead individual and worst superspreader individuals. For debug and pandemic analysis purposes.
        # They are initialized to None.
        self.__bestDeadIndividualStrain = None
        self.__worstSuperSpreaderIndividualStrain = None

        self.epidemic = True

        self.set_verbosity(verbose)

    @staticmethod
    def set_verbosity(verbose) -> None:
        """ It sets the verbosity of the **CVOA** algorithm execution. If True, when the
        :py:meth:`~metagen.metaheuristics.CVOA.cvoa` method is running, messages about the status of the pandemic
        will be shown in the standard output console.

        :param verbose: The verbosity option
        :type verbose: bool
        """
        DistributedCVOA.__verbosity = \
            print if verbose else lambda *a, **k: None

    def get_strain_id(self) -> str:
        """ It returns the identification of the strain.

        :returns: The identification of the strain.
        :rtype: str
        """
        return self.__strainID

    def initialize(self) -> None:
        pz = self.__infect_pz()
        DistributedCVOA.__verbosity(
            "\nPatient Zero (" + self.__strainID + "): \n" + str(pz))

        # Initialize strain:
        # Add the patient zero to the strain-specific infected set.
        self.__infectedStrain.add(pz)
        self.__infected_strain_super_spreader_strain.add(pz)
        # The best strain-specific individual will initially be the patient zero.
        self.best_solution = pz
        # The worst strain-specific superspreader individual will initially be the best solution.
        self.__worstSuperSpreaderIndividualStrain = self.solution_type(self.domain, connector=self.domain.get_connector())
        # The best strain-specific death individual will initially be the worst solution.
        self.__bestDeadIndividualStrain = self.solution_type(self.domain, connector=self.domain.get_connector())

        # Logical condition to ctrl the epidemic (main iteration).
        # If True, the iteration continues.
        # When there are no infected individuals, the epidemic finishes.
        self.epidemic = True

        # The iteration counter will be initially set to 0.
        self.__time = 0

    def iterate(self) -> None:
        # ***** STEP 2. SPREADING THE DISEASE. *****
        self.__propagate_disease()

        # ***** STEP 4. STOP CRITERION. *****
        # Stop if no new infected individuals.
        if not self.__infectedStrain:
            self.epidemic = False
            DistributedCVOA.__verbosity(
                "No new infected individuals in " + self.__strainID)

        # Update the elapsed pandemic time.
        self.__time += 1

    def stopping_criterion(self) -> bool:
        return not self.epidemic or self.__time > self.__pandemic_duration or ray.get(self.global_state.is_best_individual_found())

    def after_execution(self) -> None:
        DistributedCVOA.__verbosity("\n\n" + self.__strainID +
                         " converged after " + str(self.__time) + " iterations.")
        DistributedCVOA.__verbosity("Best individual: " +
                                    str(self.best_solution))

    def __propagate_disease(self) -> None:
        """ It spreads the disease through the individuals of the population.
        """
        # Initialize the new infected population set and the travel distance.
        # Each new infected individual will be added to this set.
        new_infected_population = set()
        travel_distance = 1

        # Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        # Then, add the best individual of the strain to the next population.
        self.__update_strain_global_sets()
        new_infected_population.add(self.best_solution)

        # For each infected individual in the strain:
        for individual in self.__infectedStrain:

            # ** 1. Determine the number of infections. **
            # If the current individual is superspreader the number of infected ones will be in
            # (MIN_SUPERSPREADING_RATE, MAX_SUPERSPREADING_RATE).
            # If the current individual is common the number of infected ones will be in
            # (0, MAX_SUPERSPREADING_RATE).
            if individual in self.__superSpreaderStrain:
                n_infected = random.randint(
                    self.__MIN_SUPERSPREADING_RATE, self.__MAX_SUPERSPREADING_RATE)
            else:
                n_infected = random.randint(0, self.__SPREADING_RATE)
                # n_infected = random.randint(0, self.__MAX_SUPERSPREADING_RATE)

            # ** 2. Determine the travel distance. **
            # If the current individual is a traveler, the travel distance will be in
            # (0, number of variable defined in the problem), otherwise the travel distance will be 1.
            if random.random() < self.__P_TRAVEL:
                travel_distance = random.randint(
                    0, len(self.domain.get_core().variable_list()))

            # ** 3. Infect the new individuals. **
            # For each n_infected new individuals:
            for _ in range(0, n_infected):
                # If the current disease time is not affected by the SOCIAL DISTANCING policy, the current
                # individual infects another with a travel distance (using __infect), and it is added
                # to the newly infected population.
                if self.__time < self.__SOCIAL_DISTANCING:
                    new_infected_individual = self.__infect(individual, travel_distance)
                    self.__update_new_infected_population(new_infected_population, new_infected_individual)

                # After SOCIAL_DISTANCING iterations (when the SOCIAL DISTANCING policy is applied),
                # the current individual infects another with a travel distance of one (using __infect) then,
                # the newly infected individual can be isolated or not.
                else:
                    new_infected_individual = self.__infect(individual, 1)
                    if random.random() < self.__P_ISOLATION:
                        self.__update_new_infected_population(new_infected_population, new_infected_individual)
                    else:
                        # If the new individual is isolated, and __update_isolated is true, this is sent to the
                        # __update_isolated_population.
                        if DistributedCVOA.__update_isolated:
                            self.__update_isolated_population(individual)

        # Just one print to ensure it is printed without interfering with other threads
        DistributedCVOA.__verbosity(
                          "\n[" + self.__strainID + "] - Iteration #" + str(self.__time + 1) +
                         "\n\tBest global individual: " +
                                    str(ray.get(self.global_state.get_best_individual.remote()))
                                    + "\n\tBest strain individual: " +
                                    str(self.best_solution)
                                    + "\n" + self.__r0_report(len(new_infected_population)))
        # + "\n\tR0 = " + str(len(new_infected_population) / len(self.__infectedStrain)))

        # Update the infected strain population for the next iteration
        self.__infectedStrain.clear()
        self.__infectedStrain.update(new_infected_population)

    # @staticmethod
    def __infect_pz(self) -> Solution:
        """ It builds the *patient zero*, **PZ**, for the **CVOA** algorithm.

        :returns: The *patient zero*, **PZ**
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        patient_zero:Solution = self.solution_type(self.domain, connector=self.domain.get_connector())
        patient_zero.evaluate(self.fitness_function)
        return patient_zero

    def __r0_report(self, new_infections: int):
        recovered = ray.get(self.global_state.get_recovered_len.remote())
        r0 = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "\tNew infected = " + \
                 str(new_infections) + ", Recovered = " + \
                 str(recovered) + ", R0 = " + str(r0)
        return report

    @staticmethod
    def __infect(individual, travel_distance, fitness_function):
        """ The individual infects another one located at a specific distance from it.

        :returns: The newly infected individual.
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        infected = copy.deepcopy(individual)
        infected.mutate(travel_distance)
        infected.evaluate(fitness_function)
        return infected

    def __update_strain_global_sets(self):
        """ It updates the specific strain death and superspreader's sets and the global death and recovered sets.
        """

        # A percentage,__P_SUPERSPREADER, of the infected individuals in the strain (__infectedStrain)
        # will be superspreaders.
        # A percentage, __P_DIE, of the infected individuals in the strain (__infectedStrain)
        # will die.
        number_of_super_spreaders = math.ceil(
            self.__P_SUPERSPREADER * len(self.__infectedStrain))
        number_of_deaths = math.ceil(self.__P_DIE * len(self.__infectedStrain))
        # If there are at least two infected individuals in the strain:
        # TODO: lo cambio a >= 1 (!=1 puede lanzar excepción)
        if len(self.__infectedStrain) >= 1:

            # For each infected individual:
            for individual in self.__infectedStrain:

                # Insert the current individual into superspreader set; if the insertion was successful, decrement
                # the superspreader's counter.
                if self.__insert_into_set_strain(self.__superSpreaderStrain, individual, number_of_super_spreaders,
                                                 "s"):
                    number_of_super_spreaders -= 1

                # Update the recovered and death sets.
                if self.__update_recovered_death_strain(individual, number_of_deaths):
                    number_of_deaths -= 1

                # If the current individual is better than the current global one, a new global best individual is
                # found, and its global variable is updated.
                if individual.get_fitness() < ray.get(self.global_state.get_best_individual.remote()).get_fitness():
                    ray.get(self.global_state.update_best_individual.remote(individual))
                    print(individual)
                    DistributedCVOA.__verbosity("\nNew best Individual found by " + self.__strainID + "!")
                # If the current individual is better than the current strain one, a new strain the best individual is
                # found, and its variable is updated.
                if individual.get_fitness() < self.best_solution.get_fitness():
                    self.best_solution = individual

            # Update the global death set with the strain death set.
            ray.get(self.global_state.update_deaths.remote(self.__deathStrain))

        # Remove the global dead individuals from the global recovered set.
        ray.get(self.global_state.update_recovered_with_deaths.remote())

    def __update_recovered_death_strain(self, to_insert, remaining) -> bool:
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
        dead = self.__insert_into_set_strain(self.__deathStrain, to_insert, remaining, 'd')

        # If the current individual is not dead, it is added to the recovered set.
        if not dead:
            ray.get(self.global_state.recover_if_not_dead.remote(to_insert))

        return dead

    def __insert_into_set_strain(self, bag, to_insert, remaining, ty) -> bool:
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
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    self.__worstSuperSpreaderIndividualStrain = to_insert
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    self.__bestDeadIndividualStrain = to_insert

        # If there are no individuals left to add to the set:
        else:

            # If the current individual is worse than the worst in the superspreader set, the current individual
            # replaces the worst. This operation ensures that the worst new individual will be a superspreader.
            # This action adds more diversification to the metaheuristic.
            if ty == 's':
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    if self.__worstSuperSpreaderIndividualStrain in bag:
                        bag.remove(self.__worstSuperSpreaderIndividualStrain)
                    bag.add(to_insert)
                    inserted = True
                    self.__worstSuperSpreaderIndividualStrain = to_insert

            # If the current individual is better than the best in the death set, the current individual
            # replaces the best. This operation ensures that the best new individual will be death.
            # This action adds more diversification to the metaheuristic.
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    logging.debug("bag: %s", str(bag))
                    logging.debug("__bestDeadIndividualStrain: %s",
                                  str(self.__bestDeadIndividualStrain))
                    logging.debug("contains?: %s", str(
                        self.__bestDeadIndividualStrain in bag))

                    bag.remove(self.__bestDeadIndividualStrain)
                    bag.add(to_insert)
                    inserted = True
                    self.__bestDeadIndividualStrain = to_insert

        return inserted

    def __update_new_infected_population(self, new_infected_population, new_infected_individual):
        """ It updates the next infected population with a new infected individual.

        :param new_infected_population: The population of the next iteration.
        :param new_infected_individual: The new infected individual that will be inserted into the netx iteration set.
        :type new_infected_population: set of :py:class:`~metagen.framework.Solution`
        :type new_infected_individual: :py:class:`~metagen.framework.Solution`
        """

        # If the new individual is not in global death and recovered sets, then insert it in the next population.
        if new_infected_individual not in DistributedCVOA.__deaths and new_infected_individual not in DistributedCVOA.__recovered:
            new_infected_population.add(new_infected_individual)

        # If the new individual is in the global recovered set, then check if it can be reinfected with
        # __P_REINFECTION. If it can be reinfected, insert it into the new population and remove it from the global
        # recovered set.
        elif new_infected_individual in DistributedCVOA.__recovered:
            if random.random() < self.__P_REINFECTION:
                new_infected_population.add(new_infected_individual)
                DistributedCVOA.__lock.acquire()
                DistributedCVOA.__recovered.remove(new_infected_individual)
                DistributedCVOA.__lock.release()

    @staticmethod
    def __update_isolated_population(individual):
        """ It updates the global isolated set with an individual.

        :param individual: The individual that will be inserted into the global isolated set.
        :type individual: :py:class:`~metagen.framework.Solution`
        """

        # If the individual is not in global death, recovered and isolation sets, then insert it in the isolated set.
        if individual not in DistributedCVOA.__deaths and individual not in DistributedCVOA.__recovered and individual not in DistributedCVOA.__isolated:
            DistributedCVOA.__lock.acquire()
            DistributedCVOA.__isolated.add(individual)
            DistributedCVOA.__lock.release()

    def __str__(self):
        """ String representation of a :py:class:`~metagen.metaheuristics.CVOA` object (a strain).
        """
        res = ""
        res += self.__strainID + "\n"
        res += "Max time = " + str(self.__pandemic_duration) + "\n"
        res += "Infected strain = " + str(self.__infectedStrain) + "\n"
        res += "Super spreader strain = " + \
               str(self.__superSpreaderStrain) + "\n"
        res += "Death strain = " + str(self.__deathStrain) + "\n"
        res += "MAX_SPREAD = " + str(self.__SPREADING_RATE) + "\n"
        res += "MIN_SUPERSPREAD = " + \
               str(self.__MIN_SUPERSPREADING_RATE) + "\n"
        res += "MAX_SUPERSPREAD = " + \
               str(self.__MAX_SUPERSPREADING_RATE) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.__SOCIAL_DISTANCING) + "\n"
        res += "P_ISOLATION = " + str(self.__P_ISOLATION) + "\n"
        res += "P_TRAVEL = " + str(self.__P_TRAVEL) + "\n"
        res += "P_REINFECTION = " + str(self.__P_REINFECTION) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.__P_SUPERSPREADER) + "\n"
        res += "DEATH_PERC = " + str(self.__P_DIE) + "\n"
        return res


@ray.remote
def run_strain(strain:DistributedCVOA):
    return strain.run()

def cvoa_launcher(strains:List[DistributedCVOA], verbose=True) -> Solution:

    DistributedCVOA.set_verbosity(verbose)

    # Inicializar Ray
    if not ray.is_initialized():
        ray.init()

    # Inicializar el estado global
    global_state = GlobalState.remote()
    solution_type: type[SolutionClass] = strains[0].domain.get_connector().get_type(strains[0].domain.get_core())
    ray.get(global_state.update_best_individual.remote(
        solution_type(strains[0].domain, connector=strains[0].domain.get_connector())))

    t1 = time()
    futures = [run_strain.remote(strain) for strain in strains]
    results = ray.get(futures)
    t2 = time()

    print("\n********** Results by strain **********")
    for strain, result in zip(strains, results):
        print("[" + strain.get_strain_id() + "] Best individual: " + str(result))

    print("\n********** Best result **********")
    best_solution = ray.get(global_state.get_best_individual.remote())
    print("Best individual: " + str(best_solution))

    print("\n********** Performance **********")
    print("Execution time: " + str(timedelta(milliseconds=t2 - t1)))
    print(ray.get(global_state.get_pandemic_report.remote()))

    return best_solution
