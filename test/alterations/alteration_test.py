import copy
import random
import sys
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

from utils import domain, solution


def test_random_solution() -> None:
    random.seed(123)
    repetitions = 10000

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
