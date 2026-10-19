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

import math
from typing import List, Optional, Sequence

import numpy as np
from scipy import stats


class Racing:
    """
    Racing: stop evaluating a candidate as soon as it is significantly worse than the
    population, as F-race and irace do (Birattari et al., GECCO 2002; López-Ibáñez et
    al., Operations Research Perspectives 2016).

    It needs a fitness function that yields its steps one at a time, such as the loss of
    each fold of a cross-validation, all of them in the same order for every solution,
    its value being their mean:

    .. code-block:: python

        def fitness(solution):
            for train, test in folds:
                yield loss_of(solution, train, test)

    Each candidate of an iteration races against the solutions of the population the
    iteration started from, whose values per step are known: after each step from
    ``first_steps`` on, a Friedman test over the candidate and those solutions, followed
    by Conover's comparison against the best of them by sum of ranks, decides whether the
    candidate is significantly worse, at level ``alpha``; if it is, it gets no more steps.
    The initial population has nothing to race against and is evaluated whole.

    A candidate stopped early is marked (``solution.raced_out``) and is never the best
    solution of a run. Its fitness is its mean over the steps it took, corrected by how
    the mean of the population changes from those steps to all of them, so that it stays
    comparable with the solutions evaluated whole.

    :param first_steps: The steps a candidate always takes before it can be stopped,
        defaults to 3.
    :type first_steps: int, optional
    :param alpha: The level of the tests, defaults to 0.05.
    :type alpha: float, optional
    :raises ValueError: if ``first_steps`` is below 2 or ``alpha`` is not between 0 and 1.
    """
    # Chosen by simulating the race on recorded runs (metagen-auditoria/optuna/racing/):
    # against the starting population, Friedman from step 3 at 0.05 lost the best value of
    # no run of 60 (an MLP with ten-fold cross-validation and a decision tree, GA,
    # RandomSearch and TPE) while skipping 21 to 49 % of the steps on the MLP; at 0.10 it
    # lost it in 3 of 60.

    def __init__(self, first_steps: int = 3, alpha: float = 0.05) -> None:
        if isinstance(first_steps, bool) or not isinstance(first_steps, int) or first_steps < 2:
            raise ValueError(f"first_steps must be an integer of at least 2, not {first_steps!r}")
        if not (0.0 < alpha < 1.0):
            raise ValueError(f"alpha must be between 0 and 1, not {alpha!r}")
        self.first_steps = first_steps
        self.alpha = alpha

    def eliminates(self, candidate: Sequence[float], population: Sequence[Sequence[float]]) -> bool:
        """
        Whether a candidate is significantly worse than the population over the steps it
        has taken.

        :param candidate: Its values so far, one per step.
        :type candidate: Sequence[float]
        :param population: The values per step of the solutions it races against, each at
            least as long as the candidate's.
        :type population: Sequence[Sequence[float]]
        :return: True if it should get no more steps.
        :rtype: bool
        """
        steps = len(candidate)
        if steps < self.first_steps or len(population) < 2:
            return False
        matrix = np.array([list(candidate)] + [list(values[:steps]) for values in population], dtype=float).T
        return worse_than_the_best(matrix, 0, self.alpha)

    def __repr__(self) -> str:
        return f"Racing(first_steps={self.first_steps}, alpha={self.alpha})"


def worse_than_the_best(matrix: np.ndarray, index: int, alpha: float) -> bool:
    """
    Friedman's test over the columns of a matrix of steps by solutions, lower is better,
    and, if it rejects, Conover's comparison of one column against the best by sum of
    ranks, as irace does.

    :param matrix: The values, one row per step and one column per solution.
    :type matrix: numpy.ndarray
    :param index: The column to judge.
    :type index: int
    :param alpha: The level of both tests.
    :type alpha: float
    :return: True if that column is significantly worse than the best one.
    :rtype: bool
    """
    blocks, k = matrix.shape
    ranks = np.apply_along_axis(stats.rankdata, 1, matrix)
    sums = ranks.sum(axis=0)
    if np.all(sums == sums[0]):
        return False
    if stats.friedmanchisquare(*matrix.T).pvalue >= alpha:
        return False
    squares = float((ranks ** 2).sum())
    spread = max(2.0 * (blocks * squares - float((sums ** 2).sum())), 0.0) / ((blocks - 1) * (k - 1))
    critical = float(stats.t.ppf(1.0 - alpha / 2.0, (blocks - 1) * (k - 1))) * math.sqrt(spread)
    return bool(sums[index] - sums.min() > critical)


def corrected_mean(partial: Sequence[float], population: Sequence[Sequence[float]]) -> float:
    """
    The fitness of a candidate stopped after some steps: its mean over them plus how much
    the mean of the population moves from those steps to all of them, so that easy or
    hard first steps do not make it look better or worse than it is.

    :param partial: The candidate's values, one per step taken.
    :type partial: Sequence[float]
    :param population: The values per step of the solutions it raced against, complete.
    :type population: Sequence[Sequence[float]]
    :return: Its estimated mean over every step.
    :rtype: float
    """
    steps = len(partial)
    shift = [float(np.mean(values)) - float(np.mean(values[:steps])) for values in population]
    return float(np.mean(partial)) + (float(np.mean(shift)) if shift else 0.0)


def complete(values: Optional[List[float]], steps: Optional[int]) -> bool:
    """Whether a solution's values per step are all there, so it can be raced against."""
    return values is not None and steps is not None and len(values) == steps
