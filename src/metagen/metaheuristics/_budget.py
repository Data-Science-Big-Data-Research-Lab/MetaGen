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
from __future__ import annotations

import json
import math
import os
import statistics
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from ._parameters import require_integer

if TYPE_CHECKING:
    from metagen.framework import Solution


class _Budget:
    """
    What a metaheuristic does to know how much a run has spent and when it must stop, and to
    keep its history: the limit of iterations, the budget of evaluations and seconds, and
    the record written after every iteration. It is a part of
    :py:class:`~metagen.metaheuristics.Metaheuristic` and holds no state of its own: what it
    reads and writes are the attributes of the metaheuristic.
    """
    # Moved out of base.py, which held the whole life of a run in one class of 1200 lines
    # (O-04, metagen-auditoria/auditoria-independiente-2026-11/organizacion.md). The
    # bodies are as they were.

    max_evaluations: Optional[int]
    timeout: Optional[float]
    history: List[Dict[str, Any]]
    history_file: Optional[str]
    current_iteration: int
    current_solutions: List["Solution"]
    _iteration_limit: Optional[int]
    _evaluations: int
    _steps: int
    _step_count: Optional[int]
    _seconds: float

    if TYPE_CHECKING:
        def _best_so_far(self) -> "Solution": ...  # the metaheuristic's own

    def _iterations(self, max_iterations: Optional[int], default: int,
                    horizon: Optional[Callable[[int], int]] = None) -> Optional[int]:
        """
        The ``max_iterations`` of an algorithm, and the limit of iterations its criterion
        enforces, kept in ``_iteration_limit``. Given, it is both. Not given, without a
        budget it is ``default``; with one, there is no limit of iterations. An algorithm
        that also plans its search over ``max_iterations`` (a cooling or a gamma schedule)
        passes ``horizon``, which turns ``max_evaluations`` into the iterations it buys:
        that is its ``max_iterations`` then, and only the budget stops the run. With a
        ``timeout`` alone it keeps ``default``, as limit and as horizon.

        :param max_iterations: The iterations the user gave, or None.
        :type max_iterations: int or None
        :param default: The iterations without a budget.
        :type default: int
        :param horizon: The iterations ``max_evaluations`` buys, for an algorithm that plans
            over its iterations.
        :type horizon: Callable[[int], int], optional
        :return: The ``max_iterations`` to keep: the limit, the horizon, or None.
        :rtype: int or None
        """
        require_integer("max_iterations", max_iterations, 0, optional=True)
        if max_iterations is not None or (self.max_evaluations is None and self.timeout is None):
            chosen = default if max_iterations is None else max_iterations
            self._iteration_limit = chosen
            return chosen
        self._iteration_limit = None
        if horizon is None:
            return None
        if self.max_evaluations is None:
            self._iteration_limit = default
            return default
        return max(1, horizon(self.max_evaluations))

    def _iterations_done(self) -> bool:
        """Whether the run has made the iterations its criterion allows."""
        return self._iteration_limit is not None and self.current_iteration >= self._iteration_limit

    def _limit_reached(self) -> Optional[str]:
        """The budget the run has spent, ``"max_evaluations"`` or ``"timeout"``, or None."""
        if self.max_evaluations is not None and self._spent() >= self.max_evaluations:
            return "max_evaluations"
        if self.timeout is not None and self._seconds >= self.timeout:
            return "timeout"
        return None

    def _spent(self) -> float:
        """The evaluations a budget counts: whole ones, or steps over the steps of one for a
        fitness function that yields them, so that a candidate stopped early spends less."""
        if self._step_count:
            return self._steps / self._step_count
        return self._evaluations

    def _record_history(self) -> None:
        """
        Add the record of the iteration just completed to ``history``, and to the
        ``history`` file if the run has one.
        """
        fitnesses = [solution.get_fitness() for solution in self.current_solutions]
        finite = [value for value in fitnesses if math.isfinite(value)]
        best = self._best_so_far()
        record = {
            "iteration": self.current_iteration,
            "evaluations": self._evaluations,
            **({"steps": self._steps} if self._step_count else {}),
            "seconds": self._seconds,
            "best": best.get_fitness(),
            "iteration_best": min(finite) if finite else None,
            "mean": statistics.fmean(finite) if finite else None,
            "std": statistics.pstdev(finite) if finite else None,
            "worst": max(finite) if finite else None,
            "population_size": len(self.current_solutions),
            "best_solution": {name: best[name] for name in best},
        }
        self.history.append(record)
        if self.history_file is not None:
            directory = os.path.dirname(os.path.abspath(self.history_file))
            os.makedirs(directory, exist_ok=True)
            with open(self.history_file, "a") as handle:
                handle.write(json.dumps(record) + "\n")

    def _trim_history_file(self) -> None:
        """
        On resuming, drop the lines a run wrote after its last checkpoint: they are
        written again as the run repeats those iterations.
        """
        if self.history_file is None or not os.path.exists(self.history_file):
            return
        with open(self.history_file) as handle:
            kept = [line for line in handle
                    if line.strip() and json.loads(line)["iteration"] < self.current_iteration]
        with open(self.history_file, "w") as handle:
            handle.writelines(kept)
