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
import numbers
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Tuple

from metagen.triclustering.cube import AXES

if TYPE_CHECKING:
    from metagen.framework import Solution
    from metagen.triclustering.cube import Cube


@dataclass(frozen=True, init=False)
class Tricluster:
    """
    A tricluster: a subset of the genes, one of the conditions and one of the times of
    a cube, given by their positions, at least two of each. Each is kept sorted, in the
    order of the cube, whatever the order it was given in, and none may repeat.

    Two triclusters are equal when they hold the same positions; the fitness, if any,
    does not count.

    .. code-block:: python

        from metagen.triclustering import Tricluster

        tricluster = Tricluster(genes=[17, 3, 42], conditions=[2, 0], times=[1, 2, 3])
        print(tricluster.genes, tricluster.size)            # (3, 17, 42) (3, 2, 3)

    :param genes: The positions of its genes.
    :type genes: Iterable[int]
    :param conditions: The positions of its conditions.
    :type conditions: Iterable[int]
    :param times: The positions of its times.
    :type times: Iterable[int]
    :param fitness: The fitness it was found with, if any.
    :type fitness: float, optional
    :raises ValueError: if a position is not a non-negative integer or repeats, or a
        dimension has fewer than two.
    """

    genes: Tuple[int, ...]
    conditions: Tuple[int, ...]
    times: Tuple[int, ...]
    fitness: Optional[float] = field(default=None, compare=False)

    def __init__(self, genes: Iterable[int], conditions: Iterable[int], times: Iterable[int],
                 fitness: Optional[float] = None) -> None:
        for axis, given in zip(AXES, (genes, conditions, times)):
            object.__setattr__(self, axis, _positions(axis, given))
        object.__setattr__(self, "fitness", None if fitness is None else float(fitness))

    @classmethod
    def from_solution(cls, solution: Solution) -> Tricluster:
        """
        The tricluster a solution stands for: one with the variables ``genes``,
        ``conditions`` and ``times``, each a subset of the positions of that dimension.
        Its fitness comes along if the solution has been evaluated.

        :param solution: The solution.
        :type solution: Solution
        :return: The tricluster.
        :rtype: Tricluster
        """
        fitness = solution.get_fitness()
        return cls(solution["genes"], solution["conditions"], solution["times"],
                   fitness if math.isfinite(fitness) else None)

    @property
    def size(self) -> Tuple[int, int, int]:
        """The number of its genes, conditions and times."""
        return len(self.genes), len(self.conditions), len(self.times)

    def check(self, cube: Cube) -> None:
        """
        Check that the tricluster fits in a cube: every position within the cube.

        :param cube: The cube.
        :type cube: Cube
        :raises ValueError: if it does not fit.
        """
        for axis, positions, size in zip(AXES, (self.genes, self.conditions, self.times), cube.shape):
            if positions[-1] >= size:
                raise ValueError(f"The {axis} {[p for p in positions if p >= size]} are beyond the "
                                 f"{size} {axis} of the cube.")

    def labels(self, cube: Cube) -> Dict[str, Tuple[Any, ...]]:
        """
        The names of its genes, conditions and times in a cube.

        :param cube: The cube.
        :type cube: Cube
        :return: A dictionary with the keys ``"genes"``, ``"conditions"`` and ``"times"``.
        :rtype: dict
        """
        self.check(cube)
        return {axis: tuple(names[position] for position in positions)
                for axis, names, positions in zip(AXES, (cube.genes, cube.conditions, cube.times),
                                                  (self.genes, self.conditions, self.times))}


def _positions(axis: str, given: Iterable[int]) -> Tuple[int, ...]:
    positions: List[int] = []
    try:
        items = list(given)
    except TypeError:
        raise ValueError(f"The {axis} of a tricluster must be a collection of positions, not {given!r}.") from None
    for position in items:
        if isinstance(position, bool) or not isinstance(position, numbers.Integral) or position < 0:
            raise ValueError(f"The {axis} of a tricluster must be non-negative integer positions, "
                             f"not {position!r}.")
        positions.append(int(position))
    if len(set(positions)) != len(positions):
        raise ValueError(f"The {axis} of a tricluster repeat: {positions}.")
    if len(positions) < 2:
        raise ValueError(f"A tricluster needs at least two {axis}, not {len(positions)}.")
    return tuple(sorted(positions))
