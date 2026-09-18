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
from collections.abc import Callable
from copy import deepcopy
from typing import Any, Optional, List, Tuple, cast

from metagen.framework import Domain, RelativeAlteration, Solution
from .ga_tools import (GASolution, yield_two_children, require_crossover,
                       tournament_selection)
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.tools import random_exploration
from ...logging.metagen_logger import metagen_logger


class SSGA(Metaheuristic):
    """
    Steady State Genetic Algorithm (SSGA) class for optimization problems which is a variant of the Genetic Algorithm (GA) with population replacement.
    
    :param domain: The domain representing the problem space.
    :type domain: Domain
    :param fitness_func: The fitness function used to evaluate solutions.
    :type fitness_func: Callable[[Solution], float]
    :param population_size: The size of the population (default is 10).
    :type population_size: int, optional
    :param mutation_rate: The probability of mutation for each solution (default is 0.1).
    :type mutation_rate: float, optional
    :param n_iterations: The number of generations to run the algorithm (default is 50).
    :type n_iterations: int, optional
    :param tournament_size: How many individuals compete to become a parent (default is 2,
        the mildest tournament). Raising it makes the search greedier.
    :type tournament_size: int, optional
    :param mutation_alteration_limit: How far a mutated child may move from where the
        crossover left it. Defaults to ``RelativeAlteration(0.2)``, a fifth of each
        variable's own range, so that a mutation moves a child near where the crossover
        left it; a plain number is an absolute amount and None redraws the variable over
        its whole domain.
    :type mutation_alteration_limit: RelativeAlteration or float or None, optional
    :param distribution_model: How a distributed run makes up the next population out of
        the slices, ``"global"`` (the default: shuffled, selected among all workers) or
        ``"islands"``; see :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type distribution_model: str, optional

    :ivar population_size: The size of the population.
    :vartype population_size: int
    :ivar mutation_rate: The probability of mutation for each solution.
    :vartype mutation_rate: float
    :ivar n_iterations: The number of generations to run the algorithm.
    :vartype n_iterations: int
    :ivar domain: The domain representing the problem space.
    :vartype domain: Domain
    :ivar fitness_func: The fitness function used to evaluate solutions.
    :vartype fitness_func: Callable[[Solution], float]

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import SSGA, GAConnector

        # A genetic algorithm crosses solutions over, so its domain needs the GA connector.
        domain = Domain(connector=GAConnector())
        domain.define_real("x", -5.0, 5.0)
        domain.define_real("y", -5.0, 5.0)

        def fitness_function(solution: Solution) -> float:
            return solution["x"] ** 2 + solution["y"] ** 2

        algorithm = SSGA(domain, fitness_function, population_size=10, max_iterations=50, seed=0)
        best_solution = algorithm.run()
    """

    # mutation_alteration_limit: measured on the benchmark over thirty seeds, the local
    # mutation took SSGA from 168 to 176 wins of 330 against random sampling on the
    # same budget: neutral for it, a clear gain for GA, so the two share the default.

    # Two parents to cross: a distributed slice of one individual raised IndexError (F-46).
    minimum_slice: int = 2

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10,
                 max_iterations: int = 50, mutation_rate: float = 0.1,
                 tournament_size: int = 2,
                 distributed: bool = False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, distribution_model: str = "global",
                 mutation_alteration_limit: Any = RelativeAlteration(0.2)):
        super().__init__(domain, fitness_function, population_size=population_size, distributed=distributed, log_dir=log_dir, seed=seed,
                         distribution_model=distribution_model)

        # Fails here, with a message that says what to do, instead of dying on
        # the first iteration with AttributeError: no attribute 'crossover' (A-07).
        require_crossover(domain, "SSGA")
        self.mutation_rate = mutation_rate
        self.max_iterations = max_iterations
        self.tournament_size = tournament_size
        self.mutation_alteration_limit: Any = mutation_alteration_limit

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Iterate the algorithm for one generation.
        """
        # A-01: crossing the top two every single iteration is truncation selection at
        # its most extreme. The population converged on that pair within three
        # iterations and stayed there, and since crossing a point with itself gives it
        # back, 69 % of the crossovers came out with two identical children and the
        # iteration below was skipped whole. The steady state replacement is untouched:
        # what makes this algorithm steady state is that only the two worst are
        # replaced, not how the parents are chosen.
        father = cast(GASolution, tournament_selection(solutions, self.tournament_size))
        mother = cast(GASolution, tournament_selection(solutions, self.tournament_size))

        child1, child2 = yield_two_children((father, mother), self.mutation_rate, self.fitness_function,
                                              self.mutation_alteration_limit)

        best_solution = deepcopy(self._best_so_far())

        if child1 != child2:
            # By index. This is not a bug fix: looking the individuals up with
            # solutions.index(worst) gives the same answer, because index() rescans
            # the list after the first replacement and so finds the other duplicate.
            # A-05 claims otherwise and was refuted; 4096 exhaustive cases and 200000
            # random ones give identical results either way.
            #
            # It is here because that correctness is accidental: rebuild this block
            # around a new list instead of mutating in place, a perfectly reasonable
            # refactor, and the by-value lookup starts losing a child whenever the
            # population holds a duplicate. Working by index does not depend on it.
            worst_indexes = heapq.nlargest(
                2, range(len(solutions)), key=lambda index: solutions[index].get_fitness())
            candidates = [solutions[index] for index in worst_indexes] + [child1, child2]
            best_two = heapq.nsmallest(2, candidates, key=lambda sol: sol.get_fitness())
            for index, replacement in zip(worst_indexes, best_two):
                solutions[index] = replacement
            best_solution = heapq.nsmallest(1, solutions, key=lambda sol: sol.get_fitness())[0]
        else:
            metagen_logger.info(f'[ITERATION {self.current_iteration}] Both children are the same, skipping iteration')

        return solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations
