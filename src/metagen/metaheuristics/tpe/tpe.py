import heapq
from collections import deque

from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple, Optional

from metagen.framework import Domain, Solution
from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma
from .tpe_tools import TPEConnector


class TPE(Metaheuristic):
    """
    Tree-structured Parzen Estimator (TPE) algorithm for optimization problems.

    This class implements the TPE metaheuristic which uses kernel density estimation
    to model the probability of good and bad solutions. The algorithm iteratively
    samples new solutions from regions of the search space that are more likely to
    contain good solutions.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Size of the population to maintain, defaults to 10
    :type population_size: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 50
    :type max_iterations: int, optional
    :param gamma: Fraction of best solutions to consider when building models, defaults to 0.25
    :type gamma: float, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/TPE"
    :type log_dir: str, optional

    :ivar max_iterations: Maximum number of iterations
    :vartype max_iterations: int
    :ivar gamma: Fraction of best solutions for model building
    :vartype gamma: float

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import TPE
        
        domain = Domain()
        domain.defineInteger(0, 1)
        
        fitness_function = ...

        search = TPE(domain, fitness_function, population_size=50, max_iterations=100)
        optimal_solution = search.run()
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 max_iterations: int = 50, warmup_iterations:int = 10, candidate_pool_size: int = 24,
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: str = "logs/TPE") -> None:
        """
        Initialize the TPE algorithm.

        :param domain: The problem domain that defines the solution space
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param population_size: Size of the population to maintain, defaults to 10
        :type population_size: int, optional
        :param max_iterations: Maximum number of iterations to run, defaults to 50
        :type max_iterations: int, optional
        :param gamma: Fraction of best solutions to consider when building models, defaults to 0.25
        :type gamma: float, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory for logging, defaults to "logs/TPE"
        :type log_dir: str, optional
        """
        super().__init__(domain, fitness_function, warmup_iterations=warmup_iterations, distributed=distributed, log_dir=log_dir)

        self.max_iterations = max_iterations
        self.candidate_pool_size = candidate_pool_size
        self.gamma_config = gamma_config if gamma_config else GammaConfig(gamma_function="sampled_based")
        self.solution_history = deque()
        self.domain._connector = TPEConnector()

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """

        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())

        best_solution = None
        current_solutions = []
        for _ in range(num_solutions):
            solution = solution_type(self.domain, connector=self.domain.get_connector())
            solution.evaluate(self.fitness_function)
            self.solution_history.append(solution)
            current_solutions.append(solution)

            if best_solution is None or best_solution.get_fitness() < solution.get_fitness():
                best_solution = solution

        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Executes one iteration of the TPE algorithm while controlling solution history growth.
        """

        # Compute gamma dynamically based on the configured strategy
        gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                              max_iterations=self.max_iterations, num_solutions=len(self.solution_history))

        # Determine the number of best solutions to consider
        l = max(1, round(gamma * len(self.solution_history)))  # Ensure at least one solution is considered

        # Select the best and worst solutions using heapq for efficiency
        best_solutions = heapq.nsmallest(l, self.solution_history, key=lambda sol: sol.get_fitness())
        worst_solutions = heapq.nlargest(min(len(self.solution_history) - l, self.candidate_pool_size),
                                         self.solution_history, key=lambda sol: sol.get_fitness())

        # Generate candidate solutions and select the best one
        best_candidate = self.sample_new_solution(best_solutions, worst_solutions)
        best_candidate.evaluate(self.fitness_function)

        for _ in range(self.candidate_pool_size - 1):
            candidate = self.sample_new_solution(best_solutions, worst_solutions)
            candidate.evaluate(self.fitness_function)

            if candidate.get_fitness() < best_candidate.get_fitness():
                best_candidate = candidate  # Keep the best candidate

        # Add new best candidate while controlling history size
        self.solution_history.append(best_candidate)
        self._limit_solution_history(gamma)

        # Determine best solution so far
        local_best = min(self.best_solution, best_candidate, key=lambda sol: sol.get_fitness())

        return list(self.solution_history), local_best


    def _limit_solution_history(self, gamma: float):
        """
        Ensures the solution history does not grow indefinitely.
        Keeps only the last `gamma * max_iterations` solutions.
        """
        max_history_size = max(self.candidate_pool_size, round(gamma * self.max_iterations))
        while len(self.solution_history) > max_history_size:
            self.solution_history.popleft()  # Remove oldest solutions

    def sample_new_solution(self, best_solutions: List[Solution], worst_solutions: List[Solution]) -> Solution:
        
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        new_solution = solution_type(self.domain, connector=self.domain.get_connector())

        new_solution.resample(best_solutions, worst_solutions)

        return new_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        The algorithm stops when the current iteration reaches the maximum number
        of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """Additional processing after each generation"""
        super().post_iteration()
        if self.logger:
            self.logger.writer.add_scalar('TPE/Population Size', len(self.current_solutions), self.current_iteration)