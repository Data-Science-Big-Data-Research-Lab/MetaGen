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
from typing import Dict, Literal, Mapping, Optional

import numpy as np
from scipy.stats import rankdata

from metagen.triclustering.cube import Cube
from metagen.triclustering.measures import TWO_PI, Views, msl
from metagen.triclustering.tricluster import Tricluster

#: What PEQ and SPQ do with a flat profile, one whose value is the same at every time.
FlatProfiles = Literal["exclude", "zero"]

#: The weights of TRIQ without a biological quality, and with one.
WEIGHTS: Mapping[str, float] = {"grq": 0.8, "peq": 0.1, "spq": 0.1}
WEIGHTS_WITH_BIOQ: Mapping[str, float] = {"grq": 0.4, "peq": 0.05, "spq": 0.05, "bioq": 0.5}

# Columns of profiles correlated at a time: a block of correlations takes this many
# squared floats, 32 MB, whatever the size of the tricluster.
_BLOCK = 2048


def grq(cube: Cube, tricluster: Tricluster, views: Views = "distinct") -> float:
    """
    The graphical quality of a tricluster (GRQ): ``1 − MSL / 2π``, from 0 to 1, the higher
    the better. It is 1 when every series has the same shape. ``views`` chooses the views
    MSL averages; see :py:func:`~metagen.triclustering.msl`.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, grq

        cube = Cube(np.broadcast_to(np.arange(6.0), (5, 3, 6)))    # every series rises alike
        print(grq(cube, Tricluster(range(5), range(3), range(6)), views="time"))   # 1.0

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param views: The views MSL averages, defaults to ``"distinct"``.
    :type views: str, optional
    :return: Its graphical quality.
    :rtype: float
    """
    return 1.0 - msl(cube, tricluster, views=views) / TWO_PI


def peq(cube: Cube, tricluster: Tricluster, flat_profiles: FlatProfiles = "exclude") -> float:
    """
    The Pearson quality of a tricluster (PEQ): how correlated its profiles are, from 0 to 1,
    the higher the better. A profile is the series of values of one of its genes under one
    of its conditions over its times; PEQ is the mean absolute Pearson correlation over
    every pair of profiles, so that a profile rising as another falls counts as correlated.

    A flat profile, the same value at every time, has no correlation with any other. With
    ``flat_profiles="exclude"``, the default, the pairs that hold one are left out, and PEQ
    is NaN when fewer than two profiles vary; with ``"zero"`` those pairs count as 0.
    With two times any two profiles that vary are perfectly correlated, so PEQ says
    something from three times on.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, peq

        rising = np.arange(5.0)
        values = np.stack([rising, 2 * rising + 1, -rising, np.full(5, 3.0)])  # the last is flat
        cube = Cube(values.reshape(4, 1, 5).repeat(2, axis=1))
        whole = Tricluster(range(4), range(2), range(5))
        print(peq(cube, whole), round(peq(cube, whole, flat_profiles="zero"), 4))   # 1.0 0.5357

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param flat_profiles: ``"exclude"`` or ``"zero"``, defaults to ``"exclude"``.
    :type flat_profiles: str, optional
    :return: Its Pearson quality, or NaN if fewer than two profiles vary and they are excluded.
    :rtype: float
    """
    return _correlation_quality(_profiles(cube, tricluster), flat_profiles)


def spq(cube: Cube, tricluster: Tricluster, flat_profiles: FlatProfiles = "exclude") -> float:
    """
    The Spearman quality of a tricluster (SPQ): :py:func:`peq` with Spearman's rank
    correlation, tied values taking their mean rank, so that it also counts profiles that
    rise and fall together without being straight lines of one another.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, spq

        times = np.arange(1.0, 6.0)
        values = np.stack([times, times ** 3, np.log(times)]).reshape(3, 1, 5).repeat(2, axis=1)
        print(spq(Cube(values), Tricluster(range(3), range(2), range(5))))       # 1.0

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param flat_profiles: ``"exclude"`` or ``"zero"``, defaults to ``"exclude"``.
    :type flat_profiles: str, optional
    :return: Its Spearman quality, or NaN if fewer than two profiles vary and they are excluded.
    :rtype: float
    """
    return _correlation_quality(rankdata(_profiles(cube, tricluster), axis=0), flat_profiles)


def triq(cube: Cube, tricluster: Tricluster, bioq: Optional[float] = None,
         weights: Optional[Mapping[str, float]] = None, views: Views = "distinct",
         flat_profiles: FlatProfiles = "exclude") -> float:
    """
    The quality of a tricluster (TRIQ): the weighted mean of its graphical, Pearson and
    Spearman qualities and, when it is given, its biological quality, from 0 to 1, the
    higher the better.

    .. math::

        TRIQ = \\frac{w_{gr} GRQ + w_{pe} PEQ + w_{sp} SPQ + w_{bio} BIOQ}
                     {w_{gr} + w_{pe} + w_{sp} + w_{bio}}

    The weights are 0.8, 0.1 and 0.1 without a biological quality, and 0.4, 0.05, 0.05 and
    0.5 with one. A quality that is not defined (a PEQ or SPQ with fewer than two profiles
    that vary) is left out, and its weight with it. The metaheuristics minimize: to search
    by TRIQ, give them ``1 − TRIQ``.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube, Tricluster, triq

        rng = np.random.default_rng(0)
        values = rng.normal(size=(20, 4, 6))
        values[:5, :2] = np.linspace(0, 2, 6) + rng.normal(scale=0.05, size=(5, 2, 6))
        cube = Cube(values)
        good, poor = Tricluster(range(5), range(2), range(6)), Tricluster(range(10, 15), range(2), range(6))
        print(triq(cube, good, views="time") > 0.9, triq(cube, poor, views="time") < 0.7)   # True True

    :param cube: The data.
    :type cube: Cube
    :param tricluster: The tricluster.
    :type tricluster: Tricluster
    :param bioq: Its biological quality, if any.
    :type bioq: float, optional
    :param weights: The weights, by the names ``"grq"``, ``"peq"``, ``"spq"`` and ``"bioq"``;
        they need not add up to 1.
    :type weights: Mapping[str, float], optional
    :param views: The views of GRQ, defaults to ``"distinct"``.
    :type views: str, optional
    :param flat_profiles: How PEQ and SPQ treat flat profiles, defaults to ``"exclude"``.
    :type flat_profiles: str, optional
    :return: Its quality.
    :rtype: float
    :raises ValueError: if the weights do not name exactly the qualities in use, or one is
        negative.
    """
    qualities: Dict[str, float] = {"grq": grq(cube, tricluster, views=views),
                                   "peq": peq(cube, tricluster, flat_profiles),
                                   "spq": spq(cube, tricluster, flat_profiles)}
    if bioq is not None:
        qualities["bioq"] = float(bioq)
    chosen = dict(weights) if weights is not None else dict(WEIGHTS if bioq is None else WEIGHTS_WITH_BIOQ)
    if set(chosen) != set(qualities):
        raise ValueError(f"The weights must be for {sorted(qualities)}, not {sorted(chosen)}.")
    if any(weight < 0 for weight in chosen.values()):
        raise ValueError(f"The weights cannot be negative: {chosen}.")
    defined = {name: value for name, value in qualities.items() if not math.isnan(value)}
    total = sum(chosen[name] for name in defined)
    if total <= 0:
        raise ValueError(f"The weights of the qualities that are defined, {sorted(defined)}, add up to 0.")
    return sum(chosen[name] * value for name, value in defined.items()) / total


def _profiles(cube: Cube, tricluster: Tricluster) -> np.ndarray:
    """A row per time and a column per (gene, condition), the gene in the outer loop."""
    values = cube.subcube(tricluster)
    genes, conditions, times = values.shape
    return np.transpose(values, (2, 0, 1)).reshape(times, genes * conditions)


def _correlation_quality(profiles: np.ndarray, flat_profiles: str) -> float:
    """The mean absolute Pearson correlation over the pairs of columns."""
    if flat_profiles not in ("exclude", "zero"):
        raise ValueError(f"flat_profiles must be 'exclude' or 'zero', not {flat_profiles!r}.")
    centered = profiles - profiles.mean(axis=0)
    norms = np.sqrt((centered * centered).sum(axis=0))
    # Flat exactly when every value is the same: the only case with no correlation.
    flat = np.ptp(profiles, axis=0) == 0
    if flat_profiles == "exclude":
        centered, norms = centered[:, ~flat], norms[~flat]
    columns = centered.shape[1]
    if columns < 2:
        return math.nan
    # A flat column, kept under "zero", becomes all zeros and correlates 0 with every other.
    standardized = np.divide(centered, norms, out=np.zeros_like(centered), where=norms > 0)
    total = 0.0
    for start in range(0, columns, _BLOCK):
        block = standardized[:, start:start + _BLOCK]
        for other in range(start, columns, _BLOCK):
            correlations = np.abs(block.T @ standardized[:, other:other + _BLOCK])
            if other == start:
                correlations = np.triu(correlations, k=1)
            total += float(np.minimum(correlations, 1.0).sum())
    return total / (columns * (columns - 1) / 2)
