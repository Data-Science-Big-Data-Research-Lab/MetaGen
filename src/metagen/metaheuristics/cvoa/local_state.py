"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import threading
from typing import Any, Dict, Optional

from metagen.framework import Solution
from metagen.metaheuristics.cvoa.common_tools import IndividualState, PandemicRecord, SolutionSet


class LocalPandemicState(PandemicRecord):
    """The state of a pandemic for the strains that run as threads: each call under a lock."""

    def __init__(self, initial_individual: Solution, max_evaluations: Optional[int] = None,
                 timeout: Optional[float] = None):
        # Reentrant on purpose: a call that holds it may call another that takes it again.
        # A plain Lock is not reentrant, so that thread blocked against itself (F-08). The
        # failure mode of getting the nesting wrong is a silent hang, which is reason
        # enough to let a thread reacquire a lock it already owns.
        self.lock = threading.RLock()
        super().__init__(initial_individual, max_evaluations, timeout)

    def get_individual_state(self, individual: Solution) -> IndividualState:
        with self.lock:
            return super().get_individual_state(individual)

    def get_recovered_len(self) -> int:
        with self.lock:
            return super().get_recovered_len()

    def get_infected_again(self, individual: Solution) -> None:
        with self.lock:
            super().get_infected_again(individual)

    def update_deaths(self, individuals: SolutionSet) -> None:
        with self.lock:
            super().update_deaths(individuals)

    def update_recovered_with_deaths(self) -> None:
        with self.lock:
            super().update_recovered_with_deaths()

    def recover_if_not_dead(self, individual: Solution) -> None:
        with self.lock:
            super().recover_if_not_dead(individual)

    def isolate(self, individual: Solution) -> None:
        with self.lock:
            super().isolate(individual)

    def update_best_individual(self, individual: Solution) -> None:  # type: ignore[override]
        # The strains read the best with get_best_individual; only the actor gives it back,
        # to save a call.
        with self.lock:
            super().update_best_individual(individual)

    def get_best_individual(self) -> Solution:
        with self.lock:
            return super().get_best_individual()

    def get_pandemic_report(self) -> Dict[str, Any]:
        with self.lock:
            return super().get_pandemic_report()

    def take_evaluation(self) -> bool:
        with self.lock:
            return super().take_evaluation()

    def budget_spent(self) -> bool:
        # Without a budget, nothing to ask under the lock.
        if not self.budget.limited():
            return False
        with self.lock:
            return super().budget_spent()

    def flush(self) -> None:
        """Nothing: every write is already in the state."""
