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

from metagen.framework import Domain, Solution
from .ga_tools import GASolution, yield_two_children
from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple, cast
from copy import deepcopy

from metagen.metaheuristics.tools import random_exploration


class GA(Metaheuristic):
    """
    Genetic Algorithm (GA) class for optimization problems.
    
    :param domain: The domain representing the problem space.
    :type domain: Domain
    :param fitness_func: The fitness function used to evaluate solutions.
    :type fitness_func: Callable[[Solution], float]
    :param population_size: The size of the population (default is 10).
    :type population_size: int, optional
    :param mutation_rate: The probability of mutation for each solution (default is 0.1).
    :type mutation_rate: float, optional
    :param n_generations: The number of generations to run the algorithm (default is 50).
    :type n_generations: int, optional

    :ivar population_size: The size of the population.
    :vartype population_size: int
    :ivar mutation_rate: The probability of mutation for each solution.
    :vartype mutation_rate: float
    :ivar n_generations: The number of generations to run the algorithm.
    :vartype n_generations: int
    :ivar domain: The domain representing the problem space.
    :vartype domain: Domain
    :ivar fitness_func: The fitness function used to evaluate solutions.
    :vartype fitness_func: Callable[[Solution], float]"""

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 20,
                 max_iterations: int = 50, mutation_rate: float = 0.1,
                 distributed: bool = False, log_dir: str = "logs/GA"):
        super().__init__(domain, fitness_function, population_size=population_size, distributed=distributed, log_dir=log_dir)
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """Initialize the population"""
        # current_solutions, best_solution = yield_ga_population(num_solutions, self.domain, self.fitness_function)
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """Execute one generation of the genetic algorithm"""
        num_solutions = len(solutions)
        best_parents = heapq.nsmallest(2, solutions, key=lambda sol: sol.get_fitness())
        best_solution = deepcopy(self.best_solution)
        current_solutions = [deepcopy(best_parents[0]), deepcopy(best_parents[1])]

        for _ in range(num_solutions // 2):

            father = cast(GASolution, best_parents[0])
            mother = cast(GASolution, best_parents[1])
            child1, child2 = yield_two_children((father, mother), self.mutation_rate, self.fitness_function)
            current_solutions.extend([child1, child2])

            if best_solution is None or child1 < best_solution:
                best_solution = child1
            if best_solution is None or child2 < best_solution:
                best_solution = child2

        current_solutions = current_solutions[:num_solutions]

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations
