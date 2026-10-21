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

from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Sequence, Tuple

import numpy as np

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_numpy_rng
from metagen.metaheuristics.genetic.genetic_tools import GAConnector
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes, block, hierarchical, scattered
from metagen.triclustering import Tricluster
from metagen.triclustering.cube import AXES


class Shape(ABC):
    """
    What a kind of tricluster is to TriGen: how a search represents it, crosses and
    mutates it (the domain of its genetic algorithm), how it draws the triclusters a search
    starts from, how a tricluster found grows, and how the model of chance of the
    significance draws random ones. The rest of TriGen, the memory of what was found, the
    overlap and the hierarchy, works on the cells of a tricluster, whatever its shape.
    """

    #: The name of the shape, as ``TriGen(shape=...)`` takes it.
    name: str

    @abstractmethod
    def domain(self, shape: Sequence[int], sizes: Sizes) -> Domain:
        """The search space of a tricluster of a cube of a shape, between the sizes."""

    @abstractmethod
    def to_solution(self, tricluster: Tricluster, domain: Domain) -> Solution:
        """The solution of the domain that stands for a tricluster."""

    @abstractmethod
    def from_solution(self, solution: Solution) -> Tricluster:
        """The tricluster a solution of the domain stands for."""

    @abstractmethod
    def scattered(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        """A tricluster drawn at random over the whole cube."""

    @abstractmethod
    def block(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        """A tricluster of neighboring positions, drawn at random."""

    @abstractmethod
    def hierarchical(self, hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
        """A tricluster drawn from what the triclusters found have explored least."""

    @abstractmethod
    def grow(self, tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
             shape: Tuple[int, int, int], pruning: bool = False,
             adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None
             ) -> Tuple[Tricluster, int]:
        """The tricluster grown, and how many triclusters were scored; see :py:func:`grow`."""

    @abstractmethod
    def chance(self, shape: Sequence[int], size: Sequence[int]) -> Tricluster:
        """A random tricluster of a size, for the model of chance, drawn with MetaGen's NumPy
        generator."""

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and vars(self) == vars(other)

    def __hash__(self) -> int:
        return hash(type(self))

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class CubeShape(Shape):
    """
    The cube: every combination of some genes, some conditions and some times, each a
    subset of the positions of its dimension.
    """

    name = "cube"

    def domain(self, shape: Sequence[int], sizes: Sizes) -> Domain:
        return tricluster_domain(shape, sizes)

    def to_solution(self, tricluster: Tricluster, domain: Domain) -> Solution:
        solution = solution_class(domain)(domain, connector=domain.get_connector())
        solution.set("genes", list(tricluster.genes))
        solution.set("conditions", list(tricluster.conditions))
        solution.set("times", list(tricluster.times))
        return solution

    def from_solution(self, solution: Solution) -> Tricluster:
        return Tricluster(solution["genes"], solution["conditions"], solution["times"])

    def scattered(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        return scattered(shape, sizes)

    def block(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        return block(shape, sizes)

    def hierarchical(self, hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
        return hierarchical(hierarchy, sizes)

    def grow(self, tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
             shape: Tuple[int, int, int], pruning: bool = False,
             adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None
             ) -> Tuple[Tricluster, int]:
        return grow(tricluster, score, sizes, shape, pruning=pruning, adding_genes=adding_genes)

    def chance(self, shape: Sequence[int], size: Sequence[int]) -> Tricluster:
        rng = get_numpy_rng()
        genes, conditions, times = (rng.choice(extent, count, replace=False) for extent, count in zip(shape, size))
        return Tricluster(genes, conditions, times)


#: The shapes TriGen knows, by name.
SHAPES = {CubeShape.name: CubeShape}


def shape_named(name: str) -> Shape:
    """
    The shape of a name.

    :param name: Its name, such as ``"cube"``.
    :type name: str
    :return: The shape.
    :rtype: Shape
    :raises ValueError: if no shape has that name.
    """
    if name not in SHAPES:
        raise ValueError(f"shape is one of {sorted(SHAPES)}, not {name!r}.")
    return SHAPES[name]()


def tricluster_domain(shape: Sequence[int], sizes: Sizes) -> Domain:
    """
    The search space of a tricluster: three subsets, of the genes, the conditions and the
    times of a cube, each between its smallest and largest size.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The domain, with the connector of the genetic algorithms.
    :rtype: Domain
    """
    domain = Domain(GAConnector())
    for axis, length, (smallest, largest) in zip(AXES, shape, sizes):
        domain.define_subset(axis, list(range(length)), smallest, largest)
    return domain


def grow(tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
         shape: Tuple[int, int, int], pruning: bool = False,
         adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None) -> Tuple[Tricluster, int]:
    """
    Grow a tricluster one coordinate at a time: at each step, the gene, condition or time,
    of a dimension below its largest size, that leaves the score lowest, as long as that
    score is no higher than the current one. Ties go to the first dimension, then to the
    first position.

    With ``pruning``, each step also weighs removing a gene, condition or time from a
    dimension above its smallest size, takes the addition or removal that leaves the score
    lowest, and stops when none leaves it lower than the current one.

    :param tricluster: The tricluster to grow.
    :type tricluster: Tricluster
    :param score: What to keep low, the lower the better.
    :type score: Callable[[Tricluster], float]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :param shape: The shape of the cube.
    :type shape: Tuple[int, int, int]
    :param pruning: Whether a step may remove a coordinate, defaults to False.
    :type pruning: bool, optional
    :param adding_genes: What scores the tricluster with each of many genes added at once,
        the same, but for rounding, as ``score`` on each, such as
        :py:meth:`TriclusterFitness.adding_genes`; when it gives None, or without it, each
        is scored with ``score``.
    :type adding_genes: Callable, optional
    :return: The grown tricluster, and how many triclusters were scored.
    :rtype: Tuple[Tricluster, int]
    """
    parts = [list(tricluster.genes), list(tricluster.conditions), list(tricluster.times)]
    current = score(tricluster)
    evaluations = 1
    while True:
        best: Optional[Tuple[float, int, List[int]]] = None
        for dimension in range(3):
            low, high = sizes[dimension]
            moves: List[List[int]] = []
            if len(parts[dimension]) < high:
                held = set(parts[dimension])
                additions = [position for position in range(shape[dimension]) if position not in held]
                values = (adding_genes(Tricluster(parts[0], parts[1], parts[2]), additions)
                          if dimension == 0 and adding_genes is not None and additions else None)
                if values is None:
                    moves += [parts[dimension] + [position] for position in additions]
                else:
                    # The same choice as scoring them one by one: the first lowest that qualifies.
                    evaluations += len(additions)
                    qualifies = values < current if pruning else values <= current
                    if qualifies.any():
                        index = int(np.flatnonzero(qualifies)[np.argmin(values[qualifies])])
                        if best is None or values[index] < best[0]:
                            best = (float(values[index]), dimension, parts[dimension] + [additions[index]])
            if pruning and len(parts[dimension]) > low:
                moves += [[kept for kept in parts[dimension] if kept != removed] for removed in parts[dimension]]
            for move in moves:
                trial = list(parts)
                trial[dimension] = move
                value = score(Tricluster(trial[0], trial[1], trial[2]))
                evaluations += 1
                # Without pruning, a step that leaves the score equal is taken: it only adds.
                # With pruning, only a step that lowers it, so that no step can undo another.
                better = value < current if pruning else value <= current
                if better and (best is None or value < best[0]):
                    best = (value, dimension, move)
        if best is None:
            return Tricluster(parts[0], parts[1], parts[2]), evaluations
        current = best[0]
        parts[best[1]] = best[2]
