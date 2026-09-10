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
import random
from typing import Optional

import numpy as np

# Every random draw in MetaGen goes through these two generators instead of
# through the process-wide `random` and `numpy.random` modules. Seeding a
# metaheuristic therefore makes its run reproducible without touching the random
# state of the calling application, and the application seeding its own code no
# longer changes what MetaGen does.
#
# Two generators are needed because the algorithms are split: TPE draws from
# NumPy and everything else from the standard library. `set_seed` seeds both
# from a single value, so callers never have to know which one an algorithm uses.
_python_rng: random.Random = random.Random()
_numpy_rng: np.random.Generator = np.random.default_rng()


def get_rng() -> random.Random:
    """
    Return the standard-library generator used by MetaGen.

    Call this at the point of use rather than caching the result: a cached
    reference would survive a later :func:`set_seed`.

    :return: The generator backing every ``random``-style draw in MetaGen.
    :rtype: random.Random
    """
    return _python_rng


def get_numpy_rng() -> np.random.Generator:
    """
    Return the NumPy generator used by MetaGen.

    Call this at the point of use rather than caching the result: :func:`set_seed`
    replaces this generator, and a cached reference would keep pointing at the
    previous one.

    :return: The generator backing every NumPy-style draw in MetaGen.
    :rtype: numpy.random.Generator
    """
    return _numpy_rng


def spawn_seed() -> int:
    """
    Draw a seed for a worker from MetaGen's own generator.

    Ray workers are separate processes with their own generator state, so seeding
    the driver did not make a distributed run reproducible (A-06). Every task now
    receives a seed drawn here and applies it with :func:`set_seed` before working:
    the driver's seed then determines every worker's stream. Drawing consumes one
    value of the driver's generator, so only distributed paths call this.

    :return: A seed for one worker.
    :rtype: int
    """
    return _python_rng.getrandbits(63)


def set_seed(seed: Optional[int]) -> None:
    """
    Seed both MetaGen generators from a single value.

    Passing ``None`` reseeds them from a fresh, unpredictable source, which is
    the state a freshly imported MetaGen starts in.

    :param seed: The seed to apply, or ``None`` for a non-reproducible run.
    :type seed: Optional[int]
    :return: Nothing.
    :rtype: None
    """
    global _numpy_rng
    _python_rng.seed(seed)
    _numpy_rng = np.random.default_rng(seed)
