from typing import Any, Callable, List, Sequence, Tuple

import ray

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed, spawn_seed
from metagen.metaheuristics.tools import Counts, add_calls, calls_of, random_exploration


@ray.remote
def call_method(seed: int, algorithm: Any, name: str, slice_index: int, *args: Any) -> Any:
    """
    Run a method of the algorithm in a worker, on generators seeded for this task, as the
    copy that runs slice ``slice_index``.

    The algorithm arrives as one object for all the tasks of an iteration, put in the
    object store once by the driver; each task works on its own copy of it, so what the
    method writes on it stays in the worker (F-40).

    :return: What the method returns, and the evaluations of the fitness it made, which
        the driver adds to its own.
    """
    # E-06 of the independent audit: the bound method sent with every task carried the
    # whole algorithm, the data its fitness function closes over included, once per task.
    set_seed(seed)
    algorithm.distributed_slice = slice_index
    fitness_function = algorithm.fitness_function
    before = calls_of(fitness_function)
    result = getattr(algorithm, name)(*args)
    return result, calls_of(fitness_function) - before


def assign_load_equally(neighbor_population_size: int, minimum_chunk: int = 1) -> List[int]:
    """
    Split a workload of the given size into one chunk per CPU of the cluster, no
    chunk smaller than ``minimum_chunk``.

    Sized by the cluster's CPUs, which do not change during a run, and not by the
    ones free at this instant: available_resources() lags behind the tasks that just
    finished and omits the key while every CPU is busy, which would hand the whole
    workload to a single worker.

    The minimum is the algorithm's: GA and Memetic pick a two-individual elite and need
    room for children next to it, so a population must not be split into slices too
    small for that. With a minimum of four, twenty individuals on ten CPUs make five
    slices of four, and three individuals make one slice of three.

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
def _call_counted(seed: int, function: Callable[..., Any], arguments: Tuple[Any, ...], counted: int) -> Tuple[Any, Counts]:
    """
    Run a function in a worker, on generators seeded for this task, and count the
    evaluations of the fitness function at position ``counted`` of its arguments.

    The arguments travel as one tuple so that the fitness function counted is the very one
    the function calls: each argument of a task is a copy of its own.
    """
    set_seed(seed)
    fitness_function = arguments[counted]
    before = calls_of(fitness_function)
    result = function(*arguments)
    return result, calls_of(fitness_function) - before


def scatter(function: Callable[..., Any], tasks: Sequence[Tuple[Any, ...]], counted: int) -> List[Any]:
    """
    Run a function on Ray once per task and give back what each call returned, in order.

    Every task is seeded from the driver, with seeds drawn in the order of the tasks, so a
    seeded run reproduces; and the evaluations each one makes on its copy of the fitness
    function, the argument at position ``counted``, are added to the driver's.

    :param function: The function to run, importable by the workers.
    :type function: Callable
    :param tasks: The arguments of each call.
    :type tasks: Sequence[Tuple]
    :param counted: The position of the fitness function among the arguments.
    :type counted: int
    :return: What each call returned.
    :rtype: List
    """
    # The pattern was written out by hand for every function run on Ray, and a copy that
    # missed a part of it gave F-11 (O-01, metagen-auditoria/auditoria-independiente-2026-11/organizacion.md).
    answers = ray.get([_call_counted.remote(spawn_seed(), function, tuple(arguments), counted) for arguments in tasks])
    if tasks:
        add_calls(tasks[0][counted], sum(calls for _, calls in answers))
    return [result for result, _ in answers]


def distributed_random_exploration(domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
        -> Tuple[List[Solution], Solution]:
    answers = scatter(random_exploration, [(domain, fitness_function, count)
                                           for count in assign_load_equally(num_solutions)], counted=1)
    population = [individual for subpopulation, _ in answers for individual in subpopulation]
    best_individual = min([best for _, best in answers], key=lambda sol: sol.get_fitness())
    return population, best_individual
