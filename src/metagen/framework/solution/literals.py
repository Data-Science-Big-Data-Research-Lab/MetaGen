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
from typing import Dict, List, TypeAlias, Union

Basic: TypeAlias = Union[int, float, str]
BasicVector: TypeAlias = Union[List[int], List[float], List[str]]

SolLayer: TypeAlias = Dict[str, Basic]
SolLayerVector: TypeAlias = List[SolLayer]
SolVector: TypeAlias = Union[BasicVector, SolLayerVector]
InputValue: TypeAlias = Union[Basic, SolLayer, SolVector]

