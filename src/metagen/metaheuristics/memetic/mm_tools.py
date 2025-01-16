from copy import deepcopy
from typing import Tuple, Callable, List

import ray

from metagen.framework import Solution
from metagen.metaheuristics.distributed_tools import assign_load_equally, yield_two_children



def local_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution,
                                                          fitness_function: Callable[[Solution], float],
                                                          alteration_limit: float) -> Solution:
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

def distributed_yield_mutate_evaluate_from_the_best(population_size: int, best_solution: Solution,
                                                    fitness_function: Callable[[Solution], float],
                                                    alteration_limit: float) -> List[Solution]:
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(
            remote_yield_mutate_and_evaluate_individuals_from_best.remote(count, best_solution, fitness_function,
                                                                          alteration_limit))
    return ray.get(futures)





@ray.remote
def remote_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution,
                                                           fitness_function: Callable[[Solution], float],
                                                           alteration_limit: float) -> Solution:

    return local_yield_mutate_and_evaluate_individuals_from_best(num_individuals, best_solution,
                                                                 fitness_function, alteration_limit)











def mm_distributed_offspring(parents: Tuple['GASolution', 'GASolution'], offspring_size: int, mutation_rate: float,
                             fitness_function: Callable[[Solution], float],
                             neighbor_population_size: int, alteration_limit: float) -> Tuple[
    List['GASolution'], Solution]:
    distribution = assign_load_equally(offspring_size)
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

@ray.remote
def mm_remote_offspring_individuals(parents: Tuple['GASolution', 'GASolution'], num_individuals: int,
                                    mutation_rate: float, fitness_function: Callable[[Solution], float],
                                    neighbor_population_size: int, alteration_limit: float) -> Tuple[
    List['GASolution'], 'GASolution']:
    return mm_local_offspring_individuals(parents, num_individuals, mutation_rate, fitness_function,
                                          neighbor_population_size, alteration_limit)

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

        # child1, child2 = mm_local_local_search_of_two_childs((child1, child2), neighbor_population_size, fitness_function, alteration_limit)

        child1, child2 = mm_distributed_local_search_of_two_childs((child1, child2), neighbor_population_size,
                                                             fitness_function, alteration_limit)

        # print(f'---------------------------------------- Child1 = {child1}')

        offspring.extend([child1, child2])

        if child1.get_fitness() < best_child.get_fitness():
            best_child = child1

        if child2.get_fitness() < best_child.get_fitness():
            best_child = child2

    return offspring, best_child


def mm_local_local_search_of_two_childs(children:Tuple['GASolution', 'GASolution'], neighbor_population_size: int,
                                        fitness_function: Callable[[Solution], float], alteration_limit: float) -> Tuple[
    'GASolution', 'GASolution']:
    child1 = local_yield_mutate_and_evaluate_individuals_from_best(neighbor_population_size, children[0],
                                                                   fitness_function, alteration_limit)
    child2 = local_yield_mutate_and_evaluate_individuals_from_best(neighbor_population_size, children[1],
                                                                   fitness_function, alteration_limit)
    return child1, child2

def mm_distributed_local_search_of_two_childs(children:Tuple['GASolution', 'GASolution'], neighbor_population_size: int,
                                        fitness_function: Callable[[Solution], float], alteration_limit: float) -> Tuple[
    'GASolution', 'GASolution']:

    distribution = assign_load_equally(2)

    futures = []
    for child in children:
        futures.append(mm_distributed_local_search_of_one_children.remote(neighbor_population_size, child,
                                                                   fitness_function, alteration_limit))

    results = ray.get(futures)
    # flattened_results = [individual for sublist in results for individual in sublist]

    # print(f'---------------------------------------- mm_distributed_local_search_of_two_childs = {results}')
    child1 = results[0]
    child2 = results[1]

    return child1, child2

@ray.remote
def mm_distributed_local_search_of_one_children(population_size: int, best_solution: 'GASolution',
                                                    fitness_function: Callable[[Solution], float],
                                                    alteration_limit: float) -> 'GASolution':
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(
            remote_yield_mutate_and_evaluate_individuals_from_best.remote(count, best_solution, fitness_function, alteration_limit))
    results = ray.get(futures)
    # print(f'---------------------------------------- mm_distributed_local_search_of_one_children = {results}')
    flattened_results = [individual for individual in results]
    res = min(flattened_results, key=lambda sol: sol.get_fitness())

    return res