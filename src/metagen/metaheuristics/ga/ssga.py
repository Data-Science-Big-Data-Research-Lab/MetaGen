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
import heapq
from collections.abc import Callable
from copy import deepcopy
from typing import List, Tuple, cast

from metagen.framework import Domain, Solution
from .ga_tools import GASolution, yield_two_children
from metagen.metaheuristics.base import Metaheuristic
from ...framework.solution.tools import random_exploration
from ...logging.metagen_logger import metagen_logger


class SSGA(Metaheuristic):
    """
    Steady State Genetic Algorithm (SSGA) class for optimization problems which is a variant of the Genetic Algorithm (GA) with population replacement.
    
    :param domain: The domain representing the problem space.
    :type domain: Domain
    :param fitness_func: The fitness function used to evaluate solutions.
    :type fitness_func: Callable[[Solution], float]
    :param population_size: The size of the population (default is 10).
    :type population_size: int, optional
    :param mutation_rate: The probability of mutation for each solution (default is 0.1).
    :type mutation_rate: float, optional
    :param n_iterations: The number of generations to run the algorithm (default is 50).
    :type n_iterations: int, optional

    :ivar population_size: The size of the population.
    :vartype population_size: int
    :ivar mutation_rate: The probability of mutation for each solution.
    :vartype mutation_rate: float
    :ivar n_iterations: The number of generations to run the algorithm.
    :vartype n_iterations: int
    :ivar domain: The domain representing the problem space.
    :vartype domain: Domain
    :ivar fitness_func: The fitness function used to evaluate solutions.
    :vartype fitness_func: Callable[[Solution], float]"""

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10,  warmup_iterations: int = 5,
                 max_iterations: int = 50, mutation_rate: float = 0.1,
                 distributed: bool = False, log_dir: str = "logs/SSGA"):
        super().__init__(domain, fitness_function, population_size, warmup_iterations, distributed, log_dir)
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Iterate the algorithm for one generation.
        """
        best_parents = heapq.nsmallest(2, solutions, key=lambda sol: sol.get_fitness())

        father = cast(GASolution, best_parents[0])
        mother = cast(GASolution, best_parents[1])

        child1, child2 = yield_two_children((father,mother), self.mutation_rate, self.fitness_function)

        best_solution = deepcopy(self.best_solution)

        if child1 != child2:
            worst_parents = heapq.nlargest(2, solutions, key=lambda sol: sol.get_fitness())
            candidates = [worst_parents[0], worst_parents[1], child1, child2]
            best_two = heapq.nsmallest(2, candidates, key=lambda sol: sol.get_fitness())
            for i, worst in enumerate(worst_parents):
                if worst in solutions:
                    solutions[solutions.index(worst)] = best_two[i]
            best_solution = heapq.nsmallest(1, solutions, key=lambda sol: sol.get_fitness())[0]
        else:
            metagen_logger.info(f'[ITERATION {self.current_iteration}] Both children are the same, skipping iteration')

        return solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations
