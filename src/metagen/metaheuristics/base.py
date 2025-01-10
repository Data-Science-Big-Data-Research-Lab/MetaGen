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
from typing import List, Tuple, Optional, Callable, Union
from metagen.framework import Domain, Solution
from copy import deepcopy

IS_RAY_INSTALLED = is_package_installed("ray")

if is_package_installed("tensorboard"):
    from metagen.logging import TensorBoardLogger

if IS_RAY_INSTALLED:
    import ray
    from .distributed_suite import assign_load_equally, call_distributed

class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.
    """
    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size=1, distributed=False, log_dir: str = "logs") -> None:
        """
        Initialize the metaheuristic.
        
        Args:
            domain: The problem domain
            fitness_function: Function to evaluate solutions
        """
        super().__init__()

        self.domain = domain
        self.fitness_function = fitness_function
        self.current_iteration = 0
        self.population_size = population_size
        self.distributed = distributed
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []
        self.logger = TensorBoardLogger(log_dir=log_dir) if is_package_installed("tensorboard") else None
    
    
    @abstractmethod
    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population/solutions for the metaheuristic.
        Must set self.current_solutions and self.best_solution
        """
        pass

    
    def _launch_distributed_method(self, method: Callable) -> Tuple[List[Solution], Solution]:
        distribution = assign_load_equally(len(self.current_solutions) if len(self.current_solutions)>0 else self.population_size)
        population = deepcopy(self.current_solutions)
        futures = []

        for count in distribution:

            if len(population) > 0:
                futures.append(call_distributed.remote(method, population[:count]))
                population = population[count:]
            else:
                futures.append(call_distributed.remote(method, count))

        remote_results = ray.get(futures)
        population = [individual for subpopulation in remote_results for individual in subpopulation[0]]
        best_individual = min([result[1] for result in remote_results], key=lambda sol: sol.get_fitness())

        return population, best_individual

    def _initialize(self) -> None:
        """
        Private function to initialize the population/solutions for the metaheuristic.
        """
        
        if self.distributed:
            if not IS_RAY_INSTALLED:
                raise ImportError("Ray must be installed to use distributed initialization")
            
            population, best_individual = self._launch_distributed_method(self.initialize)
        else:
            population, best_individual = self.initialize(self.population_size)

        self.current_solutions = population
        self.best_solution = best_individual

        return population, best_individual
    

    @abstractmethod
    def iterate(self, solutions: List[Solution]) -> None:
        """
        Execute one iteration of the metaheuristic.
        Must update self.current_solutions and self.best_solution if better found
        """
        pass

    def _iterate(self) -> None:
        """
        Private function to execute one iteration of the metaheuristic.
        """
        if self.distributed:
            if not IS_RAY_INSTALLED:
                raise ImportError("Ray must be installed to use distributed initialization")
            
            population, best_individual = self._launch_distributed_method(self.iterate)
        else:
            population, best_individual = self.iterate(self.current_solutions)

        self.current_solutions = population
        self.best_solution = best_individual

        return population, best_individual

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

        if self.distributed and IS_RAY_INSTALLED and not ray.is_initialized():
            ray.init()

        try:
            # Pre-execution callback
            self.pre_execution()

            # Initialize the algorithm
            self._initialize()

            # Main loop
            while not self.stopping_criterion():
                try:
                    # Pre-iteration callback
                    self.pre_iteration()

                    # Execute one iteration
                    self._iterate()
                    
                    # Post-iteration callback
                    self.post_iteration()
                    
                    # Increment iteration counter
                    self.current_iteration += 1
                except StopIteration: # Skip iteration flow
                    continue

            # Post-execution callback
            self.post_execution()
        except Exception as e:
            raise e
        finally: # Finalize Ray if necessary 
            if self.distributed and IS_RAY_INSTALLED and ray.is_initialized():
                ray.shutdown()

        return deepcopy(self.best_solution)