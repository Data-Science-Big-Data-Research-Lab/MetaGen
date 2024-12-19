# src/metagen/metaheuristics/metaheuristic.py
from abc import ABC, abstractmethod
from typing import List, Optional, Callable
from metagen.framework import Domain, Solution
from metagen.logging import TensorBoardLogger
from copy import deepcopy
import ray

class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.
    """
    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float]) -> None:
        """
        Initialize the metaheuristic.
        
        Args:
            domain: The problem domain
            fitness_function: Function to evaluate solutions
        """
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
        Perform one iteration of the metaheuristic.
        """
        pass

    def stopping_criterion(self) -> bool:
        """
        Define the stopping criterion for the metaheuristic.
        """
        return False

    def run(self) -> Solution:
        """
        Run the metaheuristic algorithm.
        """
        self.initialize()
        while not self.stopping_criterion():
            self.iterate()
            self.current_iteration += 1
        return deepcopy(self.best_solution)

class LoggingDecorator(Metaheuristic, TensorBoardLogger):
    def __init__(self, metaheuristic: Metaheuristic, log_dir: str = "logs") -> None:
        Metaheuristic.__init__(self, metaheuristic.domain, metaheuristic.fitness_function)
        TensorBoardLogger.__init__(self, log_dir)
        self.metaheuristic = metaheuristic

    def initialize(self) -> None:
        self.metaheuristic.initialize()
        self.log_initial_population(self.metaheuristic.current_solutions)

    def iterate(self) -> None:
        self.metaheuristic.iterate()
        self.log_iteration(self.metaheuristic.current_iteration, self.metaheuristic.current_solutions, self.metaheuristic.best_solution)

    def stopping_criterion(self) -> bool:
        return self.metaheuristic.stopping_criterion()

    def run(self) -> Solution:
        solution = self.metaheuristic.run()
        self.log_final_results(solution)
        self.close()
        return solution

class DistributedDecorator(Metaheuristic):
    def __init__(self, metaheuristic: Metaheuristic) -> None:
        super().__init__(metaheuristic.domain, metaheuristic.fitness_function)
        self.metaheuristic = metaheuristic
        ray.init(ignore_reinit_error=True)

    def initialize(self) -> None:
        self.metaheuristic.initialize()

    def iterate(self) -> None:
        futures = [self.distributed_evaluation.remote(solution) for solution in self.metaheuristic.current_solutions]
        self.metaheuristic.current_solutions = ray.get(futures)
        self.metaheuristic.iterate()

    @ray.remote
    def distributed_evaluation(self, solution: Solution) -> Solution:
        solution.mutate()
        solution.evaluate(self.metaheuristic.fitness_function)
        return deepcopy(solution)

    def stopping_criterion(self) -> bool:
        return self.metaheuristic.stopping_criterion()

    def run(self) -> Solution:
        solution = self.metaheuristic.run()
        ray.shutdown()
        return solution