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

import math
import random
from typing import Callable, Set, List, Tuple

import ray

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.framework.solution.bounds import SolutionClass
from metagen.logging.metagen_logger import get_metagen_logger, set_metagen_logger_level_console_output, DETAILED_INFO
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.cvoa.common_tools import StrainProperties, IndividualState, insert_into_set_strain, infect
from metagen.metaheuristics.cvoa.distributed_tools import distributed_cvoa_new_infected_population, RemotePandemicState


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

   """

    def __init__(self, global_state: RemotePandemicState, domain: Domain, fitness_function: Callable[[Solution], float],
                 strain_properties: StrainProperties = StrainProperties(), update_isolated=False,
                 log_dir="logs/DCVOA"):

        get_metagen_logger(level=DETAILED_INFO,distributed=True)


        # 1. Initialize the base class.
        super().__init__(domain, fitness_function, log_dir=log_dir)

        # 2. The Pandemic global state and strain properties.
        self.global_state: RemotePandemicState = global_state
        self.strain_properties: StrainProperties = strain_properties

        # 3. Auxiliary strain control variables.
        self.update_isolated: bool = update_isolated
        self.solution_type: type[SolutionClass] = self.domain.get_connector().get_type(self.domain.get_core())

        # 4. Strain control flow variables.

        # 4.1. Logical condition to ctrl the epidemic (main iteration).
        # If True, the iteration continues. When there are no infected individuals, the epidemic finishes.
        self.epidemic: bool = True

        # 4.2. The current iteration. The iteration counter will be initially set to 0.
        self.time: int = 0

        # 4.3. The best solution found by the strain.
        self.best_strain_solution: Solution | None = None
        self.best_strain_solution_found: bool = False

        # 4.4. The best strain-specific death individual will initially be the worst solution.
        self.best_dead: Solution = self.solution_type(self.domain, connector=self.domain.get_connector())

        # 4.5. The worst strain-specific superspreader individual will initially be the best solution.
        self.worst_superspreader: Solution = self.solution_type(self.domain, connector=self.domain.get_connector())

        # 5. Main strain sets: infected, superspreaders, infected superspreaders and deaths.
        self.infected: Set[Solution] = set()
        self.superspreaders: Set[Solution] = set()
        self.infected_superspreaders: Set[Solution] = set()
        self.dead: Set[Solution] = set()

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:

        # 1. Yield the patient zero (pz).
        pz: Solution = self.solution_type(self.domain, connector=self.domain.get_connector())
        pz.evaluate(self.fitness_function)
        get_metagen_logger(distributed=True).detailed_info(f'[{self.strain_properties.strain_id}] Patient zero: {pz}')

        # 2. Add the patient zero to the strain-specific infected set.
        self.infected.add(pz)
        self.infected_superspreaders.add(pz)

        # 3. The best strain-specific individual will initially be the patient zero.
        self.best_strain_solution = pz

        return list(self.infected), self.best_strain_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:

        # 1. Spreading the disease.

        # 1.1. Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        self.update_pandemic_global_state()

        # 1.2. Yield the new infected population distributed
        new_infected_population = distributed_cvoa_new_infected_population(self.global_state, self.domain,
                                                                           self.fitness_function,
                                                                           self.strain_properties,
                                                                           self.infected, self.superspreaders,
                                                                           self.time, self.update_isolated)

        # 1.3. Then, add the best individual of the strain to the next population.
        new_infected_population.add(self.best_strain_solution)

        get_metagen_logger(distributed=True).detailed_info(
            f'[{self.strain_properties.strain_id}] Iteration #{self.time} - {self.r0_report(len(new_infected_population))}'
            f'- Best strain individual: {self.best_strain_solution} , Best global individual: {ray.get(self.global_state.get_best_individual.remote())} ')

        # 1.4. Update the infected strain population for the next iteration
        self.infected.clear()
        self.infected.update(new_infected_population)

        # 2. Stop if no new infected individuals.
        if not self.infected:
            self.epidemic = False
            get_metagen_logger(distributed=True).detailed_info(
                f'[{self.strain_properties.strain_id}] No new infected individuals at {self.time}')

        get_metagen_logger(distributed=True).detailed_info(
            f'[{self.strain_properties.strain_id}] Iteration #{self.time} - {self.r0_report(len(new_infected_population))}'
            f'- Best strain individual: {self.best_strain_solution} , Best global individual: {ray.get(self.global_state.get_best_individual.remote())}')

        # 3. Update the elapsed pandemic time.
        self.time += 1

        return list(self.infected), self.best_strain_solution

    def update_pandemic_global_state(self) -> None:
        """ It updates the specific strain death and superspreader's sets and the global death and recovered sets.
        """

        # 1. A percentage, p_superspreader, of the infected individuals in the strain (infected) will be superspreaders.
        number_of_super_spreaders = math.ceil(self.strain_properties.p_superspreader * len(self.infected))

        # 2. A percentage, p_die, of the infected individuals in the strain (infected) will die.
        number_of_deaths = math.ceil(self.strain_properties.p_die * len(self.infected))

        # 3. If there are at least two infected individuals in the strain:
        if len(self.infected) >= 1:

            # 3.1. For each infected individual:
            for individual in self.infected:

                # 3.1.1. Insert the current individual into superspreader set; if the insertion was successful, decrement
                # the superspreader's counter.
                self.worst_superspreader, self.best_dead, inserted = insert_into_set_strain(self.worst_superspreader,
                                                                                            self.best_dead,
                                                                                            self.superspreaders,
                                                                                            individual,
                                                                                            number_of_super_spreaders,
                                                                                            's')
                if inserted:
                    number_of_super_spreaders -= 1

                # 3.1.2. Update the recovered and death sets.

                # 3.1.2.1. Insert the current individual into death set; if the insertion was successful,
                # the dead variable will be set to True; otherwise False.
                self.worst_superspreader, self.best_dead, dead = insert_into_set_strain(self.worst_superspreader,
                                                                                        self.best_dead, self.dead,
                                                                                        individual,
                                                                                        number_of_deaths, 'd')

                # 3.1.2.2. If the current individual is not dead, it is added to the recovered set.
                if dead:
                    number_of_deaths -= 1
                else:
                    ray.get(self.global_state.recover_if_not_dead.remote(individual))

                # 3.1.3. If the current individual is better than the current global one, a new global best individual is
                # found, and its global variable is updated.
                if individual.get_fitness() < ray.get(self.global_state.get_best_individual.remote()).get_fitness():
                    ray.get(self.global_state.update_best_individual.remote(individual))
                    self.best_strain_solution_found = True
                    get_metagen_logger(distributed=True).detailed_info(
                        f'[{self.strain_properties.strain_id}] New global best individual found at {self.time}! ({individual})')

                # 3.1.4. If the current individual is better than the current strain one, a new strain the best individual is
                # found, and its variable is updated.
                if individual.get_fitness() < self.best_strain_solution.get_fitness():
                    self.best_strain_solution = individual

            # 3.4. Update the global death set with the strain death set..
            ray.get(self.global_state.update_deaths.remote(self.dead))

        # 4. Remove the global dead individuals from the global recovered set.
        ray.get(self.global_state.update_recovered_with_deaths.remote())

    def infect_individuals(self, carrier_individual: Solution, travel_distance: int, n_infected: int) -> Set[Solution]:

        infected_population: Set[Solution] = set()

        for _ in range(0, n_infected):

            # If the current disease time is not affected by the social_distancing policy, the current
            # individual infects another with a travel distance (using infect), and it is added
            # to the newly infected population.
            if self.time < self.strain_properties.social_distancing:
                new_infected_individual = infect(carrier_individual, self.fitness_function, travel_distance)
                self.update_new_infected_population(infected_population, new_infected_individual)

            # After social_distancing iterations (when the social_distancing policy is applied),
            # the current individual infects another with a travel distance of one (using infect) then,
            # the newly infected individual can be isolated or not.
            else:
                new_infected_individual = infect(carrier_individual, self.fitness_function, 1)
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
        """ It updates the next infected population with a new infected individual.

        :param new_infected_population: The population of the next iteration.
        :param new_infected_individual: The new infected individual that will be inserted into the netx iteration set.
        :type new_infected_population: set of :py:class:`~metagen.framework.Solution`
        :type new_infected_individual: :py:class:`~metagen.framework.Solution`
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

    def stopping_criterion(self) -> bool:

        # When the strain is stopped?

        # First condition: When there are no infected individuals
        first_condition: bool = self.epidemic == False

        # Second condition: When the pandemic duration has been reached
        second_condition: bool = self.time > self.strain_properties.pandemic_duration

        # Third condition: When the best individual has been found and the time is greater than 1
        third_condition = self.best_strain_solution_found and self.time > 1

        return first_condition or second_condition or third_condition

    def post_execution(self) -> None:
        get_metagen_logger(distributed=True).detailed_info(
            f'[{self.strain_properties.strain_id}] Converged after {self.time} iterations with best individual: {self.best_strain_solution}')
        super().post_execution()

    def r0_report(self, new_infections: int) -> str:
        recovered = ray.get(self.global_state.get_recovered_len.remote())
        r0 = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "\tNew infected = " + str(new_infections) + ", Recovered = " + str(recovered) + ", R0 = " + str(r0)
        return report

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
