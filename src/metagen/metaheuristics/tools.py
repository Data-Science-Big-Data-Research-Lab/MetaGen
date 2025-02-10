from copy import deepcopy
from typing import Callable, Tuple, List, Set

from metagen.framework import Domain, Solution


def random_exploration (domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:

    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())

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
        neighbor = deepcopy(best_neighbor)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)

        if neighbor not in tabu_set:
            neighborhood.append(neighbor)
            if neighbor < best_neighbor:
                best_neighbor = neighbor

    return neighborhood, best_neighbor






