import copy
import math
import time
from collections.abc import MutableSet
from typing import Any, Callable, Dict, Iterable, Iterator, NamedTuple, Optional, Protocol, Set, Tuple

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_rng


# Strain Properties
class SolutionKeys:
    """
    A set of solutions kept by their key (:py:meth:`~metagen.framework.Solution._key`)
    rather than whole: it answers whether a solution is in it, counts them, and adds and
    removes them, with the equality of solutions, but holds no solution. It is never
    iterated, so the order of its keys does not matter.
    """
    # The recovered, the dead and the isolated of a pandemic were kept as whole solutions
    # and only ever asked whether one was there and how many: the isolated alone, which
    # are only counted, were most of the memory of a run, and every question rebuilt the
    # hash of the solution (E-03, metagen-auditoria/auditoria-independiente-2026-11/eficiencia.md).

    def __init__(self) -> None:
        self._keys: Set[Tuple[Any, ...]] = set()

    def __contains__(self, item: object) -> bool:
        return isinstance(item, Solution) and item._key() in self._keys

    def __len__(self) -> int:
        return len(self._keys)

    def holds(self, key: Tuple[Any, ...]) -> bool:
        """Whether the solution with this key is in the set."""
        return key in self._keys

    def add(self, item: Solution) -> None:
        self._keys.add(item._key())

    def discard(self, item: Solution) -> None:
        self._keys.discard(item._key())

    def update(self, items: Iterable[Solution]) -> None:
        self._keys.update(item._key() for item in items)

    def difference_update(self, other: "SolutionKeys") -> None:
        self._keys -= other._keys

    def keys(self) -> Set[Tuple[Any, ...]]:
        """The keys of the solutions in the set, as a new set."""
        return set(self._keys)

    def add_key(self, key: Tuple[Any, ...]) -> None:
        """Add the solution with this key."""
        self._keys.add(key)

    def discard_key(self, key: Tuple[Any, ...]) -> None:
        """Remove the solution with this key, if it is in the set."""
        self._keys.discard(key)


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

    Every newly infected individual is evaluated, and until social distancing the
    population of a strain grows geometrically, so with these defaults a pandemic over a
    continuous domain evaluates a great many solutions. With a fitness function that takes
    long, such as one that trains a model, bound it with the ``max_evaluations`` or the
    ``timeout`` of its launcher.

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


class PandemicBudget:
    """
    The evaluations and the seconds a whole pandemic may spend, shared by all its strains.
    It holds no lock: the state that owns it does.

    :param max_evaluations: The most evaluations of the fitness function, or None.
    :type max_evaluations: int or None
    :param timeout: The most seconds from its creation, or None.
    :type timeout: float or None
    """
    # A pandemic over a continuous domain evaluates tens of thousands of solutions per
    # iteration with the default properties, so a budget checked between iterations, as
    # Metaheuristic.run does, could overrun by hours with a fitness function that trains a
    # model: this one is checked before every evaluation (F-76, Y-12 of the independent audit).

    def __init__(self, max_evaluations: Optional[int] = None, timeout: Optional[float] = None) -> None:
        self.max_evaluations = max_evaluations
        self.deadline = None if timeout is None else time.monotonic() + timeout
        self.evaluations = 0

    def limited(self) -> bool:
        """Whether there is a budget at all."""
        return self.max_evaluations is not None or self.deadline is not None

    def spent(self) -> bool:
        """Whether the pandemic has spent its evaluations or its seconds."""
        return ((self.max_evaluations is not None and self.evaluations >= self.max_evaluations)
                or (self.deadline is not None and time.monotonic() >= self.deadline))

    def take(self) -> bool:
        """Count one evaluation, if the budget allows it; say whether it did."""
        if self.spent():
            return False
        self.evaluations += 1
        return True


class BudgetedFitness:
    """
    The fitness function of a pandemic with a budget: it evaluates while the shared state
    allows one more evaluation, and from then on gives infinity without calling the
    function, so that what is left of the iteration costs nothing and no solution it
    touches competes for the best. The strains stop at the end of that iteration.

    :param function: The fitness function.
    :type function: Callable[[Solution], float]
    :param state: The state the strains share, which keeps the budget.
    :type state: PandemicState
    """

    def __init__(self, function: Callable[[Solution], float], state: "PandemicState") -> None:
        self.function = function
        self.state = state
        self.spent = False
        self.__qualname__ = getattr(function, "__qualname__", type(self).__name__)

    def __call__(self, solution: Solution) -> float:
        # Once spent, always spent: a copy on a worker of Ray asks the state no more.
        if not self.spent and not self.state.take_evaluation():
            self.spent = True
        if self.spent:
            return math.inf
        return self.function(solution)


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

    def take_evaluation(self) -> bool: ...

    def budget_spent(self) -> bool: ...

    def flush(self) -> None: ...



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
           alteration_limit: Any = None, evaluate: bool = True) -> Solution:
    """ The individual infects another one located at a specific distance from it.

    :param travel_distance: How many variables the infection changes.
    :param alteration_limit: How far each of them moves, as in
        :py:meth:`~metagen.framework.Solution.mutate`.
    :param evaluate: Whether to evaluate the newly infected individual. Without it, its
        fitness is left unknown, as infinite, for whoever admits it to evaluate it.

    :returns: The newly infected individual.
    :rtype: :py:class:`~metagen.framework.Solution`
    """
    infected = copy.deepcopy(individual)
    infected.mutate(travel_distance, alteration_limit)
    if evaluate:
        infected.evaluate(fitness_function)
    else:
        infected.set_fitness(math.inf)
    return infected
