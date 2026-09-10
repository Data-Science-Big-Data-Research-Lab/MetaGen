from copy import deepcopy
from typing import Any, List, Callable, Tuple

import ray

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed, spawn_seed
from metagen.metaheuristics.tools import random_exploration


@ray.remote
def call_distributed(seed: int, function: Callable, *args: Any, **kargs: Any) -> Any:
    """
    Run a method of the algorithm in a worker, on generators seeded for this task.

    The worker is another process with its own generator state, so without the seed
    no distributed run was reproducible (A-06). The seed comes from spawn_seed() in
    the driver, so the driver's seed decides it.
    """
    set_seed(seed)
    return function(*args, **kargs)


def assign_load_equally(neighbor_population_size: int) -> List[int]:
    """
    Split a workload of the given size into one chunk per CPU of the cluster.

    Sized by the cluster's CPUs, which do not change during a run, and not by the
    ones free at this instant: available_resources() lags behind the tasks that just
    finished and omits the key while every CPU is busy, so from the second iteration
    on this handed the whole workload to a single worker (F-43).

    :param neighbor_population_size: How many units of work there are to split.
    :type neighbor_population_size: int
    :return: The size of each chunk, one per CPU, differing by at most one.
    :rtype: List[int]
    """
    num_cpus = int(ray.cluster_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size)
    if num_cpus == 0:
        num_cpus = 1
    base_count = neighbor_population_size // num_cpus
    remainder = neighbor_population_size % num_cpus
    distribution = [base_count + 1 if i < remainder else base_count for i in range(num_cpus)]
    return distribution


@ray.remote
def remote_random_exploration(seed: int, domain: Domain, fitness_function: Callable[[Solution], float],
                              num_solutions: int) -> Tuple[List[Solution], Solution]:
    set_seed(seed)
    return random_exploration(domain, fitness_function, num_solutions)


def distributed_random_exploration(domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:
    distribution = assign_load_equally(num_solutions)

    futures = []
    for count in distribution:
        futures.append(remote_random_exploration.remote(spawn_seed(), domain, fitness_function, count))

    remote_results = ray.get(futures)
    population = [individual for subpopulation in remote_results for individual in subpopulation[0]]
    best_individual = min([result[1] for result in remote_results], key=lambda sol: sol.get_fitness())

    return population, best_individual