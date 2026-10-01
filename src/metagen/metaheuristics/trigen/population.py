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
from typing import List, Sequence, Tuple

from metagen.framework.rng import get_rng
from metagen.triclustering import Tricluster

#: The smallest and largest number of genes, conditions and times of a tricluster.
Sizes = Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int]]


class DataHierarchy:
    """
    How many of the triclusters found hold each gene, condition and time: its level.
    TriGen starts the searches after the first one from the coordinates of the lowest
    levels, the least explored, so that each search looks elsewhere.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    """

    def __init__(self, shape: Sequence[int]) -> None:
        self.levels: List[List[int]] = [[0] * size for size in shape]

    def update(self, tricluster: Tricluster) -> None:
        """
        Count a tricluster found: each of its genes, conditions and times goes up a level.

        :param tricluster: The tricluster found.
        :type tricluster: Tricluster
        """
        for levels, positions in zip(self.levels, (tricluster.genes, tricluster.conditions, tricluster.times)):
            for position in positions:
                levels[position] += 1

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
        levels = self.levels[dimension]
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
    dimension and that many positions of the lowest levels of the data hierarchy.

    :param hierarchy: The data hierarchy.
    :type hierarchy: DataHierarchy
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The tricluster.
    :rtype: Tricluster
    """
    return _tricluster([hierarchy.draw(dimension, _size(bounds)) for dimension, bounds in enumerate(sizes)])


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
