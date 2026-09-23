import copy
from collections.abc import MutableSet
from typing import Any, Callable, Dict, Iterable, Iterator, NamedTuple, Optional, Protocol, Tuple

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_rng


# Strain Properties
class SolutionSet(MutableSet[Solution]):
    """
    A set of solutions that iterates in insertion order.

    CVOA keeps its populations in sets, to drop repeated individuals as the paper
    recommends, and iterates them to spread the disease. A plain set iterates in
    hash order, and the hash of a Solution depends on the hashes of its variable
    names, which Python randomizes on every interpreter start (PEP 456), so the same
    seed would give a different pandemic in every process. Backed by a dict, this
    keeps the deduplication and makes the order follow the draws alone.
    """
    # F-29: with plain sets the same seed gave a different pandemic in every process.

    def __init__(self, iterable: Iterable[Solution] = ()) -> None:
        self._items: Dict[Solution, None] = dict.fromkeys(iterable)

    def __contains__(self, item: object) -> bool:
        return item in self._items

    def __iter__(self) -> Iterator[Solution]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def add(self, item: Solution) -> None:
        self._items.setdefault(item, None)

    def discard(self, item: Solution) -> None:
        self._items.pop(item, None)

    def update(self, items: Iterable[Solution]) -> None:
        for item in items:
            self.add(item)

    def difference_update(self, items: Iterable[Solution]) -> None:
        for item in items:
            self.discard(item)

    def __repr__(self) -> str:
        return "{" + ", ".join(str(item) for item in self._items) + "}" if self._items else "set()"


class StrainProperties(NamedTuple):
    """
    The parameters of one strain. The defaults are the ones the paper fixes in its
    "Suggested parameters setup" section, from the epidemiology of COVID-19. With
    them a pandemic spends twenty-two of its thirty iterations under social
    distancing, which is the phase in which it dies out.

    :param strain_id: The name of the strain, used in the logs and in the reports.
    :param pandemic_duration: Iterations the strain runs, defaults to 30.
    :param spreading_rate: The most individuals an ordinary carrier infects per iteration,
        defaults to 5.
    :param min_superspreading_rate: The fewest individuals a superspreader infects, defaults to 6.
    :param max_superspreading_rate: The most individuals a superspreader infects, defaults to 15.
    :param social_distancing: The iteration from which isolation applies and every contagion
        is at distance one, defaults to 7.
    :param p_isolation: The probability that an individual isolates once social distancing is
        on, defaults to 0.7.
    :param p_travel: The probability that a carrier travels, which lets its infections change
        more than one variable, defaults to 0.1.
    :param p_re_infection: The probability that a recovered individual is infected again,
        defaults to 0.02.
    :param p_superspreader: The share of the carriers that superspread, defaults to 0.1.
    :param p_die: The share of the carriers that die, defaults to 0.05.
    :param max_iterations_without_improvement: Iterations the strain may spend without
        improving before it stops. None, the default, runs the whole ``pandemic_duration``.
    :param infection_alteration_limit: How far an infection moves each variable it
        changes: a ``RelativeAlteration`` (a fraction of each variable's own range), a
        plain number (an absolute amount) or None, which redraws the variable over its
        whole domain. A binary variable flips either way.
    """
    # F-28: three defaults used to differ from the paper's (pandemic_duration 10,
    # p_isolation 0.5, p_re_infection 0.001), which left three iterations under social
    # distancing instead of twenty-two, so the pandemic never reached that phase.
    strain_id: str = "Strain#1"
    pandemic_duration: int = 30
    spreading_rate: int = 5
    min_superspreading_rate: int = 6
    max_superspreading_rate: int = 15
    social_distancing: int = 7
    p_isolation: float = 0.7
    p_travel: float = 0.1
    p_re_infection: float = 0.02
    p_superspreader: float = 0.1
    p_die: float = 0.05
    # Iterations the strain may spend without improving before it gives up. None,
    # the default, means it does not give up early and runs its whole
    # pandemic_duration. Added with F-23; last on purpose, so that any existing
    # positional construction keeps working.
    max_iterations_without_improvement: Optional[int] = None
    # How far an infection moves each variable it changes. Last, like the field
    # above, so that positional constructions keep working.
    infection_alteration_limit: Any = None

# Individual state in the pandemic
IndividualState = NamedTuple("IndividualState", [("recovered", bool), ("dead", bool), ("isolated", bool)])


class PandemicState(Protocol):
    """
    What a strain asks of the state every strain shares: the recovered, the dead,
    the isolated and the best individual of the whole pandemic.

    LocalPandemicState implements it directly, under a lock, for the strains that
    run as threads; RemotePandemicStateProxy implements it for the strains that run
    on Ray, each call a synchronous call to the RemotePandemicState actor. The strain
    talks to either through this interface and does not know which one it holds.
    """
    # A-09: the interface that let the two CVOA twins become one class.

    def get_individual_state(self, individual: Solution) -> IndividualState: ...

    def get_recovered_len(self) -> int: ...

    def get_infected_again(self, individual: Solution) -> None: ...

    def update_deaths(self, individuals: SolutionSet) -> None: ...

    def update_recovered_with_deaths(self) -> None: ...

    def recover_if_not_dead(self, individual: Solution) -> None: ...

    def isolate(self, individual: Solution) -> None: ...

    def update_best_individual(self, individual: Solution) -> None: ...

    def get_best_individual(self) -> Solution: ...

    def get_pandemic_report(self) -> Dict[str, Any]: ...



def compute_n_infected_travel_distance(domain: Domain, strain_properties: StrainProperties, carrier: Solution,
                                       superspreaders: SolutionSet) -> Tuple[int, int]:
    # ** 1. Determine the number of infections. **
    if carrier in superspreaders:
        # If the current individual is superspreader the number of infected ones will be in
        # (MIN_SUPERSPREADING_RATE, MAX_SUPERSPREADING_RATE)
        n_infected = get_rng().randint(strain_properties.min_superspreading_rate,
                                    strain_properties.max_superspreading_rate)
    else:
        # If the current individual is common the number of infected ones will be in
        # (0, MAX_SUPERSPREADING_RATE)
        n_infected = get_rng().randint(0, strain_properties.spreading_rate)

    # ** 2. Determine the travel distance. **
    if get_rng().random() < strain_properties.p_travel:
        # If the current individual is a traveler, the travel distance will be in
        # (0, number of variable defined in the problem)
        travel_distance = get_rng().randint(0, len(domain.get_core().variable_list()))
    else:
        # Otherwise the travel distance will be 1.
        travel_distance = 1

    return n_infected, travel_distance


def infect(individual: Solution, fitness_function: Callable[[Solution], float], travel_distance: int,
           alteration_limit: Any = None) -> Solution:
    """ The individual infects another one located at a specific distance from it.

    :param travel_distance: How many variables the infection changes.
    :param alteration_limit: How far each of them moves, as in
        :py:meth:`~metagen.framework.Solution.mutate`.

    :returns: The newly infected individual.
    :rtype: :py:class:`~metagen.framework.Solution`
    """
    infected = copy.deepcopy(individual)
    infected.mutate(travel_distance, alteration_limit)
    infected.evaluate(fitness_function)
    return infected
