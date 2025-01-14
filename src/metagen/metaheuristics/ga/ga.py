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
from .ga_types import GASolution
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
                 fitness_func: Callable[[GASolution], float],
                 distributed: bool = False,
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_iterations: int = 50,
                 log_dir: str = "logs/GA") -> None:
        super().__init__(domain, fitness_func, population_size, distributed, log_dir)
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[GASolution], GASolution]:
        """Initialize the population"""
        solution_type: type[GASolution] = self.domain.get_connector().get_type(self.domain.get_core())
        best_solution = None
        current_solutions: List[GASolution] = []
        for _ in range(num_solutions):
            individual = solution_type(self.domain, connector=self.domain.get_connector())
            individual.evaluate(self.fitness_function)
            current_solutions.append(individual)
            if best_solution is None or individual.get_fitness() < best_solution.get_fitness():
                best_solution = individual

        return current_solutions, best_solution
    
    def yield_two_children(self, parents: Tuple[GASolution, GASolution]) -> Tuple['GASolution', 'GASolution']:
        
        child1, child2 = parents[0].crossover(parents[1])

        if random.uniform(0, 1) <= self.mutation_rate:
            child1.mutate()
        if random.uniform(0, 1) <= self.mutation_rate:
            child2.mutate()

        child1.evaluate(self.fitness_function)
        child2.evaluate(self.fitness_function)

        return child1, child2

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[GASolution], GASolution]:
        """Execute one generation of the genetic algorithm"""
        
        parents = self.select_parents()
        num_solutions = len(solutions)
        best_solution = deepcopy(self.best_solution)
        current_solutions = []

        current_solutions = [deepcopy(parents[0]), deepcopy(parents[1])]

        for _ in range(num_solutions//2):
            child1, child2 = self.yield_two_children(parents)
            current_solutions.extend([child1, child2])
            if best_solution is None or child1 < best_solution:
                best_solution = child1
            if best_solution is None or child2 < best_solution:
                best_solution = child2

        return current_solutions, best_solution

    def select_parents(self) -> Tuple[GASolution, GASolution]:
        """Select the top two parents based on fitness"""
        sorted_population = sorted(self.current_solutions, key=lambda sol: sol.get_fitness())
        return tuple(sorted_population[:2])

    def stopping_criterion(self) -> bool:
        """
        Stopping criterion. 
        """
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        print(self.best_solution)
        if self.logger is not None: 
            # Add GA-specific logging if needed
            self.logger.writer.add_scalar('GA/Population Size', 
                              len(self.current_solutions), 
                              self.current_iteration)