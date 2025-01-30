from copy import deepcopy
from typing import Tuple, Callable, List

import ray

from metagen.framework import Solution
from metagen.logging.metagen_logger import get_remote_metagen_logger
from metagen.metaheuristics.distributed_tools import assign_load_equally




def local_search_of_two_children(parents: Tuple[Solution, Solution], fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float, distribution_level:int=0) -> Tuple[Solution, Solution]:

    if distribution_level > 0:
        children_aux = distributed_population_local_search(list(parents), fitness_function, neighbor_population_size, alteration_limit, distribution_level)
        children = (children_aux[0], children_aux[1])
    else:

        children_aux = population_local_search(list(parents), fitness_function, neighbor_population_size, alteration_limit, distribution_level)
        children = (children_aux[0], children_aux[1])

    return children

def distributed_population_local_search(population: List[Solution], fitness_function: Callable[[Solution], float], neighbor_population_size: int
                  , alteration_limit: float, distribution_level:int=1) -> List[Solution]:

    distribution = assign_load_equally(len(population))

    get_remote_metagen_logger().debug(f"[LEVEL 1] Distributed local search of a population of {len(population)} individuals with {ray.available_resources().get('CPU', 0)} CPUs -- {distribution}")

    futures = []
    for count in distribution:
        futures.append(
            remote_population_local_search.remote(population[:count], fitness_function, neighbor_population_size,
                                                  alteration_limit, distribution_level))

    results = ray.get(futures)
    flattened_results = [item for sublist in results for item in sublist]

    return flattened_results



@ray.remote
def remote_population_local_search(population: List[Solution], fitness_function: Callable[[Solution], float], neighbor_population_size: int
                  , alteration_limit: float, distribution_level:int) -> List[Solution]:
    return population_local_search(population, fitness_function, neighbor_population_size, alteration_limit, distribution_level)


def population_local_search(population: List[Solution], fitness_function: Callable[[Solution], float], neighbor_population_size: int, alteration_limit: float, distribution_level:int) -> List[Solution]:


    if distribution_level >= 2:
        neighbours = []
        for individual in population:
            neighbours.append(distributed_local_search(individual, fitness_function, neighbor_population_size, alteration_limit))
    else:
        neighbours = []
        for individual in population:
            neighbours.append(local_search(individual, fitness_function, neighbor_population_size, alteration_limit))
    return neighbours





# Local Search

def local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float) -> Solution:
    best_neighbor = deepcopy(solution)
    for _ in range(neighbor_population_size):
        neighbor = deepcopy(solution)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return best_neighbor

@ray.remote
def remote_local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float) -> Solution:
    return local_search(solution, fitness_function, neighbor_population_size, alteration_limit)

def distributed_local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float) -> Solution:
    distribution = assign_load_equally(neighbor_population_size)

    get_remote_metagen_logger().debug(
        f"[LEVEL 2] Distributed local search of an individual with {neighbor_population_size} neighbours,"
        f" with {ray.available_resources().get('CPU', 0)} CPUs -- {distribution}")

    futures = []
    for count in distribution:
        futures.append(
            remote_local_search.remote(solution, fitness_function, count, alteration_limit))
    neighbourhood = ray.get(futures)
    best_neighbour = min(neighbourhood, key=lambda sol: sol.get_fitness())
    return best_neighbour
