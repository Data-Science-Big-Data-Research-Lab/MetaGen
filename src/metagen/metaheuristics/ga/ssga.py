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
from copy import deepcopy

from metagen.framework import Domain, Solution
from .ga_types import GASolution
import ray
import random
from typing import Callable, List
from metagen.metaheuristics.base import Metaheuristic


class SSGA:
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

    def __init__(self, domain: Domain, fitness_func: Callable[[GASolution], float], population_size: int = 10, mutation_rate: float = 0.1, n_iterations: int = 50) -> None:
    
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations
        self.domain: Domain = domain
        self.fitness_func: Callable[[GASolution], float] = fitness_func
        self.population: List[GASolution] = []

        self.initialize()

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        self.population = []
        solution_type: type[GASolution] = self.domain.get_connector().get_type(
            self.domain.get_core())

        for _ in range(self.population_size):
            solution = solution_type(
                self.domain, connector=self.domain.get_connector())
            solution.evaluate(self.fitness_func)
            self.population.append(solution)
        
        self.population = sorted(self.population, key=lambda sol: sol.fitness)


    def select_parents(self) -> List[GASolution]:
        """
        Select the top two parents from the population based on their fitness values.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """

        parents = self.population[:2]
        return parents
    
    def replace_wost(self, child) -> None:
        """
        Replace the solution in the population with worst fitness.

        :return: The selected parent solutions.
        :rtype: List[Solution]
        """

        worst_solution = self.population[-1]

        if worst_solution.fitness > child.fitness:
            self.population[-1] = child
        
        self.population = sorted(self.population, key=lambda sol: sol.fitness)

    def run(self) -> GASolution:
        """
        Run the steady-satate genetic algorithm for the specified number of generations and return the best solution found.

        :return: The best solution found by the genetic algorithm.
        :rtype: Solution
        """

        current_iteration = 0


        while current_iteration <= self.n_iterations:

            parent1, parent2 = self.select_parents()

            child1, child2 = parent1.crossover(parent2)

            if random.uniform(0, 1) <= self.mutation_rate:
                child1.mutate()

            if random.uniform(0, 1) <= self.mutation_rate:
                child2.mutate()
            
            if child1 == child2:
                continue

            child1.evaluate(self.fitness_func)
            child2.evaluate(self.fitness_func)

            self.replace_wost(child1)
            self.replace_wost(child2)
            
            current_iteration += 1

        best_individual = min(
            self.population, key=lambda sol: sol.get_fitness())
        
        return best_individual





class DistributedSSGA(Metaheuristic):
    """
    Distributed implementation of Steady State Genetic Algorithm (SSGA) using Ray for parallel evaluation.
    """

    def __init__(self, domain: Domain,
                 fitness_function: Callable[[GASolution], float],
                 log_dir: str = "logs/DistributedSSGA",
                 population_size: int = 10,
                 mutation_rate: float = 0.1,
                 n_iterations: int = 50) -> None:
        """
        Initialize the distributed SSGA algorithm.

        Args:
            domain: The problem domain
            fitness_func: The fitness function to evaluate solutions
            log_dir: Directory for logging
            population_size: Number of individuals in the population (default: 10)
            mutation_rate: Probability of mutation for each solution (default: 0.1)
            n_iterations: Number of iterations to run the algorithm (default: 50)
        """
        super().__init__(domain, fitness_function, log_dir)
        self.population_size: int = population_size
        self.mutation_rate: float = mutation_rate
        self.n_iterations: int = n_iterations

    def initialize(self) -> None:
        """
        Initialize the population with random solutions and evaluate them in parallel.
        """
        solution_type: type[GASolution] = self.domain.get_connector().get_type(
            self.domain.get_core())

        solutions = [
            solution_type(self.domain, connector=self.domain.get_connector())
            for _ in range(self.population_size)
        ]

        # Evaluate solutions in parallel using Ray
        futures = [DistributedSSGA.evaluate_solution.remote(solution, self.fitness_function) for solution in solutions]
        self.current_solutions = ray.get(futures)

        # Set initial best solution
        self.best_solution = deepcopy(min(self.current_solutions))

    @staticmethod
    @ray.remote
    def evaluate_solution(solution: Solution, fitness_function: Callable[[Solution], float]) -> Solution:
        """
        Evaluate a solution using the fitness function in a distributed way.

        Args:
            solution: The solution to evaluate
            fitness_function: The fitness function

        Returns:
            The evaluated solution
        """
        solution.evaluate(fitness_function)
        return solution

    def select_parents(self) -> List[GASolution]:
        """
        Select the top two parents based on fitness.
        """
        sorted_population = sorted(
            self.current_solutions, key=lambda sol: sol.get_fitness()
        )
        return sorted_population[:2]

    def replace_worst(self, child: GASolution) -> None:
        """
        Replace the solution in the population with the worst fitness.
        """
        worst_solution = self.current_solutions[-1]
        if worst_solution.fitness > child.fitness:
            self.current_solutions[-1] = child
        self.current_solutions = sorted(self.current_solutions, key=lambda sol: sol.fitness)

    def iterate(self) -> None:
        """
        Execute one iteration of the distributed SSGA with parallel evaluation.
        """
        parent1, parent2 = self.select_parents()
        child1, child2 = parent1.crossover(parent2)

        # Apply mutation
        if random.uniform(0, 1) <= self.mutation_rate:
            child1.mutate()
        if random.uniform(0, 1) <= self.mutation_rate:
            child2.mutate()

        # Evaluate offspring in parallel using Ray
        futures = [DistributedSSGA.evaluate_solution.remote(child, self.fitness_function) for child in [child1, child2]]
        evaluated_children = ray.get(futures)

        # Replace worst individuals in the population
        for child in evaluated_children:
            self.replace_worst(child)

        # Update the best solution
        current_best = min(self.current_solutions)
        if current_best < self.best_solution:
              self.best_solution = deepcopy(current_best)

    def stopping_criterion(self) -> bool:
        """
        Stopping criterion for the SSGA.
        """
        return self.current_iteration >= self.n_iterations

    def run(self) -> GASolution:
        """
        Execute the distributed SSGA algorithm.

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
