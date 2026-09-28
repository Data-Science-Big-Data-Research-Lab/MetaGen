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
from typing import Any, List, Sequence

import numpy as np

from metagen.framework.domain import SubsetDefinition
from metagen.framework.rng import get_numpy_rng

#: How far from 0 and 1 an inclusion probability is kept, so that a log never meets 0.
_EDGE = 1e-12


class SubsetModel:
    """
    The model TPE and KernelTPE fit to a subset variable: for each element, the
    probability that it is in the selection, estimated from the observed selections
    together with a prior worth ``prior_weight`` observations. The prior puts every
    element in with the same probability, the one that keeps the mean size of the
    observed selections: their mean size over the number of elements, or, before any
    observation, the middle of the sizes over it.

    :param definition: The definition of the subset.
    :type definition: SubsetDefinition
    :param selections: The observed selections, each a list of elements.
    :type selections: Sequence[Sequence[Any]]
    :param prior_weight: Weight of the prior against one observation.
    :type prior_weight: float
    """

    def __init__(self, definition: SubsetDefinition, selections: Sequence[Sequence[Any]],
                 prior_weight: float) -> None:
        self.definition = definition
        _, self.elements, self.min_size, self.max_size = definition.get_attributes()
        size = len(self.elements)
        counts = np.zeros(size)
        for selection in selections:
            for element in selection:
                counts[definition.position(element)] += 1
        # The prior keeps the size of what was observed: centered on the middle of the
        # sizes instead, a selection with no maximum would take in half the elements
        # it never saw, hundreds of them among thousands.
        mean_size = counts.sum() / len(selections) if selections else (self.min_size + self.max_size) / 2.0
        prior = mean_size / size
        total = len(selections) + prior_weight
        inclusion = (counts + prior_weight * prior) / total if total > 0 else np.full(size, prior)
        self.inclusion: np.ndarray = np.clip(inclusion, _EDGE, 1.0 - _EDGE)

    def draw(self, leaf: Any = None) -> List[Any]:
        """
        A selection drawn from the model: every element in with its probability, and
        then brought within the sizes, adding elements drawn in proportion to their
        probability of being in, or removing them in proportion to their probability
        of being out.

        :param leaf: Not used; taken so that every model of KernelTPE draws alike.
        :return: The selection, in the order of the elements.
        :rtype: list
        """
        rng = get_numpy_rng()
        chosen = rng.random(len(self.elements)) < self.inclusion
        count = int(chosen.sum())
        if count < self.min_size:
            outside = np.flatnonzero(~chosen)
            weights = self.inclusion[outside]
            added = rng.choice(outside, size=self.min_size - count, replace=False, p=weights / weights.sum())
            chosen[added] = True
        elif count > self.max_size:
            inside = np.flatnonzero(chosen)
            weights = 1.0 - self.inclusion[inside]
            removed = rng.choice(inside, size=count - self.max_size, replace=False, p=weights / weights.sum())
            chosen[removed] = False
        return [self.elements[position] for position in np.flatnonzero(chosen)]

    def log_density(self, selection: Sequence[Any]) -> float:
        """
        Log probability of a selection under the model, each element in or out on its
        own. It leaves out the sizes: keeping to them divides the probability of every
        allowed selection by the same number, so the ratio of two models ranks the
        candidates the same with it or without it.

        :param selection: A selection, as a list of elements.
        :return: Its log probability.
        :rtype: float
        """
        chosen = np.zeros(len(self.elements), dtype=bool)
        chosen[[self.definition.position(element) for element in selection]] = True
        return float(np.log(np.where(chosen, self.inclusion, 1.0 - self.inclusion)).sum())
