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
import math
import numbers
from collections.abc import Iterator
from typing import Any, Callable, Dict, List, Optional, Tuple

from metagen.framework import Solution
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.racing import corrected_mean, record_steps

# What counts the evaluations of a run, and keeps the best model they returned: what travels
# to the workers with the fitness function. It was in tools.py with the elementary searches
# and the saving of models (OF-12 of the independent audit); tools re-exports it.


#: The value and the model of the best evaluation that returned a model, or None.
BestModel = Optional[Tuple[float, Any]]


def _better(first: BestModel, second: BestModel) -> BestModel:
    """The better of two best models, the first on a tie."""
    if second is None or (first is not None and first[0] <= second[0]):
        return first
    return second


class Counts:
    """The work a fitness function has done: its calls and, for one that yields its
    steps, the steps taken and how many a whole evaluation takes, and the best model it
    was given back with a value, if any. Two of them subtract and add, so that a worker of
    Ray can give back what it did on its copy and the caller add it to its own."""

    def __init__(self, calls: int = 0, steps: int = 0, step_count: Optional[int] = None,
                 best: BestModel = None) -> None:
        self.calls, self.steps, self.step_count, self.best = calls, steps, step_count, best

    def __add__(self, other: Any) -> "Counts":
        if isinstance(other, Counts):
            return Counts(self.calls + other.calls, self.steps + other.steps,
                          self.step_count if self.step_count is not None else other.step_count,
                          _better(self.best, other.best))
        if other == 0:
            return self
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other: "Counts") -> "Counts":
        # The best model found since the other: only one better than what it already had.
        improved = self.best is not None and (other.best is None or self.best[0] < other.best[0])
        return Counts(self.calls - other.calls, self.steps - other.steps, self.step_count,
                      self.best if improved else None)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Counts) and (self.calls, self.steps) == (other.calls, other.steps)

    def __repr__(self) -> str:
        return f"Counts(calls={self.calls}, steps={self.steps})"


class CountingFitness:
    """
    The fitness function of a run, counting its calls. A worker of Ray runs on a copy of
    it, so a task gives back what it did (:py:func:`calls_of`) and the caller adds it to
    its own count (:py:func:`add_calls`).

    A fitness function may also yield its steps one at a time, such as the loss of each
    fold of a cross-validation: its value is then their mean, and with a
    :py:class:`~metagen.metaheuristics.Racing` a solution that falls significantly
    behind ``references``, the values per step of the population it races against, gets
    no more steps. Every solution so evaluated keeps its values per step in
    ``step_values`` and whether it was stopped in ``raced_out``.

    A value that is not a number, NaN, counts as the worst one, infinity: it is no
    solution's best, and the first one is logged as a warning.
    """

    def __init__(self, function: Callable[[Solution], Any], racing: Any = None,
                 step_count: Optional[int] = None, best: BestModel = None) -> None:
        self.function = function
        self.calls = 0
        self.steps = 0
        self.racing = racing
        #: The steps of a whole evaluation, learned from the first one.
        self.step_count = step_count
        #: The values per step of the solutions a candidate races against.
        self.references: List[List[float]] = []
        #: The value and the model of the best evaluation that returned a model, if any:
        #: a fitness function may return a pair, its value and the model it trained.
        self.best: BestModel = best
        #: Whether a NaN has been warned about.
        self.warned_nan = False

    def __call__(self, solution: Solution) -> float:
        self.calls += 1
        value = self.function(solution)
        if isinstance(value, tuple) and len(value) == 2:
            value, model = value
            value = self._worst_if_nan(value)
            if self.best is None or value < self.best[0]:
                self.best = (value, model)
            return value
        if not isinstance(value, Iterator):
            return self._worst_if_nan(value)
        return self._worst_if_nan(self._steps_of(solution, value))

    def _worst_if_nan(self, value: Any) -> float:
        # A value that is not a number failed far from the fitness function: None in the
        # first comparison, a NumPy array when the history was written (F-75). It is
        # converted here, and what does not convert names the function that returned it.
        if isinstance(value, bool) or not isinstance(value, numbers.Real):
            try:
                if isinstance(value, (str, bytes)):
                    raise TypeError
                value = float(value)
            except (TypeError, ValueError):
                name = getattr(self.function, "__qualname__", repr(self.function))
                raise TypeError(f"The fitness function {name} must return a number, not {value!r}.") from None
        # Every comparison with NaN is false, so a NaN that became the best could not be
        # replaced and the whole run returned it, the best model too (F-59).
        if math.isnan(value):
            if not self.warned_nan:
                self.warned_nan = True
                metagen_logger.warning("The fitness function returned NaN; it counts as the worst value, inf.")
            return math.inf
        return value

    def __getstate__(self) -> Dict[str, Any]:
        # A copy for a worker of Ray takes the value of the best model but not the model:
        # the worker only needs to know what to beat, and the model would travel with
        # every task.
        state = dict(self.__dict__)
        if self.best is not None:
            state["best"] = (self.best[0], None)
        return state

    def _steps_of(self, solution: Solution, steps: Iterator[Any]) -> float:

        values: List[float] = []
        references = self.references if self.racing is not None else []
        raced_out = False
        for step in steps:
            values.append(float(step))
            self.steps += 1
            if references and self.racing.eliminates(values, references):
                raced_out = True
                close = getattr(steps, "close", None)
                if close is not None:
                    close()
                break
        if not values:
            raise ValueError("A fitness function that yields its steps must yield at least one.")
        if not raced_out:
            if self.step_count is None:
                self.step_count = len(values)
            elif len(values) != self.step_count:
                raise ValueError(f"A fitness function that yields its steps must yield as many for every "
                                 f"solution: {len(values)} here, {self.step_count} before.")
        record_steps(solution, values, raced_out)
        return corrected_mean(values, references) if raced_out else sum(values) / len(values)


def calls_of(fitness_function: Callable[[Solution], Any]) -> Counts:
    """What a fitness function has counted so far, nothing if it does not count."""
    if isinstance(fitness_function, CountingFitness):
        return Counts(fitness_function.calls, fitness_function.steps, fitness_function.step_count,
                      fitness_function.best)
    return Counts()


def add_calls(fitness_function: Callable[[Solution], Any], counts: Any) -> None:
    """Add to a counting fitness function what was done in a worker on a copy of it, and
    keep the best model the worker found if it is better than its own."""
    if isinstance(fitness_function, CountingFitness) and isinstance(counts, Counts):
        fitness_function.calls += counts.calls
        fitness_function.steps += counts.steps
        if fitness_function.step_count is None:
            fitness_function.step_count = counts.step_count
        if counts.best is not None and counts.best[1] is not None:
            fitness_function.best = _better(fitness_function.best, counts.best)
