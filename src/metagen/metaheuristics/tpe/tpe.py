import heapq
from collections import Counter

from scipy.optimize import minimize

from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple, Optional, cast
import numpy as np
from scipy.stats import norm
from metagen.framework import Domain, Solution
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.tpe.tpe_tools import TPESolution
from copy import deepcopy
from metagen.framework.domain.literals import I, R, C
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
    :param population_size: Solutions evaluated by the initialization and by each
        warmup round, defaults to 20
    :type population_size: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 50
    :type max_iterations: int, optional
    :param gamma_config: How the fraction of best solutions used to build the models is
        scheduled over the run; see :py:class:`~metagen.metaheuristics.gamma_schedules.GammaConfig`.
        None, the default, is the sample-based schedule.
    :type gamma_config: GammaConfig or None, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed for the package's random generators, applied at the start of
        ``run()``; the same seed reproduces the run. None, the default, draws a different
        run every time.
    :type seed: int or None, optional
    :param distribution_model: How a distributed run makes up the next population out of
        the slices, ``"global"`` (the default: shuffled, selected among all workers) or
        ``"islands"``; see :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type distribution_model: str, optional

    :ivar max_iterations: Maximum number of iterations
    :vartype max_iterations: int
    :ivar gamma: Fraction of best solutions for model building
    :vartype gamma: float

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import TPE

        domain = Domain()
        domain.define_real("x", -5.0, 5.0)

        def fitness_function(solution: Solution) -> float:
            return solution["x"] ** 2

        search = TPE(domain, fitness_function, max_iterations=100)
        optimal_solution = search.run()
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 max_iterations: int = 50, warmup_iterations:int = 10, candidate_pool_size: int = 24,
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, population_size: int = 20,
                 distribution_model: str = "global") -> None:
        """
        Initialize the TPE algorithm.

        What a run costs, in fitness evaluations: ``population_size * (warmup_iterations
        + 1)`` before the first iteration, then ``candidate_pool_size`` per iteration.
        With the defaults that is 220 evaluations before iterating and 24 per
        iteration; ``max_iterations=10, candidate_pool_size=10`` is 320 evaluations,
        not 100.

        :param domain: The problem domain that defines the solution space
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param max_iterations: Maximum number of iterations to run, defaults to 50
        :type max_iterations: int, optional
        :param warmup_iterations: Rounds of random exploration before the search, each
            evaluating ``population_size`` solutions; their best seeds the model,
            defaults to 10
        :type warmup_iterations: int, optional
        :param candidate_pool_size: Solutions evaluated per iteration, defaults to 24
        :type candidate_pool_size: int, optional
        :param population_size: Solutions evaluated by the initialization and by each
            warmup round, defaults to 20
        :type population_size: int, optional
        :param gamma_config: How the fraction of best solutions used to build the models
            is scheduled over the run. None, the default, is the sample-based schedule.
        :type gamma_config: GammaConfig or None, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
        :type log_dir: str or None, optional
        """
        # F-47: population_size used to be inherited from the base class and could not
        # be set, and the docstring said it was 10. The warmup pays for itself: on the
        # behavior bench, 78 wins of 110 with warmup 5, 66 with 2 and 66 with 0.
        # TPE needs a domain wired to its own connector, which replaces the solution
        # and type classes. Rewiring the one it was given left it modified for good,
        # so comparing several metaheuristics in a loop depended on the order they
        # ran in (F-13). It works on a copy of its own instead.
        domain = deepcopy(domain)
        domain._connector = TPEConnector()

        super().__init__(domain, fitness_function, population_size=population_size,
                         warmup_iterations=warmup_iterations, distributed=distributed, log_dir=log_dir, seed=seed,
                         distribution_model=distribution_model)

        self.max_iterations = max_iterations
        self.candidate_pool_size = candidate_pool_size
        self.gamma_config = gamma_config if gamma_config else GammaConfig(gamma_function="sampled_based")

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """

        solution_type = solution_class(self.domain)

        best_solution: Optional[Solution] = None
        current_solutions: List[Solution] = []
        for _ in range(num_solutions):
            solution = solution_type(self.domain, connector=self.domain.get_connector())
            solution.evaluate(self.fitness_function)
            current_solutions.append(solution)

            if best_solution is None or solution.get_fitness() < best_solution.get_fitness():
                best_solution = solution

        # Zero initial solutions used to hand back None here and fail later, on the
        # first comparison against it, with nothing pointing at the cause.
        if best_solution is None:
            raise ValueError("TPE needs at least one initial solution")
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Executes one iteration of the TPE algorithm while controlling solution history growth.
        """

        # The population is the history: what this returns is what it gets back next
        # time. It used to live on self as well, and in distributed mode Ray runs
        # iterate on a pickled copy, so the driver's history stayed empty and this
        # divided by its length (F-40).
        history = list(solutions)
        # Compute gamma dynamically based on the configured strategy
        gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                              max_iterations=self.max_iterations, num_solutions=len(history))

        # Determine the number of best solutions to consider
        l = max(1, round(gamma * len(history)))  # Ensure at least one solution is considered

        # Select the best and worst solutions using heapq for efficiency
        best_solutions = heapq.nsmallest(l, history, key=lambda sol: sol.get_fitness())
        worst_solutions = heapq.nlargest(min(len(history) - l, self.candidate_pool_size),
                                         history, key=lambda sol: sol.get_fitness())

        # Generate candidate solutions and select the best one
        best_candidate = self.sample_new_solution(best_solutions, worst_solutions)
        best_candidate.evaluate(self.fitness_function)

        # Under the global distribution model the pool is shared among the slices, so
        # that an iteration costs the same on any number of CPUs; each slice draws its
        # share and the driver merges the histories.
        pool = self.candidate_pool_size
        if self.distributed and self.distribution_model == "global":
            pool = max(1, self.candidate_pool_size // self.distributed_slices)
        for _ in range(pool - 1):
            candidate = self.sample_new_solution(best_solutions, worst_solutions)
            candidate.evaluate(self.fitness_function)

            if candidate.get_fitness() < best_candidate.get_fitness():
                best_candidate = candidate  # Keep the best candidate

        # Add new best candidate while controlling history size
        history.append(best_candidate)
        history = self._limit_solution_history(history, gamma)

        # Determine best solution so far
        local_best = min(self._best_so_far(), best_candidate, key=lambda sol: sol.get_fitness())

        return history, local_best


    def _limit_solution_history(self, history: List[Solution], gamma: float) -> List[Solution]:
        """
        Keeps the history from growing indefinitely: only the last
        ``max(candidate_pool_size, gamma * max_iterations)`` solutions survive, the
        oldest going first.

        :param history: The solutions seen so far, oldest first.
        :type history: List[Solution]
        :param gamma: The fraction of best solutions in use this iteration.
        :type gamma: float
        :return: The history, trimmed.
        :rtype: List[Solution]
        """
        max_history_size = max(self.candidate_pool_size, round(gamma * self.max_iterations))
        return history[max(0, len(history) - max_history_size):]

    def sample_new_solution(self, best_solutions: List[Solution], worst_solutions: List[Solution]) -> Solution:
        
        # TPE's domain always carries TPEConnector -- the constructor copies the
        # domain and installs it (F-13) -- so the class built here is TPESolution,
        # the one that knows how to resample.
        solution_type = cast(type[TPESolution], solution_class(self.domain))
        new_solution = solution_type(self.domain, connector=self.domain.get_connector())

        new_solution.resample(best_solutions, worst_solutions)

        return new_solution

    def select_survivors(self, parents: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """
        TPE's population is its history, so under the global distribution model the
        next population is the histories every slice returned, merged without
        duplicates and oldest first, then trimmed as a single history would be. The
        parents are already inside: each slice returns the history it received plus
        its candidate.
        """
        merged = list({individual: None for individual in [*parents, *offspring]})
        gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                              max_iterations=self.max_iterations, num_solutions=len(merged))
        return self._limit_solution_history(merged, gamma)

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