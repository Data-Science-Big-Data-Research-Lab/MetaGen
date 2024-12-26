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
import random
from collections.abc import Callable
from typing import List

from metagen.framework import Domain
from .ga_types import GASolution
from metagen.metaheuristics.base import Metaheuristic

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

    def __init__(self, domain: Domain, fitness_func: Callable[[GASolution], float], population_size: int = 10, mutation_rate: float = 0.1, n_iterations: int = 50, log_dir: str = "logs/SSGA") -> None:
        
        super().__init__(domain, fitness_func, log_dir=log_dir)
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        self.current_solutions = []
        solution_type: type[GASolution] = self.domain.get_connector().get_type(
            self.domain.get_core())

        for _ in range(self.population_size):
            solution = solution_type(
                self.domain, connector=self.domain.get_connector())
            solution.evaluate(self.fitness_function)
            self.current_solutions.append(solution)
        
        self.current_solutions = sorted(self.current_solutions, key=lambda sol: sol.fitness)

        self.best_solution = self.current_solutions[0]


    def select_parents(self) -> List[GASolution]:
        """
        Select the top two parents from the population based on their fitness values.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """

        parents = self.current_solutions[:2]
        return parents
    
    def replace_wost(self, child) -> None:
        """
        Replace the solution in the population with worst fitness.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """

        worst_solution = self.current_solutions[-1]

        if worst_solution.fitness > child.fitness:
            self.current_solutions[-1] = child
        
        self.current_solutions = sorted(self.current_solutions, key=lambda sol: sol.fitness)
    
    def iterate(self) -> None:
        """
        Iterate the algorithm for one generation.
        """

        parent1, parent2 = self.select_parents()

        child1, child2 = parent1.crossover(parent2)

        if random.uniform(0, 1) <= self.mutation_rate:
            child1.mutate()

        if random.uniform(0, 1) <= self.mutation_rate:
            child2.mutate()
        
        if child1 == child2:
            self.skip_iteration()

        child1.evaluate(self.fitness_function)
        child2.evaluate(self.fitness_function)

        self.replace_wost(child1)
        self.replace_wost(child2)

    
    def post_execution(self) -> None:
        current_best = min(self.current_solutions, key=lambda sol: sol.fitness)
        self.best_solution = current_best if current_best.fitness < self.best_solution.fitness else self.best_solution
        super().post_execution()
    
    
    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.n_iterations

