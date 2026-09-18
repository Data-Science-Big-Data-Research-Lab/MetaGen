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

from typing import Callable, Optional

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.metaheuristics.cvoa.common_tools import StrainProperties
from metagen.metaheuristics.cvoa.cvoa_local import CVOA
from metagen.metaheuristics.cvoa.distributed_tools import PandemicStateHandle


class DistributedCVOA(CVOA):
    """
    :py:class:`~metagen.metaheuristics.cvoa.cvoa_local.CVOA` with ``distributed=True``, kept for
    backward compatibility: a strain whose infection is spread as Ray tasks over a pandemic
    state that lives in a Ray actor. It adds nothing but the constructor; strains are run through
    :py:func:`~metagen.metaheuristics.cvoa.distributed_launcher.distributed_cvoa_launcher`.
    """

    def __init__(self, global_state: PandemicStateHandle, domain: Domain, fitness_function: Callable[[Solution], float],
                 strain_properties: StrainProperties = StrainProperties(), update_isolated: bool = False,
                 log_dir: Optional[str] = None, detailed_info: bool = False, distributed: bool = True):
        super().__init__(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir,
                         distributed=True, detailed_info=detailed_info)
