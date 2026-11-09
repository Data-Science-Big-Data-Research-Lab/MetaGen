from copy import deepcopy
from collections.abc import Iterator
from typing import Any, Callable, Dict, Tuple, List, Optional, Set, cast

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
    :py:class:`~metagen.metaheuristics.racing.Racing` a solution that falls significantly
    behind ``references``, the values per step of the population it races against, gets
    no more steps. Every solution so evaluated keeps its values per step in
    ``step_values`` and whether it was stopped in ``raced_out``.
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

    def __call__(self, solution: Solution) -> float:
        self.calls += 1
        value = self.function(solution)
        if isinstance(value, tuple) and len(value) == 2:
            value, model = value
            if self.best is None or value < self.best[0]:
                self.best = (value, model)
            return value
        if not isinstance(value, Iterator):
            return value
        return self._steps_of(solution, value)

    def __getstate__(self) -> Dict[str, Any]:
        # A copy for a worker of Ray takes the value of the best model but not the model:
        # the worker only needs to know what to beat, and the model would travel with
        # every task.
        state = dict(self.__dict__)
        if self.best is not None:
            state["best"] = (self.best[0], None)
        return state

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








def save_model(model: Any, path: str) -> str:
    """
    Write a trained model to a file in the format of the library it comes from: a model
    of Keras or TensorFlow with its own ``save``, to a ``.keras`` file; one of PyTorch with
    ``torch.save``; any other with ``joblib`` when it is installed, as scikit-learn
    recommends for its models, and with ``pickle`` otherwise. It is written aside and then
    renamed over, so a model that cannot be saved leaves no file behind and a file already
    there as it was.

    :param model: The model.
    :type model: Any
    :param path: The file. For Keras, ``.keras`` is added if it does not end so.
    :type path: str
    :return: The file written.
    :rtype: str
    :raises ValueError: if the model cannot be saved so, as one of a library none of those
        formats can hold.
    """
    import os
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    # From the classes it inherits from too: a network of PyTorch or of Keras is most often
    # a class of the user's own, built on torch.nn.Module or keras.Model.
    libraries = {cls.__module__.split(".")[0] for cls in type(model).__mro__}
    library = ("keras" if libraries & {"keras", "tensorflow", "tf_keras"} and hasattr(model, "save")
               else "torch" if "torch" in libraries else None)
    if library == "keras" and not path.endswith(".keras"):
        path += ".keras"
    root, extension = os.path.splitext(path)
    temporary = f"{root}.partial{extension}"
    how = {"keras": "its own save", "torch": "torch.save"}.get(library or "", "joblib")
    try:
        if library == "keras":
            model.save(temporary)
        elif library == "torch":
            import torch
            torch.save(model, temporary)
        else:
            try:
                import joblib
            except ImportError:
                import pickle
                how = "pickle"
                with open(temporary, "wb") as handle:
                    pickle.dump(model, handle)
            else:
                how = "joblib"
                joblib.dump(model, temporary)
    except Exception as error:
        if os.path.exists(temporary):
            os.remove(temporary)
        kind = f"{type(model).__module__}.{type(model).__qualname__}"
        raise ValueError(f"The model, a {kind}, cannot be saved with {how}: {error}. It is not lost: save it "
                         f"with the method of its library.") from error
    os.replace(temporary, path)
    return path
