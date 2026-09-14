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

    This class implements the *CVOA* algorithm. It uses the :py:class:`~metagen.framework.Solution` class as an
    abstraction of an individual for the meta-heuristic.

    It solves an optimization problem defined by a :py:class:`~metagen.framework.Domain` object and an
    implementation of a fitness function.

    By instantiate :py:class:`~metagen.metaheuristics.CVOA` object, i.e. a strain, the configuration parameters must be provided.

    This class supports multiple strain execution by means of multy-threading. Each strain
    (:py:class:`~metagen.metaheuristics.CVOA` object) will execute its *CVOA* algorithm (:py:meth:`~metagen.metaheuristics.CVOA.cvoa`)
    in a thread and, finally, the best :py:class:`~metagen.framework.Solution` (i.e. the best fitness function
    is obtained).

    To launch a multi-strain execution, this module provides the :py:meth:`~metagen.metaheuristics.cvoa_launcher`
    method.

    :param strain_id: The strain name
    :param pandemic_duration: The pandemic duration, defaults to 30
    :param spreading_rate: The spreading rate, defaults to 5
    :param min_super_spreading_rate: The minimum super spreading rate, defaults to 6
    :param max_super_spreading_rate: The maximum super spreading rate, defaults to 15
    :param social_distancing: The iteration from which social distancing applies, defaults to 7
    :param p_isolation: The probability of an individual being isolated, defaults to 0.7
    :param p_travel: The probability that an individual will travel, defaults to 0.1
    :param p_re_infection: The probability of an individual being re-infected, defaults to 0.02
    :param p_superspreader: The probability of an individual being a super-spreader, defaults to 0.1
    :param p_die: The probability that an individual will die, defaults to 0.05
    :param verbose: The verbosity option, defaults to True
    :type strain_id: str
    :type pandemic_duration: int
    :type spreading_rate: int
    :type min_super_spreading_rate: int
    :type max_super_spreading_rate: int
    :type social_distancing: int
    :type p_isolation: float
    :type p_travel: float
    :type p_re_infection: float
    :type p_superspreader: float
    :type p_die: float
    :type verbose: bool

    Since A-09 this is CVOA with ``distributed=True``: the same class, spreading on
    Ray with one task per carrier and talking to the RemotePandemicState actor through
    a proxy. It is kept so that published code and documentation keep working.
    """

    def __init__(self, global_state: PandemicStateHandle, domain: Domain, fitness_function: Callable[[Solution], float],
                 strain_properties: StrainProperties = StrainProperties(), update_isolated: bool = False,
                 log_dir: Optional[str] = None, detailed_info: bool = False, distributed: bool = True):
        super().__init__(global_state, domain, fitness_function, strain_properties, update_isolated, log_dir,
                         distributed=True, detailed_info=detailed_info)
