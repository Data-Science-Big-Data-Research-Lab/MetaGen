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
import warnings
from typing import Any, Dict, List, Literal, Tuple, TypeAlias, Union

Basic: TypeAlias = Union[int, float, str]
BasicVector: TypeAlias = Union[List[int], List[float], List[str]]

SolLayer: TypeAlias = Dict[str, Basic]
SolLayerVector: TypeAlias = List[SolLayer]
SolVector: TypeAlias = Union[BasicVector, SolLayerVector]
InputValue: TypeAlias = Union[Basic, SolLayer, SolVector]


def _old_names() -> Dict[str, Any]:
    """The names of the first versions of the package, which it does not use."""
    INTEGER_TYPE = Literal["INTEGER"]
    REAL_TYPE = Literal["REAL"]
    CATEGORICAL_TYPE = Literal["CATEGORICAL"]
    LAYER_TYPE = Literal["LAYER"]
    VECTOR_TYPE = Literal["VECTOR"]
    SEQUENCE_TYPE = Literal["SEQUENCE"]
    Categories = Union[List[int], List[float], List[str]]
    IntegerDef = Tuple[INTEGER_TYPE, int, int, int]
    RealDef = Tuple[REAL_TYPE, float, float, float]
    CategoricalDef = Tuple[CATEGORICAL_TYPE, Categories]
    BasicDef = Union[IntegerDef, RealDef, CategoricalDef]
    NumericalAttributes = Union[Tuple[int, int, int], Tuple[float, float, float]]
    LayerAttributes = Union[Dict[str, BasicDef], Dict]
    LayerDef = Tuple[LAYER_TYPE, LayerAttributes]
    ComponentDef = Union[BasicDef, LayerDef]
    VectorDef = Tuple[VECTOR_TYPE, int, int, int, Union[ComponentDef, None]]
    SequenceDef = Tuple[SEQUENCE_TYPE, int, Union[ComponentDef, None]]
    VarDefinition = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, VectorDef, SequenceDef]
    return {
        "INTEGER": "INTEGER", "REAL": "REAL", "CATEGORICAL": "CATEGORICAL", "LAYER": "LAYER",
        "VECTOR": "VECTOR", "SEQUENCE": "SEQUENCE", "BASIC": "BASIC", "NUMERICAL": "NUMERICAL",
        "BASICS": ("INTEGER", "REAL", "CATEGORICAL"), "NUMERICALS": ("INTEGER", "REAL"),
        "INTEGER_TYPE": INTEGER_TYPE, "REAL_TYPE": REAL_TYPE, "CATEGORICAL_TYPE": CATEGORICAL_TYPE,
        "LAYER_TYPE": LAYER_TYPE, "VECTOR_TYPE": VECTOR_TYPE, "SEQUENCE_TYPE": SEQUENCE_TYPE,
        "METAGEN_TYPE": Literal["INTEGER", "REAL", "CATEGORICAL", "LAYER", "VECTOR", "SEQUENCE", "BASIC", "NUMERICAL"],
        "Categories": Categories, "OutputValue": Union[None, Basic, SolLayer, SolVector],
        "SolStructure": Dict[str, InputValue], "IntegerDef": IntegerDef, "RealDef": RealDef,
        "CategoricalDef": CategoricalDef, "BasicDef": BasicDef, "NumericalDef": Union[IntegerDef, RealDef],
        "NumericalAttributes": NumericalAttributes, "LayerAttributes": LayerAttributes,
        "BasicAttributes": Union[NumericalAttributes, Categories], "LayerDef": LayerDef,
        "ComponentDef": ComponentDef, "VectorDef": VectorDef, "SequenceDef": SequenceDef,
        "VectorAttributes": Tuple[int, int, int], "VarDefinition": VarDefinition,
        "DefStructure": Dict[str, VarDefinition],
    }


def __getattr__(name: str) -> Any:
    # Some forty names, of which the package uses three (OF-13 of the independent audit):
    # the rest can still be imported, with a warning, until version 2.0.
    old = _old_names()
    if name in old:
        warnings.warn(f"metagen.framework.solution.literals.{name} is deprecated and will be removed in "
                      f"version 2.0.", DeprecationWarning, stacklevel=2)
        return old[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
