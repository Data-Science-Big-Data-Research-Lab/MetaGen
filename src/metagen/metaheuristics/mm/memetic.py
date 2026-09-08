import heapq
from copy import deepcopy
from typing import Optional, Callable, Tuple, List, cast

from metagen.framework import Domain, Solution
from metagen.metaheuristics.tools import random_exploration
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.ga import GASolution
from metagen.metaheuristics.ga.ga_tools import (yield_two_children, require_crossover,
                                                tournament_selection)
from metagen.metaheuristics.mm.mm_tools import local_search_of_two_children


class Memetic(Metaheuristic):
    """
    This class implements the *Memetic* algorithm. It uses the :py:class:`~metagen.framework.Solution` class as an
    abstraction of an individual for the meta-heuristic.

    It solves an optimization problem defined by a :py:class:`~metagen.framework.Domain` object and an
    implementation of a fitness function.

    The algorithm combines genetic algorithms with local search strategies to enhance solution quality.
    Each generation involves:
    1. Selection of the parents by tournament
    2. Genetic operations (crossover and mutation)
    3. Local search improvement
    4. Population update

    :param domain: The problem domain
    :param fitness_function: The fitness function to optimize
    :param population_size: The population size, defaults to 10
    :param max_iterations: The maximum number of iterations, defaults to 20
    :param mutation_rate: The mutation rate, defaults to 0.1
    :param tournament_size: How many individuals compete to become a parent, defaults to 2
    :param neighbor_population_size: The size of neighborhood in local search, defaults to 10
    :param alteration_limit: The maximum alteration allowed in local search, defaults to 1.0
    :param distributed: Whether to use distributed computation, defaults to False
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :param distribution_level: The level of distribution (0=none), defaults to 0
    :type domain: :py:class:`~metagen.framework.Domain`
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type population_size: int
    :type max_iterations: int
    :type mutation_rate: float
    :type tournament_size: int
    :type neighbor_population_size: int
    :type alteration_limit: float
    :type distributed: bool
    :type log_dir: str or None, optional
    :type distribution_level: int

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import GAConnector, Memetic

        # The memetic algorithm crosses solutions over, so its domain needs the
        # GA connector; a plain Domain() fails on the first iteration.
        domain = Domain(connector=GAConnector())
        domain.define_real("x", -5.0, 5.0)

        def fitness_function(solution: Solution) -> float:
            return solution["x"] ** 2

        memetic = Memetic(domain, fitness_function, population_size=50, max_iterations=100)
        best_solution = memetic.run()
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10,
                 max_iterations: int = 20, mutation_rate: float = 0.1,
                 tournament_size: int = 2,
                 neighbor_population_size: int = 10, alteration_limit: float = 1.0,
                 distributed: bool = False, log_dir: Optional[str] = None,
                 distribution_level: int = 0, seed: Optional[int] = None) -> None:
        """Initialize the Memetic Algorithm with the given parameters."""
        super().__init__(domain, fitness_function, population_size=population_size, distributed=distributed, log_dir=log_dir, seed=seed)

        # Fails here, with a message that says what to do, instead of dying on
        # the first iteration with AttributeError: no attribute 'crossover' (A-07).
        require_crossover(domain, "Memetic")

        self.mutation_rate = mutation_rate
        self.max_generations = max_iterations
        self.tournament_size = tournament_size
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit

        if not distributed:
            self.distribution_level = 0
        else:
            self.distribution_level = distribution_level

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """Initialize the population with random solutions.

        :param num_solutions: The number of solutions to generate, defaults to 10
        :type num_solutions: int
        :return: A tuple containing the initial population and the best solution
        :rtype: Tuple[List[:py:class:`~metagen.framework.Solution`], :py:class:`~metagen.framework.Solution`]
        """
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[GASolution]) -> Tuple[List[Solution], Solution]:
        """Perform one iteration of the memetic algorithm.

        This method:
        1. Selects the parents by tournament
        2. Creates offspring through genetic operations
        3. Improves offspring through local search
        4. Updates the population

        :param solutions: The current population
        :type solutions: List[:py:class:`~metagen.metaheuristics.ga.GASolution`]
        :return: A tuple containing the updated population and the best solution
        :rtype: Tuple[List[:py:class:`~metagen.framework.Solution`], :py:class:`~metagen.framework.Solution`]
        """
        num_solutions = len(solutions)
        elite = heapq.nsmallest(2, solutions, key=lambda sol: sol.get_fitness())
        best_solution = deepcopy(self.best_solution)
        current_solutions = [deepcopy(elite[0]), deepcopy(elite[1])]

        for _ in range(num_solutions // 2):

            # A-01: the pair is drawn again for every crossover, as in GA. Taking the
            # two best once, outside the loop, bred the same pair every time and the
            # population converged on a couple of points. The two best still go
            # through untouched, as the elite above.
            father = cast(GASolution, tournament_selection(solutions, self.tournament_size))
            mother = cast(GASolution, tournament_selection(solutions, self.tournament_size))
            child1, child2 = yield_two_children((father, mother), self.mutation_rate, self.fitness_function)
            lc_child1, lc_child2 = local_search_of_two_children((child1, child2), self.fitness_function,
                                                                self.neighbor_population_size,
                                                                self.alteration_limit, self.distribution_level)

            current_solutions.extend([lc_child1, lc_child2])

            if best_solution is None or lc_child1 < best_solution:
                best_solution = lc_child1
            if best_solution is None or lc_child2 < best_solution:
                best_solution = lc_child2

        current_solutions = current_solutions[:num_solutions]

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the stopping criterion is met.

        The stopping criterion is met when the maximum number of generations is reached.

        :return: True if the stopping criterion is met, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_generations
