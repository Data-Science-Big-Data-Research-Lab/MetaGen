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
from typing import Any, Optional, Callable, List, cast, Mapping, Sequence

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.metaheuristics.racing import Racing
from metagen.metaheuristics._parameters import require_alteration, require_integer, require_probability
from metagen.metaheuristics.genetic import GASolution
from metagen.metaheuristics.genetic.genetic_algorithm import _Generational
from metagen.metaheuristics.genetic.genetic_tools import require_crossover
from metagen.metaheuristics.memetic.memetic_tools import local_search_of_children


class Memetic(_Generational):
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
    :param max_iterations: The maximum number of iterations, defaults to 20; with ``max_evaluations`` or ``timeout`` and no value, no limit
    :param mutation_rate: The mutation rate, defaults to 0.1
    :param tournament_size: How many individuals compete to become a parent, defaults to 2
    :param neighbor_population_size: The size of neighborhood in local search, defaults to 10
    :param alteration_limit: How far a neighbor may move in the local search, defaults
        to a fifth of each variable's own range; a plain number is an absolute amount
    :param mutation_alteration_limit: How far a mutated child may move from where the
        crossover left it. None, the default, redraws each mutated variable over its whole
        domain: the local search already works the neighborhood, and the wide mutation is
        what lets the algorithm leave it
    {options_of_a_run}
    :param distribution_level: The level of distribution (0=none), defaults to 0
    :type domain: :py:class:`~metagen.framework.Domain`
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type population_size: int
    :type max_iterations: int or None
    :type mutation_rate: float
    :type tournament_size: int
    :type neighbor_population_size: int
    :type alteration_limit: RelativeAlteration or float or None
    :type mutation_alteration_limit: RelativeAlteration or float or None, optional
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

    # mutation_alteration_limit: measured on the benchmark over thirty seeds, a local
    # mutation is a trade for this algorithm (299 to 297 wins of 330: it gains Rosenbrock
    # and loses Schwefel and the decision tree), so it keeps the wide one that GA dropped.

    # Two parents to cross: a population of one individual raised IndexError (F-46).
    minimum_population: int = 2
    # A slice of two is all elite, as in GA: a population of 20 on ten CPUs went 1-29 against
    # the sequential run, and 11-19 with slices of four and the children returned under the
    # global model (metagen-auditoria/mediciones/distribucion_lonchas).
    minimum_slice: int = 4

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10,
                 max_iterations: Optional[int] = None, mutation_rate: float = 0.1,
                 tournament_size: int = 2,
                 neighbor_population_size: int = 10,
                 alteration_limit: Any = RelativeAlteration(0.2),
                 distributed: bool = False, log_dir: Optional[str] = None,
                 distribution_level: int = 0, seed: Optional[int] = None,
                 distribution_model: str = "global",
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1, history: Optional[str] = None,
                 max_evaluations: Optional[int] = None, timeout: Optional[float] = None,
                 initial_solutions: Optional[Sequence[Mapping[str, Any]]] = None, racing: Optional[Racing] = None,
                 refit: Optional[Callable[[Solution], Any]] = None,
                 mutation_alteration_limit: Any = None) -> None:
        """Initialize the Memetic Algorithm with the given parameters."""
        require_probability("mutation_rate", mutation_rate)
        require_integer("tournament_size", tournament_size, 1)
        require_integer("neighbor_population_size", neighbor_population_size, 1)
        require_alteration("alteration_limit", alteration_limit)
        require_alteration("mutation_alteration_limit", mutation_alteration_limit)
        require_integer("distribution_level", distribution_level, 0)
        super().__init__(domain, fitness_function, population_size=population_size, distributed=distributed, log_dir=log_dir, seed=seed,
                         distribution_model=distribution_model,
                         checkpoint=checkpoint, checkpoint_every=checkpoint_every,
                         history=history, max_evaluations=max_evaluations, timeout=timeout,
                         initial_solutions=initial_solutions, racing=racing, refit=refit)

        # Fails here, with a message that says what to do, instead of dying on
        # the first iteration with AttributeError: no attribute 'crossover' (A-07).
        require_crossover(domain, "Memetic")

        self.mutation_rate = mutation_rate
        self.max_iterations = self._iterations(max_iterations, 20)
        self.tournament_size = tournament_size
        self.neighbor_population_size = neighbor_population_size
        self.alteration_limit = alteration_limit
        self.mutation_alteration_limit: Any = mutation_alteration_limit

        if not distributed:
            self.distribution_level = 0
        else:
            self.distribution_level = distribution_level

    def _improvement(self) -> Optional[Callable[[List[GASolution]], List[GASolution]]]:
        """Every child goes through the local search before it enters the population."""
        def improve(children: List[GASolution]) -> List[GASolution]:
            return cast(List[GASolution], local_search_of_children(
                children, self.fitness_function, self.neighbor_population_size, self.alteration_limit,
                self.distribution_level))
        return improve

    @property
    def max_generations(self) -> Optional[int]:
        """The same as ``max_iterations``, the name it was kept under before."""
        # Kept under that name alone, it was the one argument of a metaheuristic the report
        # did not show (F-65).
        return self.max_iterations
