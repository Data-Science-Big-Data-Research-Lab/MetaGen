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
from .local_launcher import cvoa_launcher
from metagen.metaheuristics.import_helper import is_package_installed

if is_package_installed("ray"):
    
    from .distributed_launcher import distributed_cvoa_launcher
    __all__ = ["cvoa_launcher", "distributed_cvoa_launcher"]

else:
    __all__ = ["cvoa_launcher"]


