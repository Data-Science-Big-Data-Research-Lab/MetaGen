from collections import deque
from metagen.framework import Domain, RelativeAlteration, Solution
from collections.abc import Callable
from typing import Any, List, Tuple, Deque, Optional

from metagen.metaheuristics.tools import local_search_with_tabu, solution_class
from metagen.metaheuristics.base import Metaheuristic
from copy import deepcopy

from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma


class HillClimbing(Metaheuristic):
    """
    Stochastic hill climbing for optimization problems.

    Each iteration samples several neighbors around the best solution found so far and
    moves to the best of them, if it improves. A worse neighbor is never accepted, so
    the search only ever walks uphill.

    It keeps a short memory of the solutions already visited, so as not to evaluate
    them again. :py:class:`~metagen.metaheuristics.TabuSearch` is the alternative that
    also accepts worsening moves.

    :param domain: The problem's domain to explore
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Size of the population (neighborhood) to maintain, defaults to 10
    :type population_size: int, optional
    :param warmup_iterations: Rounds of random exploration before the search, each
        evaluating ``population_size`` solutions, defaults to 5. A run costs
        ``population_size * (warmup_iterations + 1 + max_iterations)`` evaluations:
        with the defaults, 60 of them before the first iteration
    :type warmup_iterations: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 20
    :type max_iterations: int, optional
    :param tabu_size: Maximum size of the tabu list, defaults to 5
    :type tabu_size: int, optional
    :param alteration_limit: How far a neighbor may move from the current solution.
        Defaults to a fifth of each variable's own range; a plain number is an
        absolute amount instead, and None lets a mutation land anywhere in the domain.
    :type alteration_limit: RelativeAlteration or float or None, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param gamma_config: When given, each iteration samples only a share of the
        ``population_size`` neighbors, the share a gamma schedule gives for that
        iteration; see :py:class:`~metagen.metaheuristics.gamma_schedules.GammaConfig`.
        None, the default, samples them all.
    :type gamma_config: GammaConfig or None, optional
    :param seed: Seed for the package's random generators, applied at the start of
        ``run()``; the same seed reproduces the run. None, the default, draws a different
        run every time.
    :type seed: int or None, optional
    :param distribution_model: How a distributed run makes up the next population out of
        the slices, ``"global"`` (the default: shuffled, selected among all workers) or
        ``"islands"``; see :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type distribution_model: str, optional
    :param checkpoint: File the run saves its state to every ``checkpoint_every``
        iterations, and continues from if it exists when ``run()`` starts; None, the
        default, saves nothing. See :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type checkpoint: str or None, optional
    :param checkpoint_every: Iterations between two saves (default is 1).
    :type checkpoint_every: int, optional

    :ivar max_iterations: Maximum number of iterations to run
    :vartype max_iterations: int
    :ivar tabu_size: Maximum size of the tabu list
    :vartype tabu_size: int
    :ivar tabu_list: Solutions already visited, skipped when sampling neighbors
    :vartype tabu_list: Deque[Solution]
    :ivar alteration_limit: How far a neighbor may move from the current solution
    :vartype alteration_limit: RelativeAlteration or float or None

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import HillClimbing

        domain = Domain()
        domain.define_real("x", -5.0, 5.0)
        domain.define_real("y", -5.0, 5.0)

        def fitness_function(solution: Solution) -> float:
            return solution["x"] ** 2 + solution["y"] ** 2

        algorithm = HillClimbing(domain, fitness_function, population_size=10, max_iterations=20, seed=0)
        best_solution = algorithm.run()
    """
    # A-02: renamed from TabuSearch instead of rewritten, because the algorithm is good:
    # on the behavior bench it was the best of the package when it was renamed.
    # F-47: the warmup's cost went into the docstring because nobody could see it.

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10, warmup_iterations:int = 5,
                 max_iterations: int = 20, tabu_size: int = 5,
                 alteration_limit: Any = RelativeAlteration(0.2),
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, distribution_model: str = "global",
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1):
        """
        Initialize the hill climbing algorithm.

        :param domain: The problem's domain to explore
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param population_size: Size of the population (neighborhood) to maintain, defaults to 10
        :type population_size: int, optional
        :param max_iterations: Maximum number of iterations to run, defaults to 20
        :type max_iterations: int, optional
        :param tabu_size: Maximum size of the tabu list, defaults to 5
        :type tabu_size: int, optional
        :param alteration_limit: How far a neighbor may move from the current solution,
            defaults to a fifth of each variable's own range
        :type alteration_limit: RelativeAlteration or float or None, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
        :type log_dir: str or None, optional
        """
        super().__init__(domain, fitness_function, population_size, warmup_iterations, distributed, log_dir, seed=seed,
                         distribution_model=distribution_model,
                         checkpoint=checkpoint, checkpoint_every=checkpoint_every)
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.tabu_list:Deque[Solution] = deque(maxlen=tabu_size)
        self.alteration_limit: Any = alteration_limit
        self.gamma_config = gamma_config

    def initialize(self, num_solutions: int = 10) -> Tuple[List[Solution], Solution]:
        """
        Initializes the Tabu Search algorithm.

        Creates an initial solution and explores its neighborhood while respecting
        the tabu list constraints.
        """
        solution_type = solution_class(self.domain)
        first_solution = solution_type(self.domain, connector=self.domain.get_connector())
        first_solution.evaluate(self.fitness_function)

        current_neighborhood, _ = local_search_with_tabu(
            first_solution, self.fitness_function, num_solutions - 1, self.alteration_limit, list(self.tabu_list)
        )

        # The population must hold exactly `num_solutions` individuals.
        current_neighborhood.append(first_solution)

        return current_neighborhood, first_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the Tabu Search algorithm.

        Explores the neighborhood of the current best solution while respecting
        the tabu list constraints. The best solution found is added to the tabu list
        to prevent cycling.

        :param solutions: Current population of solutions
        :type solutions: List[Solution]
        :return: A tuple containing the new neighborhood solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        # The neighborhood is the whole population, or the share of it a gamma schedule gives.

        if self.gamma_config:
            gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                                  max_iterations=self.max_iterations, num_solutions=max(1, len(solutions)))
            l = max(1, round(gamma * len(solutions)))  # at least one neighbor
        else:
            l = max(1, len(solutions))  # at least one neighbor

        # Local search over `l` neighbors, skipping the ones already visited.
        current_solutions, best_solution = local_search_with_tabu(
            self._best_so_far(), self.fitness_function, l, self.alteration_limit,
            list(self.tabu_list)
        )

        # With no valid neighbor, keep the previous population.
        if not current_solutions:
            current_solutions = solutions
            best_solution = deepcopy(self._best_so_far())
        # The tabu list is fed in post_iteration, not here: in distributed mode Ray
        # runs iterate on a pickled copy and whatever it stores on self is lost, so
        # the list ended every distributed run empty (F-40).
        return current_solutions, best_solution

    def post_iteration(self) -> None:
        """
        Remembers the best solution of the iteration in the tabu list, so that the
        next neighborhood skips it. Runs on the driver, which is why the list
        survives a distributed run.
        """
        # F-40: appended here and not in iterate, which Ray runs on a copy.
        super().post_iteration()
        best_solution = self._best_so_far()
        if best_solution not in self.tabu_list:
            self.tabu_list.append(best_solution)

    def select_survivors(self, parents: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """The population is the fresh neighborhood of the best solution: under the
        global distribution model the driver keeps what the workers returned, all
        slices together, and not the previous neighborhood."""
        return offspring

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        The algorithm stops when the current iteration reaches the maximum number of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations
