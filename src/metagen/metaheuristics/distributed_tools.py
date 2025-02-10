from copy import deepcopy
from typing import List, Callable, Tuple

import ray

from metagen.framework import Domain, Solution
from metagen.metaheuristics.tools import random_exploration


@ray.remote
def call_distributed(function: Callable, *args, **kargs) -> None:
    """
    Initialize the population/solutions for the metaheuristic in a distributed manner.
    Must set self.current_solutions and self.best_solution
    """
    # metagen_remote_logger_setup(level=logging.DEBUG)
    # get_metagen_logger().info(f"Initializing distributed function {function.__name__}")
    return function(*args, **kargs)


def assign_load_equally(neighbor_population_size: int) -> List[int]:
    num_cpus = int(ray.available_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size)
    if num_cpus == 0:
        num_cpus = 1
    base_count = neighbor_population_size // num_cpus
    remainder = neighbor_population_size % num_cpus
    distribution = [base_count + 1 if i < remainder else base_count for i in range(num_cpus)]
    return distribution


@ray.remote
def remote_random_exploration(domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:
    return random_exploration(domain, fitness_function, num_solutions)


def distributed_random_exploration(domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:
    distribution = assign_load_equally(num_solutions)

    futures = []
    for count in distribution:
        futures.append(remote_random_exploration.remote(domain, fitness_function, count))

    remote_results = ray.get(futures)
    population = [individual for subpopulation in remote_results for individual in subpopulation[0]]
    best_individual = min([result[1] for result in remote_results], key=lambda sol: sol.get_fitness())

    return population, best_individual