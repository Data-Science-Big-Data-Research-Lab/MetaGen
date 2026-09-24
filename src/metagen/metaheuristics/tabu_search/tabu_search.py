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
from collections import deque
from copy import deepcopy
from typing import Any, Callable, Deque, List, Optional, Tuple

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.solution.types import Integer, Real
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.tools import solution_class


class TabuSearch(Metaheuristic):
    """
    Tabu search for optimization problems.

    A single current solution walks the search space. Each iteration samples a
    neighborhood around it and moves to the best neighbor that is not tabu, **even
    when that neighbor is worse than the current solution**: that is what lets the
    search leave a local optimum. The
    solutions visited lately are tabu, so the walk cannot turn straight back, and a
    tabu neighbor is still taken if it improves on the best solution ever found (the
    aspiration criterion). The best solution found is tracked apart from the walker
    and is what ``run()`` returns.

    **What "tabu" means on a continuous domain.** Two real-valued solutions are
    never exactly equal, so a list of visited points would forbid nothing. A
    neighbor is tabu when it lies within ``tabu_radius`` of a visited solution on
    every numeric variable, the radius being a small fraction of each variable's
    own range by default, and equal to it on every categorical one.

    **Neighbors are drawn around the current solution**, which gives the search a
    neighborhood of the current point to choose its move from.

    A run costs ``population_size * (warmup_iterations + 1 + max_iterations)``
    evaluations: the same as :py:class:`~metagen.metaheuristics.HillClimbing` with
    the same arguments, so the two compare on equal budgets.

    :param domain: The problem's domain to explore
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Neighbors sampled around the current solution on each
        iteration, defaults to 10
    :type population_size: int, optional
    :param warmup_iterations: Rounds of random exploration before the search, each
        evaluating ``population_size`` solutions, defaults to 5
    :type warmup_iterations: int, optional
    :param max_iterations: Iterations to run, defaults to 20
    :type max_iterations: int, optional
    :param tabu_size: How many of the latest visited solutions stay tabu, defaults to 10
    :type tabu_size: int, optional
    :param tabu_radius: How close to a visited solution a neighbor has to be, on every
        numeric variable, to count as tabu. Defaults to a fiftieth of each variable's
        range; a plain number is an absolute distance, and None demands equality.
        A small radius is enough to keep the walk from turning back; a large one
        forbids whole regions around every visited point.
    :type tabu_radius: RelativeAlteration or float or None, optional
    :param alteration_limit: How far a neighbor may move from the current solution.
        Defaults to a fifth of each variable's own range; a plain number is an
        absolute amount, and None lets a mutation land anywhere in the domain.
    :type alteration_limit: RelativeAlteration or float or None, optional
    :param distributed: Whether to sample the neighborhood on Ray, defaults to False.
        The islands share the current solution and the driver picks the move among
        every neighbor they return, so distributing changes the budget and not the
        algorithm.
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
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
    :param history: File the run writes its history to, one JSON line per iteration;
        None, the default, writes nothing. See :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type history: str or None, optional
    :param seed: Seed for MetaGen's generators, defaults to None
    :type seed: int or None, optional

    :ivar current_solution: Where the walk stands; None until the first iteration
    :vartype current_solution: Optional[Solution]
    :ivar tabu_list: The latest visited solutions, oldest first
    :vartype tabu_list: Deque[Solution]

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import TabuSearch

        domain = Domain()
        domain.define_real("x", -5.0, 5.0)
        domain.define_real("y", -5.0, 5.0)

        fitness_function = lambda solution: solution["x"] ** 2 + solution["y"] ** 2

        search = TabuSearch(domain, fitness_function, population_size=10, max_iterations=20, seed=0)
        best_solution = search.run()
    """
    # A-02, A-03: the first TabuSearch was a hill climber and was renamed; chaining the
    # neighbors is measured to be right for it and wrong for this class.
    # tabu_radius, measured on the eleven problems of the behavior bench over ten seeds,
    # wins against random sampling on the same budget: 90 of 110 with 0.02, 87 with 0.05,
    # 82 with 0.10 and 89 with None, so a small radius is as good as it gets and the list
    # itself matters little on those landscapes; HillClimbing scores 96.

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10, warmup_iterations: int = 5, max_iterations: int = 20,
                 tabu_size: int = 10, tabu_radius: Any = RelativeAlteration(0.02),
                 alteration_limit: Any = RelativeAlteration(0.2), distributed: bool = False,
                 log_dir: Optional[str] = None, seed: Optional[int] = None,
                 distribution_model: str = "global",
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1, history: Optional[str] = None):
        super().__init__(domain, fitness_function, population_size, warmup_iterations, distributed, log_dir,
                         seed=seed, distribution_model=distribution_model,
                         checkpoint=checkpoint, checkpoint_every=checkpoint_every,
                         history=history)
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.tabu_radius: Any = tabu_radius
        self.alteration_limit: Any = alteration_limit
        self.tabu_list: Deque[Solution] = deque(maxlen=tabu_size)
        self.current_solution: Optional[Solution] = None
        self._around: Optional[Solution] = None
        self._aspiration_level: float = float("inf")

    def pre_execution(self) -> None:
        """Start every run from nothing visited, so that a seed reproduces a run."""
        # A-06: state left over from a previous run() would change what the seed gives.
        super().pre_execution()
        self.tabu_list.clear()
        self.current_solution = None
        self._around = None

    def initialize(self, num_solutions: int = 10) -> Tuple[List[Solution], Solution]:
        """
        Draw a random solution and its first neighborhood. The walk starts from the
        best solution known after this step, which may come from the warmup.
        """
        solution_type = solution_class(self.domain)
        first_solution = solution_type(self.domain, connector=self.domain.get_connector())
        first_solution.evaluate(self.fitness_function)
        neighborhood = self._neighborhood(first_solution, num_solutions - 1)
        neighborhood.append(first_solution)
        return neighborhood, min(neighborhood, key=Solution.get_fitness)

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Sample as many neighbors around the current solution as the population
        handed in has individuals, and return them with the best of them. The move
        itself is chosen in post_iteration, on the driver.
        """
        # F-40: Ray runs this on a copy of the algorithm, so it keeps no state in self.
        around = self._around if self._around is not None else self._best_so_far()
        neighborhood = self._neighborhood(around, max(1, len(solutions)))
        return neighborhood, min(neighborhood, key=Solution.get_fitness)

    def pre_iteration(self) -> None:
        """
        Fix where this iteration's neighborhood is drawn, the current solution or the
        best known before the first move, and the aspiration level: the best fitness
        before the neighborhood is seen. Both are set on the driver, so a Ray worker
        sees them.
        """
        # F-40: what a worker needs is set here, before the algorithm is serialized.
        super().pre_iteration()
        self._around = self.current_solution if self.current_solution is not None else self._best_so_far()
        self._aspiration_level = self._best_so_far().get_fitness()

    def post_iteration(self) -> None:
        """
        Move to the best neighbor that is not tabu, or that beats the best solution
        ever found, worse than the current solution or not. If every neighbor is
        tabu, move to the one whose tabu solution is the oldest, the first to be
        forgotten. The point left and the point reached are both tabu from now on.
        """
        super().post_iteration()
        if self._around is not None and not (self.tabu_list and self.tabu_list[-1] is self._around):
            self.tabu_list.append(self._around)
        neighborhood = self.current_solutions
        admissible = [neighbor for neighbor in neighborhood
                      if not self.is_tabu(neighbor) or neighbor.get_fitness() < self._aspiration_level]
        if admissible:
            self.current_solution = min(admissible, key=Solution.get_fitness)
        else:
            self.current_solution = min(neighborhood, key=lambda n: (self._tabu_age(n), n.get_fitness()))
        self.tabu_list.append(self.current_solution)

    def select_survivors(self, parents: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """The population is the fresh neighborhood of the current solution, which
        post_iteration picks the move from: under the global distribution model the
        driver keeps what the workers returned, all slices together."""
        return offspring

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def is_tabu(self, solution: Solution) -> bool:
        """
        Whether a solution lies within ``tabu_radius`` of a recently visited one.

        :param solution: The candidate neighbor.
        :type solution: Solution
        :return: True if some visited solution is within the radius on every variable.
        :rtype: bool
        """
        return any(self._within_radius(solution, visited) for visited in self.tabu_list)

    def _tabu_age(self, solution: Solution) -> int:
        """Position in the tabu list of the oldest visited solution within the radius."""
        return next((index for index, visited in enumerate(self.tabu_list)
                     if self._within_radius(solution, visited)), len(self.tabu_list))

    def _within_radius(self, solution: Solution, visited: Solution) -> bool:
        for name, value in solution.get_variables().items():
            # An inactive variable does not tell two solutions apart; if it is active
            # in only one of them, the variable it depends on differs and fails below.
            if not solution.is_active(name):
                continue
            other = visited.get(name)
            if isinstance(value, Solution) and isinstance(other, Solution):
                if not self._within_radius(value, other):
                    return False
            elif isinstance(value, (Integer, Real)) and isinstance(other, (Integer, Real)):
                _, min_value, max_value, _ = value.get_definition().get_attributes()
                if isinstance(self.tabu_radius, RelativeAlteration):
                    radius = self.tabu_radius.of(min_value, max_value)
                else:
                    radius = self.tabu_radius or 0
                if abs(value.get() - other.get()) > radius:
                    return False
            elif value != other:
                return False
        return True

    def _neighborhood(self, around: Solution, size: int) -> List[Solution]:
        neighborhood = []
        for _ in range(size):
            neighbor = deepcopy(around)
            neighbor.mutate(alteration_limit=self.alteration_limit)
            neighbor.evaluate(self.fitness_function)
            neighborhood.append(neighbor)
        return neighborhood
