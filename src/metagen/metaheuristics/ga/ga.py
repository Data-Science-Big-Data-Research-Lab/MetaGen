import random
from collections.abc import Callable
from typing import List

from metagen.framework import Domain
from metagen.framework.solution.devsolution import Solution


class GA:
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

    def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], population_size: int = 10, mutation_rate: float = 0.1, n_generations: int = 50) -> None:
    
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_generations: int = n_generations
        self.domain: Domain = domain
        self.fitness_func: Callable[[Solution], float] = fitness_func
        self.population: List[Solution] = []

        self.initialize()

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        self.population = []
        solution_type: type[Solution] = self.domain.get_connector().get_type(
            self.domain.get_core())

        for _ in range(self.population_size):
            solution = solution_type(
                self.domain, connector=self.domain.get_connector())
            solution.evaluate(self.fitness_func)
            self.population.append(solution)

    def select_parents(self) -> List[Solution]:
        """
        Select the top two parents from the population based on their fitness values.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """

        parents = sorted(self.population, key=lambda sol: sol.fitness)[:2]
        return parents

    def run(self) -> Solution:
        """
        Run the genetic algorithm for the specified number of generations and return the best solution found.

        :return: The best solution found by the genetic algorithm.
        :rtype: Solution
        """

        for _ in range(self.n_generations):

            parent1, parent2 = self.select_parents()

            offspring = []
            for _ in range(self.population_size // 2):
                child1, child2 = parent1.crossover(parent2)

                if random.uniform(0, 1) <= self.mutation_rate:
                    child1.mutate()

                if random.uniform(0, 1) <= self.mutation_rate:
                    child2.mutate()

                child1.evaluate(self.fitness_func)
                child2.evaluate(self.fitness_func)
                offspring.extend([child1, child2])

            self.population = offspring

            best_individual = min(
                self.population, key=lambda sol: sol.get_fitness())

        best_individual = min(
            self.population, key=lambda sol: sol.get_fitness())
        return best_individual
