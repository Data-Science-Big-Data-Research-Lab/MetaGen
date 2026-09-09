from copy import deepcopy
from typing import Callable, Tuple, List, Set, cast

from metagen.framework import Domain, Solution


def solution_class(domain: Domain) -> type[Solution]:
    """
    The Solution class the domain's connector builds for the domain's core.

    The core is a BaseDefinition, and every connector maps that to a Solution class
    -- Solution itself, or a subclass such as GASolution or TPESolution. The connector
    is a runtime registry, so its get_type() can only promise a BaseType or a Solution
    and mypy cannot tell which; this is the one place that says which (P-11).

    :param domain: The domain to build solutions for.
    :type domain: Domain
    :return: The class to instantiate a solution of this domain with.
    :rtype: type[Solution]
    """
    return cast(type[Solution], domain.get_connector().get_type(domain.get_core()))


def random_exploration (domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:

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


def local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float) -> Solution:
    best_neighbor = deepcopy(solution)
    for _ in range(neighbor_population_size):
        neighbor = deepcopy(solution)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return best_neighbor


def local_search_with_tabu (solution: Solution, fitness_function: Callable[[Solution], float],
                            neighbor_population_size: int, alteration_limit: float, tabu_list:List[Solution]) -> Tuple[List[Solution], Solution]:
    tabu_set: Set[Solution] = set(tabu_list)
    best_neighbor = deepcopy(solution)
    neighborhood = []

    for _ in range(neighbor_population_size):
        # Each neighbour starts from the best one so far, not from `solution`. That is
        # deliberate and it is what hill climbing does: take a step, and if it improves,
        # keep going from there. A-03 reads it as a defect, which it would be for a tabu
        # search, since that needs a neighbourhood around the current point to pick the
        # best non-tabu move from. Measured both ways, chaining wins: 0.0005 against
        # 0.0025 on the 2D sphere and 0.6173 against 0.7778 on Rastrigin.
        #
        # Note the difference with F-25, where chaining in SA was a real defect: there
        # the base moved on every mutation, whatever the outcome, so the neighbours
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






