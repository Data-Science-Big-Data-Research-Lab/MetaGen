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
