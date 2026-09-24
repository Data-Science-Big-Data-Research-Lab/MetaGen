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