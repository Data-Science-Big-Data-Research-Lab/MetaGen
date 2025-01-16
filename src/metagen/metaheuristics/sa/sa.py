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
from metagen.framework import Domain, Solution
from metagen.metaheuristics.base import Metaheuristic
from collections.abc import Callable
from copy import deepcopy
import random
import math
import random
from copy import deepcopy
from typing import Callable, Tuple, List
from metagen.metaheuristics.base import Metaheuristic


def calculate_exploration_rate(best_solution_fitness: float, neighbor_fitness: float,
                               initial_temp: float) -> float:
    """
    Calculate the exploration rate for simulated annealing.

    Args:
        best_solution_fitness (float): Fitness of the best solution.
        neighbor_fitness (float): Fitness of the best neighbor.
        initial_temp (float): Current temperature.

    Returns:
        float: The exploration rate.
    """
    MAX_EXPONENT = 700  # This is a safe value to avoid overflow in most cases
    exponent_value = (best_solution_fitness - neighbor_fitness) / initial_temp
    exponent_value = max(min(exponent_value, MAX_EXPONENT), -MAX_EXPONENT)
    return math.exp(exponent_value)



class SA(Metaheuristic):
    """
    Simulated annealing (SA) class for optimization problems.
    
    :param domain: The domain representing the problem space.
    :type domain: Domain
    :param fitness_func: The fitness function used to evaluate solutions.
    :type fitness_func: Callable[[Solution], float]
    :param n_iterations: The number of generations to run the algorithm (default is 50).
    :type n_iterations: int, optional
    :param alteration_limit: The alteration performed over every the solution to generate the neighbor.
    :type alteration_limit: any, optional
    :param initial_temp: The initial temperature for the annealing.
    :type initial_temp: float, optional
    :param cooling_rate: Meassures the speed of the cooling procedure.
    :type cooling_rate: float, optional

    :ivar n_iterations: The number of generations to run the algorithm.
    :vartype n_iterations: int
    :ivar domain: The domain representing the problem space.
    :vartype domain: Domain
    :ivar alteration_limit: The alteration performed over every the solution to generate the neighbor.
    :vartype alteration_limit: any
    :ivar fitness_func: The fitness function used to evaluate solutions.
    :vartype fitness_func: Callable[[Solution], float]
    :ivar initial_temp: The initial temperature for the annealing.
    :vartype initial_temp: float
    :ivar cooling_rate: Meassures the speed of the cooling procedure.
    :vartype cooling_rate: float
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 log_dir: str = "logs/SA", n_iterations: int = 50,
                 alteration_limit: float = 0.1, initial_temp: float = 50.0,
                 cooling_rate: float = 0.99, neighbor_population_size: int = 1) -> None:
        """
        Initialize the distributed simulated annealing algorithm.

        Args:
            domain: The problem domain
            fitness_func: Function to evaluate solutions
            log_dir: Directory for logging
            n_iterations: Number of iterations (default: 50)
            alteration_limit: Maximum alteration for generating a neighbor (default: 0.1)
            initial_temp: Initial temperature (default: 50.0)
            cooling_rate: Cooling rate for the annealing (default: 0.99)
            neighbor_population_size: Number of neighbors to consider in each iteration (default: 10)
        """
        super().__init__(domain, fitness_function, log_dir)
        self.n_iterations = n_iterations
        self.alteration_limit = alteration_limit
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.neighbor_population_size = neighbor_population_size

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the starting solution for simulated annealing.
        """
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        best_solution = solution_type(self.domain, connector=self.domain.get_connector())
        best_solution.evaluate(self.fitness_function)
        current_solutions = [best_solution]
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Perform one iteration of the simulated annealing algorithm.
        """

        neighbor = deepcopy(solutions[0])
        neighbor.mutate(alteration_limit=self.alteration_limit)
        neighbor.evaluate(self.fitness_function)

        current_fitness = solutions[0].get_fitness()
        neighbor_fitness = neighbor.get_fitness()
        delta = current_fitness - neighbor_fitness

        # Acceptance criteria for simulated annealing
        exploration_rate = calculate_exploration_rate(self.best_solution.fitness, neighbor.fitness,
                                                      self.initial_temp)

        partial_best_solution = deepcopy(self.best_solution)

        if delta < 0 or exploration_rate > random.random():
            solutions[0] = deepcopy(neighbor)
            if current_fitness > neighbor_fitness:
                partial_best_solution = deepcopy(neighbor)

        # Update temperature
        self.initial_temp *= self.cooling_rate

        return solutions, partial_best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the stopping criterion has been reached.

        Returns:
            bool: True if the stopping criterion has been reached, False otherwise.
        """
        return self.current_iteration >= self.n_iterations



