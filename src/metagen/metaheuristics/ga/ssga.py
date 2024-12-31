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
from .ga_types import GASolution
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

    def __init__(self, domain: Domain, fitness_func: Callable[[GASolution], float], population_size: int = 10, mutation_rate: float = 0.1, n_iterations: int = 50, log_dir: str = "logs/SSGA") -> None:

        super().__init__(domain, fitness_func, log_dir=log_dir)
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        self.current_solutions, self.best_solution = ga_local_yield_and_evaluate_individuals(self.population_size, self.domain, self.fitness_function)
        self.current_solutions = sorted(self.current_solutions, key=lambda sol: sol.fitness)

    def iterate(self) -> None:
        """
        Iterate the algorithm for one generation.
        """
        child1, child2 = yield_two_children(self.select_parents(), self.mutation_rate, self.fitness_function)

        if child1 == child2:
            self.current_iteration += 1
            self.skip_iteration()

        self.replace_wost(child1)
        self.replace_wost(child2)

        self.current_solutions = sorted(self.current_solutions, key=lambda sol: sol.fitness)
        self.best_solution = self.current_solutions[0]

    def select_parents(self) -> Tuple[GASolution, GASolution]:
        """
        Select the top two parents from the population based on their fitness values.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """
        # TODO: No se cómo evitar que mypy me de un error en esta línea
        return tuple(self.current_solutions[:2])
    
    def replace_wost(self, child) -> None:
        """
        Replace the solution in the population with worst fitness.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """
        worst_solution = self.current_solutions[-1]
        if worst_solution.fitness > child.fitness:
            self.current_solutions[-1] = child

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.n_iterations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        # print(f'[{self.current_iteration}] {self.current_solutions}')
        print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('SSGA/Population Size',
                              len(self.current_solutions),
                              self.current_iteration)


class DistributedSSGA (Metaheuristic):
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

    def __init__(self, domain: Domain, fitness_func: Callable[[GASolution], float], population_size: int = 10,
                 mutation_rate: float = 0.1, n_iterations: int = 50, log_dir: str = "logs/DSSGA") -> None:

        super().__init__(domain, fitness_func, log_dir=log_dir)
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        self.current_solutions, self.best_solution = distributed_sorted_base_population(self.population_size,
                                                                                             self.domain,
                                                                                             self.fitness_function)

    def iterate(self) -> None:
        """
        Iterate the algorithm for one generation.
        """
        child1, child2 = yield_two_children(self.select_parents(), self.mutation_rate, self.fitness_function)

        if child1 == child2:
            self.skip_iteration()

        self.replace_wost(child1)
        self.replace_wost(child2)

        self.current_solutions, self.best_solution = distributed_sort(self.current_solutions)

    def select_parents(self) -> Tuple[GASolution, GASolution]:
        """
        Select the top two parents from the population based on their fitness values.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """
        # TODO: No se cómo evitar que mypy me de un error en esta línea
        return tuple(self.current_solutions[:2])

    def replace_wost(self, child) -> None:
        """
        Replace the solution in the population with worst fitness.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """
        worst_solution = self.current_solutions[-1]
        if worst_solution.fitness > child.fitness:
            self.current_solutions[-1] = child

    # def post_execution(self) -> None:
    #     current_best = min(self.current_solutions, key=lambda sol: sol.fitness)
    #     self.best_solution = current_best if current_best.fitness < self.best_solution.fitness else self.best_solution
    #     super().post_execution()

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.n_iterations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('DSSGA/Population Size',
                              len(self.current_solutions),
                              self.current_iteration)

    def run(self) -> GASolution:
        """
        Execute the distributed genetic algorithm.

        Returns:
            The best solution found.
        """
        # Initialize Ray at the start
        if not ray.is_initialized():
            ray.init()
        try:
            # Run the base Metaheuristic logic
            super().run()
            return self.best_solution
        finally:
            # Ensure Ray is properly shut down after execution
            ray.shutdown()