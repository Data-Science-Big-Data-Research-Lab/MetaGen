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

    The worker is another process with its own generator state, so it is seeded
    here to make a distributed run reproducible. The seed comes from spawn_seed() in
    the driver, so the driver's seed decides it.
    """
    # A-06: without the seed no distributed run was reproducible.
    set_seed(seed)
    return function(*args, **kargs)


def assign_load_equally(neighbor_population_size: int, minimum_chunk: int = 1) -> List[int]:
    """
    Split a workload of the given size into one chunk per CPU of the cluster, no
    chunk smaller than ``minimum_chunk``.

    Sized by the cluster's CPUs, which do not change during a run, and not by the
    ones free at this instant: available_resources() lags behind the tasks that just
    finished and omits the key while every CPU is busy, which would hand the whole
    workload to a single worker.

    The minimum is the algorithm's: GA and Memetic pick a two-individual elite, so a
    population split across more CPUs than it has individuals must not leave islands
    of one. With a minimum of two, ten individuals on ten CPUs make five islands of two.

    :param neighbor_population_size: How many units of work there are to split.
    :type neighbor_population_size: int
    :param minimum_chunk: The fewest units a chunk may hold (default is 1).
    :type minimum_chunk: int, optional
    :return: The size of each chunk, one per CPU at most, differing by at most one.
    :rtype: List[int]
    """
    # F-43: sizing by available_resources() sent everything to one worker from the
    # second iteration on. F-46: islands of one raised IndexError in GA and Memetic.
    num_cpus = int(ray.cluster_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size // max(1, minimum_chunk))
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