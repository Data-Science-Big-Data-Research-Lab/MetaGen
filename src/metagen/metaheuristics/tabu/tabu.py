from collections import deque
from metagen.framework import Domain, Solution
from collections.abc import Callable
from typing import List, Tuple

from metagen.logging.metagen_logger import get_metagen_logger
from metagen.metaheuristics.base import Metaheuristic
from copy import deepcopy

class TabuSearch(Metaheuristic):

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], log_dir: str = "logs/TS", distributed=False,
                 max_iterations: int = 10, population_size:int = 10, tabu_size: int = 5, alteration_limit: float = 1.0):
        """
        Tabu Search Algorithm for optimization problems.

        Args:
            domain (Domain): The problem's domain to explore.
            max_iterations (int): The maximum number of iterations.
            tabu_size (int): Maximum size of the tabu list.
            aspiration_criteria (callable, optional): Function to override tabu restrictions.
        """
        super().__init__(domain, fitness_function, population_size, distributed, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.tabu_list = deque(maxlen=tabu_size)
        self.alteration_limit: float = alteration_limit

    def initialize(self, num_solutions: int=10) -> Tuple[List[Solution], Solution]:
        """Initialize the Tabu Search algorithm."""
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        current_solution = solution_type(self.domain, connector=self.domain.get_connector())
        current_solution.evaluate(self.fitness_function)
        best_solution = current_solution

        current_solutions = self._generate_neighbors(num_solutions, best_solution)[0]

        return current_solutions, best_solution

    def _generate_neighbors(self, num_individuals: int, best_solution: Solution) -> Tuple[List[Solution], Solution]:

        best_solution = deepcopy(best_solution)
        current_solutions = []
        for _ in range(num_individuals):
            neighbor = deepcopy(best_solution)
            neighbor.mutate(alteration_limit=self.alteration_limit)
            neighbor.evaluate(self.fitness_function)

            if neighbor not in self.tabu_list:
                current_solutions.append(neighbor)
                if neighbor < best_solution:
                    best_solution = neighbor

        return current_solutions, best_solution
    
    def iterate(self, solutions: List[Solution] ) -> Tuple[List[Solution], Solution]:

        num_individuals = len(solutions)

        current_solutions, best_solution = self._generate_neighbors(num_individuals, self.best_solution)

        # Skip iteration if no valid neighbors
        if not current_solutions:
            self.current_iteration += 1
            self.skip_iteration()

        # Update tabu list
        self.tabu_list.append(best_solution)

        # Update iteration count
        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations


