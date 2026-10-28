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
from typing import Callable, Dict, List, Literal, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import Cube
from metagen.triclustering.tricluster import Tricluster

#: Which graphical views LSL and MSL average. See :py:func:`msl`.
Views = Literal["distinct", "time", "trlab"]

TWO_PI = 2.0 * math.pi


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
    return _average_values(cube.subcube(tricluster), views, normalized, angles)


def _average_values(values: np.ndarray, views: str, normalized: bool,
                    angles: Callable[[np.ndarray], np.ndarray]) -> float:
    """:py:func:`_average` of values already taken out, (genes, conditions, times)."""
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
    x = np.arange(1, view.shape[1] + 1, dtype=np.float64)
    centered = x - x.mean()
    # From the values less their mean: the textbook n·Σxy − Σx·Σy leaves a slope of
    # ±1e-17 on a flat series of non-integer values, and the sign decides between an
    # angle of 0 and one of 2π, the largest difference there is.
    deviations = view - view.mean(axis=1, keepdims=True)
    slope = np.einsum("sxp,x->sp", deviations, centered)[:, None, :] / (centered * centered).sum()
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
    # Only that: a NaN comes through as NaN.
    total = float((ordered * weights).sum())
    return 0.0 if total < 0.0 else total


# --- MSL of a tricluster with each of many genes added, at once ----------------------------

def _msl_adding_genes(cube: Cube, tricluster: Tricluster, candidates: Sequence[int], views: str = "distinct",
                      normalized: bool = False) -> np.ndarray:
    """
    The MSL of a tricluster with each candidate gene added to it, at once and the same,
    but for rounding, as computing each with :py:func:`msl`: the pairs that a new gene
    adds are summed from sorted prefix sums, and the segment it splits in the view with
    the genes on the X axis is replaced by the two it makes.
    """
    if views not in _VIEWS:
        raise ValueError(f"views must be one of {list(_VIEWS)}, not {views!r}.")
    positions = np.asarray(candidates, dtype=int)
    if positions.size == 0:
        return np.zeros(0)
    base = cube.subcube(tricluster)                                  # (genes, conditions, times)
    columns = np.ix_(positions, np.asarray(tricluster.conditions), np.asarray(tricluster.times))
    added = cube.values[columns]                                     # (candidates, conditions, times)
    total = np.zeros(positions.size)
    for axes, weight in _VIEWS[views]:
        if axes == _GENES_ON_X:
            total += weight * _genes_on_x(base, added, np.asarray(tricluster.genes), positions)
        else:
            # Times on X: series are genes, x the times, panels the conditions; conditions on X:
            # series are genes, x the conditions, panels the times.
            series_axes = (0, 2, 1) if axes == _TIMES_ON_X else (0, 1, 2)
            total += weight * _a_series_more(np.transpose(base, series_axes),
                                             np.transpose(added, series_axes))
    result = total / sum(weight for _, weight in _VIEWS[views])
    return result / TWO_PI if normalized else result


def _a_series_more(view: np.ndarray, added: np.ndarray) -> np.ndarray:
    """The view's value with each candidate as one more series: view (series, x, panels),
    added (candidates, x, panels)."""
    angles = _segment_angles(view)                                    # (series, segments, panels)
    new = _turn(np.arctan(np.diff(added, axis=1)))                    # (candidates, segments, panels)
    series, segments, panels = angles.shape
    within_series = _pair_sums(angles, axis=2) + _pair_sums_each(new, axis=2)
    # The new series against every old one, per segment and panel, from sorted prefix sums.
    ordered = np.sort(angles, axis=0)                                 # (series, segments, panels)
    prefix = np.concatenate([np.zeros((1, segments, panels)), np.cumsum(ordered, axis=0)], axis=0)
    against = np.zeros(new.shape[0])
    for segment in range(segments):
        for panel in range(panels):
            column, sums = ordered[:, segment, panel], prefix[:, segment, panel]
            values = new[:, segment, panel]
            below = np.searchsorted(column, values, side="right")
            lower = sums[below]
            against += values * below - lower + (sums[-1] - lower) - values * (series - below)
    within_panels = _pair_sums(angles, axis=0) + against
    count = series + 1
    pairs = count * panels * (panels - 1) // 2 + panels * count * (count - 1) // 2
    return (within_series + within_panels) / (segments * pairs)


def _genes_on_x(base: np.ndarray, added: np.ndarray, genes: np.ndarray, candidates: np.ndarray) -> np.ndarray:
    """The value of the view with the genes on the X axis with each candidate inserted at its
    place among the genes: base (genes, conditions, times), added (candidates, conditions,
    times). Series are conditions and panels times; a segment joins two consecutive genes."""
    view = np.transpose(base, (1, 0, 2))                              # (conditions, genes, times)
    angles = _segment_angles(view)                                    # (conditions, segments, times)
    conditions, segments, times = angles.shape

    def contribution(segment_angles: np.ndarray) -> np.ndarray:
        """Of segments (..., conditions, times): the pairs of times per condition and of
        conditions per time."""
        return _pair_sums_each(segment_angles, axis=-1) + _pair_sums_each(segment_angles, axis=-2)

    per_segment = contribution(np.transpose(angles, (1, 0, 2)))       # (segments,)
    total = float(per_segment.sum())
    place = np.searchsorted(genes, candidates)                        # where each one goes
    before = np.where(place > 0, place - 1, 0)
    after = np.where(place < genes.size, place, genes.size - 1)
    first = _turn(np.arctan(added - base[before]))                    # segment (previous gene, candidate)
    second = _turn(np.arctan(base[after] - added))                    # segment (candidate, next gene)
    inside = (place > 0) & (place < genes.size)
    new_total = np.full(candidates.size, total)
    replaced = np.where(inside, per_segment[np.clip(place - 1, 0, max(segments - 1, 0))], 0.0)
    new_total += np.where(place > 0, contribution(first), 0.0) + np.where(place < genes.size, contribution(second), 0.0)
    new_total -= replaced
    pairs = conditions * times * (times - 1) // 2 + times * conditions * (conditions - 1) // 2
    return new_total / ((segments + 1) * pairs)


def _pair_sums_each(values: np.ndarray, axis: int) -> np.ndarray:
    """:py:func:`_pair_sums` for each position of the first axis: the sum of ``|a - b|``
    over every pair along ``axis``, over all the other axes but the first."""
    ordered = np.sort(values, axis=axis)
    n = values.shape[axis]
    shape = [1] * values.ndim
    shape[axis] = n
    weights = (2 * np.arange(n) - n + 1).reshape(shape)
    totals = (ordered * weights).reshape(values.shape[0], -1).sum(axis=1)
    return np.maximum(totals, 0.0)


# --- The quality of a prism with each of many pixels added or taken out, at once -----------

def _prism_moves(values: np.ndarray, added: np.ndarray, removed: Sequence[int],
                 angles: Callable[[np.ndarray], np.ndarray]) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    The quality of a prism, normalized with the times on the X axis, with each of some
    pixels added to it and with each of some of its pixels taken out, at once, and a bound
    on how far each value is, by rounding, from measuring that prism on its own.

    The pairs of a pixel's series with the others are summed from the angles of the prism
    sorted per segment and their prefix sums, as :py:func:`_msl_adding_genes` does with a
    gene, and added to or taken from the pairs of the prism.

    :param values: The prism's values, (pixels, 1, times), as its shape gives them.
    :param added: The values of the pixels to add, (candidates, 1, times).
    :param removed: The positions, among the prism's pixels, of those to take out.
    :param angles: :py:func:`_segment_angles` or :py:func:`_line_angle`.
    :return: The qualities with each added, with each taken out, and the bound.
    """
    current = angles(np.transpose(values, (0, 2, 1)))[:, :, 0]           # (pixels, segments)
    count, segments = current.shape
    ordered = np.sort(current, axis=0)
    prefix = np.concatenate([np.zeros((1, segments)), np.cumsum(ordered, axis=0)], axis=0)
    total = float((ordered * (2 * np.arange(count) - count + 1)[:, None]).sum())

    def against(others: np.ndarray) -> np.ndarray:
        """The sum of |a - b| of each row of others with every pixel of the prism, over the segments."""
        result = np.zeros(others.shape[0])
        for segment in range(segments):
            column, sums = ordered[:, segment], prefix[:, segment]
            value = others[:, segment]
            below = np.searchsorted(column, value, side="right")
            lower = sums[below]
            result += value * below - lower + (sums[-1] - lower) - value * (count - below)
        return result

    def quality(totals: np.ndarray, size: int) -> np.ndarray:
        return np.maximum(totals, 0.0) / (segments * (size * (size - 1) // 2)) / TWO_PI

    more = (quality(total + against(angles(np.transpose(added, (0, 2, 1)))[:, :, 0]), count + 1)
            if len(added) else np.zeros(0))
    taken = np.asarray(removed, dtype=int)
    fewer = quality(total - against(current[taken]), count - 1) if taken.size else np.zeros(0)
    # Measured on its own, a prism's pairs are a sum of about pixels x segments terms, each
    # at most 2π times the pixels, and here the same terms are summed in another order:
    # each sum is within (terms + a few) units of rounding of the exact one, relative to the
    # pairs that divide it, and the bound takes four times both
    # (metagen-auditoria/trigen/c5/informe_c5_etapa3_cruce.md, 6).
    bound = 16.0 * ((count + 1) * segments + 16) * float(np.finfo(np.float64).eps)
    return more, fewer, bound
