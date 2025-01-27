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
import random
from copy import deepcopy
from typing import Callable, Set, NamedTuple

import ray

from metagen.framework import Solution, Domain
from metagen.metaheuristics.distributed_tools import assign_load_equally

IndividualState = NamedTuple("IndividualState", [("recovered", bool), ("dead", bool), ("isolated", bool)])
"""
A named tuple representing the state of an individual in the CVOA algorithm.

:ivar recovered: Whether the individual has recovered from infection
:vartype recovered: bool
:ivar dead: Whether the individual is dead
:vartype dead: bool
:ivar isolated: Whether the individual is isolated
:vartype isolated: bool
"""


@ray.remote
class PandemicState:
    """
    A distributed class that maintains the global state of the pandemic simulation.
    
    This class keeps track of recovered, dead, and isolated individuals, as well as
    the best solution found so far. It is designed to be used with Ray for distributed
    computing.

    :ivar recovered: Set of solutions that have recovered from infection
    :vartype recovered: Set[Solution]
    :ivar deaths: Set of solutions that have died
    :vartype deaths: Set[Solution]
    :ivar isolated: Set of solutions that are isolated
    :vartype isolated: Set[Solution]
    :ivar best_individual_found: Whether a best solution has been found
    :vartype best_individual_found: bool
    :ivar best_individual: The best solution found so far
    :vartype best_individual: Solution
    """

    def __init__(self, initial_individual: Solution):
        """
        Initialize the pandemic state.

        :param initial_individual: The initial solution to start with
        :type initial_individual: Solution
        """
        self.recovered: Set[Solution] = set()
        self.deaths: Set[Solution] = set()
        self.isolated: Set[Solution] = set()
        self.best_individual_found: bool = False
        self.best_individual: Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        """
        Get the state of a specific individual.

        :param individual: The solution to check
        :type individual: Solution
        :return: The state of the individual (recovered, dead, isolated)
        :rtype: IndividualState
        """
        result: IndividualState = IndividualState(False, False, False)
        if individual in self.recovered:
            result = result._replace(recovered=True)
        if individual in self.deaths:
            result = result._replace(dead=True)
        if individual in self.isolated:
            result = result._replace(isolated=True)
        return result

    def get_recovered_len(self) -> int:
        """
        Get the number of recovered individuals.

        :return: Number of recovered solutions
        :rtype: int
        """
        return len(self.recovered)

    def get_infected_again(self, individual: Solution) -> None:
        """
        Mark an individual as infected again by removing it from recovered set.

        :param individual: The solution to re-infect
        :type individual: Solution
        """
        self.recovered.remove(individual)

    def update_deaths(self, individuals: Set[Solution]) -> None:
        """
        Add new individuals to the deaths set.

        :param individuals: Set of solutions to mark as dead
        :type individuals: Set[Solution]
        """
        self.deaths.update(individuals)

    def update_recovered_with_deaths(self) -> None:
        """Remove dead individuals from the recovered set."""
        self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual: Solution) -> None:
        """
        Mark an individual as recovered if it's not dead.

        :param individual: The solution to potentially recover
        :type individual: Solution
        """
        if individual not in self.deaths:
            self.recovered.add(individual)

    def isolate_individual_conditional_state(self, individual: Solution, conditional_state: IndividualState) -> None:
        """
        Isolate an individual if its current state matches the conditional state.

        :param individual: The solution to potentially isolate
        :type individual: Solution
        :param conditional_state: The state condition that must be met
        :type conditional_state: IndividualState
        """
        current_state: IndividualState = self.get_individual_state(individual)
        if current_state == conditional_state:
            self.isolated.add(individual)

    def update_best_individual(self, individual: Solution) -> None:
        """
        Update the best solution found.

        :param individual: The new best solution
        :type individual: Solution
        """
        self.best_individual_found = True
        self.best_individual = individual

    def get_best_individual(self) -> Solution:
        """
        Get the best solution found so far.

        :return: The best solution
        :rtype: Solution
        """
        return self.best_individual

    def get_pandemic_report(self):
        """
        Get a report of the current pandemic state.

        :return: Dictionary containing counts of recovered, dead, isolated individuals and best solution
        :rtype: dict
        """
        return {
            "recovered": len(self.recovered),
            "deaths": len(self.deaths),
            "isolated": len(self.isolated),
            "best_individual": self.best_individual
        }


class StrainProperties(NamedTuple):
    """
    Properties that define the behavior of a virus strain in the CVOA algorithm.

    :ivar strain_id: Unique identifier for the strain
    :vartype strain_id: str
    :ivar pandemic_duration: Number of iterations the pandemic lasts
    :vartype pandemic_duration: int
    :ivar spreading_rate: Base number of individuals that get infected
    :vartype spreading_rate: int
    :ivar min_superspreading_rate: Minimum number of individuals infected by a superspreader
    :vartype min_superspreading_rate: int
    :ivar max_superspreading_rate: Maximum number of individuals infected by a superspreader
    :vartype max_superspreading_rate: int
    :ivar social_distancing: Factor that reduces infection spread
    :vartype social_distancing: int
    :ivar p_isolation: Probability of an individual being isolated
    :vartype p_isolation: float
    :ivar p_travel: Probability of an individual traveling
    :vartype p_travel: float
    :ivar p_re_infection: Probability of a recovered individual being reinfected
    :vartype p_re_infection: float
    :ivar p_superspreader: Probability of an individual being a superspreader
    :vartype p_superspreader: float
    :ivar p_die: Probability of an infected individual dying
    :vartype p_die: float
    """
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


def distributed_cvoa_new_infected_population(global_state, domain: Domain,
                                             fitness_function: Callable[[Solution], float],
                                             strain_properties: StrainProperties,
                                             carrier_population: Set[Solution], superspreaders: Set[Solution],
                                             time: int, update_isolated: bool) -> Set[Solution]:
    """
    Generate new infected population in a distributed manner using Ray.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param domain: The problem domain
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier_population: Set of current infected solutions
    :type carrier_population: Set[Solution]
    :param superspreaders: Set of superspreader solutions
    :type superspreaders: Set[Solution]
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    futures = [cvoa_remote_yield_infected_population_from_a_carrier.remote(global_state, domain, fitness_function,
                                                                           strain_properties, carrier, superspreaders,
                                                                           time, update_isolated)
               for carrier in carrier_population]

    new_infected_population = set()
    for result in ray.get(futures):
        new_infected_population.update(result)

    return new_infected_population


def cvoa_local_yield_new_infected_population(global_state, domain: Domain,
                                             fitness_function: Callable[[Solution], float],
                                             strain_properties: StrainProperties,
                                             carrier_population: Set[Solution], superspreaders: Set[Solution],
                                             time: int, update_isolated: bool) -> Set[Solution]:
    """
    Generate new infected population locally.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param domain: The problem domain
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier_population: Set of current infected solutions
    :type carrier_population: Set[Solution]
    :param superspreaders: Set of superspreader solutions
    :type superspreaders: Set[Solution]
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    new_infected_population: Set[Solution] = set()
    for carrier in carrier_population:
        new_infected_population.update(
            cvoa_local_yield_infected_population_from_a_carrier(global_state, domain, fitness_function,
                                                                strain_properties,
                                                                carrier, superspreaders, time, update_isolated))
    return new_infected_population


def cvoa_local_yield_infected_population_from_a_carrier(global_state, domain: Domain,
                                                        fitness_function: Callable[[Solution], float],
                                                        strain_properties: StrainProperties,
                                                        carrier: Solution, superspreaders: Set[Solution],
                                                        time: int, update_isolated: bool) -> Set[Solution]:
    """
    Generate new infected population from a single carrier locally.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param domain: The problem domain
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param superspreaders: Set of superspreader solutions
    :type superspreaders: Set[Solution]
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    n_infected, travel_distance = compute_n_infected_travel_distance(domain, strain_properties, carrier, superspreaders)

    return distributed_infect_individuals(global_state, fitness_function, strain_properties, carrier, n_infected,
                                          travel_distance,
                                          time, update_isolated)


@ray.remote
def cvoa_remote_yield_infected_population_from_a_carrier(global_state, domain: Domain,
                                                         fitness_function: Callable[[Solution], float],
                                                         strain_properties: StrainProperties,
                                                         carrier: Solution, superspreaders: Set[Solution],
                                                         time: int, update_isolated: bool) -> Set[Solution]:
    """
    Generate new infected population from a single carrier in a distributed manner using Ray.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param domain: The problem domain
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param superspreaders: Set of superspreader solutions
    :type superspreaders: Set[Solution]
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    return cvoa_local_yield_infected_population_from_a_carrier(global_state, domain, fitness_function,
                                                               strain_properties, carrier, superspreaders, time,
                                                               update_isolated)


def compute_n_infected_travel_distance(domain: Domain, strain_properties: StrainProperties, carrier: Solution,
                                       superspreaders: Set[Solution]) -> Tuple[int, int]:
    """
    Compute the number of infected individuals and travel distance for a carrier.

    :param domain: The problem domain
    :type domain: Domain
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param superspreaders: Set of superspreader solutions
    :type superspreaders: Set[Solution]
    :return: Number of infected individuals and travel distance
    :rtype: Tuple[int, int]
    """
    if carrier in superspreaders:
        n_infected = random.randint(strain_properties.min_superspreading_rate,
                                    strain_properties.max_superspreading_rate)
    else:
        n_infected = random.randint(0, strain_properties.spreading_rate)
    if random.random() < strain_properties.p_travel:
        travel_distance = random.randint(0, len(domain.get_core().variable_list()))
    else:
        travel_distance = 1

    return n_infected, travel_distance


def local_infect_individuals(global_state, fitness_function: Callable[[Solution], float],
                             strain_properties: StrainProperties,
                             carrier: Solution, n_infected: int, travel_distance: int, time: int,
                             update_isolated: bool) -> Set[Solution]:
    """
    Infect individuals locally.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param n_infected: Number of individuals to infect
    :type n_infected: int
    :param travel_distance: Travel distance for the infected individuals
    :type travel_distance: int
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    return cvoa_local_yield_infected_from_carrier(global_state, fitness_function, strain_properties, carrier,
                                                  n_infected, travel_distance, time, update_isolated)


def distributed_infect_individuals(global_state, fitness_function: Callable[[Solution], float],
                                   strain_properties: StrainProperties,
                                   carrier: Solution, n_infected: int, travel_distance: int, time: int,
                                   update_isolated: bool) -> Set[Solution]:
    """
    Infect individuals in a distributed manner using Ray.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param n_infected: Number of individuals to infect
    :type n_infected: int
    :param travel_distance: Travel distance for the infected individuals
    :type travel_distance: int
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    distribution = assign_load_equally(n_infected)
    futures = []
    for count in distribution:
        futures.append(
            cvoa_remote_yield_infected_from_carrier.remote(global_state, fitness_function, strain_properties, carrier,
                                                           count, travel_distance, time, update_isolated))
    new_infected_population = set()
    for result in ray.get(futures):
        new_infected_population.update(result)
    return new_infected_population


def cvoa_local_yield_infected_from_carrier(global_state, fitness_function: Callable[[Solution], float],
                                           strain_properties: StrainProperties,
                                           carrier: Solution, n_infected: int, travel_distance: int, time: int,
                                           update_isolated: bool) -> Set[Solution]:
    """
    Yield infected individuals from a carrier locally.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param n_infected: Number of individuals to infect
    :type n_infected: int
    :param travel_distance: Travel distance for the infected individuals
    :type travel_distance: int
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    new_infected_population: Set[Solution] = set()

    for _ in range(0, n_infected):

        if time < strain_properties.social_distancing:
            new_infected_individual = deepcopy(carrier)
            new_infected_individual.mutate(travel_distance)
            new_infected_individual.evaluate(fitness_function)
            update_new_infected_population(global_state, new_infected_population, new_infected_individual,
                                           strain_properties.p_re_infection)

        else:
            new_infected_individual = deepcopy(carrier)
            new_infected_individual.mutate(1)
            new_infected_individual.evaluate(fitness_function)
            if random.random() < strain_properties.p_isolation:
                update_new_infected_population(global_state, new_infected_population, new_infected_individual,
                                               strain_properties.p_re_infection)
            else:
                if update_isolated:
                    ray.remote(
                        global_state.isolate_individual_conditional_state.remote(new_infected_individual,
                                                                                 IndividualState(True, True, True)))

    return new_infected_population


@ray.remote
def cvoa_remote_yield_infected_from_carrier(global_state, fitness_function: Callable[[Solution], float],
                                            strain_properties: StrainProperties,
                                            carrier: Solution, n_infected: int, travel_distance: int, time: int,
                                            update_isolated: bool) -> Set[Solution]:
    """
    Yield infected individuals from a carrier in a distributed manner using Ray.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param strain_properties: Properties of the virus strain
    :type strain_properties: StrainProperties
    :param carrier: The current infected solution
    :type carrier: Solution
    :param n_infected: Number of individuals to infect
    :type n_infected: int
    :param travel_distance: Travel distance for the infected individuals
    :type travel_distance: int
    :param time: Current iteration
    :type time: int
    :param update_isolated: Whether to update isolation status
    :type update_isolated: bool
    :return: Set of newly infected solutions
    :rtype: Set[Solution]
    """
    return cvoa_local_yield_infected_from_carrier(global_state, fitness_function, strain_properties, carrier,
                                                  n_infected, travel_distance, time, update_isolated)


def update_new_infected_population(global_state, new_infected_population: Set[Solution],
                                   new_infected_individual: Solution, p_re_infection: float) -> None:
    """
    Update the new infected population.

    :param global_state: The global pandemic state
    :type global_state: PandemicState
    :param new_infected_population: Set of newly infected solutions
    :type new_infected_population: Set[Solution]
    :param new_infected_individual: The newly infected individual
    :type new_infected_individual: Solution
    :param p_re_infection: Probability of re-infection
    :type p_re_infection: float
    """
    individual_state: IndividualState = ray.get(global_state.get_individual_state.remote(new_infected_individual))

    if not individual_state.dead and not individual_state.recovered:
        new_infected_population.add(new_infected_individual)

    elif individual_state.recovered:
        if random.random() < p_re_infection:
            new_infected_population.add(new_infected_individual)
            ray.get(global_state.get_infected_again.remote(new_infected_individual))