from copy import deepcopy
from collections.abc import Iterator
from typing import Any, Callable, Tuple, List, Optional, Set, cast

from metagen.framework import Domain, Solution


def solution_class(domain: Domain) -> type[Solution]:
    """
    The Solution class the domain's connector builds for the domain's core.

    The core is a BaseDefinition, and every connector maps that to a Solution class
    -- Solution itself, or a subclass such as GASolution or TPESolution. The connector
    is a runtime registry, so its get_type() can only promise a BaseType or a Solution
    and a type checker cannot tell which; this is the one place that says which.

    :param domain: The domain to build solutions for.
    :type domain: Domain
    :return: The class to instantiate a solution of this domain with.
    :rtype: type[Solution]
    """
    # P-11: the single cast that replaced four copies of this line.
    return cast(type[Solution], domain.get_connector().get_type(domain.get_core()))


class Counts:
    """The work a fitness function has done: its calls and, for one that yields its
    steps, the steps taken and how many a whole evaluation takes. Two of them subtract and
    add, so that a worker of Ray can give back what it did on its copy and the caller add it
    to its own."""

    def __init__(self, calls: int = 0, steps: int = 0, step_count: Optional[int] = None) -> None:
        self.calls, self.steps, self.step_count = calls, steps, step_count

    def __add__(self, other: Any) -> "Counts":
        if isinstance(other, Counts):
            return Counts(self.calls + other.calls, self.steps + other.steps,
                          self.step_count if self.step_count is not None else other.step_count)
        if other == 0:
            return self
        return NotImplemented

    __radd__ = __add__

    def __sub__(self, other: "Counts") -> "Counts":
        return Counts(self.calls - other.calls, self.steps - other.steps, self.step_count)

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
    :py:class:`~metagen.metaheuristics.racing.Racing` a solution that falls significantly
    behind ``references``, the values per step of the population it races against, gets
    no more steps. Every solution so evaluated keeps its values per step in
    ``step_values`` and whether it was stopped in ``raced_out``.
    """

    def __init__(self, function: Callable[[Solution], Any], racing: Any = None,
                 step_count: Optional[int] = None) -> None:
        self.function = function
        self.calls = 0
        self.steps = 0
        self.racing = racing
        #: The steps of a whole evaluation, learned from the first one.
        self.step_count = step_count
        #: The values per step of the solutions a candidate races against.
        self.references: List[List[float]] = []

    def __call__(self, solution: Solution) -> float:
        self.calls += 1
        value = self.function(solution)
        if not isinstance(value, Iterator):
            return value
        return self._steps_of(solution, value)

    def _steps_of(self, solution: Solution, steps: Iterator[Any]) -> float:
        from metagen.metaheuristics.racing import corrected_mean

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
        setattr(solution, "step_values", values)
        setattr(solution, "raced_out", raced_out)
        return corrected_mean(values, references) if raced_out else sum(values) / len(values)


def calls_of(fitness_function: Callable[[Solution], Any]) -> Counts:
    """What a fitness function has counted so far, nothing if it does not count."""
    if isinstance(fitness_function, CountingFitness):
        return Counts(fitness_function.calls, fitness_function.steps, fitness_function.step_count)
    return Counts()


def add_calls(fitness_function: Callable[[Solution], Any], counts: Any) -> None:
    """Add to a counting fitness function what was done in a worker on a copy of it."""
    if isinstance(fitness_function, CountingFitness) and isinstance(counts, Counts):
        fitness_function.calls += counts.calls
        fitness_function.steps += counts.steps
        if fitness_function.step_count is None:
            fitness_function.step_count = counts.step_count


def random_exploration (domain: Domain, fitness_function: Callable[[Solution], float], num_solutions: int) \
                                                                            -> Tuple[List[Solution], Solution]:

    solution_type = solution_class(domain)

    potential:Solution = solution_type(domain, connector=domain.get_connector())
    potential.evaluate(fitness_function)

    solutions: List[Solution] = [potential]
    best:Solution = potential

    for _ in range(num_solutions-1):

        potential = solution_type(domain, connector=domain.get_connector())
        potential.evaluate(fitness_function)
        solutions.append(potential)

        if potential.get_fitness() < best.get_fitness():
            best = potential

    return solutions, best


def local_search(solution: Solution, fitness_function: Callable[[Solution], float], neighbor_population_size: int
                             , alteration_limit: float) -> Solution:
    best_neighbor = deepcopy(solution)
    for _ in range(neighbor_population_size):
        neighbor = deepcopy(solution)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)
        if neighbor.get_fitness() < best_neighbor.get_fitness():
            best_neighbor = neighbor
    return best_neighbor


def local_search_with_tabu (solution: Solution, fitness_function: Callable[[Solution], float],
                            neighbor_population_size: int, alteration_limit: float, tabu_list:List[Solution]) -> Tuple[List[Solution], Solution]:
    tabu_set: Set[Solution] = set(tabu_list)
    best_neighbor = deepcopy(solution)
    neighborhood = []

    for _ in range(neighbor_population_size):
        # Each neighbor starts from the best one so far, not from `solution`. That is
        # deliberate and it is what hill climbing does: take a step, and if it improves,
        # keep going from there. A-03 reads it as a defect, which it would be for a tabu
        # search, since that needs a neighborhood around the current point to pick the
        # best non-tabu move from. Measured both ways, chaining wins: 0.0005 against
        # 0.0025 on the 2D sphere and 0.6173 against 0.7778 on Rastrigin.
        #
        # Note the difference with F-25, where chaining in SA was a real defect: there
        # the base moved on every mutation, whatever the outcome, so the neighbors
        # drifted away from the point the Metropolis criterion was comparing against.
        # Here the base only moves when it improves.
        neighbor = deepcopy(best_neighbor)
        neighbor.mutate(alteration_limit=alteration_limit)
        neighbor.evaluate(fitness_function)

        if neighbor not in tabu_set:
            neighborhood.append(neighbor)
            if neighbor < best_neighbor:
                best_neighbor = neighbor

    return neighborhood, best_neighbor






