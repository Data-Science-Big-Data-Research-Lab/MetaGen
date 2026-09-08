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
from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.metaheuristics.tools import random_exploration
import math
from copy import deepcopy
from typing import Any, Optional, Callable, Tuple, List
from metagen.metaheuristics.base import Metaheuristic
from metagen.framework.rng import get_rng


def calculate_exploration_rate(best_solution_fitness: float, neighbor_fitness: float,
                               initial_temp: float) -> float:
    """
    Calculate the exploration rate for simulated annealing using the Metropolis criterion.

    The exploration rate determines the probability of accepting a worse solution
    based on the current temperature and the difference in fitness values.

    :param best_solution_fitness: Fitness of the current best solution
    :type best_solution_fitness: float
    :param neighbor_fitness: Fitness of the neighbor solution being considered
    :type neighbor_fitness: float
    :param initial_temp: Current temperature in the annealing process
    :type initial_temp: float
    :return: Probability of accepting the neighbor solution
    :rtype: float
    """
    MAX_EXPONENT = 700  # This is a safe value to avoid overflow in most cases
    exponent_value = (best_solution_fitness - neighbor_fitness) / initial_temp
    exponent_value = max(min(exponent_value, MAX_EXPONENT), -MAX_EXPONENT)
    return math.exp(exponent_value)


class SA(Metaheuristic):
    """
    Simulated Annealing (SA) algorithm for optimization problems.
    
    This class implements the Simulated Annealing metaheuristic which uses temperature-based
    probabilistic acceptance of worse solutions to escape local optima. The temperature
    gradually decreases according to a cooling schedule, reducing the probability of
    accepting worse solutions over time.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param max_iterations: Maximum number of iterations to run, defaults to 20
    :type max_iterations: int, optional
    :param alteration_limit: How far a neighbor may move from the current solution.
        Defaults to a fifth of each variable's own range; a plain number is an
        absolute amount instead, and None lets a mutation land anywhere in the domain.
    :type alteration_limit: RelativeAlteration or float or None, optional
    :param initial_temp: Initial temperature for annealing process, defaults to 50.0
    :type initial_temp: float, optional
    :param cooling_rate: Rate at which the temperature decreases each iteration.
        Derived from the budget when not given, so that the temperature travels from
        initial_temp down to T_min over the iterations available (F-30)
    :type cooling_rate: float or None, optional
    :param neighbor_population_size: Number of neighbors to generate in each iteration, defaults to 1
    :type neighbor_population_size: int, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional

    :ivar max_iterations: Maximum number of iterations
    :vartype max_iterations: int
    :ivar alteration_limit: How far a neighbor may move from the current solution
    :vartype alteration_limit: RelativeAlteration or float or None
    :ivar initial_temp: Current temperature in the annealing process
    :vartype initial_temp: float
    :ivar cooling_rate: Rate of temperature decrease, derived from the budget unless given
    :vartype cooling_rate: float
    :ivar neighbor_population_size: Number of neighbors per iteration
    :vartype neighbor_population_size: int
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 warmup_iterations: int = 5,
                 max_iterations: int = 20,
                 alteration_limit: Any = RelativeAlteration(0.2), initial_temp: float = 50.0,
                 cooling_rate: Optional[float] = None, neighbor_population_size: int = 1,
                 distributed=False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None) -> None:
        """
        Initialize the Simulated Annealing algorithm.

        :param domain: The problem domain that defines the solution space
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param max_iterations: Maximum number of iterations to run, defaults to 20
        :type max_iterations: int, optional
        :param alteration_limit: How far a neighbor may move from the current solution,
            defaults to a fifth of each variable's own range
        :type alteration_limit: RelativeAlteration or float or None, optional
        :param initial_temp: Initial temperature for annealing process, defaults to 50.0
        :type initial_temp: float, optional
        :param cooling_rate: Rate at which the temperature decreases each iteration.
            Derived from the budget when not given, so that the temperature travels
            from initial_temp down to T_min over max_iterations (F-30)
        :type cooling_rate: float or None, optional
        :param neighbor_population_size: Number of neighbors to generate in each iteration, defaults to 1
        :type neighbor_population_size: int, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
        :type log_dir: str or None, optional
        """
        # population_size=1: annealing walks a single point, and iterate() only ever
        # looks at solutions[0]. Inheriting the default of 20 meant the warmup drew
        # 5 x 20 solutions and the initialization 20 more, of which 39 were thrown
        # away — about 120 of SA's 135 evaluations (F-20).
        super().__init__(domain, fitness_function, population_size=1,
                         warmup_iterations=warmup_iterations, distributed=distributed,
                         log_dir=log_dir, seed=seed)
        self.max_iterations = max_iterations
        self.alteration_limit = alteration_limit
        self.initial_temp = initial_temp
        self.current_temp = self.initial_temp
        self.neighbor_population_size = neighbor_population_size

        # Floor of the cooling schedule, applied in iterate(). It was assigned and
        # never read, so the temperature decayed towards zero and the Metropolis
        # criterion silently stopped accepting anything worse (F-20).
        self.T_min = 1e-8

        # Tied to the budget instead of being a loose rate. With the 0.99 this used
        # to default to, 50 degrees became 43 over 15 iterations and reaching 0.1
        # would have taken 618 of them, so the Metropolis criterion never got cold
        # enough to discriminate and the search was a random walk (F-30). Derived,
        # the temperature travels the whole way from initial_temp to T_min in the
        # iterations actually available, whatever the budget. max() because a budget
        # of zero iterations is legal and has no schedule to speak of.
        self.cooling_rate = cooling_rate if cooling_rate is not None else (
            (self.T_min / self.initial_temp) ** (1 / max(1, self.max_iterations)))

    def pre_execution(self) -> None:
        """
        Reset the annealing schedule so that every run starts from the same state.

        The temperature was only ever set in the constructor, so a second run() on
        the same object picked up wherever the first left off. It went unnoticed
        while the schedule barely moved (F-30); with a schedule that reaches T_min
        it would break the guarantee that a seed reproduces a run (A-06).
        """
        super().pre_execution()
        self.current_temp = self.initial_temp

    def initialize(self, num_solutions: int = 1) -> Tuple[List[Solution], Solution]:
        """
        Initialize the Simulated Annealing algorithm with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 1
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the Simulated Annealing algorithm.

        In each iteration, multiple neighbor solutions are generated, and the best one
        is selected. The Metropolis criterion determines whether the selected neighbor
        replaces the current solution based on the current temperature. The temperature
        is then decreased according to the cooling schedule.

        :param solutions: Current population of solutions (expected to have one solution in SA)
        :type solutions: List[Solution]
        :return: A tuple containing the updated population and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        current_solution = deepcopy(solutions[0])
        best_solution = deepcopy(self.best_solution)

        # Generate the first neighbor and initialize best_neighbor
        neighbor = deepcopy(current_solution)
        neighbor.mutate(alteration_limit=self.alteration_limit)
        neighbor.evaluate(self.fitness_function)

        # A copy, not an alias: the loop below kept mutating the very object
        # best_neighbor pointed at, so when the first neighbor turned out to be the
        # best one, best_fitness announced its value while best_neighbor had become
        # the last one generated (F-25).
        best_neighbor = deepcopy(neighbor)
        best_fitness = neighbor.get_fitness()

        # Generate additional neighbors and update best_neighbor if needed
        for _ in range(self.neighbor_population_size - 1):
            # Each neighbor starts from the current solution. Mutating the previous
            # neighbor again built a chain that wandered away from the point being
            # explored instead of sampling its neighborhood (F-25).
            neighbor = deepcopy(current_solution)
            neighbor.mutate(alteration_limit=self.alteration_limit)
            neighbor.evaluate(self.fitness_function)

            if neighbor.get_fitness() < best_fitness:
                best_neighbor = deepcopy(neighbor)
                best_fitness = neighbor.get_fitness()

        # Decide whether to accept the best neighbor
        if best_fitness < current_solution.get_fitness():
            current_solution = best_neighbor
            if best_fitness < best_solution.get_fitness():
                best_solution = best_neighbor
        else:
            exploration_rate = calculate_exploration_rate(current_solution.get_fitness(),
                                                          best_fitness, self.current_temp)
            if get_rng().random() < exploration_rate:
                current_solution = best_neighbor

        # Cool down, no further than T_min
        self.current_temp = max(self.current_temp * self.cooling_rate, self.T_min)

        return [current_solution], best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.
        """
        return self.current_iteration >= self.max_iterations