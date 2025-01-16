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
from collections.abc import Callable
from typing import List, Tuple

import ray

from metagen.framework import Domain
from .ga_tools import GASolution, yield_ga_population, replace_wost
from metagen.metaheuristics.base import Metaheuristic
from ..distributed_suite import ga_local_yield_and_evaluate_individuals, yield_two_children, \
    ssga_local_sorted_yield_and_evaluate_individuals, distributed_sorted_base_population, distributed_sort


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

    def __init__(self, domain: Domain, fitness_function: Callable[[GASolution], float], population_size: int = 10,
                 mutation_rate: float = 0.1, n_iterations: int = 20, log_dir: str = "logs/SSGA") -> None:
        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[GASolution], GASolution]:
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        current_solutions, best_solution = yield_ga_population(num_solutions, self.domain, self.fitness_function)
        current_solutions = sorted(current_solutions, key=lambda sol: sol.get_fitness())
        return current_solutions, best_solution

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[GASolution], GASolution]:
        """
        Iterate the algorithm for one generation.
        """
        parents = tuple(solutions[:2])

        child1, child2 = yield_two_children(parents, self.mutation_rate, self.fitness_function)

        if child1 == child2:
            self.current_iteration += 1
            self.skip_iteration()

        replace_wost(child1, solutions)
        replace_wost(child2, solutions)

        solutions = sorted(solutions, key=lambda sol: sol.get_fitnes())
        best_solution = solutions[0]

        return solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.n_iterations
