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
import copy
import random
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from utils import domain, solution


def test_random_solution() -> None:
    random.seed(123)
    repetitions = 1000

    for _ in range(repetitions):
        assert solution is not None
        assert solution.get_definition() == domain.get_core()
        assert solution.get_connector() == domain.get_connector()

        variables = solution.get_variables()

        for k, v in variables.items():
            assert solution[k] is not None
            assert solution[k] == v.value
            assert solution.get(k) == v
            assert solution.is_available(k)
            assert solution.fitness == sys.float_info.max

        solution_copy = copy.deepcopy(solution)

        assert solution_copy == solution
        # Alterate all variables which is the most expensive computation
        solution_copy.mutate(alterations_number=len(variables))
        assert solution_copy != solution
