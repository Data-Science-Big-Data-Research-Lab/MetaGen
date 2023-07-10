from copy import deepcopy
from typing import Callable, List

from metagen.framework import Domain, Solution


class RandomSearch:

    def __init__(self, domain: Domain, fitness: Callable[[Solution], float], search_space_size: int = 30,
                 iterations: int = 20) -> None:

        self.domain = domain
        self.fitness = fitness
        self.search_space_size = search_space_size
        self.iterations = iterations

    def run(self) -> Solution:

        potential_solutions: List[Solution] = list()
        solution_type: type[Solution] = self.domain.get_connector().get_type(
            self.domain.get_core())
        
        for _ in range(0, self.search_space_size):
            potential_solutions.append(solution_type(
                self.domain, connector=self.domain.get_connector()))
        solution: Solution = deepcopy(min(potential_solutions))

        for _ in range(0, self.iterations):
            for ps in potential_solutions:
                ps.mutate()
                ps.evaluate(self.fitness)
                if ps < solution:
                    solution = deepcopy(ps)

        return solution
