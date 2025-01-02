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
import ray
from typing import Callable, List, Tuple

from metagen.metaheuristics.distributed_suite import ga_local_yield_and_evaluate_individuals, \
    ga_local_offspring_individuals, \
    ga_distributed_base_population, ga_distributed_offspring


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
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_generations: int = 50,
                 log_dir: str = "logs/GA") -> None:
        super().__init__(domain, fitness_func, log_dir)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.max_generations = max_generations

    def initialize(self) -> None:
        """Initialize the population"""
        self.current_solutions, self.best_solution = ga_local_yield_and_evaluate_individuals(self.population_size,
                                                                                             self.domain,
                                                                                             self.fitness_function)

    def iterate(self) -> None:
        """Execute one generation of the genetic algorithm"""
        children, best_child = ga_local_offspring_individuals(self.select_parents(),
                                                              self.population_size // 2,
                                                              self.mutation_rate,
                                                              self.fitness_function)

        if best_child.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_child
            self.current_solutions = children

    def select_parents(self) -> Tuple[GASolution, GASolution]:
        """Select the top two parents based on fitness"""
        sorted_population = sorted(self.current_solutions, key=lambda sol: sol.get_fitness())
        return tuple(sorted_population[:2])

    def stopping_criterion(self) -> bool:
        """
        Stopping criterion. 
        """
        return self.current_iteration >= self.max_generations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        
        if self.logger is not None: 
            # Add GA-specific logging if needed
            self.logger.add_scalar('GA/Population Size', 
                              len(self.current_solutions), 
                              self.current_iteration)


class DistributedGA(Metaheuristic):
    """
    Distributed implementation of Genetic Algorithm (GA) using Ray for parallel evaluation of solutions.
    """

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_generations: int = 50,
                 log_dir: str = "logs/DGA") -> None:
        """
        Initialize the distributed genetic algorithm.

        Args:
            domain: The problem domain
            fitness_function: Function to evaluate solutions
            population_size: Number of individuals in the population (default: 10)
            mutation_rate: Probability of mutation for each solution (default: 0.1)
            max_generations: Number of generations to run (default: 50)
            log_dir: Directory for logging
        """
        super().__init__(domain, fitness_function, log_dir)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.max_generations = max_generations

    def initialize(self) -> None:
        """
        Initialize the population with random solutions and evaluate them in parallel.
        """
        self.current_solutions, self.best_solution = ga_distributed_base_population(self.population_size, self.domain,
                                                                                    self.fitness_function)

    def iterate(self) -> None:
        """
        Perform one generation of the genetic algorithm with distributed evaluation.
        """
        children, best_child = ga_distributed_offspring(self.select_parents(),
                                                        self.population_size // 2,
                                                        self.mutation_rate,
                                                        self.fitness_function)

        if best_child.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_child
            self.current_solutions = children

    def select_parents(self) -> Tuple[GASolution, GASolution]:
        """Select the top two parents based on fitness"""
        sorted_population = sorted(self.current_solutions, key=lambda sol: sol.get_fitness())
        return tuple(sorted_population[:2])

    def stopping_criterion(self) -> bool:
        """
        Stopping criterion for the genetic algorithm.
        """
        return self.current_iteration >= self.max_generations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        
        if self.logger is not None: 
            # Add GA-specific logging if needed
            self.logger.add_scalar('GA/Population Size', 
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
