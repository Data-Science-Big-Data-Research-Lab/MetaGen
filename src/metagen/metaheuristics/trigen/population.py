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
from typing import List, Optional, Sequence, Tuple

import numpy as np

from metagen.framework.rng import get_rng
from metagen.triclustering import Tricluster

#: The smallest and largest number of genes, conditions and times of a tricluster.
Sizes = Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]


class DataHierarchy:
    """
    How many of the triclusters found hold each gene, condition and time: its level.
    TriGen starts the searches after the first one from the coordinates of the lowest
    levels, the least explored, so that each search looks elsewhere.

    With ``cells``, it also counts how many triclusters found hold each cell, and the genes
    of a tricluster are drawn by the cells they have held in its conditions and times: a
    gene of a tricluster found in some times is as unexplored as any other in the rest.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param cells: Whether to count the cells too, defaults to False.
    :type cells: bool, optional
    """

    def __init__(self, shape: Sequence[int], cells: bool = False) -> None:
        self.levels: List[List[int]] = [[0] * size for size in shape]
        #: How many triclusters found hold each cell; None without ``cells``.
        self.cells: Optional[np.ndarray] = np.zeros(tuple(shape), dtype=np.int32) if cells else None

    def update(self, tricluster: Tricluster) -> None:
        """
        Count a tricluster found: each of its genes, conditions and times goes up a level.

        :param tricluster: The tricluster found.
        :type tricluster: Tricluster
        """
        for levels, positions in zip(self.levels, (tricluster.genes, tricluster.conditions, tricluster.times)):
            for position in positions:
                levels[position] += 1
        if self.cells is not None:
            self.cells[tricluster.cell_index()] += 1

    def draw(self, dimension: int, size: int) -> List[int]:
        """
        ``size`` positions of a dimension, the lowest levels first: a level with fewer
        positions than are still missing goes in whole, and from the level that has more
        they are drawn at random.

        :param dimension: 0 for the genes, 1 for the conditions, 2 for the times.
        :type dimension: int
        :param size: How many positions, at most the size of the dimension.
        :type size: int
        :return: The positions, sorted.
        :rtype: List[int]
        """
        return _lowest(self.levels[dimension], size)

    def draw_genes(self, conditions: Sequence[int], times: Sequence[int], size: int) -> List[int]:
        """
        ``size`` genes, those that the triclusters found hold the fewest cells of in some
        conditions and times first, drawn level by level as :py:meth:`draw` does. Without
        ``cells``, the genes of the lowest levels, as :py:meth:`draw` gives them.

        :param conditions: The conditions.
        :type conditions: Sequence[int]
        :param times: The times.
        :type times: Sequence[int]
        :param size: How many genes, at most the number of genes.
        :type size: int
        :return: The genes, sorted.
        :rtype: List[int]
        """
        if self.cells is None:
            return self.draw(0, size)
        held = self.cells[(slice(None),) + np.ix_(list(conditions), list(times))].sum(axis=(1, 2))
        return _lowest([int(count) for count in held], size)


def _lowest(levels: Sequence[int], size: int) -> List[int]:
    """``size`` positions, the lowest levels first: a level with fewer positions than are
    still missing goes in whole, and from the level that has more they are drawn at random."""
    chosen: List[int] = []
    for level in sorted(set(levels)):
        if len(chosen) == size:
            break
        at_level = [position for position, count in enumerate(levels) if count == level]
        missing = size - len(chosen)
        chosen.extend(at_level if len(at_level) <= missing else get_rng().sample(at_level, missing))
    return sorted(chosen)


def _tricluster(parts: Sequence[Sequence[int]]) -> Tricluster:
    genes, conditions, times = parts
    return Tricluster(genes, conditions, times)


def _size(bounds: Tuple[int, int]) -> int:
    return get_rng().randint(bounds[0], bounds[1])


def scattered(shape: Sequence[int], sizes: Sizes) -> Tricluster:
    """
    A tricluster drawn at random: in each dimension, a size between its bounds, both
    included, and that many positions from the whole dimension.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The tricluster.
    :rtype: Tricluster
    """
    return _tricluster([get_rng().sample(range(length), _size(bounds)) for length, bounds in zip(shape, sizes)])


def block(shape: Sequence[int], sizes: Sizes) -> Tricluster:
    """
    A tricluster of consecutive positions in each dimension: a size between its bounds and
    a start drawn uniformly among those that fit, so that every window of that size is as
    likely.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The tricluster.
    :rtype: Tricluster
    """
    windows: List[range] = []
    for length, bounds in zip(shape, sizes):
        size = _size(bounds)
        start = get_rng().randint(0, length - size)
        windows.append(range(start, start + size))
    return _tricluster(windows)


def hierarchical(hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
    """
    A tricluster from the least explored coordinates: a size between its bounds in each
    dimension and that many positions of the lowest levels of the data hierarchy. With a
    hierarchy of cells, the conditions and times are drawn first, and then the genes that
    the triclusters found hold the fewest cells of in them.

    :param hierarchy: The data hierarchy.
    :type hierarchy: DataHierarchy
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The tricluster.
    :rtype: Tricluster
    """
    if hierarchy.cells is None:
        return _tricluster([hierarchy.draw(dimension, _size(bounds)) for dimension, bounds in enumerate(sizes)])
    genes = _size(sizes[0])
    conditions = hierarchy.draw(1, _size(sizes[1]))
    times = hierarchy.draw(2, _size(sizes[2]))
    return Tricluster(hierarchy.draw_genes(conditions, times, genes), conditions, times)


def initial_population(shape: Sequence[int], sizes: Sizes, hierarchy: DataHierarchy, first: bool,
                       population_size: int, random_fraction: float) -> List[Tricluster]:
    """
    The triclusters a search starts from. The first search starts half from scattered
    triclusters and half from blocks of consecutive positions. Each later search draws
    ``floor(random_fraction · population_size)`` of them that way, half and half, and the
    rest from the data hierarchy.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :param hierarchy: The data hierarchy.
    :type hierarchy: DataHierarchy
    :param first: Whether this is the first search.
    :type first: bool
    :param population_size: How many triclusters.
    :type population_size: int
    :param random_fraction: The share drawn without the hierarchy in later searches.
    :type random_fraction: float
    :return: The triclusters, scattered first, then blocks, then hierarchical.
    :rtype: List[Tricluster]
    """
    unguided = population_size if first else exact_floor(random_fraction, population_size)
    scattered_count = unguided // 2
    population = [scattered(shape, sizes) for _ in range(scattered_count)]
    population += [block(shape, sizes) for _ in range(unguided - scattered_count)]
    population += [hierarchical(hierarchy, sizes) for _ in range(population_size - unguided)]
    return population


def exact_floor(fraction: float, count: int) -> int:
    """
    ``floor(fraction · count)`` without the rounding of floating point: 0.29 · 100 is
    28.999999999999996 as a float, and a plain ``int`` would give 28.

    :param fraction: A fraction.
    :type fraction: float
    :param count: A count.
    :type count: int
    :return: The largest integer not above their product.
    :rtype: int
    """
    # A product that rounding left a hair below an integer is that integer; no fraction
    # written with a sensible number of decimals comes that close to one without being it.
    return math.floor(fraction * count + 1e-9)
