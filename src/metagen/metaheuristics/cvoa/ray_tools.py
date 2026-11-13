from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Set, Tuple, TypeAlias, cast

from metagen.metaheuristics.import_helper import ray_missing

# Wrapped, as in the distributed launcher: imported bare, asking for DistributedCVOA without
# Ray gave Python's own "No module named 'ray'", with nothing about what to install (F-70).
try:
    import ray
except ImportError as error:
    raise ImportError(ray_missing("the distributed CVOA")) from error
from metagen.framework import Solution, Domain
from metagen.metaheuristics.cvoa.common_tools import (IndividualState, PandemicBudget, PandemicState, SolutionKeys,
                                                     StrainProperties, SolutionSet)
from metagen.framework.rng import set_seed, spawn_seed

if TYPE_CHECKING:
    from metagen.metaheuristics.cvoa.cvoa import CVOA

# A handle to the RemotePandemicState actor. Ray builds it with
# RemotePandemicState.remote(...) and every method is called through .remote(); mypy
# sees the decorated class, not the handle, so the handle is typed as Any here and
# the calls that go through it are annotated at the point of use (P-11).
PandemicStateHandle: TypeAlias = Any

# Remote pandemic state (ray support)
@ray.remote
class RemotePandemicState:
    def __init__(self, initial_individual: Solution, max_evaluations: Optional[int] = None,
                 timeout: Optional[float] = None):
        self.budget = PandemicBudget(max_evaluations, timeout)
        self.recovered: SolutionKeys = SolutionKeys()
        self.deaths: SolutionKeys = SolutionKeys()
        self.isolated: SolutionKeys = SolutionKeys()
        self.best_individual_found: bool = False
        self.best_individual: Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        # The key once, not a hash per set (E-03).
        key = individual._key()
        return IndividualState(self.recovered.holds(key), self.deaths.holds(key), self.isolated.holds(key))

    # Recovered
    def get_recovered_len(self) -> int:
        return len(self.recovered)

    def get_infected_again(self, individual: Solution) -> None:
        # Several tasks can infect the same recovered point again at once: each read it
        # as recovered before the other took it out, and remove() raised KeyError.
        self.recovered.discard(individual)

    # Deaths
    def update_deaths(self, individuals: SolutionSet) -> None:
        self.deaths.update(individuals)

    # Recovered and Deaths
    def update_recovered_with_deaths(self) -> None:
        self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual: Solution) -> None:
        if individual not in self.deaths:
            self.recovered.add(individual)

    # Isolated
    def isolate(self, individual: Solution) -> None:
        """
        Count an individual as isolated. It does not join the recovered, so the point
        stays open to be infected again.
        """
        # F-45.
        self.isolated.add(individual)

    # Best Individual
    def update_best_individual(self, individual: Solution) -> Solution:
        # Only if it is better: a strain decides it is from the best it last saw, and
        # another may have found a better one since (E-09). Gives back the best.
        if individual.get_fitness() < self.best_individual.get_fitness():
            self.best_individual_found = True
            self.best_individual = individual
        return self.best_individual

    def get_best_individual(self) -> Solution:
        return self.best_individual

    def get_pandemic_report(self) -> Dict[str, Any]:
        return {
            "recovered": len(self.recovered),
            "deaths": len(self.deaths),
            "isolated": len(self.isolated),
            "best_individual": self.best_individual
        }

    # What the tasks of an iteration read and write in one call each (E-09 of the
    # independent audit): one call to the actor per infected individual made the contagion
    # of a pandemic on Ray two orders of magnitude slower than in threads.
    def snapshot(self) -> Tuple[Set[Tuple[Any, ...]], Set[Tuple[Any, ...]]]:
        return self.recovered.keys(), self.deaths.keys()

    def apply(self, log: List[Tuple[str, Tuple[Any, ...]]]) -> Solution:
        for operation, key in log:
            if operation == "recover":
                if not self.deaths.holds(key):
                    self.recovered.add_key(key)
            elif operation == "discard":
                self.recovered.discard_key(key)
            else:
                self.isolated.add_key(key)
        return self.best_individual

    def add_deaths(self, keys: List[Tuple[Any, ...]]) -> None:
        for key in keys:
            self.deaths.add_key(key)

    # Budget
    def take_evaluation(self) -> bool:
        return self.budget.take()

    def budget_spent(self) -> bool:
        return self.budget.spent()

    def budget_limited(self) -> bool:
        return self.budget.limited()


class RemotePandemicStateProxy:
    """
    The strain's view of the RemotePandemicState actor: the same methods as
    LocalPandemicState, as calls to the actor. The strain and the contagion tasks hold
    this instead of the handle, so the code that talks to the state is written once for
    threads and for Ray. It pickles with the handle inside, which is how it reaches the
    tasks.

    What a strain writes on the recovered and the isolated is sent together, before the
    next call that reads them and when the strain ends (:py:meth:`flush`); the best of the
    pandemic is the one the actor gave back last, which it gives back with every write.
    """
    # A-09: eleven ray.get calls left the strain's code when this proxy came in. E-09 of
    # the independent audit: a strain still made a synchronous call for every carrier it
    # recovered and two more for every individual it compared with the best of the
    # pandemic, most of the time of a pandemic on Ray.

    def __init__(self, handle: PandemicStateHandle):
        self.handle = handle
        # Whether the pandemic has a budget, asked once: without one, the strains do not
        # call the actor to know whether it is spent.
        self._limited: Optional[bool] = None
        # The keys of the dead this strain has sent: a strain sent all its dead every
        # iteration, which the actor hashed again (E-09).
        self._deaths_sent: Set[Tuple[Any, ...]] = set()
        # The writes on the recovered and the isolated not sent yet, in order.
        self._pending: List[Tuple[str, Tuple[Any, ...]]] = []
        # The best of the pandemic as the actor last gave it back.
        self._best: Optional[Solution] = None

    def flush(self) -> None:
        """Send the writes not sent yet, and learn the best of the pandemic."""
        if self._pending:
            pending, self._pending = self._pending, []
            self._best = ray.get(self.handle.apply.remote(pending))

    def light(self) -> "RemotePandemicStateProxy":
        """A proxy of the same actor without the record of the dead sent, to travel with a task."""
        proxy = RemotePandemicStateProxy(self.handle)
        proxy._limited = self._limited
        return proxy

    def get_individual_state(self, individual: Solution) -> IndividualState:
        self.flush()
        state: IndividualState = ray.get(self.handle.get_individual_state.remote(individual))
        return state

    def get_recovered_len(self) -> int:
        self.flush()
        recovered: int = ray.get(self.handle.get_recovered_len.remote())
        return recovered

    def get_infected_again(self, individual: Solution) -> None:
        self._pending.append(("discard", individual._key()))

    def update_deaths(self, individuals: SolutionSet) -> None:
        self.flush()
        # Only the dead this strain has not sent yet: the set of the dead only grows.
        new = []
        for individual in individuals:
            key = individual._key()
            if key not in self._deaths_sent:
                self._deaths_sent.add(key)
                new.append(key)
        if new:
            ray.get(self.handle.add_deaths.remote(new))

    def update_recovered_with_deaths(self) -> None:
        self.flush()
        ray.get(self.handle.update_recovered_with_deaths.remote())

    def recover_if_not_dead(self, individual: Solution) -> None:
        self._pending.append(("recover", individual._key()))

    def isolate(self, individual: Solution) -> None:
        # Sent with the next flush; F-42 was a call to the actor that was never waited on.
        self._pending.append(("isolate", individual._key()))

    def update_best_individual(self, individual: Solution) -> None:
        self._best = ray.get(self.handle.update_best_individual.remote(individual))

    def get_best_individual(self) -> Solution:
        if self._best is None:
            self._best = ray.get(self.handle.get_best_individual.remote())
        return cast(Solution, self._best)

    def get_pandemic_report(self) -> Dict[str, Any]:
        self.flush()
        report: Dict[str, Any] = ray.get(self.handle.get_pandemic_report.remote())
        return report

    def take_evaluation(self) -> bool:
        allowed: bool = ray.get(self.handle.take_evaluation.remote())
        return allowed

    def budget_spent(self) -> bool:
        if self._limited is None:
            self._limited = bool(ray.get(self.handle.budget_limited.remote()))
        if not self._limited:
            return False
        spent: bool = ray.get(self.handle.budget_spent.remote())
        return spent


class _IterationView:
    """
    The pandemic state the carriers of one task of one iteration see: the recovered and the
    dead at the start of the iteration, with what the task itself has changed on top. What
    it changes is kept in ``log``, which the strain sends to the actor once every task has
    finished, in the order of the tasks. ``isolated`` tells only the ones isolated here: no
    rule of the pandemic reads it.
    """
    # E-09 of the independent audit: every infected individual asked the actor its state,
    # and isolating or recovering it was another call. On a continuous domain no two tasks
    # reach the same point, and the pandemic takes the same path as before; on a small
    # discrete one, what a task sees no longer depends on what the others did meanwhile,
    # and the log is applied in the order of the tasks, so it is reproducible.

    def __init__(self, recovered: Set[Tuple[Any, ...]], dead: Set[Tuple[Any, ...]],
                 actor: "RemotePandemicStateProxy") -> None:
        self._recovered, self._dead, self._actor = recovered, dead, actor
        self._added: Set[Tuple[Any, ...]] = set()
        self._removed: Set[Tuple[Any, ...]] = set()
        self._isolated: Set[Tuple[Any, ...]] = set()
        self.log: List[Tuple[str, Tuple[Any, ...]]] = []

    def _is_recovered(self, key: Tuple[Any, ...]) -> bool:
        return key in self._added or (key in self._recovered and key not in self._removed)

    def get_individual_state(self, individual: Solution) -> IndividualState:
        key = individual._key()
        return IndividualState(self._is_recovered(key), key in self._dead, key in self._isolated)

    def get_infected_again(self, individual: Solution) -> None:
        key = individual._key()
        self._added.discard(key)
        self._removed.add(key)
        self.log.append(("discard", key))

    def recover_if_not_dead(self, individual: Solution) -> None:
        key = individual._key()
        if key not in self._dead:
            self._removed.discard(key)
            self._added.add(key)
        self.log.append(("recover", key))

    def isolate(self, individual: Solution) -> None:
        key = individual._key()
        self._isolated.add(key)
        self.log.append(("isolate", key))

    # What a task does not change, it asks the actor.
    def get_recovered_len(self) -> int:
        return self._actor.get_recovered_len()

    def update_deaths(self, individuals: SolutionSet) -> None:
        self._actor.update_deaths(individuals)

    def update_recovered_with_deaths(self) -> None:
        self._actor.update_recovered_with_deaths()

    def update_best_individual(self, individual: Solution) -> None:
        self._actor.update_best_individual(individual)

    def get_best_individual(self) -> Solution:
        return self._actor.get_best_individual()

    def get_pandemic_report(self) -> Dict[str, Any]:
        return self._actor.get_pandemic_report()

    def take_evaluation(self) -> bool:
        return self._actor.take_evaluation()

    def budget_spent(self) -> bool:
        return self._actor.budget_spent()

    def flush(self) -> None:
        """Nothing: the strain sends ``log`` once every task of the iteration has finished."""


@ray.remote
def _infect_from_carriers(seeds: List[int], strain_class: "type[CVOA]", actor: RemotePandemicStateProxy,
                          snapshot: Tuple[Set[Tuple[Any, ...]], Set[Tuple[Any, ...]]], domain: Domain,
                          fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
                          carriers: List[Solution], superspreaders: SolutionSet,
                          time: int) -> Tuple[SolutionSet, List[Tuple[str, Tuple[Any, ...]]]]:
    view = _IterationView(snapshot[0], snapshot[1], actor)
    infected = SolutionSet()
    for seed, carrier in zip(seeds, carriers):
        # Seeded per carrier, from the strain's generator, as when each carrier was a task
        # of its own: the strain's seed reaches every carrier alike (A-06).
        set_seed(seed)
        # With the budget spent, the carriers left would infect without evaluating (F-76).
        # Without a budget the proxy knows it already and asks nothing.
        if view.budget_spent():
            break
        infected.update(strain_class.infect_from_carrier(view, domain, fitness_function, strain_properties, carrier,
                                                         superspreaders, time))
    return infected, view.log


def spread_on_ray(strain_class: "type[CVOA]", state: PandemicState, domain: Domain,
                  fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
                  carriers: Iterable[Solution], superspreaders: SolutionSet, time: int) -> SolutionSet:
    """
    The contagion step of one iteration on Ray: the carriers split into one task per CPU,
    each running the strain class's own infect_from_carrier for each of its carriers, so a
    subclass's rules for isolation or admission run in the tasks too. Every task sees the
    pandemic as it was when the iteration started, with its own changes, and what they
    change reaches the shared state together, in the order of the tasks.

    :return: The newly infected population, in carrier order.
    :rtype: SolutionSet
    """
    # A-09: there used to be a second level of tasks that split one carrier's few
    # infections across CPUs; it only added dispatch. E-09: and one task per carrier, each
    # asking the actor about every individual it infected.
    from metagen.metaheuristics.distributed_tools import assign_load_equally

    carriers = list(carriers)
    # One seed per carrier, drawn in carrier order as when each was a task.
    seeds = [spawn_seed() for _ in carriers]
    if not carriers:
        return SolutionSet()
    proxy = cast(RemotePandemicStateProxy, state)
    # What the strain wrote before the iteration is in the snapshot.
    proxy.flush()
    actor = proxy.light()
    # Built by the actor once and read by every task from the object store.
    snapshot = proxy.handle.snapshot.remote()
    futures = []
    start = 0
    for count in assign_load_equally(len(carriers)):
        futures.append(_infect_from_carriers.remote(seeds[start:start + count], strain_class, actor, snapshot, domain,
                                                    fitness_function, strain_properties, carriers[start:start + count],
                                                    superspreaders, time))
        start += count
    new_infected_population = SolutionSet()
    log: List[Tuple[str, Tuple[Any, ...]]] = []
    for infected, changes in ray.get(futures):
        new_infected_population.update(infected)
        log.extend(changes)
    if log:
        proxy._best = ray.get(proxy.handle.apply.remote(log))
    return new_infected_population
