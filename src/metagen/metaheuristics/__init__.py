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
from metagen.metaheuristics.import_helper import is_package_installed
from metagen.metaheuristics.cvoa import cvoa_launcher
from metagen.metaheuristics.ga import GA, SSGA, GAConnector
from metagen.metaheuristics.sa import SA
from metagen.metaheuristics.ts import TabuSearch
from metagen.metaheuristics.tpe import TPE
from metagen.metaheuristics.rs import RandomSearch

export = ["RandomSearch", "GA", "SSGA", "GAConnector", "SA", "TPE", "cvoa_launcher", "TabuSearch"]

if is_package_installed("ray"):
    from metagen.metaheuristics.mm import Memetic
    export.append("Memetic")
    

__all__ = export











