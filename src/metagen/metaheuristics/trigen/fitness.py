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

import numpy as np

from metagen.framework import Solution
from metagen.framework.rng import get_numpy_rng
from metagen.triclustering import Cube, Tricluster, lsl, msl, msr3d, triq
from metagen.triclustering.cube import AXES
from metagen.triclustering.measures import Views, _msl_adding_genes
from metagen.triclustering.quality import FlatProfiles

#: The measure of coherence the fitness takes as its quality term.
Measure = Literal["msl", "lsl", "msr3d", "msr3d_normalized", "triq"]

#: What the size of a tricluster is measured against.
SizeReference = Literal["dataset", "max"]

#: How the fitness scores a tricluster: a weighted mean of its terms, or its significance.
Scoring = Literal["weighted", "significance"]

# The model of chance: the quality of random triclusters is measured at NULL_SIZES sizes
# drawn log-uniformly over every size the cube allows, NULL_SAMPLES triclusters each, and
# its mean and the logarithm of its deviation are fitted as linear in the logarithms of
# the three sizes. Measured in the phase 4c probes (metagen-auditoria/trigen/mediciones/
# sonda_significacion3.py): an error of about 0.1 deviations against 300 samples per
# size, in under a second on yeast.
NULL_SIZES = 30
NULL_SAMPLES = 60

#: The weights of the fitness: its quality, the size of each dimension and the overlap of
#: each dimension with the triclusters already found.
WEIGHTS: Mapping[str, float] = {"quality": 0.8, "genes": 0.04, "conditions": 0.03, "times": 0.03,
                                "overlap_genes": 0.04, "overlap_conditions": 0.03, "overlap_times": 0.03}

_MEASURES = ("msl", "lsl", "msr3d", "msr3d_normalized", "triq")


class TriclusterFitness:
    """
    The fitness TriGen minimizes. It scores a tricluster in one of two ways.

    **Weighted**, ``scoring="weighted"``, the default: how coherent a tricluster is, how
    small, and how much it repeats of the triclusters already found, as a weighted mean of
    seven terms,

    .. math::

        FF = \\frac{w_f Q + \\sum_X w_X \\left(1 - \\frac{|X|}{R_X}\\right)
                  + \\sum_X w_{oX} O_X}{w_f + \\sum_X w_X + \\sum_X w_{oX}}

    over the genes, the conditions and the times :math:`X`.

    - :math:`Q` is the quality: ``"msl"`` (MSL / 2π, the default), ``"lsl"`` (LSL / 2π),
      ``"msr3d"`` (MSR3D, in the units of the data squared), ``"msr3d_normalized"`` (MSR3D
      divided by the variance of the cube, so that the weights mean the same whatever the
      scale of the data) or ``"triq"`` (1 − TRIQ).
    - :math:`1 - |X| / R_X` favors larger triclusters. :math:`R_X` is the size of that
      dimension in the cube, or, with ``size_reference="max"``, the largest size allowed.
    - :math:`O_X = \\sum_{s} |X \\cap X_s| / (|X| \\cdot |S|)` is the share of its
      coordinates that the triclusters already found, :math:`S`, hold, 0 while none has
      been found: it penalizes overlap.

    The weights are 0.8 for the quality, 0.04, 0.03 and 0.03 for the sizes of the genes,
    conditions and times, and 0.04, 0.03 and 0.03 for their overlaps.

    **By significance**, ``scoring="significance"``: how unlikely the quality of the
    tricluster is among random triclusters of its same size in the cube,

    .. math::

        z = \\frac{\\mu(|G|, |C|, |T|) - Q}{\\sigma(|G|, |C|, |T|)}, \\qquad
        FF = -\\left(z(X) - \\max\\left(0, \\max_s z(X \\cap X_s)\\right)\\right),

    where :math:`\\mu` and :math:`\\sigma` are the mean and the deviation of the quality of
    random triclusters of that size, and :math:`X \\cap X_s` is the tricluster of the
    genes, conditions and times that :math:`X` shares with the tricluster found
    :math:`X_s`, left out when it shares fewer than two in a dimension. There is no size
    term and there are no weights: a part of a pattern scores lower than the whole pattern,
    because the same coherence over less data is likelier by chance, and adding coordinates
    that do not follow the pattern brings the quality back towards that of chance. Only the
    significance not already found counts: a tricluster found, or one found with other
    coordinates added, scores no better than 0, while a new pattern that only shares some
    conditions or times with one found keeps its whole score.

    The model of chance is fitted from random triclusters drawn with MetaGen's generator
    over every size the cube allows, so it does not depend on the sizes TriGen is bounded
    to; TriGen fits it at the start of each run. It follows MSL, the default quality,
    closely; with ``"msr3d"`` it can be off by a few deviations at some sizes.

    ``found`` is the list of triclusters already found; TriGen adds to it between one
    search and the next.

    It is called on a solution with three subset variables, ``genes``, ``conditions`` and
    ``times``, and on a :py:class:`~metagen.triclustering.Tricluster` with
    :py:meth:`evaluate`.

    .. code-block:: python

        from metagen.metaheuristics import TriclusterFitness
        from metagen.triclustering import Tricluster, plant

        cube, planted = plant((60, 6, 8), [(15, 3, 5)], noise=0.05, seed=0)
        fitness = TriclusterFitness(cube)
        before = fitness.evaluate(planted[0])
        fitness.found.append(planted[0])                         # now it repeats a tricluster found
        print(fitness.evaluate(planted[0]) > before)            # True

        significance = TriclusterFitness(cube, scoring="significance")
        whole, part = planted[0], Tricluster(planted[0].genes[:5], planted[0].conditions, planted[0].times)
        print(significance.significance(whole) > significance.significance(part))   # True

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
    :param scoring: ``"weighted"`` or ``"significance"``, defaults to ``"weighted"``. The
        weights and the size reference only apply to ``"weighted"``.
    :type scoring: str, optional
    :raises ValueError: if an option is unknown, the weights are not the seven, or one is
        negative or not finite, the maximum sizes are missing or do not fit the cube, or
        weights are given with ``scoring="significance"``.
    """

    def __init__(self, cube: Cube, measure: Measure = "msl", views: Views = "distinct",
                 flat_profiles: FlatProfiles = "exclude", weights: Optional[Mapping[str, float]] = None,
                 size_reference: SizeReference = "dataset", max_sizes: Optional[Sequence[int]] = None,
                 found: Optional[Sequence[Tricluster]] = None, scoring: Scoring = "weighted") -> None:
        if scoring not in ("weighted", "significance"):
            raise ValueError(f"scoring must be 'weighted' or 'significance', not {scoring!r}.")
        if scoring == "significance" and weights is not None:
            raise ValueError("The weights only apply to scoring='weighted'.")
        if measure not in _MEASURES:
            raise ValueError(f"measure must be one of {list(_MEASURES)}, not {measure!r}.")
        if views not in ("distinct", "time", "trlab"):
            raise ValueError(f"views must be one of ['distinct', 'time', 'trlab'], not {views!r}.")
        if flat_profiles not in ("exclude", "zero"):
            raise ValueError(f"flat_profiles must be 'exclude' or 'zero', not {flat_profiles!r}.")
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
        # The variance of the cube, for the normalized MSR3D; computed once, when first needed.
        self._spread: Optional[float] = None
        self.views = views
        self.flat_profiles = flat_profiles
        self.weights: Dict[str, float] = chosen
        self.references: Tuple[int, int, int] = references
        self.found: List[Tricluster] = list(found or [])
        self.scoring = scoring
        # The fitted model of chance: coefficients of the mean and of the log deviation.
        self._chance: Optional[Tuple[np.ndarray, np.ndarray]] = None
        # The coordinates of the triclusters found as sets, built again only when the
        # list changes, not on every evaluation.
        self._found_sets: Tuple[Tuple[Tricluster, ...], List[Tuple[set, set, set]]] = ((), [])

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
        if self.measure == "msr3d_normalized":
            if self._spread is None:
                self._spread = float(np.var(self.cube.values))
            return msr3d(self.cube, tricluster) / self._spread if self._spread > 0 else 0.0
        return 1.0 - triq(self.cube, tricluster, views=self.views, flat_profiles=self.flat_profiles)

    def adding_genes(self, tricluster: Tricluster, candidates: Sequence[int],
                     quality_only: bool = False) -> Optional[np.ndarray]:
        """
        The fitness, or with ``quality_only`` the quality term, of a tricluster with each
        candidate gene added to it, at once: the same, but for rounding, as evaluating each,
        and much faster for many candidates. Only for MSL; None for the other measures.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :param candidates: The genes to add, one at a time, none of them in it.
        :type candidates: Sequence[int]
        :param quality_only: Whether to give the quality term alone, defaults to False.
        :type quality_only: bool, optional
        :return: A value per candidate, in their order, or None.
        :rtype: numpy.ndarray or None
        """
        if self.measure != "msl":
            return None
        quality = _msl_adding_genes(self.cube, tricluster, candidates, views=self.views, normalized=True)
        if quality_only or len(candidates) == 0:
            return quality
        genes, conditions, times = len(tricluster.genes) + 1, len(tricluster.conditions), len(tricluster.times)
        base = self.terms(tricluster)
        positions = np.asarray(candidates, dtype=int)
        if self.scoring == "significance":
            if self._chance is None:
                self.fit_chance()
            assert self._chance is not None
            mean, deviation = self._chance
            row = np.array([1.0, math.log(genes), math.log(conditions), math.log(times)])
            z = (float(row @ mean) - quality) / float(np.exp(row @ deviation))
            fitness = -(z - base["z_found"])
            # A gene of a tricluster found changes what it shares with it: those, one by one.
            found_genes = set().union(*(set(found.genes) for found in self.found)) if self.found else set()
            for index, position in enumerate(positions):
                if int(position) in found_genes:
                    fitness[index] = self.evaluate(Tricluster(list(tricluster.genes) + [int(position)],
                                                              tricluster.conditions, tricluster.times))
            return fitness
        weights = self.weights
        found = self._sets_of_found()
        shared = sum(len(set(tricluster.genes) & sets[0]) for sets in found)
        extra = np.zeros(positions.size)
        for sets in found:
            extra += np.isin(positions, list(sets[0]))
        overlap_genes = (shared + extra) / (genes * len(found)) if found else np.zeros(positions.size)
        total = (weights["quality"] * quality
                 + weights["genes"] * (1.0 - genes / self.references[0])
                 + weights["conditions"] * (1.0 - base["conditions"]) + weights["times"] * (1.0 - base["times"])
                 + weights["overlap_genes"] * overlap_genes
                 + weights["overlap_conditions"] * base["overlap_conditions"]
                 + weights["overlap_times"] * base["overlap_times"])
        return total / sum(weights.values())

    def fit_chance(self) -> None:
        """
        Fit the model of chance of ``scoring="significance"``, drawing random triclusters
        with MetaGen's generator, so a seed set before makes it reproducible. TriGen fits it
        at the start of each run. Used on its own, the first significance asked for fits it
        if it has not been fitted; fit it before handing the fitness to an algorithm that
        evaluates in other processes, which would otherwise each fit their own.
        """
        rng = get_numpy_rng()
        shape = self.cube.shape
        sizes = [tuple(int(round(math.exp(rng.uniform(math.log(2), math.log(extent))))) for extent in shape)
                 for _ in range(NULL_SIZES)]
        means, deviations = [], []
        for size in sizes:
            values = []
            for _ in range(NULL_SAMPLES):
                genes, conditions, times = (rng.choice(extent, count, replace=False)
                                            for extent, count in zip(shape, size))
                values.append(self.quality(Tricluster(genes, conditions, times)))
            means.append(float(np.mean(values)))
            deviations.append(max(float(np.std(values)), 1e-12))
        design = np.column_stack([np.ones(len(sizes))] + [np.log([size[axis] for size in sizes]) for axis in range(3)])
        self._chance = (np.linalg.lstsq(design, np.array(means), rcond=None)[0],
                        np.linalg.lstsq(design, np.log(deviations), rcond=None)[0])

    def significance(self, tricluster: Tricluster, quality: Optional[float] = None) -> float:
        """
        How many deviations the quality of a tricluster is better than that of random
        triclusters of its same size in the cube, z: around 0 for a tricluster no better
        than chance, and higher the more unlikely its coherence is by chance.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :param quality: Its quality term, if already known.
        :type quality: float, optional
        :return: Its significance, z.
        :rtype: float
        """
        if self._chance is None:
            self.fit_chance()
        assert self._chance is not None
        mean, deviation = self._chance
        row: np.ndarray = np.array([1.0, *np.log(tricluster.size)])
        value = self.quality(tricluster) if quality is None else quality
        return (float(row @ mean) - value) / float(np.exp(row @ deviation))

    def _sets_of_found(self) -> List[Tuple[set, set, set]]:
        current = tuple(self.found)
        if current != self._found_sets[0]:
            self._found_sets = (current, [_sets(tricluster) for tricluster in current])
        return self._found_sets[1]

    def terms(self, tricluster: Tricluster) -> Dict[str, float]:
        """
        Every term of the fitness of a tricluster, unweighted, and the fitness: the quality;
        the size of each dimension as a share of its reference (``"genes"``,
        ``"conditions"``, ``"times"``); its overlap with the triclusters found in each
        dimension (``"overlap_genes"``, ...); with ``scoring="significance"``, its
        significance, ``"z"``, and the largest significance it shares with a tricluster
        found, ``"z_found"``; and ``"fitness"``.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :return: The terms by name.
        :rtype: Dict[str, float]
        """
        terms: Dict[str, float] = {"quality": self.quality(tricluster)}
        own = (tricluster.genes, tricluster.conditions, tricluster.times)
        for axis, positions, reference in zip(AXES, own, self.references):
            terms[axis] = len(positions) / reference
        found = self._sets_of_found()
        for index, (axis, positions) in enumerate(zip(AXES, own)):
            mine = set(positions)
            shared = sum(len(mine & sets[index]) for sets in found)
            terms[f"overlap_{axis}"] = shared / (len(mine) * len(found)) if found else 0.0
        if self.scoring == "significance":
            # Only what is new counts. Scaling z by the overlap instead, -z * (1 - O),
            # scored the tricluster found padded with noise better than the tricluster
            # found itself (review of 2 October 2026; SPEC-fase4c-significacion.md, §14):
            # the noise lowers O faster than it lowers z.
            terms["z"] = self.significance(tricluster, terms["quality"])
            terms["z_found"] = max([0.0] + [self.significance(shared) for shared in
                                            (_shared(tricluster, found) for found in self.found)
                                            if shared is not None])
            terms["fitness"] = -(terms["z"] - terms["z_found"])
            return terms
        weights = self.weights
        total = (weights["quality"] * terms["quality"]
                 + sum(weights[axis] * (1.0 - terms[axis]) for axis in AXES)
                 + sum(weights[f"overlap_{axis}"] * terms[f"overlap_{axis}"] for axis in AXES))
        terms["fitness"] = total / sum(weights.values())
        return terms


def _shared(tricluster: Tricluster, other: Tricluster) -> Optional[Tricluster]:
    """The tricluster of the coordinates two triclusters share, or None if they share
    fewer than two in a dimension."""
    genes, conditions, times = (sorted(set(mine) & set(theirs)) for mine, theirs in
                                zip((tricluster.genes, tricluster.conditions, tricluster.times),
                                    (other.genes, other.conditions, other.times)))
    if min(len(genes), len(conditions), len(times)) < 2:
        return None
    return Tricluster(genes, conditions, times)


def _sets(tricluster: Tricluster) -> Tuple[set, set, set]:
    return set(tricluster.genes), set(tricluster.conditions), set(tricluster.times)


def _three(sizes: Sequence[int]) -> Tuple[int, int, int]:
    values = tuple(int(size) for size in sizes)
    if len(values) != 3:
        raise ValueError(f"Give one size per dimension ({', '.join(AXES)}), not {sizes!r}.")
    first, second, third = values
    return first, second, third
