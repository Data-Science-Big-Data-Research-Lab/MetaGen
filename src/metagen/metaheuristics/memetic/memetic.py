from typing import Callable, Tuple, List

import ray

from metagen.framework import Domain
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.distributed_tools import ga_local_yield_and_evaluate_individuals, \
    ga_local_offspring_individuals, mm_local_offspring_individuals, ga_distributed_base_population, \
    ga_distributed_offspring, mm_distributed_offspring
from metagen.metaheuristics.ga import GASolution
from metagen.metaheuristics.ga.ga_tools import yield_ga_population


class Memetic(Metaheuristic):

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_generations: int = 20,
                 neighbor_population_size: int = 10,
                 alteration_limit: float = 1.0,
                 log_dir: str = "logs/MM") -> None:
        super().__init__(domain, fitness_function, log_dir)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.max_generations = max_generations
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit

    def initialize(self, num_solutions=10) -> Tuple[List[GASolution], GASolution]:
        """Initialize the population"""
        current_solutions, best_solution = yield_ga_population(num_solutions, self.domain, self.fitness_function)
        return current_solutions, best_solution

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[GASolution], GASolution]:
        """Execute one generation of the genetic algorithm"""

        sorted_population = sorted(self.current_solutions, key=lambda sol: sol.get_fitness())
        parents = tuple(sorted_population[:2])

        children, best_child = mm_local_offspring_individuals(self.select_parents(),
                                                              self.population_size // 2, self.mutation_rate,
                                                              self.fitness_function,
                                                              self.neighbor_population_size,
                                                              self.alteration_limit)

        if best_child.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_child
            self.current_solutions = children


    def stopping_criterion(self) -> bool:
        """
        Stopping criterion.
        """
        return self.current_iteration >= self.max_generations












class DistributedMemetic(Metaheuristic):
    """
    Distributed implementation of Memetic Algorithm (MM) using Ray for parallel evaluation of solutions.
    """

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 max_generations: int = 20,
                 neighbor_population_size: int = 10,
                 alteration_limit: float = 1.0,
                 log_dir: str = "logs/DMM") -> None:
        super().__init__(domain, fitness_function, log_dir)
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.max_generations = max_generations
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit

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
        children, best_child = mm_distributed_offspring(self.select_parents(),
                                                        self.population_size // 2,
                                                        self.mutation_rate,
                                                        self.fitness_function,
                                                        self.neighbor_population_size,
                                                        self.alteration_limit)

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
        # print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('DMM/Population Size',
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
