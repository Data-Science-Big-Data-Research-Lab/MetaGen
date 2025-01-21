from collections import deque
from metagen.framework import Domain, Solution
from collections.abc import Callable
from typing import List, Tuple, Deque

from metagen.framework.solution.tools import local_search_with_tabu
from metagen.logging.metagen_logger import get_metagen_logger
from metagen.metaheuristics.base import Metaheuristic
from copy import deepcopy

class TabuSearch(Metaheuristic):

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10, max_iterations: int = 10, tabu_size: int = 5, alteration_limit: float = 1.0,
                 distributed=False, log_dir: str = "logs/TS"):
        """
        Tabu Search Algorithm for optimization problems.

        Args:
            domain (Domain): The problem's domain to explore.
            max_iterations (int): The maximum number of iterations.
            tabu_size (int): Maximum size of the ts list.
            aspiration_criteria (callable, optional): Function to override ts restrictions.
        """
        super().__init__(domain, fitness_function, population_size, distributed, log_dir)
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.tabu_list:Deque[Solution] = deque(maxlen=tabu_size)
        self.alteration_limit: float = alteration_limit

    def initialize(self, num_solutions: int=10) -> Tuple[List[Solution], Solution]:
        """Initialize the Tabu Search algorithm."""

        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        first_solution = solution_type(self.domain, connector=self.domain.get_connector())
        first_solution.evaluate(self.fitness_function)

        current_neighborhood = local_search_with_tabu(first_solution, self.fitness_function, num_solutions, self.alteration_limit, list(self.tabu_list))[0]

        return current_neighborhood, first_solution


    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:

        current_solutions, best_solution = local_search_with_tabu(self.best_solution, self.fitness_function, len(solutions), self.alteration_limit,
                                                                  list(self.tabu_list))

        if not current_solutions:
            current_solutions = solutions
            best_solution = deepcopy(self.best_solution)
        else:
            self.tabu_list.append(best_solution)

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations




