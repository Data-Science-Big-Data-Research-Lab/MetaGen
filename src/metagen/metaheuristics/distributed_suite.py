import random
from copy import deepcopy
from typing import List, Callable, Tuple, Optional, Set, NamedTuple

import ray

from metagen.framework import Domain, Solution


# Común a todos los algoritmos
def task_environment() -> None:
    worker_id = ray.get_runtime_context().get_worker_id()
    print(f'This task is running on worker {worker_id}')


def resources_avialable(distribution, message="") -> None:
    available_resources = ray.available_resources()
    cpu_resources = available_resources.get('CPU', 0)
    print(f"{message} , CPUs = {cpu_resources}, distribution = {distribution}")


def assign_load_equally(neighbor_population_size: int) -> List[int]:
    num_cpus = int(ray.available_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size)
    if num_cpus == 0:
        num_cpus = 1
    base_count = neighbor_population_size // num_cpus
    remainder = neighbor_population_size % num_cpus
    distribution = [base_count + 1 if i < remainder else base_count for i in range(num_cpus)]
    return distribution


# ******************** Para SSGA ********************
# Población inicial ordenada

def ssga_local_sorted_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                                     fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    subpopulation, best_subpopulation_individual = ga_local_yield_and_evaluate_individuals(num_individuals, domain,
                                                                                           fitness_function)
    subpopulation = sorted(subpopulation, key=lambda sol: sol.fitness)
    return subpopulation, best_subpopulation_individual


@ray.remote
def ssga_remote_sorted_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                                      fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    task_environment()
    return ssga_local_sorted_yield_and_evaluate_individuals(num_individuals, domain, fitness_function)


def distributed_sorted_base_population(population_size: int, domain: Domain,
                                       fitness_function: Callable[[Solution], float]) -> [List['GASolution'],
                                                                                          'GASolution']:
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(ssga_remote_sorted_yield_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    population = sorted(population, key=lambda sol: sol.get_fitness())
    best_individual = min(partial_best)
    return population, best_individual


def distributed_sort(population: List['GASolution']) -> Tuple[List['GASolution'], 'GASolution']:
    distribution = assign_load_equally(len(population))
    futures = []
    for count in distribution:
        futures.append(remote_sort_population.remote(population[:count]))
        population = population[count:]
    remote_results = ray.get(futures)
    all_subpopulations = [individual for sublist in remote_results for individual in sublist]
    population = sorted(all_subpopulations, key=lambda sol: sol.get_fitness())
    return population, population[0]


@ray.remote
def remote_sort_population(population: List['GASolution']) -> List['GASolution']:
    return sorted(population, key=lambda sol: sol.get_fitness())


# ******************** Para GA ********************
# Población inicial

def ga_local_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                            fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    from metagen.metaheuristics.ga import GASolution
    solution_type: type[GASolution] = domain.get_connector().get_type(domain.get_core())
    best_subpopulation_individual = solution_type(domain, connector=domain.get_connector())
    best_subpopulation_individual.evaluate(fitness_function)
    subpopulation: List[GASolution] = [best_subpopulation_individual]
    for _ in range(num_individuals - 1):
        individual = solution_type(domain, connector=domain.get_connector())
        individual.evaluate(fitness_function)
        subpopulation.append(individual)
        if individual.get_fitness() < best_subpopulation_individual.get_fitness():
            best_subpopulation_individual = individual
    return subpopulation, best_subpopulation_individual


@ray.remote
def ga_remote_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                             fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    task_environment()
    return ga_local_yield_and_evaluate_individuals(num_individuals, domain, fitness_function)


def ga_distributed_base_population(population_size: int, domain: Domain,
                                   fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    distribution = assign_load_equally(population_size)
    resources_avialable(distribution, 'Base population')
    futures = []
    for count in distribution:
        futures.append(ga_remote_yield_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best, key=lambda sol: sol.get_fitness())
    return population, best_individual


# Offspring

def yield_two_children(parents: Tuple['GASolution', 'GASolution'], mutation_rate: float,
                       fitness_function: Callable[[Solution], float]) -> Tuple['GASolution', 'GASolution']:
    child1, child2 = parents[0].crossover(parents[1])
    if random.uniform(0, 1) <= mutation_rate:
        child1.mutate()
    if random.uniform(0, 1) <= mutation_rate:
        child2.mutate()
    child1.evaluate(fitness_function)
    child2.evaluate(fitness_function)
    return child1, child2


def ga_local_offspring_individuals(parents: Tuple['GASolution', 'GASolution'], num_individuals: int,
                                   mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    offspring = []
    child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
    best_child = min(child1, child2, key=lambda sol: sol.get_fitness())
    offspring.extend([child1, child2])
    for _ in range(num_individuals - 1):
        child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
        offspring.extend([child1, child2])
        if child1.get_fitness() < best_child.get_fitness():
            best_child = child1
        if child2.get_fitness() < best_child.get_fitness():
            best_child = child2
    return offspring, best_child


@ray.remote
def ga_remote_offspring_individuals(parents: Tuple['GASolution', 'GASolution'], num_individuals: int,
                                    mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple[
    List['GASolution'], 'GASolution']:
    task_environment()
    return ga_local_offspring_individuals(parents, num_individuals, mutation_rate, fitness_function)


def ga_distributed_offspring(parents: Tuple['GASolution', 'GASolution'], offspring_size: int, mutation_rate: float,
                             fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'], Solution]:
    distribution = assign_load_equally(offspring_size)
    resources_avialable(distribution, 'Offspring')
    futures = []
    for count in distribution:
        futures.append(ga_remote_offspring_individuals.remote(parents, count, mutation_rate, fitness_function))
    remote_results = ray.get(futures)
    all_offsprings = [result[0] for result in remote_results]
    offspring = [individual for subpopulation in all_offsprings for individual in subpopulation]
    partial_best_children = [result[1] for result in remote_results]
    best_child = min(partial_best_children, key=lambda sol: sol.get_fitness())
    return offspring, best_child


# ******************** Para MM ********************

def mm_local_offspring_individuals(parents: Tuple['GASolution', 'GASolution'], num_individuals: int,
                                   mutation_rate: float, fitness_function: Callable[[Solution], float],
                                   neighbor_population_size: int, alteration_limit: float) -> Tuple[
    List['GASolution'], 'GASolution']:
    offspring = []
    child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
    best_child = min(child1, child2, key=lambda sol: sol.get_fitness())

    offspring.extend([child1, child2])

    for _ in range(num_individuals - 1):
        child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
        child1 = local_yield_mutate_and_evaluate_individuals_from_best(neighbor_population_size, child1,
                                                                       fitness_function, alteration_limit)
        child2 = local_yield_mutate_and_evaluate_individuals_from_best(neighbor_population_size, child2,
                                                                       fitness_function, alteration_limit)

        offspring.extend([child1, child2])

        if child1.get_fitness() < best_child.get_fitness():
            best_child = child1

        if child2.get_fitness() < best_child.get_fitness():
            best_child = child2

    return offspring, best_child


@ray.remote
def mm_remote_offspring_individuals(parents: Tuple['GASolution', 'GASolution'], num_individuals: int,
                                    mutation_rate: float, fitness_function: Callable[[Solution], float],
                                    neighbor_population_size: int, alteration_limit: float) -> Tuple[
    List['GASolution'], 'GASolution']:
    task_environment()
    return mm_local_offspring_individuals(parents, num_individuals, mutation_rate, fitness_function,
                                          neighbor_population_size, alteration_limit)


def mm_distributed_offspring(parents: Tuple['GASolution', 'GASolution'], offspring_size: int, mutation_rate: float,
                             fitness_function: Callable[[Solution], float],
                             neighbor_population_size: int, alteration_limit: float) -> Tuple[
    List['GASolution'], Solution]:
    distribution = assign_load_equally(offspring_size)
    resources_avialable(distribution, 'Memetic Offspring')
    futures = []
    for count in distribution:
        futures.append(mm_remote_offspring_individuals.remote(parents, count, mutation_rate, fitness_function,
                                                              neighbor_population_size, alteration_limit))
    remote_results = ray.get(futures)
    all_offsprings = [result[0] for result in remote_results]
    offspring = [individual for subpopulation in all_offsprings for individual in subpopulation]
    partial_best_children = [result[1] for result in remote_results]
    best_child = min(partial_best_children, key=lambda sol: sol.get_fitness())
    return offspring, best_child


# ******************** Para RS ********************

def distributed_base_population(population_size: int, domain: Domain,
                                fitness_function: Callable[[Solution], float]) -> [List[Solution], Solution]:
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(remote_yield_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best, key=lambda sol: sol.get_fitness())
    return population, best_individual


def local_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                         fitness_function: Callable[[Solution], float]) -> Tuple[
    List[Solution], Solution]:
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    best_subpopulation_individual = solution_type(domain, connector=domain.get_connector())
    best_subpopulation_individual.evaluate(fitness_function)
    subpopulation: List[Solution] = [best_subpopulation_individual]
    for _ in range(num_individuals - 1):
        individual = solution_type(domain, connector=domain.get_connector())
        individual.evaluate(fitness_function)
        subpopulation.append(individual)
        if individual.get_fitness() < best_subpopulation_individual.get_fitness():
            best_subpopulation_individual = individual
    return subpopulation, best_subpopulation_individual


@ray.remote
def remote_yield_and_evaluate_individuals(num_individuals: int, domain: Domain,
                                          fitness_function: Callable[[Solution], float]) -> [List[Solution], Solution]:
    return local_yield_and_evaluate_individuals(num_individuals, domain, fitness_function)


def distributed_mutation_and_evaluation(population: List[Solution], fitness_function: Callable[[Solution], float],
                                        alteration_limit: Optional[float] = None) -> Tuple[List[Solution], Solution]:
    distribution = assign_load_equally(len(population))
    futures = []
    for count in distribution:
        futures.append(remote_mutate_and_evaluate_population.remote(population[:count], fitness_function,
                                                                    alteration_limit=alteration_limit))
        population = population[count:]
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best, key=lambda sol: sol.get_fitness())
    return population, best_individual


def local_mutate_and_evaluate_population(population: List[Solution], fitness_function: Callable[[Solution], float],
                                         alteration_limit: Optional[float] = None) -> [List[Solution], Solution]:
    # print('Population = ' + str(population))
    first_individual = population[0]
    # print('First individual = '+str(first_individual))
    first_individual.mutate(alteration_limit=alteration_limit)
    first_individual.evaluate(fitness_function)
    best_subpopulation_individual = first_individual
    for individual in population[1:]:
        individual.mutate(alteration_limit=alteration_limit)
        individual.evaluate(fitness_function)
        if individual.get_fitness() < best_subpopulation_individual.get_fitness():
            best_subpopulation_individual = individual
    return population, best_subpopulation_individual


@ray.remote
def remote_mutate_and_evaluate_population(population: List[Solution], fitness_function: Callable[[Solution], float],
                                          alteration_limit: Optional[float] = None) -> [List[Solution], Solution]:
    return local_mutate_and_evaluate_population(population, fitness_function, alteration_limit=alteration_limit)


# ******************** Para SA ********************
def distributed_yield_mutate_evaluate_from_the_best(population_size: int, best_solution: Solution,
                                                    fitness_function: Callable[[Solution], float],
                                                    alteration_limit: Optional[float] = None) -> List[Solution]:
    distribution = assign_load_equally(population_size)
    resources_avialable(distribution, 'Neighborhood')
    futures = []
    for count in distribution:
        futures.append(
            remote_yield_mutate_and_evaluate_individuals_from_best.remote(count, best_solution, fitness_function,
                                                                          alteration_limit=alteration_limit))
    return ray.get(futures)


def local_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution,
                                                          fitness_function: Callable[[Solution], float],
                                                          alteration_limit: Optional[float]) -> Solution:
    best_neighbor = deepcopy(best_solution)
    best_neighbor.mutate(alteration_limit=alteration_limit)
    best_neighbor.evaluate(fitness_function)
    for _ in range(num_individuals - 1):
        neighbor = deepcopy(best_solution)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return best_neighbor


@ray.remote
def remote_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution,
                                                           fitness_function: Callable[[Solution], float],
                                                           alteration_limit: float) -> Solution:
    task_environment()
    return local_yield_mutate_and_evaluate_individuals_from_best(num_individuals, best_solution,
                                                                 fitness_function, alteration_limit)


# ******************** Para TS ********************
def local_yield_mutate_evaluate_population_from_the_best(population_size: int, best_solution: Solution,
                                                         fitness_function: Callable[[Solution], float],
                                                         alteration_limit: Optional[float] = None) -> Tuple[
    List[Solution], Solution]:
    neighbor_population = []
    best_neighbor = deepcopy(best_solution)
    best_neighbor.mutate(alteration_limit=alteration_limit)
    best_neighbor.evaluate(fitness_function)
    neighbor_population.append(best_neighbor)
    for _ in range(population_size - 1):
        neighbor = deepcopy(best_solution)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        neighbor_population.append(neighbor)
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return neighbor_population, best_neighbor


# ******************** Para CVOA ********************

IndividualState = NamedTuple("IndividualState", [("recovered", bool), ("dead", bool), ("isolated", bool)])


@ray.remote
class PandemicState:
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


def compute_n_infected_travel_distance(domain: Domain, strain_properties: StrainProperties, carrier: Solution,
                                       superspreaders: Set[Solution]) -> Tuple[int, int]:
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
    return cvoa_local_yield_infected_from_carrier(global_state, fitness_function, strain_properties, carrier,
                                                  n_infected, travel_distance, time, update_isolated)


def distributed_infect_individuals(global_state, fitness_function: Callable[[Solution], float],
                                   strain_properties: StrainProperties,
                                   carrier: Solution, n_infected: int, travel_distance: int, time: int,
                                   update_isolated: bool) -> Set[Solution]:
    distribution = assign_load_equally(n_infected)
    resources_avialable(distribution, 'CVOA Infection')
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
