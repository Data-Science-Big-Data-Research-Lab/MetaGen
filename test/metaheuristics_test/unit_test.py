import random

import numpy as np
import pytest
import ray
from pytest_csv_params.decorator import csv_params

from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, GAConnector, SSGA, TPE
from metagen.metaheuristics.gamma_schedules import GammaConfig
from metagen.metaheuristics.mm.memetic import Memetic


import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metaheuristics_test.metaheuristic_factory import get_metaheuristic
from metaheuristics_test.problems.dispatcher import problem_dispatcher
from utils import metaheuristic_parameters_resource_path, str_to_bool, safe_str_to_bool, safe_str, safe_int, safe_float

import warnings

warnings.filterwarnings("ignore", module="sklearn")

@csv_params(data_file=metaheuristic_parameters_resource_path("rs.csv"),
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
        ray.init(num_cpus=4, ignore_reinit_error=True)

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


@csv_params(data_file=metaheuristic_parameters_resource_path("sa.csv"),
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
        ray.init(num_cpus=4, ignore_reinit_error=True)

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

@csv_params(data_file=metaheuristic_parameters_resource_path("ts.csv"),
            id_col="ID#",
            data_casts={"active":safe_str_to_bool, "problem": safe_str, "population_size": safe_int,
                        "warmup_iterations": safe_int, "max_iterations": safe_int, "tabu_size": safe_int,
                        "alteration_limit": safe_float,"gamma":safe_str, "gamma_min": safe_float, "gamma_max": safe_float,"gamma_alpha": safe_float,
                        "distributed": safe_str_to_bool,"log_dir": safe_str, "seed": safe_int, "logging_level":safe_int})
def test_ts(active:bool, problem: str, population_size: int, warmup_iterations: int, max_iterations: int,
            tabu_size: int, alteration_limit: float, gamma: str, gamma_min:float, gamma_max:float, gamma_alpha:float,
            distributed: bool, log_dir: str, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    metagen_logger.setLevel(logging_level)

    if distributed:
        ray.init(num_cpus=4, ignore_reinit_error=True)

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


@csv_params(data_file=metaheuristic_parameters_resource_path("ga.csv"),
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
        ray.init(num_cpus=4, ignore_reinit_error=True)


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

@csv_params(data_file=metaheuristic_parameters_resource_path("ga.csv"),
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
        ray.init(num_cpus=4, ignore_reinit_error=True)

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



@csv_params(data_file=metaheuristic_parameters_resource_path("mm.csv"),
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
        ray.init(num_cpus=4, ignore_reinit_error=True)

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

@csv_params(data_file=metaheuristic_parameters_resource_path("tpe.csv"),
            id_col="ID#",
            data_casts={"active": safe_str_to_bool, "problem": safe_str, "max_iterations": safe_int,
                        "warmup_iterations": safe_int, "candidate_pool_size": safe_int,
                        "gamma":safe_str, "gamma_min": safe_float, "gamma_max": safe_float,"gamma_alpha": safe_float,
                        "distributed": safe_str_to_bool, "log_dir": safe_str, "seed": safe_int, "logging_level":safe_int})
def test_tpe(active:bool, problem: str, max_iterations: int, warmup_iterations: int,
             candidate_pool_size: int, gamma: str, gamma_min:float, gamma_max:float, gamma_alpha:float,
             distributed: bool, log_dir: str, seed: int, logging_level:int) -> None:

    if not active:
        pytest.skip('Skipped')

    metagen_logger.setLevel(logging_level)

    # Set random seeds for reproducibility
    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    # Initialize Ray if using distributed execution
    if distributed:
        ray.init(num_cpus=4, ignore_reinit_error=True)

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

@csv_params(data_file=metaheuristic_parameters_resource_path("global.csv"),
            id_col="ID#",
            data_casts={"active": safe_str_to_bool, "metaheuristic": safe_str, "problem": safe_str,
                        "population_size": safe_int, "max_iterations": safe_int,
                        "tabu_size": safe_int, "alteration_limit": safe_float, "initial_temp": safe_float,
                        "cooling_rate": safe_float, "neighbor_population_size": safe_int, "mutation_rate": safe_float,
                        "candidate_pool_size": safe_int, "gamma": safe_str, "gamma_min": safe_float, "gamma_max": safe_float,
                        "gamma_alpha": safe_float, "distributed": safe_str_to_bool, "log_dir": safe_str,
                        "distribution_level": safe_int, "seed": safe_int, "logging_level": safe_int})

def test_metaheuristic(active: bool, metaheuristic: str, problem: str,
                       population_size: int, max_iterations: int,
                       tabu_size: int, alteration_limit: float, initial_temp: float, cooling_rate: float,
                       neighbor_population_size: int, mutation_rate: float, candidate_pool_size: int,
                       gamma: str, gamma_min: float, gamma_max: float, gamma_alpha: float,
                       distributed: bool, log_dir: str, distribution_level: int, seed: int, logging_level: int) -> None:

    if not active:
        pytest.skip('Skipped')

    # Configuración de logging
    metagen_logger.setLevel(logging_level)

    # Configuración de la semilla para reproducibilidad
    random.seed(seed)
    np.random.seed(seed)
    initial_best = float('inf')

    # Obtener la definición del problema y la función de fitness
    if metaheuristic in ['mm', 'ssga', 'ga']:
        problem_definition, fitness_function = problem_dispatcher(problem, GAConnector())
    else:
        problem_definition, fitness_function = problem_dispatcher(problem)

    # Inicializar Ray si es necesario
    if distributed:
        ray.init(num_cpus=4, ignore_reinit_error=True)

    # Obtener el algoritmo correspondiente usando la nueva función `get_metaheuristic`
    message, algorithm = get_metaheuristic(metaheuristic, problem_definition, fitness_function,
                                           distributed, log_dir,
                                           population_size=population_size, max_iterations=max_iterations,
                                           tabu_size=tabu_size, alteration_limit=alteration_limit,
                                           initial_temp=initial_temp, cooling_rate=cooling_rate,
                                           neighbor_population_size=neighbor_population_size,
                                           mutation_rate=mutation_rate, candidate_pool_size=candidate_pool_size,
                                           gamma=gamma, gamma_min=gamma_min, gamma_max=gamma_max, gamma_alpha=gamma_alpha,
                                           distribution_level=distribution_level)

    # Registrar mensaje de inicio
    metagen_logger.info(message)

    # Volver a inicializar la semilla antes de ejecutar el algoritmo
    random.seed(seed)
    np.random.seed(seed)

    # Ejecutar el algoritmo
    solution = algorithm.run()

    # Apagar Ray si fue usado
    if distributed:
        ray.shutdown()

    # Mostrar el resultado
    print(f" ---- Solution found: {solution}")

    # Verificar que la solución es válida
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best