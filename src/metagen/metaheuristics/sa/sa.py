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
import ray
import math
import random
from copy import deepcopy
from typing import Callable, Any
from metagen.metaheuristics.base import Metaheuristic

class SA:
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

    def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], n_iterations: int = 50, alteration_limit: float =0.1, initial_temp: float = 50.0, cooling_rate: float=0.99) -> None:
    
        self.domain: Domain = domain
        self.n_iterations: int = n_iterations
        self.initial_temp: float = initial_temp
        self.alteration_limit: Any = alteration_limit
        self.cooling_rate: float = cooling_rate
        self.solution = None
        self.fitness_func: Callable[[Solution], float] = fitness_func

        self.initialize()

    def initialize(self):
        """
        Initialize the population of solutions by creating and evaluating initial solutions.
        """
        solution_type: type[Solution] = self.domain.get_connector().get_type(
            self.domain.get_core())
        self.solution = solution_type(
            self.domain, connector=self.domain.get_connector())
        self.solution.evaluate(self.fitness_func)
        

    def run(self) -> Solution:
        """
        Run the simulated annealing for the specified number of generations and return the best solution found.

        :return: The best solution found by the simulated annealing.
        :rtype: Solution
        """

        current_iteration = 0
        temperature = self.initial_temp


        while current_iteration <= self.n_iterations:

            neighbour = deepcopy(self.solution)

            neighbour.mutate(alteration_limit=self.alteration_limit)

            neighbour.evaluate(self.fitness_func)

            exploration_rate = math.exp((self.solution.fitness - neighbour.fitness) / temperature) 

            if neighbour.fitness < self.solution.fitness or exploration_rate > random.random():
                self.solution = neighbour
            
            temperature *= self.cooling_rate

            current_iteration += 1
        
        return self.solution




class DistributedSA(Metaheuristic):
    """
    Distributed implementation of Simulated Annealing (SA) using Ray for parallel evaluation.
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 log_dir: str = "logs/SA", n_iterations: int = 50,
                 alteration_limit: float = 0.1, initial_temp: float = 50.0,
                 cooling_rate: float = 0.99) -> None:
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
        """
        super().__init__(domain, fitness_function, log_dir)
        self.n_iterations = n_iterations
        self.alteration_limit = alteration_limit
        self.initial_temp = initial_temp
        self.cooling_rate = cooling_rate
        self.solution = None

    def initialize(self) -> None:
        """
        Initialize the starting solution for simulated annealing.
        """
        solution_type: type[Solution] = self.domain.get_connector().get_type(
            self.domain.get_core())
        self.solution = solution_type(
            self.domain, connector=self.domain.get_connector())
        self.solution.evaluate(self.fitness_function)

    @staticmethod
    @ray.remote
    def evaluate_solution(solution: Solution, fitness_func: Callable[[Solution], float]) -> Solution:
        """
        Evaluate a solution using the fitness function in a distributed way.

        Args:
            solution: The solution to evaluate
            fitness_func: The fitness function

        Returns:
            The evaluated solution
        """
        solution.evaluate(fitness_func)
        return solution

    def iterate(self) -> None:
        """
        Perform one iteration of the simulated annealing algorithm.
        """
        # Generate a neighbor solution
        neighbour = deepcopy(self.solution)
        neighbour.mutate(alteration_limit=self.alteration_limit)

        # Evaluate the neighbor in parallel using Ray
        future = DistributedSA.evaluate_solution.remote(neighbour, self.fitness_function)
        neighbour = ray.get(future)

        # Acceptance criteria for simulated annealing
        exploration_rate = math.exp((self.solution.fitness - neighbour.fitness) / self.initial_temp)
        if neighbour.fitness < self.solution.fitness or exploration_rate > random.random():
            self.solution = neighbour

        # Update temperature
        self.initial_temp *= self.cooling_rate

    def run(self) -> Solution:
        """
        Execute the distributed simulated annealing algorithm.

        Returns:
            The best solution found
        """
        # Initialize Ray at the start
        if not ray.is_initialized():
            ray.init()

        try:
            # Run the main loop of the metaheuristic
            super().run()
            return self.solution

        finally:
            # Ensure Ray is properly shut down after execution
            ray.shutdown()




