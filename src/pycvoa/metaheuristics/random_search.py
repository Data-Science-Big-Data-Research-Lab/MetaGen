from copy import deepcopy
from typing import Callable, List

from pycvoa.problem import Domain, Solution
from pycvoa.problem.support import build_random_solution, alter_potential_solution


# Random search method receives a Domain and a fitness function as input arguments
#
def random_search(domain: Domain, fitness: Callable[[Solution], float], search_space_size: int = 30,
                  iterations=20) -> Solution:

    potential_solutions: List[Solution] = list()
    for _ in range(0, search_space_size):
        potential_solutions.append(build_random_solution(domain, fitness))
    solution: Solution = deepcopy(min(potential_solutions))

    for _ in range(0, iterations):
        for ps in potential_solutions:
            alter_potential_solution(ps, domain)
            ps.fitness = fitness(ps)
            if ps < solution:
                solution = deepcopy(ps)

    return solution
