from itertools import pairwise
from typing import TypeAlias, Tuple, Literal, Union, List, Dict, Final, Any, Mapping, Sequence

# PYCVOA literals
INTEGER: Final = "INTEGER"
REAL: Final = "REAL"
CATEGORICAL: Final = "CATEGORICAL"
LAYER: Final = "LAYER"
VECTOR: Final = "VECTOR"
BASIC: Final = "BASIC"
NUMERICAL: Final = "NUMERICAL"
BASICS: Final = ("INTEGER", "REAL", "CATEGORICAL")
NUMERICALS: Final = ("INTEGER", "REAL")

# PYCVOA literals
INTEGER_TYPE = Literal["INTEGER"]
REAL_TYPE = Literal["REAL"]
CATEGORICAL_TYPE = Literal["CATEGORICAL"]
LAYER_TYPE = Literal["LAYER"]
VECTOR_TYPE = Literal["VECTOR"]
PYCVOA_TYPE = Literal["INTEGER", "REAL", "CATEGORICAL", "LAYER", "VECTOR", "BASIC", "NUMERICAL"]

# PYCVOA variable values
BasicValue: TypeAlias = Union[int, float, str]
Categories: TypeAlias = Union[List[int], List[float], List[str]]
LayerValue: TypeAlias = Dict[str, BasicValue]
VectorValueI: TypeAlias = Union[List[int], List[float], List[str], List[LayerValue]]
BasicVectorValue: TypeAlias = Union[List[int], List[float], List[str]]

# CategoryList: TypeAlias = Sequence[BasicValue]


BasicValueList: TypeAlias = List[BasicValue]
LayerValueList: TypeAlias = List[LayerValue]

IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, Categories]
BasicDef: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef]
NumericalDef: TypeAlias = Union[IntegerDef, RealDef]
NumericalAttributes: TypeAlias = Union[Tuple[int, int, int], Tuple[float, float, float]]
LayerAttributes: TypeAlias = Union[Dict[str, BasicDef], Dict]
LayerDef: TypeAlias = Tuple[LAYER_TYPE, LayerAttributes]
ComponentDef: TypeAlias = Union[BasicDef, LayerDef]
VectorDef: TypeAlias = Tuple[VECTOR_TYPE, int, int, int, Union[ComponentDef, None]]
VectorAttributes: TypeAlias = Tuple[int, int, int]
VarDefinition: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, VectorDef]
DefStructure: TypeAlias = Dict[str, VarDefinition]

# VALUES types
OptInt: TypeAlias = int | None
OptFloat: TypeAlias = float | None
OptStr: TypeAlias = str | None
OptDict: TypeAlias = dict | None
NumericaVectorValues: TypeAlias = List[int] | List[float]
IntOrIntList: TypeAlias = int | List[int]

NumericalValue: TypeAlias = int | float
VectorValue: TypeAlias = Union[BasicValueList, LayerValueList]
SupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue]
OptSupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue, None]
VarStructureType: TypeAlias = Dict[str, SupportedValues]
LayerVectorValue: TypeAlias = List[LayerValue]
OptLayerValue: TypeAlias = Union[LayerValue, None]

LayerInput: TypeAlias = Mapping[str, BasicValue]
VectorInput: TypeAlias = Union[Sequence[int], Sequence[float], Sequence[str], Sequence[LayerInput]]
BasicVectorInput: TypeAlias = Union[Sequence[int], Sequence[float], Sequence[str]]
LayerVectorInput: TypeAlias = Sequence[LayerInput]
SupportedInput: TypeAlias = Union[BasicValue, LayerInput, VectorInput]


def is_basic_value(value: Any) -> bool:
    r = False
    if isinstance(value, (int, float, str)):
        r = True
    return r


def is_categories_value(value: Any):
    r = False
    if is_basic_vector_value(value) and len(value) >= 2:
        r = True
    return r


def is_layer_value(value: Any) -> bool:
    r = False
    if isinstance(value, dict):
        r = all(isinstance(k, str) and is_basic_value(v)
                for k, v in list(value.items()))
    return r


def is_basic_vector_value(value: Any) -> bool:
    r = False
    if isinstance(value, list):
        r = all(type(x) == type(y) and is_basic_value(x)
                for x, y in pairwise(value))
    return r


def is_layer_vector_value(value: Any) -> bool:
    r = False
    if isinstance(value, list):
        r = all(is_layer_value(x) for x in value)
    return r
