import random
from copy import deepcopy
from typing import Callable, Set, Tuple
import ray
from metagen.framework import Solution, Domain
from metagen.metaheuristics.cvoa.common_tools import IndividualState, StrainProperties, \
    compute_n_infected_travel_distance
from metagen.metaheuristics.distributed_tools import assign_load_equally

# Remote pandemic state (ray support)
@ray.remote
class RemotePandemicState:
    def __init__(self, initial_individual: Solution):
        self.recovered: Set[Solution] = set()
        self.deaths: Set[Solution] = set()
        self.isolated: Set[Solution] = set()
        self.best_individual_found: bool = False
        self.best_individual: Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
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
        return len(self.recovered)

    def get_infected_again(self, individual: Solution) -> None:
        self.recovered.remove(individual)

    # Deaths
    def update_deaths(self, individuals: Set[Solution]) -> None:
        self.deaths.update(individuals)

    # Recovered and Deaths
    def update_recovered_with_deaths(self) -> None:
        self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual: Solution) -> None:
        if individual not in self.deaths:
            self.recovered.add(individual)

    # Isolated
    def isolate_individual_conditional_state(self, individual: Solution, conditional_state: IndividualState) -> None:
        current_state: IndividualState = self.get_individual_state(individual)
        if current_state == conditional_state:
            self.isolated.add(individual)

    # Best Individual
    def update_best_individual(self, individual: Solution) -> None:
        self.best_individual_found = True
        self.best_individual = individual

    def get_best_individual(self) -> Solution:
        return self.best_individual

    def get_pandemic_report(self):
        return {
            "recovered": len(self.recovered),
            "deaths": len(self.deaths),
            "isolated": len(self.isolated),
            "best_individual": self.best_individual
        }





def distributed_cvoa_new_infected_population(global_state, domain: Domain,
                                             fitness_function: Callable[[Solution], float],
                                             strain_properties: StrainProperties,
                                             carrier_population: Set[Solution], superspreaders: Set[Solution],
                                             time: int, update_isolated: bool) -> Set[Solution]:

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
    return cvoa_local_yield_infected_population_from_a_carrier(global_state, domain, fitness_function,
                                                               strain_properties, carrier, superspreaders, time,
                                                               update_isolated)


def local_infect_individuals(global_state, fitness_function: Callable[[Solution], float],
                             strain_properties: StrainProperties,
                             carrier: Solution, n_infected: int, travel_distance: int, time: int,
                             update_isolated: bool) -> Set[Solution]:
    return cvoa_local_yield_infected_from_carrier(global_state, fitness_function, strain_properties, carrier,
                                                  n_infected, travel_distance, time, update_isolated)


def distributed_infect_individuals(global_state, fitness_function: Callable[[Solution], float],
                                   strain_properties: StrainProperties,
                                   carrier: Solution, n_infected: int, travel_distance: int, time: int,
                                   update_isolated: bool) -> Set[Solution]:
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
    return cvoa_local_yield_infected_from_carrier(global_state, fitness_function, strain_properties, carrier,
                                                  n_infected, travel_distance, time, update_isolated)


def update_new_infected_population(global_state, new_infected_population: Set[Solution],
                                   new_infected_individual: Solution, p_re_infection: float) -> None:
    individual_state: IndividualState = ray.get(global_state.get_individual_state.remote(new_infected_individual))

    if not individual_state.dead and not individual_state.recovered:
        new_infected_population.add(new_infected_individual)

    elif individual_state.recovered:
        if random.random() < p_re_infection:
            new_infected_population.add(new_infected_individual)
            ray.get(global_state.get_infected_again.remote(new_infected_individual))
