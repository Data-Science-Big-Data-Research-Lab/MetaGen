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

from typing import TYPE_CHECKING, Any, Optional, Sequence, Tuple

import numpy as np

if TYPE_CHECKING:
    from metagen.triclustering.tricluster import Tricluster

#: The three dimensions of a cube, in the order of its axes.
AXES: Tuple[str, str, str] = ("genes", "conditions", "times")

# How many positions an error message lists per dimension before it stops.
_LISTED = 10


class Cube:
    """
    A three-dimensional dataset: a value for every gene, condition and time, such as
    the expression of a set of genes under several conditions over time. The first
    axis holds the genes, the second the conditions and the third the times. Any data
    of that shape fits: the "genes" may be places, sensors or instances, and the
    "conditions", features.

    A cube holds no missing values: gaps have to be removed or filled in before, since
    whatever stands for them, a zero for instance, would read as data. For removing
    them, :py:meth:`without_missing` drops the genes, conditions or times that hold any.
    The values cannot be changed once the cube is built.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube

        values = np.random.default_rng(0).normal(size=(30, 4, 6))
        cube = Cube(values, conditions=["a", "b", "c", "d"], times=[0, 1, 2, 4, 8, 16])
        print(cube.shape)                                   # (30, 4, 6)

    :param values: The values, with shape (genes, conditions, times).
    :type values: array-like
    :param genes: The names of the genes; their positions by default.
    :type genes: Sequence, optional
    :param conditions: The names of the conditions; their positions by default.
    :type conditions: Sequence, optional
    :param times: The names of the times; their positions by default.
    :type times: Sequence, optional
    :raises ValueError: if the values are not a three-dimensional array of numbers with
        at least two genes, two conditions and two times, if some are missing or
        infinite, or if the names do not match the shape.
    """

    def __init__(self, values: Any, genes: Optional[Sequence[Any]] = None,
                 conditions: Optional[Sequence[Any]] = None, times: Optional[Sequence[Any]] = None) -> None:
        try:
            array = np.array(values, dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ValueError(f"The values of a cube must be numbers: {error}") from None
        if array.ndim != 3:
            raise ValueError(f"The values of a cube must have three dimensions (genes, conditions, times), "
                             f"not {array.ndim}.")
        for axis, size in zip(AXES, array.shape):
            if size < 2:
                raise ValueError(f"A cube needs at least two {axis}, not {size}.")
        missing = ~np.isfinite(array)
        if missing.any():
            where = ", ".join(f"{axis} {_positions(np.flatnonzero(missing.any(axis=others)))}"
                              for axis, others in zip(AXES, ((1, 2), (0, 2), (0, 1))))
            raise ValueError(f"The cube holds {int(missing.sum())} missing or infinite values, in {where}. "
                             f"Remove them, for instance with Cube.without_missing, or fill them in first.")
        array.setflags(write=False)
        self._values = array
        self._names = tuple(_names(axis, given, size)
                            for axis, given, size in zip(AXES, (genes, conditions, times), array.shape))

    @classmethod
    def without_missing(cls, values: Any, genes: Optional[Sequence[Any]] = None,
                        conditions: Optional[Sequence[Any]] = None, times: Optional[Sequence[Any]] = None,
                        axis: str = "genes") -> Tuple[Cube, Tuple[int, ...]]:
        """
        Build a cube from values with gaps by dropping, along one axis, every position
        that holds a missing or infinite value. By default a gene with any gap goes.

        .. code-block:: python

            import numpy as np
            from metagen.triclustering import Cube

            values = np.random.default_rng(0).normal(size=(30, 4, 6))
            values[7, 2, 3] = np.nan
            cube, kept = Cube.without_missing(values)
            print(cube.shape, 7 in kept)                    # (29, 4, 6) False

        :param values: The values, with shape (genes, conditions, times).
        :type values: array-like
        :param genes: The names of the genes; their positions by default.
        :param conditions: The names of the conditions; their positions by default.
        :param times: The names of the times; their positions by default.
        :param axis: The axis to drop along: ``"genes"``, ``"conditions"`` or ``"times"``.
        :type axis: str
        :return: The cube, and the positions in the given values of what it keeps along
            that axis.
        :rtype: Tuple[Cube, Tuple[int, ...]]
        :raises ValueError: if the axis is not one of the three, or too little is left.
        """
        if axis not in AXES:
            raise ValueError(f"The axis must be one of {list(AXES)}, not {axis!r}.")
        try:
            array = np.array(values, dtype=np.float64)
        except (TypeError, ValueError) as error:
            raise ValueError(f"The values of a cube must be numbers: {error}") from None
        if array.ndim != 3:
            raise ValueError(f"The values of a cube must have three dimensions (genes, conditions, times), "
                             f"not {array.ndim}.")
        index = AXES.index(axis)
        others = tuple(other for other in range(3) if other != index)
        kept = tuple(int(position) for position in np.flatnonzero(np.isfinite(array).all(axis=others)))
        names = [genes, conditions, times]
        own = names[index]
        if own is not None:
            given = list(own)
            if len(given) != array.shape[index]:
                raise ValueError(f"There are {len(given)} names of {axis} for {array.shape[index]} {axis}.")
            names[index] = [given[position] for position in kept]
        return cls(np.take(array, kept, axis=index), *names), kept

    @property
    def values(self) -> np.ndarray:
        """The values, read-only, with shape (genes, conditions, times)."""
        return self._values

    @property
    def shape(self) -> Tuple[int, int, int]:
        """The number of genes, conditions and times."""
        genes, conditions, times = self._values.shape
        return genes, conditions, times

    @property
    def genes(self) -> Tuple[Any, ...]:
        """The names of the genes."""
        return self._names[0]

    @property
    def conditions(self) -> Tuple[Any, ...]:
        """The names of the conditions."""
        return self._names[1]

    @property
    def times(self) -> Tuple[Any, ...]:
        """The names of the times."""
        return self._names[2]

    def subcube(self, tricluster: Tricluster) -> np.ndarray:
        """
        The values of a tricluster: its genes, conditions and times, in the order of the
        cube.

        :param tricluster: The tricluster.
        :type tricluster: Tricluster
        :return: An array with shape (its genes, its conditions, its times).
        :rtype: numpy.ndarray
        :raises ValueError: if the tricluster does not fit in the cube.
        """
        tricluster.check(self)
        return self._values[np.ix_(tricluster.genes, tricluster.conditions, tricluster.times)]

    def __repr__(self) -> str:
        genes, conditions, times = self.shape
        return f"Cube({genes} genes, {conditions} conditions, {times} times)"


def _names(axis: str, given: Optional[Sequence[Any]], size: int) -> Tuple[Any, ...]:
    if given is None:
        return tuple(range(size))
    names = tuple(given)
    if len(names) != size:
        raise ValueError(f"There are {len(names)} names of {axis} for {size} {axis}.")
    return names


def _positions(positions: np.ndarray) -> str:
    shown = [int(position) for position in positions[:_LISTED]]
    return str(shown)[:-1] + (", ...]" if len(positions) > _LISTED else "]")
