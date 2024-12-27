import os
import random
from copy import deepcopy
import platform
from typing import List, Callable, Tuple, Optional

import ray
from ray.thirdparty_files import psutil

from metagen.framework import Domain, Solution


def task_environment() -> None:
    worker_id = ray.get_runtime_context().get_worker_id()
    print(f'This task is running on worker {worker_id}')

def resources_avialable(distribution, message = "") -> None:
    available_resources = ray.available_resources()
    cpu_resources = available_resources.get('CPU', 0)
    print(f"{message} , CPUs = {cpu_resources}, distribution = {distribution}")


def assign_load_equally(neighbor_population_size: int) -> List[int]:
    num_cpus = int(ray.available_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size)
    base_count = neighbor_population_size // num_cpus
    remainder = neighbor_population_size % num_cpus
    distribution = [base_count + 1 if i < remainder else base_count for i in range(num_cpus)]
    return distribution


# Para GA -> Población inicial

def ga_local_yield_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'],'GASolution']:
    from metagen.metaheuristics.ga import GASolution
    solution_type: type[GASolution] = domain.get_connector().get_type(domain.get_core())
    best_subpopulation_individual = solution_type(domain, connector=domain.get_connector())
    best_subpopulation_individual.evaluate(fitness_function)
    subpopulation:List[GASolution] = [best_subpopulation_individual]
    for _ in range(num_individuals-1):
            individual = solution_type(domain, connector=domain.get_connector())
            individual.evaluate(fitness_function)
            subpopulation.append(individual)
            if individual.fitness < best_subpopulation_individual.fitness:
                best_subpopulation_individual = individual
    return subpopulation, best_subpopulation_individual

@ray.remote
def ga_remote_yield_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'],'GASolution']:
    task_environment()
    return ga_local_yield_and_evaluate_individuals(num_individuals, domain, fitness_function)

def ga_distributed_base_population(population_size: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'],'GASolution']:
    distribution = assign_load_equally(population_size)
    resources_avialable(distribution, 'Base population')
    futures = []
    for count in distribution:
        futures.append(ga_remote_yield_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best)
    return population, best_individual

# Para GA -> Offspring

def yield_two_children(parents:List['GASolution'], mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple['GASolution','GASolution']:
    child1, child2 = parents[0].crossover(parents[1])
    if random.uniform(0, 1) <= mutation_rate:
        child1.mutate()
    if random.uniform(0, 1) <= mutation_rate:
        child2.mutate()
    child1.evaluate(fitness_function)
    child2.evaluate(fitness_function)
    return child1, child2

def ga_local_offspring_individuals(parents:List['GASolution'], num_individuals: int, mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'],'GASolution']:
    offspring = []
    child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
    best_child = min(child1, child2)
    offspring.extend([child1, child2])
    for _ in range(num_individuals-1):
        child1, child2 = yield_two_children(parents, mutation_rate, fitness_function)
        offspring.extend([child1, child2])
        if child1 < best_child:
            best_child = child1
        if child2 < best_child:
            best_child = child2
    return offspring, best_child

@ray.remote
def ga_remote_offspring_individuals(parents:List['GASolution'], num_individuals: int, mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'],'GASolution']:
    task_environment()
    return ga_local_offspring_individuals(parents, num_individuals, mutation_rate, fitness_function)

def ga_distributed_offspring(parents:List['GASolution'], offspring_size: int, mutation_rate: float, fitness_function: Callable[[Solution], float]) -> Tuple[List['GASolution'], Solution]:
    distribution = assign_load_equally(offspring_size)
    resources_avialable(distribution, 'Offspring')
    futures = []
    for count in distribution:
        futures.append(ga_remote_offspring_individuals.remote(parents, count, mutation_rate, fitness_function))
    remote_results = ray.get(futures)
    all_offsprings = [result[0] for result in remote_results]
    offspring = [individual for subpopulation in all_offsprings for individual in subpopulation]
    partial_best_children = [result[1] for result in remote_results]
    best_child = min(partial_best_children)
    return offspring, best_child



# Para RS:

def distributed_base_population(population_size: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> [List[Solution], Solution]:
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(remote_yield_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best)
    return population, best_individual

def local_yield_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> Tuple[List[Solution],Solution]:
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    best_subpopulation_individual = solution_type(domain, connector=domain.get_connector())
    best_subpopulation_individual.evaluate(fitness_function)
    subpopulation:List[Solution] = [best_subpopulation_individual]
    for _ in range(num_individuals-1):
            individual = solution_type(domain, connector=domain.get_connector())
            individual.evaluate(fitness_function)
            subpopulation.append(individual)
            if individual.fitness < best_subpopulation_individual.fitness:
                best_subpopulation_individual = individual
    return subpopulation, best_subpopulation_individual

@ray.remote
def remote_yield_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> [List[Solution], Solution]:
    return local_yield_and_evaluate_individuals(num_individuals, domain, fitness_function)




def distributed_mutation_and_evaluation(population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Tuple[List[Solution],Solution]:
    distribution = assign_load_equally(len(population))
    futures = []
    for count in distribution:
        futures.append(remote_mutate_and_evaluate_population.remote(population[:count], fitness_function, alteration_limit=alteration_limit))
        population = population[count:]
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best)
    return population, best_individual

def local_mutate_and_evaluate_population(population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> [List[Solution],Solution]:
    # print('Population = ' + str(population))
    first_individual = population[0]
    # print('First individual = '+str(first_individual))
    first_individual.mutate(alteration_limit=alteration_limit)
    first_individual.evaluate(fitness_function)
    best_subpopulation_individual = first_individual
    for individual in population[1:]:
        individual.mutate(alteration_limit=alteration_limit)
        individual.evaluate(fitness_function)
        if individual.fitness < best_subpopulation_individual.fitness:
            best_subpopulation_individual = individual
    return population, best_subpopulation_individual

@ray.remote
def remote_mutate_and_evaluate_population (population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> [List[Solution],Solution]:
    return local_mutate_and_evaluate_population(population, fitness_function, alteration_limit=alteration_limit)




# Para SA:
def distributed_yield_mutate_evaluate_from_the_best(population_size: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> List[Solution]:
    distribution = assign_load_equally(population_size)
    futures= []
    for count in distribution:
        futures.append(remote_yield_mutate_and_evaluate_individuals_from_best.remote(count, best_solution, fitness_function, alteration_limit=alteration_limit))
    return ray.get(futures)


def local_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Solution:
        best_neighbor = deepcopy(best_solution)
        best_neighbor.mutate(alteration_limit=alteration_limit)
        best_neighbor.evaluate(fitness_function)
        for _ in range(num_individuals - 1):
            neighbor = deepcopy(best_solution)
            neighbor.mutate(alteration_limit=alteration_limit)
            neighbor.evaluate(fitness_function)
            if neighbor.fitness < best_neighbor.fitness:
                best_neighbor = neighbor
        return best_neighbor

@ray.remote
def remote_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Solution:
    return local_yield_mutate_and_evaluate_individuals_from_best(num_individuals, best_solution, fitness_function, alteration_limit=alteration_limit)


