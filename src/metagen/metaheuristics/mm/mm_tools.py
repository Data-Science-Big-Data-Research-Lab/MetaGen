from typing import Tuple, Callable, List

from metagen.framework import Solution
# The one implementation. This module carried a byte-for-byte copy of it (A-09).
from metagen.metaheuristics.tools import local_search


def local_search_of_two_children(parents: Tuple[Solution, Solution], fitness_function: Callable[[Solution], float],
                             neighbor_population_size: int, alteration_limit: float, distribution_level:int=0) -> Tuple[Solution, Solution]:
    """
    Performs local search on two parent solutions to improve their fitness.

    :param parents: A tuple containing two parent solutions
    :param fitness_function: Function to evaluate solution fitness
    :param neighbor_population_size: Number of neighbors to generate in local search
    :param alteration_limit: Maximum allowed change in solution during local search
    :param distribution_level: Level of distribution for parallel processing, defaults to 0
    :type parents: Tuple[:py:class:`~metagen.framework.Solution`, :py:class:`~metagen.framework.Solution`]
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type neighbor_population_size: int
    :type alteration_limit: float
    :type distribution_level: int
    :return: Tuple containing two improved solutions
    :rtype: Tuple[:py:class:`~metagen.framework.Solution`, :py:class:`~metagen.framework.Solution`]
    """
    if distribution_level > 0:
        # Imported here, and not at the top of the module, so that a memetic run
        # that never distributes does not need Ray installed (F-24).
        from metagen.metaheuristics.mm.mm_distributed_tools import \
            distributed_population_local_search

        children_aux = distributed_population_local_search(list(parents), fitness_function, neighbor_population_size, alteration_limit, distribution_level)
        children = (children_aux[0], children_aux[1])
    else:
        children_aux = population_local_search(list(parents), fitness_function, neighbor_population_size, alteration_limit, distribution_level)
        children = (children_aux[0], children_aux[1])

    return children


def population_local_search(population: List[Solution], fitness_function: Callable[[Solution], float], neighbor_population_size: int, alteration_limit: float, distribution_level:int) -> List[Solution]:
    """
    Performs local search on a population of solutions.

    :param population: List of solutions to improve
    :param fitness_function: Function to evaluate solution fitness
    :param neighbor_population_size: Number of neighbors to generate in local search
    :param alteration_limit: Maximum allowed change in solution during local search
    :param distribution_level: Level of distribution for parallel processing
    :type population: List[:py:class:`~metagen.framework.Solution`]
    :type fitness_function: Callable[[:py:class:`~metagen.framework.Solution`], float]
    :type neighbor_population_size: int
    :type alteration_limit: float
    :type distribution_level: int
    :return: List of improved solutions
    :rtype: List[:py:class:`~metagen.framework.Solution`]
    """

    if distribution_level >= 2:
        # Same reason as in local_search_of_two_children: only the distributing
        # branch may reach Ray (F-24).
        from metagen.metaheuristics.mm.mm_distributed_tools import \
            distributed_local_search

        neighbours = []
        for individual in population:
            neighbours.append(distributed_local_search(individual, fitness_function, neighbor_population_size, alteration_limit))
    else:
        neighbours = []
        for individual in population:
            neighbours.append(local_search(individual, fitness_function, neighbor_population_size, alteration_limit))
    return neighbours


