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
from .common_tools import StrainProperties
from .probabilistic_cvoa import ProbabilisticCVOA
from .cvoa import CVOA
from .local_launcher import cvoa_launcher
from metagen.metaheuristics.import_helper import is_package_installed

__all__ = ["CVOA", "ProbabilisticCVOA", "StrainProperties", "cvoa_launcher"]
if is_package_installed("ray"):
    __all__ += ["distributed_cvoa_launcher"]


def __getattr__(name: str) -> object:
    # The launcher on Ray, imported when it is first asked for: imported with the package, it
    # started Ray's own import for every run (O-14 of the independent audit).
    if name == "distributed_cvoa_launcher":
        from .distributed_launcher import distributed_cvoa_launcher
        return distributed_cvoa_launcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


