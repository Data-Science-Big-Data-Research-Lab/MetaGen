import logging
import random
import warnings

import numpy as np
import pytest
import ray
from pytest_csv_params.decorator import csv_params

from metagen.logging.metagen_logger import get_metagen_logger, metagen_logger_setup
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, GAConnector, SSGA
from metaheuristics.problems.dispatcher import problem_dispatcher
from utils import resource_path, str_to_bool

warnings.filterwarnings('ignore')

@pytest.fixture(autouse=True)
def reset_logger():
    logger = logging.getLogger('metagen_logger')
    yield
    # Remove all handlers associated with the logger
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()


@csv_params(data_file=resource_path("rs_parameters.csv"),
            id_col="ID#",
            data_casts={"problem":str,"population_size": int, "max_iterations":int,
                        "distributed":str_to_bool, "log_dir":str,"seed": int})
def test_rs(problem: str, population_size: int, max_iterations:int, distributed:bool, log_dir:str, seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup()
    get_metagen_logger().info('Running Random Search')

    if distributed:
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem)
    algorithm = RandomSearch(problem_definition, fitness_function, population_size, max_iterations, distributed, log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("sa_parameters.csv"),
            id_col="ID#",
            data_casts={"problem":str,
                        "max_iterations":int,
                        "alteration_limit": float, "initial_temp": float,
                        "cooling_rate": float, "neighbor_population_size": int,
                        "distributed":str_to_bool, "log_dir":str,"seed": int})

def test_sa(problem: str, max_iterations:int, alteration_limit: float, initial_temp: float,
            cooling_rate: float, neighbor_population_size: int, distributed:bool, log_dir:str, seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup()
    get_metagen_logger().info('Running Simulated Annealing')

    if distributed:
        print('ray init')
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem)
    algorithm = SA(problem_definition, fitness_function, max_iterations, alteration_limit, initial_temp,
                   cooling_rate, neighbor_population_size, distributed, log_dir)

    random.seed(seed)
    np.random.seed(seed)

    solution = algorithm.run()
    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("ts_parameters.csv"),
            id_col="ID#",
            data_casts={"problem":str,"population_size": int, "max_iterations":int,
                        "tabu_size":int, "alteration_limit": float,
                        "distributed":str_to_bool, "log_dir":str,"seed": int})
def test_ts(problem: str, population_size: int, max_iterations:int, tabu_size:int, alteration_limit:float, distributed:bool, log_dir:str, seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup()
    get_metagen_logger().info('Running Tabu Search')

    if distributed:
        ray.init(num_cpus=4)


    problem_definition, fitness_function = problem_dispatcher(problem)
    algorithm = TabuSearch(problem_definition, fitness_function, population_size, max_iterations, tabu_size, alteration_limit, distributed, log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("ga_parameters.csv"),
            id_col="ID#",
            data_casts={"problem":str,"population_size": int, "max_iterations":int, "mutation_rate": float,
                        "distributed":str_to_bool, "log_dir":str,"seed": int})
def test_ga(problem: str, population_size: int, max_iterations:int, mutation_rate:float, distributed:bool, log_dir:str, seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup()
    get_metagen_logger().info('Running Genetic Algorithm')

    if distributed:
        ray.init(num_cpus=4)


    problem_definition, fitness_function = problem_dispatcher(problem,GAConnector())
    algorithm = GA(problem_definition, fitness_function, population_size, max_iterations, mutation_rate, distributed, log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best

@csv_params(data_file=resource_path("ga_parameters.csv"),
            id_col="ID#",
            data_casts={"problem":str,"population_size": int, "max_iterations":int, "mutation_rate": float,
                        "distributed":str_to_bool, "log_dir":str,"seed": int})
def test_ssga(problem: str, population_size: int, max_iterations:int, mutation_rate:float, distributed:bool, log_dir:str, seed: int) -> None:

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup()
    get_metagen_logger().info('Running Steady State Genetic Algorithm')

    if distributed:
        ray.init(num_cpus=4)


    problem_definition, fitness_function = problem_dispatcher(problem,GAConnector())
    algorithm = SSGA(problem_definition, fitness_function, population_size, max_iterations, mutation_rate, distributed, log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best

