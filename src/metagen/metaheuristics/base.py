# src/metagen/metaheuristics/metaheuristic.py
from abc import ABC, abstractmethod
from typing import List, Optional
from metagen.framework import Domain, Solution
from metagen.logging import TensorBoardLogger
from copy import deepcopy

class Metaheuristic(TensorBoardLogger, ABC):
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
        super().__init__(log_dir=log_dir)
        self.domain = domain
        self.fitness_function = fitness_function
        self.current_iteration = 0
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []

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
        # Log final results
        self.log_final_results(self.best_solution)
        self.close()

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
        # Log iteration metrics
        self.log_iteration(
            self.current_iteration, 
            self.current_solutions, 
            self.best_solution
        )

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
            # Pre-iteration callback
            self.pre_iteration()

            # Execute one iteration
            self.iterate()
            
            # Post-iteration callback
            self.post_iteration()
            
            # Increment iteration counter
            self.current_iteration += 1

        # Post-execution callback
        self.post_execution()
        
        return deepcopy(self.best_solution)