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
import importlib.util
from typing import Callable


def is_package_installed(package_name: str) -> bool:
    """
    Whether an optional package, such as Ray or TensorBoard, can be imported.

    A directory with the package's name and no ``__init__.py``, such as the ``ray``
    folder Ray leaves in the temporary directory, is found as a namespace package with
    nothing in it, and does not count: the package has to have a file to import from.

    :param package_name: The name the package is imported by.
    :type package_name: str
    :return: True if the package is installed, otherwise False.
    :rtype: bool
    """
    # F-52: find_spec alone took such a folder in the current directory for Ray, and
    # importing metagen.metaheuristics then failed on ray.remote.
    try:
        spec = importlib.util.find_spec(package_name)
    except ImportError:
        return False
    return spec is not None and spec.origin is not None


def ray_missing(purpose: str) -> str:
    """
    The message of the error raised when Ray is needed and not installed.

    :param purpose: What needs Ray, such as ``"distributed execution"``.
    :type purpose: str
    :return: The message, which says how to install it.
    :rtype: str
    """
    # One message for every place that needs Ray: there were four ways of saying it
    # (O-01, metagen-auditoria/auditoria-independiente-2026-11/organizacion.md).
    return (f"Ray is not installed, and {purpose} needs it. "
            f"Install it with: pip install pymetagen-datalabupo[distributed]")


def require_ray(purpose: str) -> None:
    """
    Raise an ``ImportError`` that says how to install Ray, when it is not installed.

    :param purpose: What needs Ray, such as ``"distributed execution"``.
    :type purpose: str
    :raises ImportError: if Ray is not installed.
    """
    if not is_package_installed("ray"):
        raise ImportError(ray_missing(purpose))


def start_ray(enabled: bool) -> Callable[[], None]:
    """
    Start Ray when ``enabled`` and nobody has started it, and give back what stops it: a
    function that shuts Ray down only if it was started here, so that a runtime the user
    started, or connected to a cluster, outlives the run that used it.

    :param enabled: Whether the caller runs on Ray.
    :type enabled: bool
    :return: The function to call when the caller ends, also on the way out of an error.
    :rtype: Callable[[], None]
    """
    # The same lines were in run() and in the distributed launcher of CVOA, and a fix made
    # to one of them reached the other later: F-21 and F-44 (O-01).
    if not enabled:
        return lambda: None
    import ray
    if ray.is_initialized():
        return lambda: None
    ray.init()

    def stop() -> None:
        if ray.is_initialized():
            ray.shutdown()

    return stop
