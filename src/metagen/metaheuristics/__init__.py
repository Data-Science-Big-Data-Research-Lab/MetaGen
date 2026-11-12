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
from metagen.metaheuristics import _renamed_modules
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.cvoa import CVOA, ProbabilisticCVOA, StrainProperties, cvoa_launcher
from metagen.metaheuristics.gamma_schedules import GammaConfig
from metagen.metaheuristics.genetic import GA, SSGA, GAConnector, GASolution, GAStructure
from metagen.metaheuristics.genetic.genetic_tools import GAInteger, GAReal
from metagen.metaheuristics.simulated_annealing import SA
from metagen.metaheuristics.hill_climbing import HillClimbing
from metagen.metaheuristics.tabu_search import TabuSearch
from metagen.metaheuristics.tpe import TPE, KernelTPE
from metagen.metaheuristics.random_search import RandomSearch
from metagen.metaheuristics.memetic import Memetic
from metagen.metaheuristics.trigen import TriGen, TriGenGA, TriGenResult, TriclusterFitness
from metagen.metaheuristics.trigen.report import trigen_report
from metagen.metaheuristics.trigen.shape import prism_parts
from metagen.metaheuristics.tools import local_search, local_search_with_tabu, random_exploration, solution_class
from metagen.metaheuristics.import_helper import is_package_installed
from metagen.metaheuristics.racing import Racing

# The module paths of earlier releases (metagen.metaheuristics.ga, ...rs, ...) stay importable.
_renamed_modules.install()

# Memetic is exported whether or not Ray is installed: memetic_tools imports it only
# for a distributed run (F-24).
# What the package offers: the algorithms, and what writing one of your own takes (the base
# class, the connector and types of the genetic algorithms, the tools the algorithms are
# built from). It is the public API: what is not here, or in the __all__ of
# metagen.framework, metagen.framework.domain, metagen.framework.solution,
# metagen.triclustering, metagen.triclustering.data, metagen.reporting or metagen.logging,
# may move between releases. The documentation imports from nowhere else.
__all__ = ["RandomSearch", "GA", "SSGA", "SA", "HillClimbing", "TabuSearch", "TPE", "KernelTPE", "Memetic",
           "CVOA", "ProbabilisticCVOA", "StrainProperties", "cvoa_launcher",
           "TriGen", "TriGenGA", "TriGenResult", "TriclusterFitness", "trigen_report", "prism_parts",
           "Racing", "GammaConfig", "Metaheuristic", "GAConnector", "GASolution", "GAStructure", "GAInteger", "GAReal",
           "random_exploration", "local_search", "local_search_with_tabu", "solution_class"]

#: The names that need Ray, imported when they are first asked for, so that the package
#: imports without it.
_WITH_RAY = {"DistributedCVOA": "metagen.metaheuristics.cvoa.distributed_cvoa",
             "distributed_cvoa_launcher": "metagen.metaheuristics.cvoa.distributed_launcher"}
if is_package_installed("ray"):
    __all__ += list(_WITH_RAY)


def __getattr__(name: str) -> object:
    if name in _WITH_RAY:
        import importlib
        return getattr(importlib.import_module(_WITH_RAY[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
