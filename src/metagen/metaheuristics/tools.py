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
from copy import deepcopy
from typing import Any, Callable, Tuple, List, Set, cast

from metagen.framework import Domain, Solution
# Re-exported: they were defined here, and the package and its users import them from here.
from metagen.metaheuristics.evaluation import BestModel, Counts, CountingFitness, add_calls, calls_of
from metagen.metaheuristics.model_io import save_model


def solution_class(domain: Domain) -> type[Solution]:
    """
    The Solution class the domain's connector builds for the domain's core.

    The core is a BaseDefinition, and every connector maps that to a Solution class
    -- Solution itself, or a subclass such as GASolution or TPESolution. The connector
    is a runtime registry, so its get_type() can only promise a BaseType or a Solution
    and a type checker cannot tell which; this is the one place that says which.

    :param domain: The domain to build solutions for.
    :type domain: Domain
    :return: The class to instantiate a solution of this domain with.
    :rtype: type[Solution]
    """
    # P-11: the single cast that replaced four copies of this line.
    return cast(type[Solution], domain.get_connector().get_type(domain.get_core()))


def random_exploration(domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
        -> Tuple[List[Solution], Solution]:
    """
    Draw solutions of the domain at random and evaluate them: how most metaheuristics build
    their first population.

    :param domain: The domain to draw from; its connector gives the class of the solutions.
    :type domain: Domain
    :param fitness_function: The function that evaluates a solution.
    :type fitness_function: Callable[[Solution], float]
    :param num_solutions: How many solutions to draw, at least one.
    :type num_solutions: int
    :return: The solutions drawn, in order, and the best of them, the first on a tie.
    :rtype: Tuple[List[Solution], Solution]
    """
    solution_type = solution_class(domain)

    potential:Solution = solution_type(domain, connector=domain.get_connector())
    potential.evaluate(fitness_function)

    solutions: List[Solution] = [potential]
    best:Solution = potential

    for _ in range(num_solutions-1):

        potential = solution_type(domain, connector=domain.get_connector())
        potential.evaluate(fitness_function)
        solutions.append(potential)

        if potential.get_fitness() < best.get_fitness():
            best = potential

    return solutions, best


def local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int,
                 alteration_limit: Any) -> Solution:
    """
    Mutate copies of a solution and keep the best: each neighbor is the solution mutated once
    within ``alteration_limit``, and it replaces the best so far only when it is strictly better.

    :param solution: The solution to search around, which is not changed.
    :type solution: Solution
    :param fitness_function: The function that evaluates a solution.
    :type fitness_function: Callable[[Solution], float]
    :param neighbor_population_size: How many neighbors to draw and evaluate.
    :type neighbor_population_size: int
    :param alteration_limit: How far a mutation may move each variable: a number, a
        :py:class:`~metagen.framework.RelativeAlteration`, or None for the whole domain.
    :type alteration_limit: float or RelativeAlteration or None
    :return: The best neighbor, or a copy of the solution when none is better.
    :rtype: Solution
    """
    best_neighbor = deepcopy(solution)
    for neighbor in neighborhood(solution, fitness_function, neighbor_population_size, alteration_limit):
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return best_neighbor


def neighborhood(around: Solution, fitness_function: Callable[[Solution], float], size: int,
                 alteration_limit: Any) -> List[Solution]:
    """
    Draw and evaluate ``size`` neighbors of a solution: each one a copy of it mutated once
    within ``alteration_limit``, in the order they are drawn.

    :param around: The solution to draw them around, which is not changed.
    :type around: Solution
    :param fitness_function: The function that evaluates a solution.
    :type fitness_function: Callable[[Solution], float]
    :param size: How many neighbors to draw.
    :type size: int
    :param alteration_limit: How far a mutation may move each variable: a number, a
        :py:class:`~metagen.framework.RelativeAlteration`, or None for the whole domain.
    :type alteration_limit: float or RelativeAlteration or None
    :return: The neighbors, evaluated.
    :rtype: List[Solution]
    """
    # Written in local_search, in TabuSearch and twice in SA (OF-06 of the independent
    # audit). local_search_with_tabu does not use it: each of its neighbors starts from
    # the best one so far, on purpose (see there).
    neighbors = []
    for _ in range(size):
        neighbor = deepcopy(around)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        neighbors.append(neighbor)
    return neighbors


def local_search_with_tabu(solution: Solution, fitness_function: Callable[[Solution], float],
                           neighbor_population_size: int, alteration_limit: Any,
                           tabu_list: List[Solution]) -> Tuple[List[Solution], Solution]:
    """
    The local search of hill climbing: each neighbor is the best one so far mutated once, so the
    search moves on as soon as it improves, and the neighbors equal to a solution of
    ``tabu_list`` are evaluated but left out of the neighborhood and never become the best.

    :param solution: The solution to search around, which is not changed.
    :type solution: Solution
    :param fitness_function: The function that evaluates a solution.
    :type fitness_function: Callable[[Solution], float]
    :param neighbor_population_size: How many neighbors to draw and evaluate.
    :type neighbor_population_size: int
    :param alteration_limit: How far a mutation may move each variable: a number, a
        :py:class:`~metagen.framework.RelativeAlteration`, or None for the whole domain.
    :type alteration_limit: float or RelativeAlteration or None
    :param tabu_list: The solutions already visited.
    :type tabu_list: List[Solution]
    :return: The neighbors not in the tabu list, and the best of them, or a copy of the
        solution when none is better.
    :rtype: Tuple[List[Solution], Solution]
    """
    tabu_set: Set[Solution] = set(tabu_list)
    best_neighbor = deepcopy(solution)
    neighborhood = []

    for _ in range(neighbor_population_size):
        # Each neighbor starts from the best one so far, not from `solution`. That is
        # deliberate and it is what hill climbing does: take a step, and if it improves,
        # keep going from there. A-03 reads it as a defect, which it would be for a tabu
        # search, since that needs a neighborhood around the current point to pick the
        # best non-tabu move from. Measured both ways, chaining wins: 0.0005 against
        # 0.0025 on the 2D sphere and 0.6173 against 0.7778 on Rastrigin.
        #
        # Note the difference with F-25, where chaining in SA was a real defect: there
        # the base moved on every mutation, whatever the outcome, so the neighbors
        # drifted away from the point the Metropolis criterion was comparing against.
        # Here the base only moves when it improves.
        neighbor = deepcopy(best_neighbor)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)

        if neighbor not in tabu_set:
            neighborhood.append(neighbor)
            if neighbor < best_neighbor:
                best_neighbor = neighbor

    return neighborhood, best_neighbor


__all__ = ["BestModel", "Counts", "CountingFitness", "add_calls", "calls_of", "local_search",
           "local_search_with_tabu", "neighborhood", "random_exploration", "save_model", "solution_class"]
