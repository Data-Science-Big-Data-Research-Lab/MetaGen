from copy import deepcopy
from typing import Callable, Tuple, List
from metagen.framework import Domain
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.ga import GASolution
from metagen.metaheuristics.ga.ga_tools import yield_ga_population, yield_two_children
from metagen.metaheuristics.mm.mm_tools import local_search_of_two_children




class Memetic(Metaheuristic):

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 population_size: int = 10,
                 distributed: bool = False,
                 mutation_rate: float = 0.1,
                 max_generations: int = 20,
                 neighbor_population_size: int = 10,
                 alteration_limit: float = 1.0,
                 log_dir: str = "logs/MM",
                 distribution_level:int =0) -> None:
        super().__init__(domain, fitness_function, population_size, distributed, log_dir)
        self.mutation_rate = mutation_rate
        self.max_generations = max_generations
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit
        self.distribution_level = distribution_level

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

        child1, child2 = yield_two_children(parents, self.mutation_rate, self.fitness_function)
        best_child = min(child1, child2, key=lambda sol: sol.get_fitness())
        children = []
        children.extend([child1, child2])

        for _ in range(num_solutions // 2):

            child1, child2 = yield_two_children(parents, self.mutation_rate, self.fitness_function)


            lc = local_search_of_two_children((child1, child2), self.fitness_function, self.neighbor_population_size, self.alteration_limit, self.distribution_level)

            children.extend(lc)
            if best_solution is None or child1 < best_solution:
                best_child = child1
            if best_solution is None or child2 < best_solution:
                best_child = child2

        if best_child.get_fitness() < best_solution.get_fitness():
            best_solution = best_child
            current_solutions = children

        return current_solutions, best_solution






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
