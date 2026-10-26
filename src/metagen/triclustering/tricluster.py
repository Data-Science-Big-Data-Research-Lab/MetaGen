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
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import AXES

if TYPE_CHECKING:
    from metagen.framework import Solution
    from metagen.triclustering.cube import Cube

#: The cells of a tricluster: three vectors of the same length, the gene, the condition
#: and the time of each cell.
Cells = Tuple[np.ndarray, np.ndarray, np.ndarray]


class Tricluster:
    """
    A tricluster: a set of cells of a cube, each a gene, a condition and a time, given by
    their positions.

    Most triclusters are **cubes**, every combination of some genes, some conditions and
    some times, at least two of each; ``Tricluster(genes, conditions, times)`` builds one,
    and it keeps only its three lists, each sorted in the order of the cube, whatever the
    order it was given in, and none repeating. Any other set of cells is built with
    :py:meth:`from_cells`, which keeps the cells themselves; a set of cells that makes up a
    cube is kept as that cube.

    Two triclusters are equal when they hold the same cells; the fitness, if any, does not
    count. ``genes``, ``conditions`` and ``times`` are the positions a tricluster holds in
    each dimension, and ``size`` how many; for a cube, its cells are their combinations.

    .. code-block:: python

        from metagen.triclustering import Tricluster

        tricluster = Tricluster(genes=[17, 3, 42], conditions=[2, 0], times=[1, 2, 3])
        print(tricluster.genes, tricluster.size, tricluster.n_cells)    # (3, 17, 42) (3, 2, 3) 18

        steps = Tricluster.from_cells(genes=[0, 1, 2], conditions=[0, 0, 0], times=[0, 1, 2])
        print(steps.is_cube, steps.n_cells, steps.shared_cells(tricluster))    # False 3 0

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
    # A cube keeps its three lists and no cells: a cube of 500 genes, 10 conditions and 10
    # times is 520 positions and 50 000 cells, and a population of TriGen holds hundreds of
    # them (metagen-auditoria/trigen/SPEC-C5-etapa2-ventanas.md, 2.0b). Its hash is the one
    # of its three lists, as it always was: TriGen keeps the triclusters found in sets, and
    # another hash would change the order it goes through them, and with it its results.

    __slots__ = ("genes", "conditions", "times", "fitness", "_cells")

    genes: Tuple[int, ...]
    conditions: Tuple[int, ...]
    times: Tuple[int, ...]
    fitness: Optional[float]
    _cells: Optional[Cells]

    def __init__(self, genes: Iterable[int], conditions: Iterable[int], times: Iterable[int],
                 fitness: Optional[float] = None) -> None:
        for axis, given in zip(AXES, (genes, conditions, times)):
            object.__setattr__(self, axis, _positions(axis, given))
        object.__setattr__(self, "fitness", None if fitness is None else float(fitness))
        object.__setattr__(self, "_cells", None)

    @classmethod
    def from_cells(cls, genes: Iterable[int], conditions: Iterable[int], times: Iterable[int],
                   fitness: Optional[float] = None) -> Tricluster:
        """
        A tricluster of any shape, given by its cells: the gene, the condition and the
        time of each, in three sequences of the same length. If the cells make up a cube
        with at least two positions in each dimension, the tricluster is that cube.

        :param genes: The gene of each cell.
        :type genes: Iterable[int]
        :param conditions: The condition of each cell.
        :type conditions: Iterable[int]
        :param times: The time of each cell.
        :type times: Iterable[int]
        :param fitness: The fitness it was found with, if any.
        :type fitness: float, optional
        :return: The tricluster.
        :rtype: Tricluster
        :raises ValueError: if a position is not a non-negative integer, the three do not
            have the same length, a cell repeats, or there are fewer than two cells.
        """
        columns = [np.asarray(_coordinates(axis, given), dtype=np.int64)
                   for axis, given in zip(AXES, (genes, conditions, times))]
        if len({len(column) for column in columns}) != 1:
            raise ValueError(f"The cells of a tricluster need a gene, a condition and a time each, "
                             f"not {[len(column) for column in columns]} of them.")
        if len(columns[0]) < 2:
            raise ValueError(f"A tricluster needs at least two cells, not {len(columns[0])}.")
        order = np.lexsort((columns[2], columns[1], columns[0]))
        g, c, t = (column[order] for column in columns)
        if np.any((np.diff(g) == 0) & (np.diff(c) == 0) & (np.diff(t) == 0)):
            raise ValueError("The cells of a tricluster repeat.")
        return cls._from_sorted_cells(g, c, t, fitness)

    @classmethod
    def _from_sorted_cells(cls, g: np.ndarray, c: np.ndarray, t: np.ndarray,
                           fitness: Optional[float] = None) -> Tricluster:
        """:py:meth:`from_cells` for cells already checked, at least two, none repeating, and
        sorted by gene, then by condition, then by time."""
        projections = [np.unique(column) for column in (g, c, t)]
        if (all(len(positions) >= 2 for positions in projections)
                and len(g) == math.prod(len(positions) for positions in projections)):
            return cls(projections[0].tolist(), projections[1].tolist(), projections[2].tolist(), fitness=fitness)
        tricluster = cls.__new__(cls)
        for axis, positions in zip(AXES, projections):
            object.__setattr__(tricluster, axis, tuple(positions.tolist()))
        object.__setattr__(tricluster, "fitness", None if fitness is None else float(fitness))
        cells = tuple(np.ascontiguousarray(column, dtype=np.int32) for column in (g, c, t))
        for column in cells:
            column.setflags(write=False)
        object.__setattr__(tricluster, "_cells", cells)
        return tricluster

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
    def is_cube(self) -> bool:
        """Whether it is a cube: every combination of its genes, conditions and times."""
        return self._cells is None

    @property
    def size(self) -> Tuple[int, int, int]:
        """The number of its genes, conditions and times."""
        return len(self.genes), len(self.conditions), len(self.times)

    @property
    def n_cells(self) -> int:
        """The number of its cells."""
        if self._cells is None:
            return math.prod(self.size)
        return len(self._cells[0])

    def cells(self) -> Cells:
        """
        Its cells, sorted by gene, then by condition, then by time.

        :return: Three vectors of the same length: the gene, the condition and the time of
            each cell.
        :rtype: Tuple[numpy.ndarray, numpy.ndarray, numpy.ndarray]
        """
        if self._cells is not None:
            return self._cells
        grid = np.meshgrid(np.asarray(self.genes), np.asarray(self.conditions), np.asarray(self.times),
                           indexing="ij")
        g, c, t = (axis.ravel() for axis in grid)
        return g, c, t

    def cell_index(self) -> Tuple[Any, ...]:
        """
        Its cells as an index of an array the shape of a cube, to read or write them at
        once: ``values[tricluster.cell_index()]``. For a cube, the index of every
        combination of its genes, conditions and times, an array of its size; for any other
        shape, its cells, a vector.

        :return: The index.
        :rtype: tuple
        """
        if self._cells is None:
            return np.ix_(self.genes, self.conditions, self.times)
        return self._cells

    def mask(self, shape: Sequence[int]) -> np.ndarray:
        """
        Its cells as a mask over a cube of a shape.

        :param shape: The number of genes, conditions and times of the cube.
        :type shape: Sequence[int]
        :return: A boolean array of that shape, true at its cells.
        :rtype: numpy.ndarray
        :raises ValueError: if it does not fit in that shape.
        """
        self._fits(shape)
        mask = np.zeros(tuple(shape), dtype=bool)
        if self._cells is None:
            mask[np.ix_(self.genes, self.conditions, self.times)] = True
        else:
            mask[self._cells] = True
        return mask

    def shared_cells(self, other: Tricluster) -> int:
        """
        The number of cells it shares with another tricluster.

        :param other: The other tricluster.
        :type other: Tricluster
        :return: The cells both hold.
        :rtype: int
        """
        if self._cells is None and other._cells is None:
            return math.prod(len(set(mine) & set(theirs)) for mine, theirs in
                             zip((self.genes, self.conditions, self.times),
                                 (other.genes, other.conditions, other.times)))
        shape = tuple(max(mine[-1], theirs[-1]) + 1 for mine, theirs in
                      zip((self.genes, self.conditions, self.times), (other.genes, other.conditions, other.times)))
        flat = [np.ravel_multi_index(tricluster.cells(), shape) for tricluster in (self, other)]
        return int(np.intersect1d(flat[0], flat[1], assume_unique=True).size)

    def require_cube(self, what: str) -> None:
        """
        Check that it is a cube, for what is only defined on cubes.

        :param what: What needs it, for the message.
        :type what: str
        :raises ValueError: if it is not a cube.
        """
        if self._cells is not None:
            raise ValueError(f"{what} is defined for a tricluster that is a cube, every combination of "
                             f"its genes, conditions and times; this one holds {self.n_cells} of the "
                             f"{math.prod(self.size)} combinations.")

    def check(self, cube: Cube) -> None:
        """
        Check that the tricluster fits in a cube: every position within the cube.

        :param cube: The cube.
        :type cube: Cube
        :raises ValueError: if it does not fit.
        """
        self._fits(cube.shape)

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

    def _fits(self, shape: Sequence[int]) -> None:
        for axis, positions, size in zip(AXES, (self.genes, self.conditions, self.times), shape):
            if positions[-1] >= size:
                raise ValueError(f"The {axis} {[p for p in positions if p >= size]} are beyond the "
                                 f"{size} {axis} of the cube.")

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Tricluster):
            return NotImplemented
        if (self._cells is None) != (other._cells is None):
            return False      # a set of cells that makes up a cube is always kept as one
        if self._cells is None:
            return (self.genes, self.conditions, self.times) == (other.genes, other.conditions, other.times)
        assert other._cells is not None
        return all(np.array_equal(mine, theirs) for mine, theirs in zip(self._cells, other._cells))

    def __hash__(self) -> int:
        if self._cells is None:
            return hash((self.genes, self.conditions, self.times))
        return hash(tuple(column.tobytes() for column in self._cells))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"A tricluster cannot be changed: {name}.")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"A tricluster cannot be changed: {name}.")

    def __reduce__(self) -> Tuple[Any, ...]:
        if self._cells is None:
            return Tricluster, (self.genes, self.conditions, self.times, self.fitness)
        return _from_cells, (tuple(column.tolist() for column in self._cells), self.fitness)

    def __repr__(self) -> str:
        if self._cells is None:
            return (f"Tricluster(genes={self.genes!r}, conditions={self.conditions!r}, times={self.times!r}, "
                    f"fitness={self.fitness!r})")
        return f"Tricluster.from_cells({self.n_cells} cells, size={self.size!r}, fitness={self.fitness!r})"


def _from_cells(cells: Tuple[List[int], List[int], List[int]], fitness: Optional[float]) -> Tricluster:
    return Tricluster.from_cells(*cells, fitness=fitness)


def _coordinates(axis: str, given: Iterable[int]) -> List[int]:
    if isinstance(given, np.ndarray) and given.dtype.kind in "iu" and given.ndim == 1:
        if given.size and int(given.min()) < 0:
            raise ValueError(f"The {axis} of a tricluster must be non-negative integer positions.")
        return given.tolist()
    try:
        items = list(given)
    except TypeError:
        raise ValueError(f"The {axis} of a tricluster must be a collection of positions, not {given!r}.") from None
    positions: List[int] = []
    for position in items:
        if type(position) is int and position >= 0:      # the common case, without the abstract check
            positions.append(position)
            continue
        if isinstance(position, bool) or not isinstance(position, numbers.Integral) or position < 0:
            raise ValueError(f"The {axis} of a tricluster must be non-negative integer positions, "
                             f"not {position!r}.")
        positions.append(int(position))
    return positions


def _positions(axis: str, given: Iterable[int]) -> Tuple[int, ...]:
    positions = _coordinates(axis, given)
    if len(set(positions)) != len(positions):
        raise ValueError(f"The {axis} of a tricluster repeat: {positions}.")
    if len(positions) < 2:
        raise ValueError(f"A tricluster needs at least two {axis}, not {len(positions)}.")
    return tuple(sorted(positions))
