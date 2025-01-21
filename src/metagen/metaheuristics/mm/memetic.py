import heapq
from copy import deepcopy
from typing import Callable, Tuple, List, cast

from metagen.framework import Domain, Solution
from metagen.framework.solution.tools import yield_potential_solutions
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.ga import GASolution
from metagen.metaheuristics.ga.ga_tools import yield_two_children
from metagen.metaheuristics.mm.mm_tools import local_search_of_two_children


class Memetic(Metaheuristic):

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size: int = 10,
                 max_iterations: int = 20, mutation_rate: float = 0.1,
                 neighbor_population_size: int = 10, alteration_limit: float = 1.0,
                 distributed: bool = False, log_dir: str = "logs/MM",
                 distribution_level: int = 0) -> None:
        super().__init__(domain, fitness_function, population_size, distributed, log_dir)

        self.mutation_rate = mutation_rate
        self.max_generations = max_iterations
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit

        if not distributed:
            self.distribution_level = 0
        else:
            self.distribution_level = distribution_level

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        current_solutions, best_solution = yield_potential_solutions(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[Solution], Solution]:

        num_solutions = len(solutions)
        best_parents = heapq.nsmallest(2, solutions, key=lambda sol: sol.get_fitness())
        best_solution = deepcopy(self.best_solution)
        current_solutions = [deepcopy(best_parents[0]), deepcopy(best_parents[1])]

        for _ in range(num_solutions // 2):

            father = cast(GASolution, best_parents[0])
            mother = cast(GASolution, best_parents[1])
            child1, child2 = yield_two_children((father, mother), self.mutation_rate, self.fitness_function)
            lc_child1, lc_child2 = local_search_of_two_children((child1, child2), self.fitness_function,
                                                                self.neighbor_population_size,
                                                                self.alteration_limit, self.distribution_level)

            current_solutions.extend([lc_child1, lc_child2])

            if best_solution is None or lc_child1 < best_solution:
                best_solution = lc_child1
            if best_solution is None or lc_child2 < best_solution:
                best_solution = lc_child2

        current_solutions = current_solutions[:num_solutions]

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_generations
