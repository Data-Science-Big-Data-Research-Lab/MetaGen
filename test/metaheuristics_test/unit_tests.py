import logging
import random

import numpy as np
import pytest
import ray
from pytest_csv_params.decorator import csv_params

from metagen.logging.metagen_logger import get_metagen_logger, metagen_logger_setup
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, GAConnector, SSGA
from metagen.metaheuristics.mm.memetic import Memetic
from metaheuristics_test.metaheuristic_factory import get_metaheuristic
from metaheuristics_test.problems.dispatcher import problem_dispatcher
from utils import resource_path, str_to_bool, safe_str_to_bool, safe_str, safe_int, safe_float

import warnings

warnings.filterwarnings("ignore", module="sklearn")

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
    metagen_logger_setup(logging.DEBUG)
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
    metagen_logger_setup(logging.DEBUG)
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



@csv_params(data_file=resource_path("mm_parameters.csv"),
            id_col="ID#",
            data_casts={"active": str_to_bool, "problem": str, "population_size": int, "max_iterations": int, "mutation_rate": float,
                        "neighbor_population_size": int, "alteration_limit": float,
                        "distributed": str_to_bool, "log_dir": str, "distribution_level": int, "seed": int})
def test_mm(active: bool, problem: str, population_size: int, max_iterations: int, mutation_rate: float,
            neighbor_population_size: int, alteration_limit: float,
            distributed: bool, log_dir: str,
            distribution_level: int,
            seed: int) -> None:
    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    logging.Logger("metagen_logger")
    metagen_logger_setup(logging.INFO)
    get_metagen_logger().info(f'Running Memetic Algorithm')

    if distributed:
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    algorithm = Memetic(problem_definition, fitness_function, population_size,
                        max_iterations, mutation_rate, neighbor_population_size, alteration_limit,
                        distributed, log_dir,
                        distribution_level)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("metaheuristic_parameters.csv"),
            id_col="ID#",
            data_casts={"active": safe_str_to_bool, "metaheuristic":safe_str, "problem": safe_str,
                        "population_size": safe_int, "max_iterations": safe_int,
                        "tabu_size": safe_int, "alteration_limit": safe_float, "initial_temp": safe_float, "cooling_rate": safe_float,
                        "neighbor_population_size": safe_int, "mutation_rate": safe_float,
                        "distributed": safe_str_to_bool, "log_dir": safe_str, "distribution_level": safe_int, "seed": safe_int})

def test_metaheuristic(active: bool, metaheuristic:str, problem: str,
                       population_size: int, max_iterations: int,
                       tabu_size: int, alteration_limit: float, initial_temp: float, cooling_rate: float,
                       neighbor_population_size: int, mutation_rate: float,
                       distributed: bool, log_dir: str, distribution_level: int, seed: int) -> None:

    if not active:
        pytest.skip('Skipped')

    if metaheuristic == 'mm' or metaheuristic == 'ssga' or metaheuristic == 'ga':
        problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    else:
        problem_definition, fitness_function = problem_dispatcher(problem)

    message, algorithm = get_metaheuristic(metaheuristic, problem_definition, fitness_function, distributed, log_dir,
                                  population_size=population_size, max_iterations=max_iterations,
                                  tabu_size=tabu_size, alteration_limit=alteration_limit,
                                  initial_temp=initial_temp, cooling_rate=cooling_rate,
                                  neighbor_population_size=neighbor_population_size,
                                  mutation_rate=mutation_rate, distribution_level=distribution_level)

    if distributed:
        ray.init(num_cpus=4)

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    get_metagen_logger().info(message)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    get_metagen_logger().info(f"Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best