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
from typing import Dict, List, Literal, Mapping, Optional, Sequence, Tuple

from metagen.framework import Solution
from metagen.triclustering import Cube, Tricluster, lsl, msl, msr3d, triq
from metagen.triclustering.cube import AXES
from metagen.triclustering.measures import Views
from metagen.triclustering.quality import FlatProfiles

#: The measure of coherence the fitness takes as its quality term.
Measure = Literal["msl", "lsl", "msr3d", "triq"]

#: What the size of a tricluster is measured against.
SizeReference = Literal["dataset", "max"]

#: The weights of the fitness: its quality, the size of each dimension and the overlap of
#: each dimension with the triclusters already found.
WEIGHTS: Mapping[str, float] = {"quality": 0.8, "genes": 0.04, "conditions": 0.03, "times": 0.03,
                                "overlap_genes": 0.04, "overlap_conditions": 0.03, "overlap_times": 0.03}

_MEASURES = ("msl", "lsl", "msr3d", "triq")


class TriclusterFitness:
    """
    The fitness TriGen minimizes: how coherent a tricluster is, how small, and how much it
    repeats of the triclusters already found, as a weighted mean of seven terms,

    .. math::

        FF = \\frac{w_f Q + \\sum_X w_X \\left(1 - \\frac{|X|}{R_X}\\right)
                  + \\sum_X w_{oX} O_X}{w_f + \\sum_X w_X + \\sum_X w_{oX}}

    over the genes, the conditions and the times :math:`X`.

    - :math:`Q` is the quality: ``"msl"`` (MSL / 2π, the default), ``"lsl"`` (LSL / 2π),
      ``"msr3d"`` (MSR3D, in the units of the data squared) or ``"triq"`` (1 − TRIQ).
    - :math:`1 - |X| / R_X` favors larger triclusters. :math:`R_X` is the size of that
      dimension in the cube, or, with ``size_reference="max"``, the largest size allowed.
    - :math:`O_X = \\sum_{s} |X \\cap X_s| / (|X| \\cdot |S|)` is the share of its
      coordinates that the triclusters already found, :math:`S`, hold, 0 while none has
      been found: it penalizes overlap.

    The weights are 0.8 for the quality, 0.04, 0.03 and 0.03 for the sizes of the genes,
    conditions and times, and 0.04, 0.03 and 0.03 for their overlaps. ``found`` is the list
    of triclusters already found; TriGen adds to it between one search and the next.

    It is called on a solution with three subset variables, ``genes``, ``conditions`` and
    ``times``, and on a :py:class:`~metagen.triclustering.Tricluster` with
    :py:meth:`evaluate`.

    .. code-block:: python

        from metagen.metaheuristics import TriclusterFitness
        from metagen.triclustering import plant

        cube, planted = plant((60, 6, 8), [(15, 3, 5)], noise=0.05, seed=0)
        fitness = TriclusterFitness(cube)
        before = fitness.evaluate(planted[0])
        fitness.found.append(planted[0])
        print(fitness.evaluate(planted[0]) > before)            # True: it now repeats a found one

    :param cube: The data.
    :type cube: Cube
    :param measure: The quality term, defaults to ``"msl"``.
    :type measure: str, optional
    :param views: The views of MSL, LSL and TRIQ, defaults to ``"distinct"``.
    :type views: str, optional
    :param flat_profiles: How TRIQ's correlations treat flat profiles, defaults to ``"exclude"``.
    :type flat_profiles: str, optional
    :param weights: The weights, by the names ``"quality"``, ``"genes"``, ``"conditions"``,
        ``"times"``, ``"overlap_genes"``, ``"overlap_conditions"`` and ``"overlap_times"``;
        they need not add up to 1.
    :type weights: Mapping[str, float], optional
    :param size_reference: ``"dataset"`` or ``"max"``, defaults to ``"dataset"``.
    :type size_reference: str, optional
    :param max_sizes: The largest number of genes, conditions and times a tricluster may
        have; needed with ``size_reference="max"``.
    :type max_sizes: Sequence[int], optional
    :param found: The triclusters already found, defaults to none.
    :type found: Sequence[Tricluster], optional
    :raises ValueError: if an option is unknown, the weights are not the seven, or one is
        negative or not finite, or the maximum sizes are missing or do not fit the cube.
    """

    def __init__(self, cube: Cube, measure: Measure = "msl", views: Views = "distinct",
                 flat_profiles: FlatProfiles = "exclude", weights: Optional[Mapping[str, float]] = None,
                 size_reference: SizeReference = "dataset", max_sizes: Optional[Sequence[int]] = None,
                 found: Optional[Sequence[Tricluster]] = None) -> None:
        if measure not in _MEASURES:
            raise ValueError(f"measure must be one of {list(_MEASURES)}, not {measure!r}.")
        chosen = dict(WEIGHTS if weights is None else weights)
        if set(chosen) != set(WEIGHTS):
            raise ValueError(f"The weights must be for {sorted(WEIGHTS)}, not {sorted(chosen)}.")
        if not all(math.isfinite(weight) and weight >= 0 for weight in chosen.values()) \
                or sum(chosen.values()) <= 0:
            raise ValueError(f"The weights must be finite, not negative, and not all zero: {chosen}.")
        if size_reference == "dataset":
            references = cube.shape
        elif size_reference == "max":
            if max_sizes is None:
                raise ValueError("size_reference='max' needs max_sizes.")
            references = _three(max_sizes)
            if any(largest < 1 or largest > size for largest, size in zip(references, cube.shape)):
                raise ValueError(f"The maximum sizes {references} do not fit a cube of shape {cube.shape}.")
        else:
            raise ValueError(f"size_reference must be 'dataset' or 'max', not {size_reference!r}.")
        self.cube = cube
        self.measure = measure
        self.views = views
        self.flat_profiles = flat_profiles
        self.weights: Dict[str, float] = chosen
        self.references: Tuple[int, int, int] = references
        self.found: List[Tricluster] = list(found or [])
        # Fails early on an unknown choice of views or of flat profiles, not mid-search.
        self.quality(Tricluster((0, 1), (0, 1), (0, 1)))

    def __call__(self, solution: Solution) -> float:
        """
        The fitness of a solution with the subset variables ``genes``, ``conditions`` and
        ``times``.

        :param solution: The solution.
        :type solution: Solution
        :return: Its fitness, the lower the better.
        :rtype: float
        """
        return self.evaluate(Tricluster(solution["genes"], solution["conditions"], solution["times"]))

    def evaluate(self, tricluster: Tricluster) -> float:
        """
        The fitness of a tricluster.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :return: Its fitness, the lower the better.
        :rtype: float
        """
        return self.terms(tricluster)["fitness"]

    def quality(self, tricluster: Tricluster) -> float:
        """
        The quality term of a tricluster, the lower the better.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :return: Its quality term.
        :rtype: float
        """
        if self.measure == "msl":
            return msl(self.cube, tricluster, views=self.views, normalized=True)
        if self.measure == "lsl":
            return lsl(self.cube, tricluster, views=self.views, normalized=True)
        if self.measure == "msr3d":
            return msr3d(self.cube, tricluster)
        return 1.0 - triq(self.cube, tricluster, views=self.views, flat_profiles=self.flat_profiles)

    def terms(self, tricluster: Tricluster) -> Dict[str, float]:
        """
        Every term of the fitness of a tricluster, unweighted, and the fitness: the quality;
        the size of each dimension as a share of its reference (``"genes"``,
        ``"conditions"``, ``"times"``); its overlap with the triclusters found in each
        dimension (``"overlap_genes"``, ...); and ``"fitness"``.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :return: The terms by name.
        :rtype: Dict[str, float]
        """
        terms: Dict[str, float] = {"quality": self.quality(tricluster)}
        own = (tricluster.genes, tricluster.conditions, tricluster.times)
        for axis, positions, reference in zip(AXES, own, self.references):
            terms[axis] = len(positions) / reference
        for index, (axis, positions) in enumerate(zip(AXES, own)):
            mine = set(positions)
            shared = sum(len(mine & set((other.genes, other.conditions, other.times)[index]))
                         for other in self.found)
            terms[f"overlap_{axis}"] = shared / (len(mine) * len(self.found)) if self.found else 0.0
        weights = self.weights
        total = (weights["quality"] * terms["quality"]
                 + sum(weights[axis] * (1.0 - terms[axis]) for axis in AXES)
                 + sum(weights[f"overlap_{axis}"] * terms[f"overlap_{axis}"] for axis in AXES))
        terms["fitness"] = total / sum(weights.values())
        return terms


def _three(sizes: Sequence[int]) -> Tuple[int, int, int]:
    values = tuple(int(size) for size in sizes)
    if len(values) != 3:
        raise ValueError(f"Give one size per dimension ({', '.join(AXES)}), not {sizes!r}.")
    first, second, third = values
    return first, second, third
