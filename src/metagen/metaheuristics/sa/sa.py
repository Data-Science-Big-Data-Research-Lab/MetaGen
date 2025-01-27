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
from metagen.framework.solution.tools import yield_potential_solutions
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
    Calculate the exploration rate for simulated annealing using the Metropolis criterion.

    The exploration rate determines the probability of accepting a worse solution
    based on the current temperature and the difference in fitness values.

    :param best_solution_fitness: Fitness of the current best solution
    :type best_solution_fitness: float
    :param neighbor_fitness: Fitness of the neighbor solution being considered
    :type neighbor_fitness: float
    :param initial_temp: Current temperature in the annealing process
    :type initial_temp: float
    :return: Probability of accepting the neighbor solution
    :rtype: float
    """
    MAX_EXPONENT = 700  # This is a safe value to avoid overflow in most cases
    exponent_value = (best_solution_fitness - neighbor_fitness) / initial_temp
    exponent_value = max(min(exponent_value, MAX_EXPONENT), -MAX_EXPONENT)
    return math.exp(exponent_value)


class SA(Metaheuristic):
    """
    Simulated Annealing (SA) algorithm for optimization problems.
    
    This class implements the Simulated Annealing metaheuristic which uses temperature-based
    probabilistic acceptance of worse solutions to escape local optima. The temperature
    gradually decreases according to a cooling schedule, reducing the probability of
    accepting worse solutions over time.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param max_iterations: Maximum number of iterations to run, defaults to 20
    :type max_iterations: int, optional
    :param alteration_limit: Maximum proportion of solution to alter when generating neighbors, defaults to 0.1
    :type alteration_limit: float, optional
    :param initial_temp: Initial temperature for annealing process, defaults to 50.0
    :type initial_temp: float, optional
    :param cooling_rate: Rate at which temperature decreases, defaults to 0.99
    :type cooling_rate: float, optional
    :param neighbor_population_size: Number of neighbors to generate in each iteration, defaults to 1
    :type neighbor_population_size: int, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/SA"
    :type log_dir: str, optional

    :ivar max_iterations: Maximum number of iterations
    :vartype max_iterations: int
    :ivar alteration_limit: Maximum proportion of solution to alter
    :vartype alteration_limit: float
    :ivar initial_temp: Current temperature in the annealing process
    :vartype initial_temp: float
    :ivar cooling_rate: Rate of temperature decrease
    :vartype cooling_rate: float
    :ivar neighbor_population_size: Number of neighbors per iteration
    :vartype neighbor_population_size: int
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], max_iterations: int = 20,
                 alteration_limit: float = 0.1, initial_temp: float = 50.0,
                 cooling_rate: float = 0.99, neighbor_population_size: int = 1, distributed=False,
                 log_dir: str = "logs/SA") -> None:
        """
        Initialize the Simulated Annealing algorithm.

        :param domain: The problem domain that defines the solution space
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param max_iterations: Maximum number of iterations to run, defaults to 20
        :type max_iterations: int, optional
        :param alteration_limit: Maximum proportion of solution to alter when generating neighbors, defaults to 0.1
        :type alteration_limit: float, optional
        :param initial_temp: Initial temperature for annealing process, defaults to 50.0
        :type initial_temp: float, optional
        :param cooling_rate: Rate at which temperature decreases, defaults to 0.99
        :type cooling_rate: float, optional
        :param neighbor_population_size: Number of neighbors to generate in each iteration, defaults to 1
        :type neighbor_population_size: int, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory for logging, defaults to "logs/SA"
        :type log_dir: str, optional
        """
        super().__init__(domain, fitness_function, distributed=distributed, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.alteration_limit = alteration_limit
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.neighbor_population_size = neighbor_population_size

    def initialize(self, num_solutions: int = 1) -> Tuple[List[Solution], Solution]:
        """
        Initialize the Simulated Annealing algorithm with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 1
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        current_solutions, best_solution = yield_potential_solutions(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the Simulated Annealing algorithm.

        In each iteration, a neighbor solution is generated and may be accepted based on
        the Metropolis criterion and current temperature. The temperature is then decreased
        according to the cooling schedule.

        :param solutions: Current population of solutions
        :type solutions: List[Solution]
        :return: A tuple containing the updated population and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        current_solution = deepcopy(solutions[0])
        best_solution = deepcopy(self.best_solution)

        # Generate neighbor
        neighbor = deepcopy(current_solution)
        neighbor.mutate(self.alteration_limit)
        neighbor.evaluate(self.fitness_function)

        # Calculate acceptance probability
        if neighbor.get_fitness() < current_solution.get_fitness():
            current_solution = neighbor
            if neighbor.get_fitness() < best_solution.get_fitness():
                best_solution = neighbor
        else:
            exploration_rate = calculate_exploration_rate(current_solution.get_fitness(),
                                                         neighbor.get_fitness(), self.initial_temp)
            if random.random() < exploration_rate:
                current_solution = neighbor

        # Cool down
        self.initial_temp *= self.cooling_rate

        return [current_solution], best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        The algorithm stops when the current iteration reaches the maximum number
        of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations
