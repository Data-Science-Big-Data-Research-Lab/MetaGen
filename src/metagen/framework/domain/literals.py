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
from typing import (Final, List, Literal, Mapping, Optional,
                    Tuple, TypeAlias, Union)

DF_META = Literal["DEFINITION"]
DF: Final = "DEFINITION"

I_META = Literal["INTEGER"]
I: Final = "INTEGER"
R_META = Literal["REAL"]
R: Final = "REAL"
C_META = Literal["CATEGORICAL"]
C: Final = "CATEGORICAL"
D_META = Literal["DYNAMIC"]
D: Final = "DYNAMIC"
S_META = Literal["STATIC"]
S: Final = "STATIC"

METAGEN_TYPE = Literal["DEFINITION", "INTEGER",
                       "REAL", "CATEGORICAL", "DYNAMIC", "STATIC"]

BacicVal: TypeAlias = Union[int, float, str, List[int], List[float], List[str]]
DefVal: TypeAlias = Mapping[str, Union[BacicVal, "DefVal"]]
CatVal: TypeAlias = Union[List[int], List[float], List[str]]
StrVal: TypeAlias = Union[List[int], List[float], List[str], List[DefVal]]
MetaVal: TypeAlias = Union[BacicVal,
                           Mapping[str, Union[BacicVal, DefVal]], StrVal]

IntAttr: TypeAlias = Tuple[I_META, int, int, Optional[int]]
RealAttr: TypeAlias = Tuple[R_META, float, float, Optional[float]]
CatAttr: TypeAlias = Tuple[C_META, CatVal]
BaseAttr: TypeAlias = Union[IntAttr, RealAttr, CatAttr]
DefAttr: TypeAlias = Tuple[DF_META, Mapping[str, Union[BaseAttr, "DefAttr"]]]
DymAttr: TypeAlias = Tuple[D_META, int, int,
                           Optional[int], Union[BaseAttr, DefAttr, None]]
StaAttr: TypeAlias = Tuple[S_META, int, Union[BaseAttr, DefAttr, None]]
Attributes: TypeAlias = Union[BaseAttr, DefAttr, DymAttr, StaAttr]

DefType: TypeAlias = Mapping[str, Attributes]
