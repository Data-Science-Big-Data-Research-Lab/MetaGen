import random

import numpy as np
import pytest
import ray
from pytest_csv_params.decorator import csv_params

from metagen.logging.metagen_logger import metagen_logger, set_metagen_logger_level
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, GAConnector, SSGA, TPE
from metagen.metaheuristics.gamma_schedules import GammaConfig
from metagen.metaheuristics.mm.memetic import Memetic


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metaheuristics_test.metaheuristic_factory import get_metaheuristic
from metaheuristics_test.problems.dispatcher import problem_dispatcher
from utils import resource_path, str_to_bool, safe_str_to_bool, safe_str, safe_int, safe_float

import warnings

warnings.filterwarnings("ignore", module="sklearn")

@csv_params(data_file=resource_path("rs_parameters.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool,"problem":safe_str,"population_size": safe_int, "max_iterations":safe_int,
                        "distributed":safe_str_to_bool, "log_dir":safe_str,"seed": safe_int, "logging_level":safe_int})
def test_rs(active: bool, problem: str, population_size: int, max_iterations:int, distributed:bool,
            log_dir:str, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem)

    algorithm = RandomSearch(problem_definition, fitness_function,
                             population_size=population_size, max_iterations=max_iterations,
                             distributed=distributed, log_dir=log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("sa_parameters.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool, "problem":safe_str, "warmup_iterations":safe_int,
                        "max_iterations":safe_int, "alteration_limit": safe_int, "initial_temp": safe_float,
                        "cooling_rate": safe_float, "neighbor_population_size": safe_int,
                        "distributed":safe_str_to_bool, "log_dir":str,"seed": safe_int, "logging_level":safe_int})

def test_sa(active: bool, problem: str, warmup_iterations:int, max_iterations:int, alteration_limit: int, initial_temp: float,
            cooling_rate: float, neighbor_population_size: int, distributed:bool, log_dir:str, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        print('ray init')
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem)
    algorithm = SA(problem_definition, fitness_function, warmup_iterations=warmup_iterations,
                   max_iterations=max_iterations,
                   alteration_limit=alteration_limit, initial_temp=initial_temp,
                   cooling_rate=cooling_rate, neighbor_population_size=neighbor_population_size,
                   distributed=distributed, log_dir=log_dir)

    random.seed(seed)
    np.random.seed(seed)

    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("ts_parameters.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool, "problem": safe_str, "population_size": safe_int,
                        "warmup_iterations": safe_int, "max_iterations": safe_int, "tabu_size": safe_int,
                        "alteration_limit": safe_float,"gamma":safe_str, "gamma_min": safe_float, "gamma_max": safe_float,"gamma_alpha": safe_float,
                        "distributed": safe_str_to_bool,"log_dir": safe_str, "seed": safe_int, "logging_level":safe_int})
def test_ts(active:bool, problem: str, population_size: int, warmup_iterations: int, max_iterations: int,
            tabu_size: int, alteration_limit: float, gamma: str, gamma_min:float, gamma_max:float, gamma_alpha:float,
            distributed: bool, log_dir: str, seed: int, logging_level:int) -> None:
    """
    Test for Tabu Search.

    This function initializes the Tabu Search algorithm with parameters from a CSV file,
    runs the optimization process, and verifies that the solution is valid.

    :param problem: The problem to solve.
    :param population_size: The size of the neighborhood population.
    :param warmup_iterations: Number of warmup iterations before starting the main search.
    :param max_iterations: The maximum number of iterations.
    :param tabu_size: The size of the tabu list.
    :param alteration_limit: Maximum proportion of a solution to alter.
    :param distributed: Whether to use distributed computation.
    :param log_dir: Directory for logging.
    :param seed: Random seed for reproducibility.
    """

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        print('ray init')
        ray.init(num_cpus=4)

    if gamma != '':
        gamma_config = GammaConfig(
            gamma_function=gamma,
            minimum=gamma_min,
            maximum=gamma_max,
            alpha=gamma_alpha
        )
    else:
        gamma_config = None

    # Get problem definition and fitness function
    problem_definition, fitness_function = problem_dispatcher(problem)

    # Initialize Tabu Search algorithm
    algorithm = TabuSearch(problem_definition, fitness_function, population_size=population_size,
                           warmup_iterations=warmup_iterations,
                           max_iterations=max_iterations, tabu_size=tabu_size, alteration_limit=alteration_limit,
                           gamma_config=gamma_config, distributed=distributed, log_dir=log_dir)

    # Run the optimization algorithm
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    # Assertions to ensure the solution is valid
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best


@csv_params(data_file=resource_path("ga_parameters.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool, "problem":safe_str,"population_size": safe_int,
                        "max_iterations":safe_int, "mutation_rate": safe_float,"distributed":safe_str_to_bool,
                        "log_dir":safe_str,"seed": safe_int, "logging_level":safe_int})
def test_ga(active:bool, problem: str, population_size: int, max_iterations:int, mutation_rate:float,
            distributed:bool, log_dir:str, seed: int, logging_level:int) -> None:


    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        ray.init(num_cpus=4)


    problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    algorithm = GA(problem_definition, fitness_function, population_size=population_size, max_iterations=max_iterations,
                   mutation_rate=mutation_rate, distributed=distributed, log_dir=log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best

@csv_params(data_file=resource_path("ga_parameters.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool, "problem":str,"population_size": int, "max_iterations":int, "mutation_rate": float,
                        "distributed":str_to_bool, "log_dir":str,"seed": int, "logging_level":safe_int})
def test_ssga(active:bool, problem: str, population_size: int, max_iterations:int, mutation_rate:float,
              distributed:bool, log_dir:str, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    algorithm = SSGA(problem_definition, fitness_function, population_size=population_size, max_iterations=max_iterations,
                   mutation_rate=mutation_rate, distributed=distributed, log_dir=log_dir)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best



@csv_params(data_file=resource_path("mm_parameters.csv"),
            id_col="ID#",
            data_casts={"active": safe_str_to_bool, "problem": safe_str, "population_size": safe_int, "max_iterations": safe_int, "mutation_rate": float,
                        "neighbor_population_size": safe_int, "alteration_limit": safe_float,
                        "distributed": safe_str_to_bool, "log_dir": safe_str, "distribution_level": safe_int, "seed": safe_int, "logging_level":safe_int})
def test_mm(active: bool, problem: str, population_size: int, max_iterations: int, mutation_rate: float,
            neighbor_population_size: int, alteration_limit: float,
            distributed: bool, log_dir: str,
            distribution_level: int,
            seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        ray.init(num_cpus=4)

    problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    algorithm = Memetic(problem_definition, fitness_function, population_size=population_size,
                        max_iterations=max_iterations, mutation_rate=mutation_rate,
                        neighbor_population_size=neighbor_population_size, alteration_limit=alteration_limit,
                        distributed=distributed, log_dir=log_dir,
                        distribution_level=distribution_level)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best

@csv_params(data_file=resource_path("tpe_parameters.csv"),
            id_col="ID#",
            data_casts={"active": safe_str_to_bool, "problem": safe_str, "max_iterations": safe_int,
                        "warmup_iterations": safe_int, "candidate_pool_size": safe_int,
                        "gamma":safe_str, "gamma_min": safe_float, "gamma_max": safe_float,"gamma_alpha": safe_float,
                        "distributed": safe_str_to_bool, "log_dir": safe_str, "seed": safe_int, "logging_level":safe_int})
def test_tpe(active:bool, problem: str, max_iterations: int, warmup_iterations: int,
             candidate_pool_size: int, gamma: str, gamma_min:float, gamma_max:float, gamma_alpha:float,
             distributed: bool, log_dir: str, seed: int, logging_level:int) -> None:
    """
    Test for Tree-structured Parzen Estimator (TPE) metaheuristic.

    The test initializes the TPE algorithm with parameters provided in a CSV file,
    runs the optimization process, and verifies that the solution is valid.

    :param problem: The problem to solve.
    :param population_size: The size of the population.
    :param max_iterations: The maximum number of iterations.
    :param warmup_iterations: Number of initial random exploration iterations.
    :param candidate_pool_size: The number of candidates sampled in each iteration.
    :param distributed: Whether to use distributed computation.
    :param log_dir: Directory for logging.
    :param seed: Random seed for reproducibility.
    """

    if not active:
        pytest.skip('Skipped')

    metagen_logger.setLevel(logging_level)

    # Set random seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    # Initialize Ray if using distributed execution
    if distributed:
        ray.init(num_cpus=4)

    if gamma != '':
        gamma_config = GammaConfig(
            gamma_function=gamma,
            minimum=gamma_min,
            maximum=gamma_max,
            alpha=gamma_alpha
        )
    else:
        gamma_config = None

    # Get problem definition and fitness function
    problem_definition, fitness_function = problem_dispatcher(problem)

    # Initialize TPE algorithm
    algorithm = TPE(problem_definition, fitness_function, max_iterations=max_iterations,
                    warmup_iterations=warmup_iterations, candidate_pool_size=candidate_pool_size,
                    gamma_config=gamma_config,distributed=distributed, log_dir=log_dir)

    # Run the optimization algorithm
    solution = algorithm.run()

    # Shutdown Ray if it was used
    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    # Validate the solution
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
                        "distributed": safe_str_to_bool, "log_dir": safe_str, "distribution_level": safe_int, "seed": safe_int, "logging_level":safe_int})

def test_metaheuristic(active: bool, metaheuristic:str, problem: str,
                       population_size: int, max_iterations: int,
                       tabu_size: int, alteration_limit: float, initial_temp: float, cooling_rate: float,
                       neighbor_population_size: int, mutation_rate: float,
                       distributed: bool, log_dir: str, distribution_level: int, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    metagen_logger.setLevel(logging_level)

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
        ray.init(num_cpus=4, ignore_reinit_error=True)

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.info(message)

    random.seed(seed)
    np.random.seed(seed)
    solution = algorithm.run()

    if distributed:
        ray.shutdown()

    print(f" ---- Solution found: {solution}")

    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best