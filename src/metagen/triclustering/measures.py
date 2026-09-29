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
from typing import Callable, Dict, List, Literal, Tuple

import numpy as np

from metagen.triclustering.cube import Cube
from metagen.triclustering.tricluster import Tricluster

#: Which graphical views LSL and MSL average. See :py:func:`msl`.
Views = Literal["distinct", "time", "trlab"]

TWO_PI = 2.0 * math.pi


def msr3d(cube: Cube, tricluster: Tricluster) -> float:
    """
    The mean squared residue of a tricluster (MSR3D): how far its values are from the
    sum of the effects of their gene, condition and time, the mean of the squared
    three-way interaction residues

    .. math::

        r_{gct} = x_{gct} - x_{gc\\cdot} - x_{g\\cdot t} - x_{\\cdot ct}
                  + x_{g\\cdot\\cdot} + x_{\\cdot c\\cdot} + x_{\\cdot\\cdot t} - x_{\\cdot\\cdot\\cdot}

    where a dot stands for the mean over that dimension. It is zero for a tricluster of
    coherent values, the lower the better, and it is in the units of the data squared,
    so its scale is the data's.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, msr3d

        genes, conditions, times = np.meshgrid(np.arange(5), np.arange(3), np.arange(4), indexing="ij")
        cube = Cube(1.0 * genes + 2.0 * conditions + 0.5 * times)     # additive: no interaction
        print(round(msr3d(cube, Tricluster([0, 2, 4], [0, 1], [1, 2, 3])), 12))   # 0.0

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :return: Its mean squared residue.
    :rtype: float
    """
    values = cube.subcube(tricluster)
    residue = (values
               - values.mean(axis=2, keepdims=True) - values.mean(axis=1, keepdims=True)
               - values.mean(axis=0, keepdims=True)
               + values.mean(axis=(1, 2), keepdims=True) + values.mean(axis=(0, 2), keepdims=True)
               + values.mean(axis=(0, 1), keepdims=True)
               - values.mean())
    return float((residue ** 2).mean())


def msl(cube: Cube, tricluster: Tricluster, views: Views = "distinct", normalized: bool = False) -> float:
    """
    The multi-slope measure of a tricluster (MSL): how alike the shapes of its series
    are, read from the plots used to judge a tricluster by eye.

    A view plots the tricluster with one dimension on the X axis, another as the
    series and the third as the panels. In each series of each panel, every segment
    between two consecutive points has the angle ``arctan(Δy)``, with the points one
    unit apart, taken in ``[0, 2π)`` (a negative angle has ``2π`` added). Two series
    of the same panel, or one series in two panels, differ by the mean absolute
    difference of the angles of their segments; a view is worth the mean of those
    differences, and MSL is the mean of the views chosen:

    - ``"distinct"``, the default: the three views, with the genes, the times and the
      conditions on the X axis in turn.
    - ``"time"``: only the view with the times on the X axis, the time-series view.
    - ``"trlab"``: the view with the genes on the X axis counted twice and the one with
      the times once.

    MSL is zero when every series has the same shape, the lower the better, and it is
    in ``[0, 2π]``; ``normalized=True`` divides it by ``2π``. A slope along the genes or
    the conditions depends on the order they have in the cube: it means something when
    that order does (doses, temperatures, positions), and ``views="time"`` leaves it out
    otherwise.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, msl

        values = np.random.default_rng(0).normal(size=(10, 4, 6))
        values[:5] = np.arange(6) * 2.0 + np.arange(4)[:, None]    # five genes that rise alike
        cube = Cube(values)
        print(round(msl(cube, Tricluster(range(5), range(4), range(6)), views="time"), 12))   # 0.0
        print(msl(cube, Tricluster(range(5, 10), range(4), range(6)), views="time") > 1)     # True

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param views: The views to average, defaults to ``"distinct"``.
    :type views: str, optional
    :param normalized: Whether to divide the value by ``2π``, defaults to False.
    :type normalized: bool, optional
    :return: Its multi-slope measure.
    :rtype: float
    :raises ValueError: if ``views`` is not one of the three.
    """
    return _average(cube, tricluster, views, normalized, _segment_angles)


def lsl(cube: Cube, tricluster: Tricluster, views: Views = "distinct", normalized: bool = False) -> float:
    """
    The least-squares-lines measure of a tricluster (LSL): like :py:func:`msl`, but each
    series of each panel is summed up by the angle of its least squares line, fitted
    with the points one unit apart, instead of the angles of its segments. Two series
    differ by the absolute difference of those angles. The views, the range and the
    normalization are those of :py:func:`msl`.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, lsl

        values = np.random.default_rng(0).normal(size=(10, 4, 6))
        values[:5] = np.arange(6) * 2.0 + np.arange(5)[:, None, None]   # parallel lines
        cube = Cube(values)
        print(round(lsl(cube, Tricluster(range(5), range(4), range(6)), views="time"), 12))   # 0.0

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param views: The views to average, defaults to ``"distinct"``.
    :type views: str, optional
    :param normalized: Whether to divide the value by ``2π``, defaults to False.
    :type normalized: bool, optional
    :return: Its least-squares-lines measure.
    :rtype: float
    :raises ValueError: if ``views`` is not one of the three.
    """
    return _average(cube, tricluster, views, normalized, _line_angle)


# A view as the axes of the tricluster's (genes, conditions, times) values that become
# (series, X axis, panels).
_GENES_ON_X = (1, 0, 2)
_TIMES_ON_X = (0, 2, 1)
_CONDITIONS_ON_X = (0, 1, 2)

_VIEWS: Dict[str, List[Tuple[Tuple[int, int, int], float]]] = {
    "distinct": [(_GENES_ON_X, 1.0), (_TIMES_ON_X, 1.0), (_CONDITIONS_ON_X, 1.0)],
    "time": [(_TIMES_ON_X, 1.0)],
    "trlab": [(_GENES_ON_X, 2.0), (_TIMES_ON_X, 1.0)],
}


def _average(cube: Cube, tricluster: Tricluster, views: str, normalized: bool,
             angles: Callable[[np.ndarray], np.ndarray]) -> float:
    if views not in _VIEWS:
        raise ValueError(f"views must be one of {list(_VIEWS)}, not {views!r}.")
    values = cube.subcube(tricluster)
    chosen = _VIEWS[views]
    total = sum(weight * _view(angles(np.transpose(values, axes))) for axes, weight in chosen)
    result = total / sum(weight for _, weight in chosen)
    return result / TWO_PI if normalized else result


def _turn(angles: np.ndarray) -> np.ndarray:
    """Angles from ``arctan`` taken to ``[0, 2π)``: a negative one gets ``2π`` added."""
    return np.where(angles < 0, angles + TWO_PI, angles)


def _segment_angles(view: np.ndarray) -> np.ndarray:
    """(series, x, panels) values to (series, segments, panels) angles."""
    return _turn(np.arctan(np.diff(view, axis=1)))


def _line_angle(view: np.ndarray) -> np.ndarray:
    """(series, x, panels) values to (series, 1, panels) angles of the least squares lines."""
    n = view.shape[1]
    x = np.arange(1, n + 1, dtype=np.float64)
    sum_x, sum_xx = x.sum(), (x * x).sum()
    sum_y = view.sum(axis=1, keepdims=True)
    sum_xy = np.einsum("sxp,x->sp", view, x)[:, None, :]
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
    return _turn(np.arctan(slope))


def _view(angles: np.ndarray) -> float:
    """
    The mean, over every pair of series in the same panel and every pair of panels of
    the same series, of the mean absolute difference of their angles.
    """
    series, segments, panels = angles.shape
    within_series = _pair_sums(angles, axis=2)      # panels compared, per series and segment
    within_panels = _pair_sums(angles, axis=0)      # series compared, per panel and segment
    pairs = series * panels * (panels - 1) // 2 + panels * series * (series - 1) // 2
    return float((within_series + within_panels) / (segments * pairs))


def _pair_sums(values: np.ndarray, axis: int) -> float:
    """
    The sum of ``|a - b|`` over every pair of values along an axis, over all the other
    positions. Sorted, the i-th of n values is larger than i of the others and smaller
    than n - 1 - i, so the sum is ``Σ (2i - n + 1) · a_(i)``: n log n instead of n².
    """
    ordered = np.sort(values, axis=axis)
    n = values.shape[axis]
    shape = [1, 1, 1]
    shape[axis] = n
    weights = (2 * np.arange(n) - n + 1).reshape(shape)
    # A sum of absolute values: the weighted sum can round a hair below zero when every
    # value is the same, and a measure that should read 0 would read -0.0 or -1e-17.
    return max(0.0, float((ordered * weights).sum()))
