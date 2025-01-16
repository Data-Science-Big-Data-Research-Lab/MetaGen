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

from metagen.framework import Domain
from .ga_tools import GASolution, yield_two_children, yield_ga_population
from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple
import random
from copy import deepcopy


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

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 distributed: bool = False,
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_iterations: int = 50,
                 log_dir: str = "logs/GA") -> None:
        super().__init__(domain, fitness_function, population_size, distributed, log_dir)
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[GASolution], GASolution]:
        """Initialize the population"""
        current_solutions, best_solution = yield_ga_population(num_solutions, self.domain, self.fitness_function)
        return current_solutions, best_solution

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[GASolution], GASolution]:
        """Execute one generation of the genetic algorithm"""

        sorted_population = sorted(solutions, key=lambda sol: sol.get_fitness())
        parents = tuple(sorted_population[:2])
        num_solutions = len(solutions)
        best_solution = deepcopy(self.best_solution)
        current_solutions = [deepcopy(parents[0]), deepcopy(parents[1])]

        for _ in range(num_solutions // 2):
            child1, child2 = yield_two_children(parents, self.mutation_rate, self.fitness_function)
            current_solutions.extend([child1, child2])
            if best_solution is None or child1 < best_solution:
                best_solution = child1
            if best_solution is None or child2 < best_solution:
                best_solution = child2

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        """
        Stopping criterion. 
        """
        return self.current_iteration >= self.max_iterations
