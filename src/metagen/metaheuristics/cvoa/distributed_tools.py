from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, TypeAlias
import ray
from metagen.framework import Solution, Domain
from metagen.metaheuristics.cvoa.common_tools import IndividualState, PandemicState, StrainProperties, SolutionSet
from metagen.framework.rng import set_seed, spawn_seed

if TYPE_CHECKING:
    from metagen.metaheuristics.cvoa.cvoa_local import CVOA

# A handle to the RemotePandemicState actor. Ray builds it with
# RemotePandemicState.remote(...) and every method is called through .remote(); mypy
# sees the decorated class, not the handle, so the handle is typed as Any here and
# the calls that go through it are annotated at the point of use (P-11).
PandemicStateHandle: TypeAlias = Any

# Remote pandemic state (ray support)
@ray.remote
class RemotePandemicState:
    def __init__(self, initial_individual: Solution):
        self.recovered: SolutionSet = SolutionSet()
        self.deaths: SolutionSet = SolutionSet()
        self.isolated: SolutionSet = SolutionSet()
        self.best_individual_found: bool = False
        self.best_individual: Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        result: IndividualState = IndividualState(False, False, False)
        if individual in self.recovered:
            result = result._replace(recovered=True)
        if individual in self.deaths:
            result = result._replace(dead=True)
        if individual in self.isolated:
            result = result._replace(isolated=True)
        return result

    # Recovered
    def get_recovered_len(self) -> int:
        return len(self.recovered)

    def get_infected_again(self, individual: Solution) -> None:
        self.recovered.remove(individual)

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
        Count an individual as isolated. It does not join the recovered: MetaGen
        departs from the paper here on purpose, see LocalPandemicState.isolate.
        """
        # F-45.
        self.isolated.add(individual)

    # Best Individual
    def update_best_individual(self, individual: Solution) -> None:
        self.best_individual_found = True
        self.best_individual = individual

    def get_best_individual(self) -> Solution:
        return self.best_individual

    def get_pandemic_report(self) -> Dict[str, Any]:
        return {
            "recovered": len(self.recovered),
            "deaths": len(self.deaths),
            "isolated": len(self.isolated),
            "best_individual": self.best_individual
        }


class RemotePandemicStateProxy:
    """
    The strain's view of the RemotePandemicState actor: the same methods as
    LocalPandemicState, each a synchronous call to the actor. The strain and the
    contagion tasks hold this instead of the handle, so the code that talks to the
    state is written once for threads and for Ray. It pickles with the handle
    inside, which is how it reaches the tasks.
    """
    # A-09: eleven ray.get calls left the strain's code when this proxy came in.

    def __init__(self, handle: PandemicStateHandle):
        self.handle = handle

    def get_individual_state(self, individual: Solution) -> IndividualState:
        state: IndividualState = ray.get(self.handle.get_individual_state.remote(individual))
        return state

    def get_recovered_len(self) -> int:
        recovered: int = ray.get(self.handle.get_recovered_len.remote())
        return recovered

    def get_infected_again(self, individual: Solution) -> None:
        ray.get(self.handle.get_infected_again.remote(individual))

    def update_deaths(self, individuals: SolutionSet) -> None:
        ray.get(self.handle.update_deaths.remote(individuals))

    def update_recovered_with_deaths(self) -> None:
        ray.get(self.handle.update_recovered_with_deaths.remote())

    def recover_if_not_dead(self, individual: Solution) -> None:
        ray.get(self.handle.recover_if_not_dead.remote(individual))

    def isolate(self, individual: Solution) -> None:
        # Waited on, not wrapped in ray.remote(...), which raised (F-42).
        ray.get(self.handle.isolate.remote(individual))

    def update_best_individual(self, individual: Solution) -> None:
        ray.get(self.handle.update_best_individual.remote(individual))

    def get_best_individual(self) -> Solution:
        best: Solution = ray.get(self.handle.get_best_individual.remote())
        return best

    def get_pandemic_report(self) -> Dict[str, Any]:
        report: Dict[str, Any] = ray.get(self.handle.get_pandemic_report.remote())
        return report


@ray.remote
def _infect_from_carrier(seed: int, strain_class: "type[CVOA]", state: PandemicState, domain: Domain,
                         fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
                         carrier: Solution, superspreaders: SolutionSet, time: int) -> SolutionSet:
    # Seeded from the strain's generator, so the strain's seed reaches every task (A-06).
    set_seed(seed)
    return strain_class.infect_from_carrier(state, domain, fitness_function, strain_properties, carrier,
                                            superspreaders, time)


def spread_on_ray(strain_class: "type[CVOA]", state: PandemicState, domain: Domain,
                  fitness_function: Callable[[Solution], float], strain_properties: StrainProperties,
                  carriers: Iterable[Solution], superspreaders: SolutionSet, time: int) -> SolutionSet:
    """
    The contagion step of one iteration on Ray: one task per carrier, each running the
    strain class's own infect_from_carrier, so a subclass's variant of isolation or
    admission runs in the tasks too.

    :return: The newly infected population, in carrier order.
    :rtype: SolutionSet
    """
    # A-09: there used to be a second level of tasks that split one carrier's few
    # infections across CPUs; it only added dispatch.
    futures = [_infect_from_carrier.remote(spawn_seed(), strain_class, state, domain, fitness_function,
                                           strain_properties, carrier, superspreaders, time)
               for carrier in carriers]
    new_infected_population = SolutionSet()
    for result in ray.get(futures):
        new_infected_population.update(result)
    return new_infected_population
