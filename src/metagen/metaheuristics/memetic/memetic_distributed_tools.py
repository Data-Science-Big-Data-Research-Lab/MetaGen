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
from typing import Callable, List

from metagen.metaheuristics.import_helper import require_ray

require_ray("the distributed memetic algorithm")
import ray  # noqa: E402 - after the check, so that a missing Ray says how to install it

from metagen.framework import Solution
from metagen.logging.metagen_logger import get_remote_metagen_logger
from metagen.metaheuristics.distributed_tools import assign_load_equally, scatter
from metagen.metaheuristics.memetic.memetic_tools import population_local_search
from metagen.metaheuristics.tools import local_search


def distributed_population_local_search(population: List[Solution], fitness_function: Callable[[Solution], float],
                                    neighbor_population_size: int, alteration_limit: float, distribution_level:int=1) -> List[Solution]:
    """
    Performs distributed local search on a population of solutions.

    :param population: List of solutions to improve
    :param fitness_function: Function to evaluate solution fitness
    :param neighbor_population_size: Number of neighbors to generate in local search
    :param alteration_limit: Maximum allowed change in solution during local search
    :param distribution_level: Level of distribution for parallel processing, defaults to 1
    :type population: List[:py:class:`~metagen.framework.Solution`]
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type neighbor_population_size: int
    :type alteration_limit: float
    :type distribution_level: int
    :return: List of improved solutions
    :rtype: List[:py:class:`~metagen.framework.Solution`]
    """
    distribution = assign_load_equally(len(population))

    get_remote_metagen_logger().debug(f"[LEVEL 1] Distributed local search of a population of {len(population)} individuals with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")

    tasks = []
    for count in distribution:
        tasks.append((population[:count], fitness_function, neighbor_population_size, alteration_limit,
                      distribution_level))
        # Advance the cursor, as base.py does. Without it every worker got the same
        # opening slice: with 9 individuals over 3 workers, only the first 3 were
        # ever searched and the population came back as three copies of them (F-11).
        population = population[count:]
    flattened_results = [item for improved in scatter(population_local_search, tasks, counted=1) for item in improved]
    return flattened_results

def distributed_local_search(solution: Solution, fitness_function: Callable[[Solution], float],
                         neighbor_population_size: int, alteration_limit: float) -> Solution:
    """
    Performs distributed local search on a single solution using multiple workers.

    :param solution: Solution to improve
    :param fitness_function: Function to evaluate solution fitness
    :param neighbor_population_size: Number of neighbors to generate
    :param alteration_limit: Maximum allowed change in solution
    :type solution: :py:class:`~metagen.framework.Solution`
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type neighbor_population_size: int
    :type alteration_limit: float
    :return: Improved solution
    :rtype: :py:class:`~metagen.framework.Solution`
    """
    distribution = assign_load_equally(neighbor_population_size)

    get_remote_metagen_logger().debug(
        f"[LEVEL 2] Distributed local search of an individual with {neighbor_population_size} neighbors,"
        f" with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")

    neighbors = scatter(local_search, [(solution, fitness_function, count, alteration_limit) for count in distribution],
                        counted=1)
    best_neighbor = min(neighbors, key=lambda sol: sol.get_fitness())
    return best_neighbor
