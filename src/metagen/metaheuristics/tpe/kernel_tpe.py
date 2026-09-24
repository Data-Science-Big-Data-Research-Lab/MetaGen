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
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, cast

import numpy as np
from scipy.stats import norm

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_numpy_rng
from metagen.framework.solution.types import Categorical, Integer, Real, Structure
from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma
from metagen.metaheuristics.tools import solution_class
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
      counts, with the prior adding one to every category.
    - **Candidates are drawn from the model of the best solutions**, ``n_candidates``
      of them per iteration, **and only the one that maximizes** ``l(x) / g(x)``, the
      ratio of the densities under the best and the rest, **is evaluated**: one
      evaluation per iteration.

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
    :param max_iterations: Iterations to run, one evaluation each, defaults to 100
    :type max_iterations: int, optional
    :param warmup_iterations: Rounds of random exploration before the search, each
        evaluating ``population_size`` solutions, defaults to 5
    :type warmup_iterations: int, optional
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
    :param distributed: Whether to run on Ray, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed for MetaGen's generators, defaults to None
    :type seed: int or None, optional
    :param distribution_model: ``"global"`` or ``"islands"``; see
        :py:class:`~metagen.metaheuristics.base.Metaheuristic`
    :type distribution_model: str, optional

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

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 max_iterations: int = 100, warmup_iterations: int = 5, n_candidates: int = 24,
                 prior_weight: float = 1.0, gamma_config: Optional[GammaConfig] = None,
                 population_size: int = 20, distributed: bool = False, log_dir: Optional[str] = None,
                 seed: Optional[int] = None, distribution_model: str = "global") -> None:
        super().__init__(domain, fitness_function, max_iterations=max_iterations,
                         warmup_iterations=warmup_iterations, candidate_pool_size=1, gamma_config=gamma_config,
                         distributed=distributed, log_dir=log_dir, seed=seed, population_size=population_size,
                         distribution_model=distribution_model)
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

        :param best_solutions: The best fraction of the history, the observations of ``l``.
        :type best_solutions: List[Solution]
        :param worst_solutions: The rest of the history, the observations of ``g``.
        :type worst_solutions: List[Solution]
        :return: The candidate to evaluate, unevaluated.
        :rtype: Solution
        """
        good = _observations(best_solutions)
        bad = _observations(worst_solutions)
        # One model per variable and side, shared by every candidate: building the
        # kernels once here instead of once per candidate costs 24 times less and
        # draws the same numbers in the same order.
        models: Dict[Path, Tuple[_Model, _Model]] = {}
        solution_type = solution_class(self.domain)
        best_candidate: Optional[Solution] = None
        best_score = -math.inf
        for _ in range(self.n_candidates):
            candidate = solution_type(self.domain, connector=self.domain.get_connector())
            drawn = []
            for path, leaf in _leaves(candidate):
                if path not in good:
                    continue
                if path not in models:
                    models[path] = (_model(leaf, good[path], self.prior_weight),
                                    _model(leaf, bad.get(path, []), self.prior_weight))
                model_good, model_bad = models[path]
                value = model_good.draw(leaf)
                leaf.set(value)
                drawn.append((path, value, model_good, model_bad))
            # Scored once every variable is drawn, so that a conditional variable counts
            # only when the value drawn for the one it depends on makes it active.
            score = 0.0
            for path, value, model_good, model_bad in drawn:
                if candidate.is_active(cast(str, path[0])):
                    score += model_good.log_density(value) - model_bad.log_density(value)
            if score > best_score:
                best_candidate, best_score = candidate, score
        assert best_candidate is not None
        return best_candidate


Leaf = Union[Integer, Real, Categorical]


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
    if isinstance(value, (Integer, Real, Categorical)):
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
        value = low + round((value - low) / step) * step
    if integer:
        value = round(value)
    return min(max(value, low), high)


class _CategoricalModel:
    """The Parzen estimator of a categorical variable: counts plus the prior."""

    def __init__(self, categories: Sequence[Any], values: Sequence[Any], prior_weight: float) -> None:
        self.categories = list(categories)
        weights = np.array([prior_weight + sum(1 for v in values if v == category) for category in categories],
                           dtype=float)
        self.probabilities = weights / weights.sum()

    def draw(self, leaf: Leaf) -> Any:
        return self.categories[int(get_numpy_rng().choice(len(self.categories), p=self.probabilities))]

    def log_density(self, value: Any) -> float:
        return float(np.log(self.probabilities[self.categories.index(value)]))


class _NumericModel:
    """The adaptive Parzen estimator of an integer or real variable, truncated to its domain."""

    def __init__(self, low: float, high: float, step: Optional[float], integer: bool, values: Sequence[Any],
                 prior_weight: float) -> None:
        self.low, self.high, self.step, self.integer = low, high, step, integer
        self.mus, self.sigmas, self.weights = _kernels([float(v) for v in values], low, high, prior_weight)
        # Truncated to the domain, so a kernel spilling past the bounds does not undercount.
        self.mass = np.maximum(norm.cdf(high, self.mus, self.sigmas) - norm.cdf(low, self.mus, self.sigmas), 1e-300)

    def draw(self, leaf: Leaf) -> Any:
        rng = get_numpy_rng()
        component = int(rng.choice(len(self.mus), p=self.weights))
        for _ in range(20):
            drawn = rng.normal(self.mus[component], self.sigmas[component])
            if self.low <= drawn <= self.high:
                break
        else:
            drawn = min(max(drawn, self.low), self.high)
        return _snap(float(drawn), self.low, self.high, self.step, self.integer)

    def log_density(self, value: Any) -> float:
        densities = self.weights * norm.pdf(float(value), self.mus, self.sigmas) / self.mass
        return float(np.log(max(densities.sum(), 1e-300)))


_Model = Union[_CategoricalModel, _NumericModel]


def _model(leaf: Leaf, values: Sequence[Any], prior_weight: float) -> _Model:
    """The Parzen estimator of a variable given the observed values."""
    if isinstance(leaf, Categorical):
        _, categories = leaf.get_definition().get_attributes()
        return _CategoricalModel(categories, values, prior_weight)
    low, high, step = _bounds(leaf)
    return _NumericModel(low, high, step, isinstance(leaf, Integer), values, prior_weight)


def _draw(leaf: Leaf, values: Sequence[Any], prior_weight: float) -> Any:
    """One value of the variable drawn from the Parzen estimator of the given observations."""
    return _model(leaf, values, prior_weight).draw(leaf)


def _log_density(leaf: Leaf, value: Any, values: Sequence[Any], prior_weight: float) -> float:
    """Log density of a value under the Parzen estimator of the given observations."""
    return _model(leaf, values, prior_weight).log_density(value)
