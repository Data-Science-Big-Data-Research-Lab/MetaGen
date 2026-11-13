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
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional

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

# The generators of a thread running under own_generators. Threads drawing from one
# generator get their numbers in the order they happen to run, which no seed controls.
# The count keeps every other run off the thread-local lookup, which cost a genetic
# algorithm on a cheap fitness 6 % of its time.
_thread_generators = threading.local()
_threads_with_own_generators: int = 0
_threads_with_own_generators_lock = threading.Lock()


def get_rng() -> random.Random:
    """
    Return the standard-library generator used by MetaGen.

    Call this at the point of use rather than caching the result: a cached
    reference would survive a later :func:`set_seed`.

    :return: The generator backing every ``random``-style draw in MetaGen.
    :rtype: random.Random
    """
    return getattr(_thread_generators, "python", _python_rng) if _threads_with_own_generators else _python_rng


def get_numpy_rng() -> np.random.Generator:
    """
    Return the NumPy generator used by MetaGen.

    Call this at the point of use rather than caching the result: :func:`set_seed`
    replaces this generator, and a cached reference would keep pointing at the
    previous one.

    :return: The generator backing every NumPy-style draw in MetaGen.
    :rtype: numpy.random.Generator
    """
    return getattr(_thread_generators, "numpy", _numpy_rng) if _threads_with_own_generators else _numpy_rng


@contextmanager
def own_generators(seed: Optional[int]) -> Iterator[None]:
    """
    Give the calling thread its own two generators for the duration of the block.

    Every draw the thread makes inside comes from them, so what it draws does not depend
    on what other threads are drawing; :func:`set_seed`, :func:`get_state` and
    :func:`set_state` called inside work on them too. The other threads keep working on
    the generators of the process. Blocks may nest: the generators of the outer one are
    back when the inner one ends.

    :param seed: The seed of the thread's generators, or ``None`` for an unpredictable one.
    :type seed: Optional[int]
    :return: Nothing; the generators the thread had are back when the block ends.
    :rtype: Iterator[None]
    """
    global _threads_with_own_generators
    # A run with a seed in a thread nests one of these inside the one a CVOA strain or a
    # caller may already hold: deleting the generators on the way out left the outer block
    # on the generators of the process (F-77).
    outer = (getattr(_thread_generators, "python", None), getattr(_thread_generators, "numpy", None))
    _thread_generators.python = random.Random(seed)
    _thread_generators.numpy = np.random.default_rng(seed)
    with _threads_with_own_generators_lock:
        _threads_with_own_generators += 1
    try:
        yield
    finally:
        with _threads_with_own_generators_lock:
            _threads_with_own_generators -= 1
        if outer[0] is None:
            del _thread_generators.python
            del _thread_generators.numpy
        else:
            _thread_generators.python, _thread_generators.numpy = outer


def has_own_generators() -> bool:
    """
    Whether the calling thread draws from generators of its own, inside :func:`own_generators`.

    :return: True inside a block of :func:`own_generators` of this thread.
    :rtype: bool
    """
    return bool(_threads_with_own_generators) and hasattr(_thread_generators, "python")


@contextmanager
def seeded(seed: Optional[int]) -> Iterator[None]:
    """
    The generators of a run with ``seed``: on the main thread, the process's, seeded with
    :func:`set_seed`; on any other thread, generators of the thread's own, so that runs
    with a seed in several threads at once draw what each would draw alone. Without a
    seed, nothing changes.

    :param seed: The seed of the run, or ``None``.
    :type seed: Optional[int]
    :return: Nothing.
    :rtype: Iterator[None]
    """
    # Two runs with a seed in two threads reseeded the generators of the process and drew
    # from them in turns, so neither gave what it gives alone (F-77, X-04 of the
    # independent audit). The main thread keeps the generators of the process: a run there
    # costs the same as before, and leaves them where it always did.
    if seed is None or threading.current_thread() is threading.main_thread():
        yield
        return
    with own_generators(seed):
        yield


def spawn_seed() -> int:
    """
    Draw a seed for a worker from MetaGen's own generator.

    Ray workers are separate processes with their own generator state, so seeding
    the driver alone does not make a distributed run reproducible. Every task
    receives a seed drawn here and applies it with :func:`set_seed` before working:
    the driver's seed then determines every worker's stream. Drawing consumes one
    value of the driver's generator, so only the paths that need it call this: the
    distributed ones, and the launcher of several CVOA strains on threads.

    :return: A seed for one worker.
    :rtype: int
    """
    # A-06: before this, no distributed run was reproducible. From the thread's own
    # generator when it has one, so that a run with a seed in a thread seeds its tasks (F-77).
    return get_rng().getrandbits(63)


def set_seed(seed: Optional[int]) -> None:
    """
    Seed both MetaGen generators from a single value.

    Passing ``None`` reseeds them from a fresh, unpredictable source, which is
    the state a freshly imported MetaGen starts in. Inside :func:`own_generators`, it
    seeds the generators of the calling thread.

    :param seed: The seed to apply, or ``None`` for a non-reproducible run.
    :type seed: Optional[int]
    :return: Nothing.
    :rtype: None
    """
    global _numpy_rng
    if has_own_generators():
        _thread_generators.python.seed(seed)
        _thread_generators.numpy = np.random.default_rng(seed)
        return
    _python_rng.seed(seed)
    _numpy_rng = np.random.default_rng(seed)


def get_state() -> Dict[str, Any]:
    """
    The state of both MetaGen generators, to save a run and continue it later.

    :return: The state of the standard-library and the NumPy generators.
    :rtype: dict
    """
    return {"random": get_rng().getstate(), "numpy": get_numpy_rng().bit_generator.state}


def set_state(state: Dict[str, Any]) -> None:
    """
    Put both MetaGen generators back in a state returned by :func:`get_state`.

    :param state: The state to restore.
    :type state: dict
    :return: Nothing.
    :rtype: None
    """
    global _numpy_rng
    numpy_rng = np.random.default_rng()
    numpy_rng.bit_generator.state = state["numpy"]
    if has_own_generators():
        _thread_generators.python.setstate(state["random"])
        _thread_generators.numpy = numpy_rng
        return
    _python_rng.setstate(state["random"])
    _numpy_rng = numpy_rng
