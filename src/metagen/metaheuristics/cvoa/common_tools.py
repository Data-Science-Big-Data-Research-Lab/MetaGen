import copy
import random
from typing import NamedTuple, Set, Tuple, Callable

from metagen.framework import Domain, Solution
from metagen.logging.metagen_logger import metagen_logger


# Strain Properties
class StrainProperties(NamedTuple):
    strain_id: str = "Strain#1"
    pandemic_duration: int = 10
    spreading_rate: int = 5
    min_superspreading_rate: int = 6
    max_superspreading_rate: int = 15
    social_distancing: int = 7
    p_isolation: float = 0.5
    p_travel: float = 0.1
    p_re_infection: float = 0.001
    p_superspreader: float = 0.1
    p_die: float = 0.05

# Individual state in the pandemic
IndividualState = NamedTuple("IndividualState", [("recovered", bool), ("dead", bool), ("isolated", bool)])



def compute_n_infected_travel_distance(domain: Domain, strain_properties: StrainProperties, carrier: Solution,
                                       superspreaders: Set[Solution]) -> Tuple[int, int]:
    # ** 1. Determine the number of infections. **
    if carrier in superspreaders:
        # If the current individual is superspreader the number of infected ones will be in
        # (MIN_SUPERSPREADING_RATE, MAX_SUPERSPREADING_RATE)
        n_infected = random.randint(strain_properties.min_superspreading_rate,
                                    strain_properties.max_superspreading_rate)
    else:
        # If the current individual is common the number of infected ones will be in
        # (0, MAX_SUPERSPREADING_RATE)
        n_infected = random.randint(0, strain_properties.spreading_rate)

    # ** 2. Determine the travel distance. **
    if random.random() < strain_properties.p_travel:
        # If the current individual is a traveler, the travel distance will be in
        # (0, number of variable defined in the problem)
        travel_distance = random.randint(0, len(domain.get_core().variable_list()))
    else:
        # Otherwise the travel distance will be 1.
        travel_distance = 1

    return n_infected, travel_distance


def infect(individual: Solution, fitness_function: Callable[[Solution],float],travel_distance:int) -> Solution:
    """ The individual infects another one located at a specific distance from it.

    :returns: The newly infected individual.
    :rtype: :py:class:`~metagen.framework.Solution`
    """
    infected = copy.deepcopy(individual)
    infected.mutate(travel_distance)
    infected.evaluate(fitness_function)
    return infected


def insert_into_set_strain(strain_worst_superspreader:Solution, strain_best_dead:Solution,bag: Set[Solution], to_insert: Solution, remaining: int, ty: str) -> Tuple[Solution, Solution, bool]:
    """ Insert an individual in the strain sets (death or superspreader).

    :param bag: The set where the individual has to be inserted.
    :type bag: set of :py:class:`~metagen.framework.Solution`

    :param to_insert: The individual that has to be inserted.
    :type to_insert: :py:class:`~metagen.framework.Solution`

    :param remaining: The number of individuals remaining to be added in the set.
    :type remaining: int

    :param ty: The set where the individual will be inserted ('s' if it is the superspreader set, 'd' if it is the death set).
    :type ty: str

    :returns: A tuple containing:
        - The updated worst superspreader in the strain.
        - The updated best dead in the strain.
        - A boolean indicating whether the individual was successfully inserted.
    :rtype: Tuple[:py:class:`~metagen.framework.Solution`, :py:class:`~metagen.framework.Solution`, bool]
    """
    worst_superspreader = copy.deepcopy(strain_worst_superspreader)
    best_dead = copy.deepcopy(strain_best_dead)

    # Initialization of the returned value.
    inserted = False

    # If there are still individuals to be added to the set:
    if remaining > 0:
        # The individual is inserted and the returned value is True.
        bag.add(to_insert)
        inserted = True

        # The worst superspreader individual (in the case of an insertion in the superspreader set) or the best
        # death individual (in the case of an insertion in the death set) are updated considering the previous
        # insertion. That is for the efficient updating of strain sets.
        if ty == 's':
            if to_insert > worst_superspreader:
                worst_superspreader = to_insert
        elif ty == 'd':
            if to_insert < best_dead:
                best_dead = to_insert

        # If there are no individuals left to add to the set:
    else:

        # If the current individual is worse than the worst in the superspreader set, the current individual
        # replaces the worst. This operation ensures that the worst new individual will be a superspreader.
        # This action adds more diversification to the metaheuristic.
        if ty == 's':
            if to_insert > worst_superspreader:
                if worst_superspreader in bag:
                    bag.remove(worst_superspreader)
                bag.add(to_insert)
                inserted = True
                worst_superspreader = to_insert

        # If the current individual is better than the best in the death set, the current individual
        # replaces the best. This operation ensures that the best new individual will be death.
        # This action adds more diversification to the metaheuristic.
        elif ty == 'd':
            if to_insert < best_dead:
                metagen_logger.debug("bag: %s", str(bag))
                metagen_logger.debug("__bestDeadIndividualStrain: %s", str(best_dead))
                metagen_logger.debug("contains?: %s", str(best_dead in bag))
                bag.remove(best_dead)
                bag.add(to_insert)
                inserted = True
                best_dead = to_insert

    return worst_superspreader, best_dead, inserted






















