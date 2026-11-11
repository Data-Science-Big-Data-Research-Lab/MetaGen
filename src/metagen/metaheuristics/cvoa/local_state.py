import threading
from typing import Any, Dict

from metagen.framework import Solution
from metagen.metaheuristics.cvoa.common_tools import IndividualState, SolutionKeys, SolutionSet


# Local pandemic state (multi-threading)
class LocalPandemicState:
    def __init__(self, initial_individual:Solution):
        # Lock fot multi-threading safety access to the shared structures.
        # Reentrant on purpose: isolate_individual_conditional_state holds it and
        # calls get_individual_state, which takes it again. A plain Lock is not
        # reentrant, so that thread blocked against itself (F-08). The failure mode
        # of getting the nesting wrong is a silent hang, which is reason enough to
        # let a thread reacquire a lock it already owns.
        self.lock = threading.RLock()
        self.recovered: SolutionKeys = SolutionKeys()
        self.deaths: SolutionKeys = SolutionKeys()
        self.isolated: SolutionKeys = SolutionKeys()
        self.best_individual_found:bool = False
        self.best_individual:Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        with self.lock:
            # The key once, not a hash per set (E-03).
            key = individual._key()
            return IndividualState(self.recovered.holds(key), self.deaths.holds(key), self.isolated.holds(key))

    # Recovered
    def get_recovered_len(self) -> int:
        with self.lock:
            return len(self.recovered)

    def get_infected_again(self, individual:Solution) -> None:
        # Several strains can infect the same recovered point again at once: each read it
        # as recovered before the other took it out, and remove() raised KeyError.
        with self.lock:
            self.recovered.discard(individual)

    # Deaths
    def update_deaths(self, individuals:SolutionSet)-> None:
        with self.lock:
            self.deaths.update(individuals)

    # Recovered and Deaths
    def update_recovered_with_deaths(self)-> None:
        with self.lock:
            self.recovered.difference_update(self.deaths)

    def recover_if_not_dead(self, individual:Solution)-> None:
        with self.lock:
            if individual not in self.deaths:
                self.recovered.add(individual)

    # Isolated
    def isolate(self, individual: Solution) -> None:
        """
        Count an individual as isolated.

        It does not join the recovered, so the point stays open to be infected again.
        """
        # F-45: sending it to the recovered was measured to search worse on binary
        # domains. The set used to demand a state no individual can have, so it never
        # held anyone.
        with self.lock:
            self.isolated.add(individual)

    # Best Individual
    def update_best_individual(self, individual:Solution) -> None:
        with self.lock:
            self.best_individual_found = True
            self.best_individual = individual

    def get_best_individual(self) -> Solution:
        with self.lock:
            return self.best_individual

    def get_pandemic_report(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "recovered": len(self.recovered),
                 "deaths": len(self.deaths),
                 "isolated": len(self.isolated),
                "best_individual": self.best_individual
            }