"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import pathlib
import random
import warnings
import numpy as np
from dispatcher import problem_dispatcher
from metagen.metaheuristics import RandomSearch, GA, GAConnector, TabuSearch#CVOA, SSGA, SA, GA, GAConnector, cvoa_launcher
from pytest_csv_params.decorator import csv_params
import ray
import os

warnings.filterwarnings('ignore')

resources_path = pathlib.Path(__file__).parents[0].resolve().as_posix() + "/resources"

"""@csv_params(data_file=resources_path+"/examples.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_cvoa(example: str, iterations: int, seed: int) -> None:
    rs.seed(seed)
    np.rs.seed(seed)

    problem_definition, fitness_function = problem_dispatcher(example)
    algorithm = CVOA(problem_definition, fitness_function, pandemic_duration=iterations)
    algorithm.initialize()

    initial_best = algorithm.best_solution
    assert initial_best is not None

    rs.seed(seed)
    np.rs.seed(seed)

    solution = cvoa_launcher([algorithm], iterations)
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best.fitness
"""
@csv_params(data_file=resources_path+"/examples_ga.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_ga(example: str, iterations: int, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)

    distributed = False
    problem_definition, fitness_function = problem_dispatcher(example, connector=GAConnector())
    algorithm = GA(problem_definition, fitness_function, population_size=50, mutation_rate=0.5, max_iterations=iterations, distributed=distributed)

    if distributed:
        current_folder = os.path.dirname(os.path.abspath(__file__))
        ray.init(runtime_env={"working_dir": current_folder})
        initial_best = float('inf') # Cannot initialize in the distributed case
    else:
        algorithm._initialize()
        initial_best = algorithm.partial_best_solution.fitness if algorithm.partial_best_solution else float('inf')

    random.seed(seed)
    np.random.seed(seed)
    
    assert initial_best is not None
    solution = algorithm.run()
    assert solution is not None
    print(solution)

    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best 

"""
@csv_params(data_file=resources_path+"/examples_ga.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_ssga(example: str, iterations: int, seed: int) -> None:
    rs.seed(seed)
    np.rs.seed(seed)

    problem_definition, fitness_function = problem_dispatcher(example, connector=GAConnector())
    algorithm = SSGA(problem_definition, fitness_function, n_iterations=iterations)
    algorithm.initialize()

    rs.seed(seed)
    np.rs.seed(seed)

    initial_best = algorithm.best_solution
    assert initial_best is not None
    solution = algorithm.run()
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best.fitness

@csv_params(data_file=resources_path+"/examples.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_sa(example: str, iterations: int, seed: int) -> None:
    rs.seed(seed)
    np.rs.seed(seed)

    problem_definition, fitness_function = problem_dispatcher(example)
    algorithm = SA(problem_definition, fitness_function, n_iterations=iterations)
    algorithm.initialize()

    rs.seed(seed)
    np.rs.seed(seed)

    initial_best = algorithm.best_solution
    assert initial_best is not None
    solution = algorithm.run()
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    # assert solution.fitness <= initial_best.fitness, cannot be guaranteed in this case"""

@csv_params(data_file=resources_path+"/examples.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_rs(example: str, iterations: int, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)

    distributed = True
    problem_definition, fitness_function = problem_dispatcher(example)
    algorithm = RandomSearch(problem_definition, fitness_function, population_size=50, max_iterations=iterations, distributed=distributed)

    if distributed:
        current_folder = os.path.dirname(os.path.abspath(__file__))
        ray.init(runtime_env={"working_dir": current_folder})
        initial_best = float('inf') # Cannot initialize in the distributed case
    else:
        algorithm._initialize()
        initial_best = algorithm.partial_best_solution.fitness if algorithm.partial_best_solution else float('inf')

    random.seed(seed)
    np.random.seed(seed)

    
    assert initial_best is not None
    solution = algorithm.run()
    print(solution)
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best 

@csv_params(data_file=resources_path+"/examples.csv", id_col="ID#",
            data_casts={"iterations": int, "seed": int})
def test_ts(example: str, iterations: int, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)

    distributed = True
    problem_definition, fitness_function = problem_dispatcher(example)
    algorithm = TabuSearch(problem_definition, fitness_function, population_size=50, max_iterations=iterations, distributed=distributed)

    if distributed:
        current_folder = os.path.dirname(os.path.abspath(__file__))
        ray.init(runtime_env={"working_dir": current_folder})
        initial_best = float('inf') # Cannot initialize in the distributed case
    else:
        algorithm._initialize()
        initial_best = algorithm.partial_best_solution.fitness if algorithm.partial_best_solution else float('inf')

    random.seed(seed)
    np.random.seed(seed)

    
    assert initial_best is not None
    solution = algorithm.run()
    print(solution)
    assert solution is not None
    assert hasattr(solution, 'fitness')
    assert solution.fitness < float('inf')
    assert solution.fitness <= initial_best 


if __name__ == "__main__":
    test_ts("simple-1", 50, 0)
