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
import heapq
import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast, Mapping

import numpy as np
from scipy.stats import norm

from metagen.framework import Domain, Solution
from metagen.framework.domain import DynamicStructureDefinition
from metagen.framework.rng import get_numpy_rng
from metagen.framework.solution.types import Categorical, Integer, Permutation, Real, Structure, Subset
from metagen.metaheuristics.racing import Racing
from metagen.metaheuristics._parameters import require_integer, require_number
from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.tpe.subset_model import SubsetModel
from metagen.metaheuristics.tpe.tpe import TPE

Path = Tuple[Union[str, int], ...]


class KernelTPE(TPE):
    """
    A Tree-structured Parzen Estimator that models each variable with a mixture of
    kernels and evaluates one candidate per iteration, which suits a fitness function
    that is expensive to evaluate.

    It keeps a history of evaluated solutions, splits it into the best fraction
    ``gamma`` and the rest, and models each variable on its own:

    - **The model is a mixture of kernels**, one per observation, plus a wide prior
      centered on the domain: a Parzen estimator. The width of each kernel is the
      distance to its nearest neighbor, clipped between the prior's width divided by
      the number of observations and the prior's width; integers are modeled on the
      real line and rounded to their grid; a categorical variable is modeled by its
      counts, with the prior adding ``prior_weight`` to every category; a subset by the
      probability that each element is in, with a prior worth ``prior_weight``
      observations that keeps the mean size of the observed selections.
    - **Candidates are drawn from the model of the best solutions**, ``n_candidates``
      of them per iteration, **and only the one that maximizes** ``l(x) / g(x)``, the
      ratio of the densities under the best and the rest, **is evaluated**: one
      evaluation per iteration. A subset is drawn from the model of the best and does not
      enter the ratio.

    :py:class:`~metagen.metaheuristics.TPE` shares the history, the ``gamma`` schedules
    and the warmup, and evaluates a pool of candidates per iteration.

    A run costs ``population_size * (warmup_iterations + 1) + max_iterations``
    evaluations: 220 with the defaults. The history is never trimmed, since every
    observation is a kernel. On a dynamic structure the length is not modeled: a
    candidate is born with a random length and the positions it has are drawn from
    the observations that have them. Under the global
    distribution model every slice proposes and evaluates one candidate, so an
    iteration costs as many evaluations as there are slices.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param max_iterations: Iterations to run, one evaluation each, defaults to 100. With
        ``max_evaluations`` and no value, the iterations the budget buys after the warmup
        and the initialization; with ``timeout`` alone, 100
    :type max_iterations: int or None, optional
    :param warmup_iterations: Rounds of random exploration before the search, each
        evaluating ``population_size`` solutions, all of which join the history the
        model is built on. None, the default, is 5, or fewer with ``max_evaluations``:
        the warmup and the initialization then take at most a quarter of the budget.
    :type warmup_iterations: int or None, optional
    :param n_candidates: Candidates drawn from the model of the best solutions per
        iteration, of which the best scoring one is evaluated, defaults to 24
    :type n_candidates: int, optional
    :param prior_weight: Weight of the prior kernel against one observation, defaults to 1.0
    :type prior_weight: float, optional
    :param gamma_config: How the fraction of best solutions is scheduled, defaults to
        the sample-based schedule
    :type gamma_config: GammaConfig, optional
    :param population_size: Random solutions evaluated to start with, defaults to 20
    :type population_size: int, optional
    {options_of_a_run}

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import KernelTPE

        domain = Domain()
        domain.define_integer("max_depth", 1, 20)
        domain.define_real("learning_rate", 0.001, 0.1)
        domain.define_categorical("criterion", ["gini", "entropy"])

        fitness_function = lambda solution: (solution["max_depth"] - 7) ** 2 + solution["learning_rate"]

        search = KernelTPE(domain, fitness_function, max_iterations=100, seed=0)
        best_solution = search.run()
    """
    # Measured on the behavior bench: the l(x)/g(x) selection on MetaGen's single-Gaussian
    # model won 26 of 100 against random sampling, against 70 for MetaGen's TPE as it is;
    # on the mixture of kernels it wins 98 of 110 on the same 480 evaluations.
    # F-35: the length of a dynamic structure is not modeled, here or in TPE.

    default_max_iterations = 100
    default_warmup_iterations = 5

    # Its history is never trimmed and every observation is a kernel, so the warmup's
    # samples join it (F-53): on the behavior bench, 30 seeds, 296 -> 301 wins of 330
    # against random sampling, better on Griewank and Schwefel and worse on none
    # (metagen-auditoria/mediciones/f53/tabla.md).
    keeps_warmup = True

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 max_iterations: Optional[int] = None, warmup_iterations: Optional[int] = None, n_candidates: int = 24,
                 prior_weight: float = 1.0, gamma_config: Optional[GammaConfig] = None,
                 population_size: int = 20, distributed: bool = False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, distribution_model: str = "global",
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1, history: Optional[str] = None,
                 max_evaluations: Optional[int] = None, timeout: Optional[float] = None,
                 initial_solutions: Optional[Sequence[Mapping[str, Any]]] = None, racing: Optional[Racing] = None,
                 refit: Optional[Callable[[Solution], Any]] = None) -> None:
        require_integer("n_candidates", n_candidates, 1)
        require_number("prior_weight", prior_weight, above=0)
        super().__init__(domain, fitness_function, max_iterations=max_iterations,
                         warmup_iterations=warmup_iterations, candidate_pool_size=1, gamma_config=gamma_config,
                         distributed=distributed, log_dir=log_dir, seed=seed, population_size=population_size,
                         distribution_model=distribution_model,
                         checkpoint=checkpoint, checkpoint_every=checkpoint_every,
                         history=history, max_evaluations=max_evaluations, timeout=timeout,
                         initial_solutions=initial_solutions, racing=racing, refit=refit)
        self.n_candidates = n_candidates
        self.prior_weight = prior_weight

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Split the history, draw ``n_candidates`` from the model of the best part,
        evaluate the one that scores highest under ``l(x) / g(x)`` and add it to
        the history.
        """
        history = list(solutions)
        gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                              max_iterations=self.max_iterations, num_solutions=len(history))
        how_many_best = max(1, round(gamma * len(history)))
        best_solutions = heapq.nsmallest(how_many_best, history, key=Solution.get_fitness)
        best_ids = {id(solution) for solution in best_solutions}
        worst_solutions = [solution for solution in history if id(solution) not in best_ids]

        candidate = self.propose(best_solutions, worst_solutions)
        candidate.evaluate(self.fitness_function)
        history.append(candidate)
        local_best = min(self._best_so_far(), candidate, key=Solution.get_fitness)
        return history, local_best

    def _limit_solution_history(self, history: List[Solution], gamma: float) -> List[Solution]:
        """Every observation is a kernel of the model: nothing is forgotten."""
        return history

    def propose(self, best_solutions: List[Solution], worst_solutions: List[Solution]) -> Solution:
        """
        Draw ``n_candidates`` solutions from the model of the best ones and return the
        candidate that maximizes the sum over its variables of ``log l(x) - log g(x)``.
        Permutations and subsets are drawn but stay out of the sum.

        :param best_solutions: The best fraction of the history, the observations of ``l``.
        :type best_solutions: List[Solution]
        :param worst_solutions: The rest of the history, the observations of ``g``.
        :type worst_solutions: List[Solution]
        :return: The candidate to evaluate, unevaluated.
        :rtype: Solution
        """
        good = _observations(best_solutions)
        bad = _observations(worst_solutions)
        good_lengths = _lengths(best_solutions)
        bad_lengths = _lengths(worst_solutions)
        # One model per variable and side, shared by every candidate: building the
        # kernels once here instead of once per candidate costs 24 times less and
        # draws the same numbers in the same order.
        models: Dict[Path, Tuple[_Model, _Model]] = {}
        length_models: Dict[Path, Tuple[_CategoricalModel, _CategoricalModel]] = {}
        solution_type = solution_class(self.domain)
        candidates: List[Tuple[Solution, List[Tuple[Path, Any, _Model, _Model]]]] = []
        for _ in range(self.n_candidates):
            candidate = solution_type(self.domain, connector=self.domain.get_connector())
            drawn: List[Tuple[Path, Any, _Model, _Model]] = []
            # The length of a dynamic structure is drawn from a model of the lengths of the
            # best, as a categorical variable is, before its elements, and scored once: it was
            # the one the candidate was built with, at random, and the proposals collapsed to
            # the shortest length (X-06, metagen-auditoria/auditoria-independiente-2026-11/eficacia.md).
            # Measured, 20 seeds on a dynamic structure whose best length is 8: 14 -> 18 wins
            # against random sampling, length-1 proposals 73 % -> 33 %; the polynomial problem of
            # the bench, 10 seeds, mean 0.0215 -> 0.0164. Averaging the terms of the elements, so
            # that lengths compare, did better on the first (3.20 against 4.20) and broke the
            # second (5 of 10 wins, mean 0.137): every coefficient counts there.
            for path, structure in _dynamic_structures(candidate):
                if path not in good_lengths or not candidate.is_active(cast(str, path[0])):
                    continue
                key = path + ("length",)
                if key not in length_models:
                    allowed = _allowed_lengths(cast(DynamicStructureDefinition, structure.get_definition()))
                    length_models[key] = (_CategoricalModel(allowed, good_lengths[path], self.prior_weight),
                                          _CategoricalModel(allowed, bad_lengths.get(path, []), self.prior_weight))
                length_good, length_bad = length_models[key]
                length = int(length_good.choose())
                if length != len(structure):
                    structure.set(structure._new_elements(length))
                drawn.append((key, length, length_good, length_bad))
            for path, leaf in _leaves(candidate):
                if path not in good:
                    continue
                if isinstance(leaf, Permutation):
                    # An ordering has no density: take the one of a good solution,
                    # drawn at random, moved by one swap. It does not enter the score.
                    chosen = good[path][int(get_numpy_rng().integers(len(good[path])))]
                    leaf.set(list(chosen))
                    leaf.mutate(alteration_limit=1)
                    continue
                if path not in models:
                    models[path] = (_model(leaf, good[path], self.prior_weight),
                                    _model(leaf, bad.get(path, []), self.prior_weight))
                model_good, model_bad = models[path]
                value = model_good.draw(leaf)
                leaf.set(value)
                drawn.append((path, value, model_good, model_bad))
            candidates.append((candidate, drawn))

        # Scored once every candidate is drawn: scoring draws nothing, so the numbers come
        # out in the same order, and each model takes the values of every candidate at
        # once, a matrix of points by kernels, instead of one call per candidate and
        # variable, which was most of the cost of an iteration (E-04,
        # metagen-auditoria/auditoria-independiente-2026-11/eficiencia.md). The terms of a
        # candidate are added in the same order, so the scores are the same, bit for bit.
        # A conditional variable counts only when the value drawn for the one it depends
        # on makes it active.
        counted: List[List[Tuple[_Model, _Model, Any]]] = []
        for candidate, drawn in candidates:
            terms: List[Tuple[_Model, _Model, Any]] = []
            for path, value, model_good, model_bad in drawn:
                # A subset is drawn from the model of the best and stays out of the score.
                # Its density is a product over every element, so the term outweighs the
                # other variables and always picks the most typical selection: the proposals
                # collapsed and, selecting features over six problems, twenty seeds, the
                # algorithm won 64 of 120 against random sampling on the same budget; out of
                # the score, 120 of 120. See metagen-auditoria/mediciones/subconjuntos/INFORME.md.
                if isinstance(model_good, SubsetModel):
                    continue
                if candidate.is_active(cast(str, path[0])):
                    terms.append((model_good, model_bad, value))
            counted.append(terms)
        densities = _log_densities_by_model([term for terms in counted for term in terms])

        best_candidate: Optional[Solution] = None
        best_score = -math.inf
        position = 0
        for (candidate, _), terms in zip(candidates, counted):
            score = 0.0
            for _term in terms:
                good_density, bad_density = densities[position]
                score += good_density - bad_density
                position += 1
            if score > best_score:
                best_candidate, best_score = candidate, score
        assert best_candidate is not None
        return best_candidate


Leaf = Union[Integer, Real, Categorical, Permutation, Subset]



def _dynamic_structures(solution: Solution, prefix: Path = ()) -> List[Tuple[Path, Structure]]:
    """Every dynamic structure of a solution, by the path that reaches it, outer ones first."""
    found: List[Tuple[Path, Structure]] = []
    for name, value in solution.get_variables().items():
        found.extend(_dynamic_structures_of(value, prefix + (name,)))
    return found


def _dynamic_structures_of(value: Any, path: Path) -> List[Tuple[Path, Structure]]:
    if isinstance(value, Solution):
        return _dynamic_structures(value, path)
    if isinstance(value, Structure):
        found: List[Tuple[Path, Structure]] = []
        if isinstance(value.get_definition(), DynamicStructureDefinition):
            found.append((path, value))
        for index in range(len(value)):
            found.extend(_dynamic_structures_of(value.get(index), path + (index,)))
        return found
    return []


def _lengths(solutions: Sequence[Solution]) -> Dict[Path, List[int]]:
    """The lengths of every dynamic structure, by path, across the given solutions, where active."""
    observed: Dict[Path, List[int]] = {}
    for solution in solutions:
        for path, structure in _dynamic_structures(solution):
            if solution.is_active(cast(str, path[0])):
                observed.setdefault(path, []).append(len(structure))
    return observed


def _allowed_lengths(definition: DynamicStructureDefinition) -> List[int]:
    _, min_length, max_length, step, _ = definition.get_attributes()
    return list(range(min_length, max_length + 1, step or 1))


def _log_densities_by_model(terms: Sequence[Tuple[Any, Any, Any]]) -> List[Tuple[float, float]]:
    """
    The log densities of ``l`` and ``g`` at the value of every term, in order, asking each
    model once for all the values it is given.

    :param terms: The model of the best, the model of the rest and the value, per term.
    :return: The log density under each model, per term.
    """
    asked: Dict[int, Tuple[Any, List[Any]]] = {}
    for model_good, model_bad, value in terms:
        for model in (model_good, model_bad):
            asked.setdefault(id(model), (model, []))[1].append(value)
    answered = {key: iter(model.log_densities(values)) for key, (model, values) in asked.items()}
    return [(next(answered[id(model_good)]), next(answered[id(model_bad)])) for model_good, model_bad, _ in terms]


def _leaves(solution: Solution, prefix: Path = ()) -> List[Tuple[Path, Leaf]]:
    """Every basic variable of a solution with the path that reaches it, groups and
    structures included; a structure's positions are addressed by index."""
    found: List[Tuple[Path, Leaf]] = []
    for name, value in solution.get_variables().items():
        found.extend(_leaves_of(value, prefix + (name,)))
    return found


def _leaves_of(value: Any, path: Path) -> List[Tuple[Path, Leaf]]:
    if isinstance(value, Solution):
        return _leaves(value, path)
    if isinstance(value, Structure):
        found: List[Tuple[Path, Leaf]] = []
        for index in range(len(value)):
            found.extend(_leaves_of(value.get(index), path + (index,)))
        return found
    if isinstance(value, (Integer, Real, Categorical, Permutation, Subset)):
        return [(path, value)]
    return []


def _observations(solutions: Sequence[Solution]) -> Dict[Path, List[Any]]:
    """The observed values of every variable, by path, across the given solutions."""
    observed: Dict[Path, List[Any]] = {}
    for solution in solutions:
        for path, leaf in _leaves(solution):
            # A conditional variable's values count only where it was active.
            if solution.is_active(cast(str, path[0])):
                observed.setdefault(path, []).append(leaf.get())
    return observed


def _bounds(leaf: Union[Integer, Real]) -> Tuple[float, float, Optional[float]]:
    _, min_value, max_value, step = leaf.get_definition().get_attributes()
    return float(min_value), float(max_value), (float(step) if step else None)


def _is_log(leaf: Union[Integer, Real]) -> bool:
    return bool(leaf.get_definition().log)


def _kernels(values: Sequence[float], low: float, high: float, prior_weight: float) \
        -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    The adaptive Parzen estimator: one Gaussian per observation whose width is the
    distance to its nearest neighbor, clipped between the prior's width over the
    number of observations and the prior's width, plus the prior itself, a Gaussian
    centered on the domain as wide as it. Returns the means, widths and weights.
    """
    prior_mu = (low + high) / 2.0
    prior_sigma = max(high - low, 1e-12)
    mus = np.array(sorted([*values, prior_mu]), dtype=float)
    if len(mus) == 1:
        sigmas = np.array([prior_sigma])
    else:
        gaps = np.diff(mus)
        left = np.concatenate([[math.inf], gaps])
        right = np.concatenate([gaps, [math.inf]])
        sigmas = np.minimum(left, right)
        sigmas = np.where(np.isfinite(sigmas), sigmas, np.maximum(left, right))
        sigmas = np.where(np.isfinite(sigmas), sigmas, prior_sigma)
        minimum_sigma = prior_sigma / min(100.0, 1.0 + len(values))
        sigmas = np.clip(sigmas, minimum_sigma, prior_sigma)
    prior_index = int(np.searchsorted(mus, prior_mu))
    sigmas = sigmas.astype(float)
    sigmas[prior_index] = prior_sigma
    weights = np.ones(len(mus))
    weights[prior_index] = prior_weight
    return mus, sigmas, weights / weights.sum()


def _snap(value: float, low: float, high: float, step: Optional[float], integer: bool) -> float:
    value = min(max(value, low), high)
    if step:
        # The nearest grid point, but never past the last one inside the range: when the
        # step does not divide the range, rounding up went beyond it, and the clipping
        # that followed left the value off the grid and, for an integer, a float the
        # domain rejected (F-61).
        last = math.floor((high - low) / step + 1e-9)
        value = low + min(max(round((value - low) / step), 0), last) * step
    if integer:
        return int(min(max(round(value), low), high))
    return min(max(value, low), high)


class _CategoricalModel:
    """The Parzen estimator of a categorical variable: counts plus the prior."""

    def __init__(self, categories: Sequence[Any], values: Sequence[Any], prior_weight: float) -> None:
        self.categories = list(categories)
        weights = np.array([prior_weight + sum(1 for v in values if v == category) for category in categories],
                           dtype=float)
        self.probabilities = weights / weights.sum()

    def draw(self, leaf: Leaf) -> Any:
        return self.choose()

    def choose(self) -> Any:
        """A category, drawn with the probabilities of the model."""
        return self.categories[int(get_numpy_rng().choice(len(self.categories), p=self.probabilities))]

    def log_density(self, value: Any) -> float:
        return float(np.log(self.probabilities[self.categories.index(value)]))

    def log_densities(self, values: Sequence[Any]) -> List[float]:
        return [self.log_density(value) for value in values]


class _NumericModel:
    """The adaptive Parzen estimator of an integer or real variable, truncated to its domain."""

    def __init__(self, low: float, high: float, step: Optional[float], integer: bool, values: Sequence[Any],
                 prior_weight: float, log: bool = False) -> None:
        self.low, self.high, self.step, self.integer, self.log = low, high, step, integer, log
        # On a logarithmic scale the kernels live on the logarithm; the Jacobian of the
        # change of variable is the same for l(x) and g(x), so their ratio is unchanged.
        def scale(value: float) -> float:
            return math.log(value) if log else value

        self.space_low, self.space_high = scale(low), scale(high)
        self.mus, self.sigmas, self.weights = _kernels([scale(float(v)) for v in values], self.space_low,
                                                       self.space_high, prior_weight)
        # Truncated to the domain, so a kernel spilling past the bounds does not undercount.
        self.mass = np.maximum(norm.cdf(self.space_high, self.mus, self.sigmas)
                               - norm.cdf(self.space_low, self.mus, self.sigmas), 1e-300)
        # What Generator.choice(n, p=weights) computes on every call, once: drawing with it
        # validated and accumulated the weights for every candidate (E-04). Searching a
        # uniform in it gives the same kernel and draws the same number.
        self.cumulative = self.weights.cumsum()
        self.cumulative /= self.cumulative[-1]

    def draw(self, leaf: Leaf) -> Any:
        rng = get_numpy_rng()
        component = int(self.cumulative.searchsorted(rng.random(), side="right"))
        for _ in range(20):
            drawn = rng.normal(self.mus[component], self.sigmas[component])
            if self.space_low <= drawn <= self.space_high:
                break
        else:
            drawn = min(max(drawn, self.space_low), self.space_high)
        if self.log:
            drawn = math.exp(drawn)
        return _snap(float(drawn), self.low, self.high, self.step, self.integer)

    def log_density(self, value: Any) -> float:
        return self.log_densities([value])[0]

    def log_densities(self, values: Sequence[Any]) -> List[float]:
        """The log density at every value, all in one matrix of values by kernels."""
        points = np.array([math.log(float(value)) if self.log else float(value) for value in values])
        densities = self.weights * norm.pdf(points[:, None], self.mus, self.sigmas) / self.mass
        return [float(np.log(max(total, 1e-300))) for total in densities.sum(axis=1)]


_Model = Union[_CategoricalModel, _NumericModel, SubsetModel]


ModeledLeaf = Union[Integer, Real, Categorical, Subset]


def _model(leaf: ModeledLeaf, values: Sequence[Any], prior_weight: float) -> _Model:
    """The Parzen estimator of a variable given the observed values."""
    if isinstance(leaf, Subset):
        return SubsetModel(leaf.get_definition(), values, prior_weight)
    if isinstance(leaf, Categorical):
        _, categories = leaf.get_definition().get_attributes()
        return _CategoricalModel(categories, values, prior_weight)
    low, high, step = _bounds(leaf)
    return _NumericModel(low, high, step, isinstance(leaf, Integer), values, prior_weight, log=_is_log(leaf))


def _draw(leaf: ModeledLeaf, values: Sequence[Any], prior_weight: float) -> Any:
    """One value of the variable drawn from the Parzen estimator of the given observations."""
    return _model(leaf, values, prior_weight).draw(leaf)


def _log_density(leaf: ModeledLeaf, value: Any, values: Sequence[Any], prior_weight: float) -> float:
    """Log density of a value under the Parzen estimator of the given observations."""
    return _model(leaf, values, prior_weight).log_density(value)
