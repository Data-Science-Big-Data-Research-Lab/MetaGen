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
from typing import List, Tuple, Optional, Callable
from metagen.framework import Domain, Solution
from copy import deepcopy

from metagen.logging.metagen_logger import metagen_logger
from ..framework.solution.tools import random_exploration

IS_RAY_INSTALLED = is_package_installed("ray")

if is_package_installed("tensorboard"):
    from metagen.logging.tensorboard_logger import TensorBoardLogger

if IS_RAY_INSTALLED:
    import ray
    from .distributed_tools import assign_load_equally, call_distributed


class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.

    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param population_size: The size of the population (default is 1).
    :type population_size: int, optional
    :param distributed: Whether to use distributed computation (default is False).
    :type distributed: bool, optional
    :param log_dir: Directory for logging (default is "logs").
    :type log_dir: str, optional

    :ivar domain: The problem domain.
    :vartype domain: Domain
    :ivar fitness_function: Function to evaluate solutions.
    :vartype fitness_function: Callable[[Solution], float]
    :ivar population_size: The size of the population.
    :vartype population_size: int
    :ivar distributed: Whether distributed computation is enabled.
    :vartype distributed: bool
    :ivar logger: Logger instance for TensorBoard, if available.
    :vartype logger: Optional[TensorBoardLogger]
    :ivar current_iteration: The current iteration of the algorithm.
    :vartype current_iteration: int
    :ivar best_solution: The best solution found so far.
    :vartype best_solution: Optional[Solution]
    :ivar current_solutions: The current population of solutions.
    :vartype current_solutions: List[Solution]
    :ivar best_solution_fitnesses: List of fitness values of the best solutions per iteration.
    :vartype best_solution_fitnesses: List[float]
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size=20,
                 warmup_iterations: int = 0, distributed=False,
                 log_dir: str = "logs") -> None:
        super().__init__()

        self.domain = domain
        self.fitness_function = fitness_function
        self.population_size = population_size
        self.warmup_iterations = warmup_iterations
        self.distributed = distributed
        self.logger = TensorBoardLogger(log_dir=log_dir) if is_package_installed("tensorboard") else None

        self.current_iteration = 0
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []
        self.best_solution_fitnesses: List[float] = []

    def _launch_distributed_method(self, method: Callable) -> Tuple[List[Solution], Solution]:
        """
        Launch a distributed method using Ray.

        :param method: The method to distribute.
        :type method: Callable
        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        distribution = assign_load_equally(
            len(self.current_solutions) if len(self.current_solutions) > 0 else self.population_size)
        population = deepcopy(self.current_solutions)
        population_size = len(population)
        futures = []

        if population_size > 0:
            metagen_logger.info(
                f"[ITERATION {self.current_iteration}] Distributing with {ray.available_resources().get('CPU', 0)} CPUs -- {distribution}")
        else:
            metagen_logger.info(
                f"Distributing the initialization with {ray.available_resources().get('CPU', 0)} CPUs -- {distribution}")

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

    def _initialize(self) -> Tuple[List[Solution], Solution]:
        """
        Private function to initialize the population/solutions for the metaheuristic.

        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
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

    def _iterate(self) -> Tuple[List[Solution], Solution]:
        """
        Private function to execute one iteration of the metaheuristic.

        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        if self.current_iteration < self.warmup_iterations:
            metagen_logger.debug(
                f'[ITERATION {self.current_iteration}] Warmup iteration: {self.current_iteration}/{self.warmup_iterations}')
            population, best_individual = random_exploration(
                self.domain, self.fitness_function, len(self.current_solutions)
            )
        else:
            if self.distributed:
                if not IS_RAY_INSTALLED:
                    raise ImportError("Ray must be installed to use distributed initialization")
                population, best_individual = self._launch_distributed_method(self.iterate)
            else:
                population, best_individual = self.iterate(self.current_solutions)

        self.current_solutions = population
        self.best_solution = best_individual

        return population, best_individual

    def pre_execution(self) -> None:
        """
        Callback executed before algorithm execution starts.
        Override this method to add custom pre-execution setup.
        """
        pass

    @abstractmethod
    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population/solutions for the metaheuristic.
        Must set self.current_solutions and self.best_solution.

        :param num_solutions: The number of solutions to initialize.
        :type num_solutions: int
        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        pass

    def pre_iteration(self) -> None:
        """
        Callback executed before each iteration.
        Override this method to add custom pre-iteration processing.
        """
        pass

    @abstractmethod
    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the metaheuristic.

        :param solutions: The current population of solutions.
        :type solutions: List[Solution]
        :return: A tuple containing the updated population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        pass

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.
        Override this method to implement custom stopping criteria.

        :return: True if the algorithm should stop, False otherwise.
        :rtype: bool
        """
        return False

    def post_iteration(self) -> None:
        """
        Callback executed after each iteration.
        Override this method to add custom post-iteration processing.
        """
        metagen_logger.debug(f'[ITERATION {self.current_iteration}] POPULATION ({len(self.current_solutions)}): {self.current_solutions}')
        metagen_logger.info(f'[ITERATION {self.current_iteration}] BEST SOLUTION: {self.best_solution}')
        self.best_solution_fitnesses.append(self.best_solution.get_fitness())
        if self.logger: 
            # Log iteration metrics
            self.logger.writer.add_scalar('Population Size',
                                          len(self.current_solutions),
                                          self.current_iteration)
            self.logger.log_iteration(
                self.current_iteration, 
                self.current_solutions, 
                self.best_solution
            )

    def post_execution(self) -> None:
        """
        Callback executed after algorithm execution completes.
        Override this method to add custom post-execution cleanup.
        """
        if self.logger:
            # Log final results
            self.logger.log_final_results(self.best_solution)
            self.logger.close()

    def run(self) -> Solution:
        """
        Execute the metaheuristic algorithm.

        :return: The best solution found.
        :rtype: Solution
        """
        if self.distributed and IS_RAY_INSTALLED and not ray.is_initialized():
            ray.init()

        self.pre_execution()

        self._initialize()

        while not self.stopping_criterion():
            self.pre_iteration()

            self._iterate()

            self.post_iteration()
                    
            self.current_iteration += 1

        self.post_execution()

        if self.distributed and IS_RAY_INSTALLED and ray.is_initialized():
                ray.shutdown()

        return deepcopy(self.best_solution)
