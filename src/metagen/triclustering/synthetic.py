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
from typing import List, Literal, Optional, Sequence, Tuple

import numpy as np

from metagen.framework.rng import get_numpy_rng
from metagen.triclustering.cube import AXES, Cube
from metagen.triclustering.tricluster import Tricluster

#: The kind of block :py:func:`plant` puts in a cube.
Pattern = Literal["constant", "additive", "multiplicative"]

_PATTERNS = ("constant", "additive", "multiplicative")


def plant(shape: Sequence[int], sizes: Sequence[Sequence[int]], pattern: Pattern = "additive",
          noise: float = 0.0, seed: Optional[int] = None) -> Tuple[Cube, List[Tricluster]]:
    """
    A cube of random values with triclusters planted in it, for trying out a
    triclustering on data whose answer is known.

    The background is standard normal noise, independent in every cell. Each size
    ``(genes, conditions, times)`` in ``sizes`` plants one tricluster, at genes, conditions
    and times drawn at random; no two share a gene, so no two share a cell. Its values
    follow the pattern, with parameters drawn for each tricluster:

    - ``"constant"``: one value, :math:`\\mu`, drawn from ``[-3, 3]``.
    - ``"additive"``: :math:`\\mu + \\alpha_g + \\beta_c + \\gamma_t`, the effects standard normal.
    - ``"multiplicative"``: :math:`\\mu \\cdot \\alpha_g \\cdot \\beta_c \\cdot \\gamma_t`, with
      :math:`\\mu` in ``[1, 3]`` and the effects in ``[0.5, 2]``.

    ``noise`` is the standard deviation of normal noise added inside the triclusters.

    With a ``seed``, the cube is drawn from a generator of its own seeded with it; without
    one, from MetaGen's generator, the one :py:func:`~metagen.framework.rng.set_seed` seeds.

    .. code-block:: python

        from metagen.triclustering import msr3d, plant

        cube, planted = plant((100, 8, 10), [(20, 3, 5), (15, 4, 4)], pattern="additive", seed=0)
        print(cube.shape, [t.size for t in planted])             # (100, 8, 10) [(20, 3, 5), (15, 4, 4)]
        print(round(msr3d(cube, planted[0]), 12))                # 0.0

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The number of genes, conditions and times of each tricluster to plant;
        with none, the cube is noise alone.
    :type sizes: Sequence[Sequence[int]]
    :param pattern: ``"constant"``, ``"additive"`` or ``"multiplicative"``, defaults to
        ``"additive"``.
    :type pattern: str, optional
    :param noise: The standard deviation of the noise inside the triclusters, defaults to 0.
    :type noise: float, optional
    :param seed: A seed for this cube alone, defaults to None.
    :type seed: int, optional
    :return: The cube, and the triclusters planted, in the order of ``sizes``.
    :rtype: Tuple[Cube, List[Tricluster]]
    :raises ValueError: if the shape or the sizes are not valid, the triclusters need more
        genes than the cube has, the pattern is unknown or the noise is negative or not finite.
    """
    dimensions = _counts("shape", shape)
    wanted = [_counts("size", size) for size in sizes]
    for size in wanted:
        if any(part > whole for part, whole in zip(size, dimensions)):
            raise ValueError(f"A tricluster of size {size} does not fit in a cube of shape {dimensions}.")
    if sum(size[0] for size in wanted) > dimensions[0]:
        raise ValueError(f"The triclusters need {sum(size[0] for size in wanted)} genes and do not share any; "
                         f"the cube has {dimensions[0]}.")
    if pattern not in _PATTERNS:
        raise ValueError(f"pattern must be one of {list(_PATTERNS)}, not {pattern!r}.")
    if not (noise >= 0 and math.isfinite(noise)):
        raise ValueError(f"noise is a standard deviation, finite and not negative, not {noise}.")

    # A generator of its own with a seed, so that the cube does not depend on anything
    # else drawn before; MetaGen's otherwise, never NumPy's global one.
    rng = np.random.default_rng(seed) if seed is not None else get_numpy_rng()
    values = rng.normal(size=dimensions)
    genes = rng.permutation(dimensions[0])
    planted: List[Tricluster] = []
    start = 0
    for gene_count, condition_count, time_count in wanted:
        positions = (genes[start:start + gene_count],
                     rng.choice(dimensions[1], size=condition_count, replace=False),
                     rng.choice(dimensions[2], size=time_count, replace=False))
        start += gene_count
        tricluster = Tricluster(*positions)
        block = _block(rng, pattern, tricluster.size)
        if noise > 0:
            block = block + rng.normal(scale=noise, size=block.shape)
        values[np.ix_(tricluster.genes, tricluster.conditions, tricluster.times)] = block
        planted.append(tricluster)
    return Cube(values), planted


def _block(rng: np.random.Generator, pattern: str, size: Tuple[int, int, int]) -> np.ndarray:
    genes, conditions, times = size
    if pattern == "constant":
        return np.full(size, rng.uniform(-3.0, 3.0))
    if pattern == "additive":
        mean = rng.uniform(-3.0, 3.0)
        return (mean + rng.normal(size=(genes, 1, 1)) + rng.normal(size=(1, conditions, 1))
                + rng.normal(size=(1, 1, times)))
    mean = rng.uniform(1.0, 3.0)
    return (mean * rng.uniform(0.5, 2.0, size=(genes, 1, 1)) * rng.uniform(0.5, 2.0, size=(1, conditions, 1))
            * rng.uniform(0.5, 2.0, size=(1, 1, times)))


def _counts(what: str, given: Sequence[int]) -> Tuple[int, int, int]:
    counts = tuple(given)
    if len(counts) != 3 or any(isinstance(n, bool) or not isinstance(n, numbers.Integral) or n < 2
                               for n in counts):
        raise ValueError(f"A {what} is three integers, one per dimension ({', '.join(AXES)}), "
                         f"each at least 2, not {given!r}.")
    first, second, third = (int(n) for n in counts)
    return first, second, third
