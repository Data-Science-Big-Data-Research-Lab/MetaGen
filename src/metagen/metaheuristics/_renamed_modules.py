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
"""
Module paths of earlier releases, kept importable.

The modules of the metaheuristics are named after their algorithm. Code written against
the earlier short names (``metagen.metaheuristics.ga``, ``...rs``, ``...cvoa.cvoa_local``...)
keeps working: importing one of them returns the module under its current name, the same
object, and emits a ``DeprecationWarning`` that gives the name to use instead.
"""
import importlib
import importlib.abc
import importlib.machinery
import importlib.util
import sys
import warnings
from types import ModuleType
from typing import Dict, Optional, Sequence

_PREFIX = "metagen.metaheuristics."

#: Former module path, relative to ``metagen.metaheuristics``, and its current one.
RENAMED_MODULES: Dict[str, str] = {
    "rs": "random_search",
    "rs.random_search": "random_search.random_search",
    "hc": "hill_climbing",
    "hc.hill_climbing": "hill_climbing.hill_climbing",
    "ts": "tabu_search",
    "ts.tabu_search": "tabu_search.tabu_search",
    "sa": "simulated_annealing",
    "sa.sa": "simulated_annealing.simulated_annealing",
    "ga": "genetic",
    "ga.ga": "genetic.genetic_algorithm",
    "ga.ssga": "genetic.steady_state_genetic_algorithm",
    "ga.ga_tools": "genetic.genetic_tools",
    "mm": "memetic",
    "mm.memetic": "memetic.memetic",
    "mm.mm_tools": "memetic.memetic_tools",
    "mm.mm_distributed_tools": "memetic.memetic_distributed_tools",
    "cvoa.cvoa_local": "cvoa.cvoa",
    "cvoa.cvoa_probabilistic": "cvoa.probabilistic_cvoa",
    "cvoa.cvoa_distributed": "cvoa.distributed_cvoa",
    "cvoa.distributed_tools": "cvoa.ray_tools",
    "cvoa.local_tools": "cvoa.local_state",
}


class _RenamedModuleFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Resolves a former module path to the module under its current name."""

    def find_spec(self, fullname: str, path: Optional[Sequence[str]],
                  target: Optional[ModuleType] = None) -> Optional[importlib.machinery.ModuleSpec]:
        if not fullname.startswith(_PREFIX) or fullname[len(_PREFIX):] not in RENAMED_MODULES:
            return None
        return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec: importlib.machinery.ModuleSpec) -> ModuleType:
        current = _PREFIX + RENAMED_MODULES[spec.name[len(_PREFIX):]]
        warnings.warn(f"{spec.name} is now {current}; the former path will be removed in a future "
                      f"major version.", DeprecationWarning, stacklevel=2)
        return importlib.import_module(current)

    def exec_module(self, module: ModuleType) -> None:
        """The module is already loaded under its current name: nothing to run."""


def install() -> None:
    """Put the finder first on ``sys.meta_path``, once.

    First, because a former path such as ``metagen.metaheuristics.hc.hill_climbing`` ends
    in a file name that still exists: the standard path finder would load that file again
    as a second, separate module.
    """
    if not any(isinstance(finder, _RenamedModuleFinder) for finder in sys.meta_path):
        sys.meta_path.insert(0, _RenamedModuleFinder())
