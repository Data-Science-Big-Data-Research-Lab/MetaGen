import pathlib
import random
import warnings
import numpy as np
from dispatcher import example_dispatcher
from pytest_csv_params.decorator import csv_params

warnings.filterwarnings('ignore')


@csv_params(data_file=pathlib.Path(__file__).parents[0].resolve().as_posix() + "/resources/examples.csv", id_col="ID#",
            data_casts={"expected_fitness": float, "iterations": int, "seed": int})
def test_random_solution(example: str, expected_fitness: float, iterations: int, seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    solution = example_dispatcher(example, iterations)

    assert solution.fitness <= expected_fitness
