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

from typing import Callable, Sequence, Tuple

from metagen.triclustering.tricluster import Tricluster

#: A measure of how alike a found tricluster is to a planted one, from 0 to 1.
Similarity = Callable[[Tricluster, Tricluster], float]


def _dimensions(tricluster: Tricluster) -> Tuple[set, set, set]:
    return set(tricluster.genes), set(tricluster.conditions), set(tricluster.times)


def _common_cells(first: Tricluster, second: Tricluster) -> int:
    # A cell is common when its gene, condition and time all are: the product of the
    # three intersections, without listing any cell.
    common = 1
    for mine, theirs in zip(_dimensions(first), _dimensions(second)):
        common *= len(mine & theirs)
    return common


def _cells(tricluster: Tricluster) -> int:
    genes, conditions, times = tricluster.size
    return genes * conditions * times


def cell_jaccard(first: Tricluster, second: Tricluster) -> float:
    """
    The cells two triclusters share, over the cells of either: 1 when they are the
    same, 0 when they share none.

    .. code-block:: python

        from metagen.triclustering import Tricluster, cell_jaccard

        a = Tricluster([0, 1, 2, 3], [0, 1], [0, 1])       # 16 cells
        b = Tricluster([2, 3, 4, 5], [0, 1], [0, 1])       # 16 cells, 8 of them in a
        print(cell_jaccard(a, b))                          # 0.3333333333333333

    :param first: A tricluster.
    :type first: Tricluster
    :param second: Another.
    :type second: Tricluster
    :return: Their Jaccard index over cells.
    :rtype: float
    """
    common = _common_cells(first, second)
    return common / (_cells(first) + _cells(second) - common)


def cell_recall(found: Tricluster, planted: Tricluster) -> float:
    """
    The share of the cells of a planted tricluster that a found one holds.

    :param found: The tricluster found.
    :type found: Tricluster
    :param planted: The tricluster planted.
    :type planted: Tricluster
    :return: The share, from 0 to 1.
    :rtype: float
    """
    return _common_cells(found, planted) / _cells(planted)


def cell_precision(found: Tricluster, planted: Tricluster) -> float:
    """
    The share of the cells of a found tricluster that belong to a planted one.

    :param found: The tricluster found.
    :type found: Tricluster
    :param planted: The tricluster planted.
    :type planted: Tricluster
    :return: The share, from 0 to 1.
    :rtype: float
    """
    return _common_cells(found, planted) / _cells(found)


def coordinate_jaccard(first: Tricluster, second: Tricluster) -> float:
    """
    The genes, conditions and times two triclusters share, over those of either, all
    counted together.

    :param first: A tricluster.
    :type first: Tricluster
    :param second: Another.
    :type second: Tricluster
    :return: Their Jaccard index over coordinates.
    :rtype: float
    """
    pairs = list(zip(_dimensions(first), _dimensions(second)))
    return sum(len(a & b) for a, b in pairs) / sum(len(a | b) for a, b in pairs)


def coordinate_recall(found: Tricluster, planted: Tricluster) -> float:
    """
    The share of the genes, conditions and times of a planted tricluster, all counted
    together, that a found one holds.

    :param found: The tricluster found.
    :type found: Tricluster
    :param planted: The tricluster planted.
    :type planted: Tricluster
    :return: The share, from 0 to 1.
    :rtype: float
    """
    pairs = list(zip(_dimensions(found), _dimensions(planted)))
    return sum(len(a & b) for a, b in pairs) / sum(len(b) for _, b in pairs)


def recovery(found: Sequence[Tricluster], planted: Sequence[Tricluster],
             similarity: Similarity = cell_jaccard) -> float:
    """
    How much of what was planted has been found: for each planted tricluster, its
    similarity to the most similar one found; their mean. It is 1 when every planted
    tricluster has been found exactly, and 0 when none shares anything with what was
    found or nothing was.

    .. code-block:: python

        from metagen.triclustering import Tricluster, recovery, relevance

        planted = [Tricluster([0, 1, 2], [0, 1], [0, 1]), Tricluster([5, 6], [2, 3], [2, 3])]
        found = [Tricluster([0, 1, 2], [0, 1], [0, 1]), Tricluster([8, 9], [0, 1], [0, 1])]
        print(recovery(found, planted), relevance(found, planted))   # 0.5 0.5

    :param found: The triclusters found.
    :type found: Sequence[Tricluster]
    :param planted: The triclusters planted, at least one.
    :type planted: Sequence[Tricluster]
    :param similarity: How alike a found and a planted tricluster are, from 0 to 1,
        called as ``similarity(found, planted)``; defaults to :py:func:`cell_jaccard`.
    :type similarity: Callable, optional
    :return: The recovery, from 0 to 1.
    :rtype: float
    :raises ValueError: if nothing was planted.
    """
    if not planted:
        raise ValueError("Recovery needs at least one planted tricluster.")
    return sum(max((similarity(one, target) for one in found), default=0.0) for target in planted) / len(planted)


def relevance(found: Sequence[Tricluster], planted: Sequence[Tricluster],
              similarity: Similarity = cell_jaccard) -> float:
    """
    How much of what was found was planted: for each tricluster found, its similarity
    to the most similar one planted; their mean. It is 1 when everything found is
    exactly something planted. See :py:func:`recovery`.

    :param found: The triclusters found, at least one.
    :type found: Sequence[Tricluster]
    :param planted: The triclusters planted.
    :type planted: Sequence[Tricluster]
    :param similarity: How alike a found and a planted tricluster are, from 0 to 1,
        called as ``similarity(found, planted)``; defaults to :py:func:`cell_jaccard`.
    :type similarity: Callable, optional
    :return: The relevance, from 0 to 1.
    :rtype: float
    :raises ValueError: if nothing was found.
    """
    if not found:
        raise ValueError("Relevance needs at least one tricluster found.")
    return sum(max((similarity(one, target) for target in planted), default=0.0) for one in found) / len(found)
