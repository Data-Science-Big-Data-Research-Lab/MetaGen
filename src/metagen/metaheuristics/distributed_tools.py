from typing import List, Callable

import ray

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
