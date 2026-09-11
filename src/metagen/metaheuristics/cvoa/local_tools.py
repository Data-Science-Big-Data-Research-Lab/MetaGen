import threading

from metagen.framework import Solution
from metagen.metaheuristics.cvoa.common_tools import IndividualState, SolutionSet


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
        self.recovered: SolutionSet = SolutionSet()
        self.deaths: SolutionSet = SolutionSet()
        self.isolated: SolutionSet = SolutionSet()
        self.best_individual_found:bool = False
        self.best_individual:Solution = initial_individual

    def get_individual_state(self, individual: Solution) -> IndividualState:
        with self.lock:
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
        with self.lock:
            return len(self.recovered)

    def get_infected_again(self, individual:Solution) -> None:
        with self.lock:
            self.recovered.remove(individual)

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

        It does not join the recovered: MetaGen departs from the paper's Algorithm 3
        here on purpose, so the point stays open to be infected again. Sending it to
        the recovered locks 70 % of every carrier's neighborhood and was measured to
        search worse on binary domains (F-45). The set used to demand a state no
        individual can have, so it never held anyone.
        """
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

    def get_pandemic_report(self):
        with self.lock:
            return {
                "recovered": len(self.recovered),
                 "deaths": len(self.deaths),
                 "isolated": len(self.isolated),
                "best_individual": self.best_individual
            }