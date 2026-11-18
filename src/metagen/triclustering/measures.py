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

from typing import Literal

import numpy as np

from metagen.triclustering.cube import Cube
from metagen.triclustering.tricluster import Tricluster
from metagen.triclustering._lines import average, line_angle, segment_angles

#: Which graphical views LSL and MSL average. See :py:func:`msl`.
Views = Literal["distinct", "time", "trlab"]



def msr3d(cube: Cube, tricluster: Tricluster, normalized: bool = False) -> float:
    """
    The mean squared residue of a tricluster (MSR3D): how far its values are from the
    sum of the effects of their gene, condition and time, the mean of the squared
    three-way interaction residues

    .. math::

        r_{gct} = x_{gct} - x_{gc\\cdot} - x_{g\\cdot t} - x_{\\cdot ct}
                  + x_{g\\cdot\\cdot} + x_{\\cdot c\\cdot} + x_{\\cdot\\cdot t} - x_{\\cdot\\cdot\\cdot}

    where a dot stands for the mean over that dimension. It is zero for a tricluster of
    coherent values, the lower the better, and it is in the units of the data squared,
    so its scale is the data's. ``normalized=True`` divides it by the variance of all the
    values of the cube, which takes the scale out: it is then the same for the data in any
    units, and below 1 for values with no pattern.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, msr3d

        genes, conditions, times = np.meshgrid(np.arange(5), np.arange(3), np.arange(4), indexing="ij")
        cube = Cube(1.0 * genes + 2.0 * conditions + 0.5 * times)     # additive: no interaction
        print(round(msr3d(cube, Tricluster([0, 2, 4], [0, 1], [1, 2, 3])), 12))   # 0.0

        noise = Cube(np.random.default_rng(0).normal(scale=50.0, size=(40, 6, 8)))
        tricluster = Tricluster(range(10), range(3), range(4))
        print(round(msr3d(noise, tricluster)), round(msr3d(noise, tricluster, normalized=True), 3))   # 660 0.265

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param normalized: Whether to divide it by the variance of the values of the cube,
        defaults to False. For a cube whose values are all the same, it is then 0.
    :type normalized: bool, optional
    :return: Its mean squared residue.
    :rtype: float
    """
    # Centered first: the residue does not change with a constant, and with values far
    # from zero the means would otherwise lose the digits the residue lives in.
    values = cube.subcube(tricluster)
    values = values - values.mean()
    residue = (values
               - values.mean(axis=2, keepdims=True) - values.mean(axis=1, keepdims=True)
               - values.mean(axis=0, keepdims=True)
               + values.mean(axis=(1, 2), keepdims=True) + values.mean(axis=(0, 2), keepdims=True)
               + values.mean(axis=(0, 1), keepdims=True)
               - values.mean())
    value = float((residue ** 2).mean())
    if not normalized:
        return value
    spread = float(np.var(cube.values))
    return value / spread if spread > 0 else 0.0


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
      the times once, the views of the definition of MSL in the TriGen publications, as
      TrLab computes it.

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
    return average(cube, tricluster, views, normalized, segment_angles)


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
    return average(cube, tricluster, views, normalized, line_angle)
