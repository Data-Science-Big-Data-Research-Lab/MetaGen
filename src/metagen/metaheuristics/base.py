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

from abc import ABC, abstractmethod
from .import_helper import is_package_installed
from typing import List, Optional
from metagen.framework import Domain, Solution
from copy import deepcopy

if is_package_installed("tensorboard"):
    from metagen.logging import TensorBoardLogger


class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.
    """
    def __init__(self, domain: Domain, fitness_function, log_dir: str = "logs") -> None:
        """
        Initialize the metaheuristic.
        
        Args:
            domain: The problem domain
            fitness_function: Function to evaluate solutions
            algorithm_name: Name of the algorithm for logging
            max_iterations: Maximum number of iterations
        """
        super().__init__()

        self.domain = domain
        self.fitness_function = fitness_function
        self.current_iteration = 0
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []
        self.logger = TensorBoardLogger(log_dir=log_dir) if is_package_installed("tensorboard") else None
        

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the population/solutions for the metaheuristic.
        Must set self.current_solutions and self.best_solution
        """
        pass

    @abstractmethod
    def iterate(self) -> None:
        """
        Execute one iteration of the metaheuristic.
        Must update self.current_solutions and self.best_solution if better found
        """
        pass

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.
        Override this method to implement custom stopping criteria.
        """
        return False

    def pre_execution(self) -> None:
        """
        Callback executed before algorithm execution starts.
        Override this method to add custom pre-execution setup.
        """
        pass

    def post_execution(self) -> None:
        """
        Callback executed after algorithm execution completes.
        Override this method to add custom post-execution cleanup.
        """

        if self.logger:
            # Log final results
            self.logger.log_final_results(self.best_solution)
            self.logger.close()

    def pre_iteration(self) -> None:
        """
        Callback executed before each iteration.
        Override this method to add custom pre-iteration processing.
        """
        pass

    def post_iteration(self) -> None:
        """
        Callback executed after each iteration.
        Override this method to add custom post-iteration processing.
        """
        if self.logger: 
            # Log iteration metrics
            self.logger.log_iteration(
                self.current_iteration, 
                self.current_solutions, 
                self.best_solution
            )
    
    def skip_iteration(self) -> None:
        """
        Callback executed when an iteration is skipped.
        Override this method to add custom skip-iteration processing.
        """
        raise StopIteration("Skipping iteration")

    def run(self) -> Solution:
        """
        Execute the metaheuristic algorithm.
        """
        # Pre-execution callback
        self.pre_execution()

        # Initialize the algorithm
        self.initialize()
        
        # Main loop
        while not self.stopping_criterion():
            try:
                # Pre-iteration callback
                self.pre_iteration()

                # Execute one iteration
                self.iterate()
                
                # Post-iteration callback
                self.post_iteration()
                
                # Increment iteration counter
                self.current_iteration += 1
            except StopIteration:
                continue

        # Post-execution callback
        self.post_execution()
        
        return deepcopy(self.best_solution)