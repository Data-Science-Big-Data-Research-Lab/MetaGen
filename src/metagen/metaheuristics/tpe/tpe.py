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
import heapq


from metagen.metaheuristics.racing import Racing
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics._parameters import require_integer
import math
from typing import Callable, List, Tuple, Optional, cast, Any, Mapping, Sequence
from metagen.framework import Domain, Solution
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.tpe.tpe_tools import TPESolution
from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma
from .tpe_tools import TPEConnector


class TPE(Metaheuristic):
    # The docstring described a kernel density estimate that samples the promising
    # regions; it now says what the code does, without changing the code, which is the
    # TPE the published article evaluates (AUD-001 and AUD-002 of
    # metagen-auditoria/AUDITORIA-2026-11-16.md). The mixture of kernels sampled from the
    # model of the best is KernelTPE.
    """
    Tree-structured Parzen Estimator (TPE) for optimization problems, with one normal
    density per variable for the best solutions and one for the rest.

    It keeps a history of the solutions it has evaluated, splits it into the best
    fraction ``gamma`` and the rest, and builds every candidate variable by variable:

    - **A real or an integer** is modeled by a normal density fitted to its values in
      the best solutions, ``l``, and another fitted to its values in the rest, ``g``. A
      candidate starts from a value ``v`` drawn uniformly over the domain, and takes a
      value drawn from ``l`` with probability ``l(v) / (l(v) + g(v))``, or from ``g``
      otherwise, clipped to the range and placed on the grid of the step. A variable on
      a logarithmic scale is modeled on its logarithm.
    - **A categorical variable** takes one of the categories of the best solutions, each
      with its frequency among them; when they all share one, a category drawn uniformly.
    - **A subset** includes every element with the probability it has among the best
      solutions, together with a prior worth one of them; **a permutation** takes the
      ordering of one of the best solutions, moved by one swap; **a structure** is built
      position by position, from the best solutions that have each position.

    Every iteration evaluates ``candidate_pool_size`` candidates and adds the best of
    them to the history, which keeps its most recent solutions.

    :py:class:`~metagen.metaheuristics.KernelTPE` models each variable with a mixture of
    kernels instead, draws its candidates from the model of the best solutions and
    evaluates only the one that maximizes ``l(x) / g(x)``.

    What a run costs, in fitness evaluations: ``population_size * (warmup_iterations
    + 1)`` before the first iteration, then ``candidate_pool_size`` per iteration.
    With the defaults that is 220 evaluations before iterating and 24 per
    iteration; ``max_iterations=10, candidate_pool_size=10`` is 320 evaluations,
    not 100.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Solutions evaluated by the initialization and by each
        warmup round, defaults to 20
    :type population_size: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 50. With
        ``max_evaluations`` and no value, the iterations the budget buys after the
        warmup and the initialization; with ``timeout`` alone, 50
    :type max_iterations: int or None, optional
    :param warmup_iterations: Rounds of random exploration before the search, each
        evaluating ``population_size`` solutions; their best is kept as the best
        of the run so far. None, the default, is 10, or fewer with ``max_evaluations``:
        the warmup and the initialization then take at most a quarter of the budget.
    :type warmup_iterations: int or None, optional
    :param candidate_pool_size: Solutions evaluated per iteration, defaults to 24
    :type candidate_pool_size: int, optional
    :param gamma_config: How the fraction of best solutions used to build the models is
        scheduled over the run; see :py:class:`~metagen.metaheuristics.GammaConfig`.
        None, the default, is the sample-based schedule.
    :type gamma_config: GammaConfig or None, optional
    {options_of_a_run}

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

    #: The iterations of a run that sets no budget and no max_iterations.
    default_max_iterations: int = 50
    #: The warmup rounds when ``warmup_iterations`` is not given and the budget leaves room for them.
    default_warmup_iterations: int = 10

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 max_iterations: Optional[int] = None, warmup_iterations: Optional[int] = None,
                 candidate_pool_size: int = 24,
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, population_size: int = 20,
                 distribution_model: str = "global",
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1, history: Optional[str] = None,
                 max_evaluations: Optional[int] = None, timeout: Optional[float] = None,
                 initial_solutions: Optional[Sequence[Mapping[str, Any]]] = None, racing: Optional[Racing] = None,
                 refit: Optional[Callable[[Solution], Any]] = None) -> None:
        # F-47: population_size used to be inherited from the base class and could not
        # be set, and the docstring said it was 10. The warmup pays for itself: on the
        # behavior bench, 78 wins of 110 with warmup 5, 66 with 2 and 66 with 0. It pays
        # through the best solution it hands on, not through the model, which never sees
        # its samples (F-53). Letting them into TPE's history was measured and left out:
        # 234 wins of 330 against random sampling before and after, 30 seeds, worse on
        # Ackley (p = 0.002), and TPE is the one the published article evaluates.
        # KernelTPE, which keeps its whole history, does take them in.
        # TPE needs a domain wired to its own connector, which replaces the solution
        # and type classes. Rewiring the one it was given left it modified for good,
        # so comparing several metaheuristics in a loop depended on the order they
        # ran in (F-13). It works on a copy of its own instead.
        domain = domain._with_connector(TPEConnector())

        require_integer("population_size", population_size, 1)
        require_integer("warmup_iterations", warmup_iterations, 0, optional=True)
        require_integer("candidate_pool_size", candidate_pool_size, 1)
        warmup_iterations = self._warmup_for(warmup_iterations, population_size, max_evaluations)

        super().__init__(domain, fitness_function, population_size=population_size,
                         warmup_iterations=warmup_iterations, distributed=distributed, log_dir=log_dir, seed=seed,
                         distribution_model=distribution_model,
                         checkpoint=checkpoint, checkpoint_every=checkpoint_every,
                         history=history, max_evaluations=max_evaluations, timeout=timeout,
                         initial_solutions=initial_solutions, racing=racing, refit=refit)

        # The gamma schedule and the size of the history are planned over max_iterations,
        # so a budget of evaluations becomes the iterations it buys.
        start = population_size * (warmup_iterations + 1)
        self.max_iterations: int = cast(int, self._iterations(
            max_iterations, self.default_max_iterations,
            horizon=lambda budget: math.ceil((budget - start) / candidate_pool_size)))
        self.candidate_pool_size = candidate_pool_size
        self.gamma_config = gamma_config if gamma_config else GammaConfig(gamma_function="sampled_based")

    def _warmup_for(self, warmup_iterations: Optional[int], population_size: int,
                    max_evaluations: Optional[int]) -> int:
        """
        The warmup rounds of the run: the ones given, or the default, reduced so that the
        warmup and the initialization take at most a quarter of ``max_evaluations``.
        """
        # With the defaults the warmup and the initialization cost 220 evaluations (120 in
        # KernelTPE), so a budget of 100, a usual one for tuning, was random sampling and the
        # model never ran: 0 iterations of it, 44 wins of 90 against random sampling on the
        # nine functions of the bench, 10 seeds (Y-10,
        # metagen-auditoria/auditoria-independiente-2026-11/eficacia-fable.md). The runs of
        # the article give max_iterations, not max_evaluations, and are not affected.
        if warmup_iterations is not None:
            return warmup_iterations
        if max_evaluations is None:
            return self.default_warmup_iterations
        return min(self.default_warmup_iterations, max(0, max_evaluations // 4 // population_size - 1))

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
        # share and the driver merges the histories. The first slices take what the
        # division leaves over: with the whole quotient only, 10 candidates on 4 CPUs
        # were 8 (metagen-preproduction, 30 October 2026).
        pool = self.candidate_pool_size
        if self.distributed and self.distribution_model == "global":
            share, left_over = divmod(self.candidate_pool_size, self.distributed_slices)
            pool = max(1, share + (1 if self.distributed_slice < left_over else 0))
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
        return self._iterations_done()

    def post_iteration(self) -> None:
        """Additional processing after each generation"""
        super().post_iteration()
        if self.logger:
            self.logger.writer.add_scalar('TPE/Population Size', len(self.current_solutions), self.current_iteration)