from typing import TypeAlias, Tuple, Literal, Union, List, Dict, Final, Any

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

BasicValue: TypeAlias = int | float | str
LayerValue: TypeAlias = Dict[str, BasicValue]
BasicValueList: TypeAlias = List[BasicValue]
LayerValueList: TypeAlias = List[LayerValue]
CategoryList: TypeAlias = Union[List[int], List[float], List[str]]

IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, CategoryList]
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
VectorValue: TypeAlias = Union[BasicValueList, List[LayerValue]]
SupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue]
OptSupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue, None]
VarStructureType: TypeAlias = Dict[str, SupportedValues]
LayerVectorValue: TypeAlias = List[LayerValue]
OptLayerValue: TypeAlias = Union[LayerValue, None]


def is_layer_value(value: Any) -> bool:
    r = True
    if type(value) is dict:
        i = 0
        while r and i < len(value.keys()):
            if type(value.keys()[i]) != str:
                r = False
            i += 1
        if r:
            i = 0
            while r and i < len(value.values()):
                if type(value.values()[i]) not in [int, float, str]:
                    r = False
                i += 1
    return r


def is_layer_vector_value(value: Any) -> bool:
    r = True
    if type(value) is list:
        i = 0
        while r and i < len(value):
            if not is_layer_value(value[i]):
                r = False
            i += 1
    return r


def is_basic_vector_value(value: Any) -> bool:
    r = False
    if isinstance(value, list):
        if isinstance(value[0], Union[int, float, str]):
            i = 1
            r = True
            while r and i < len(value):
                if not isinstance(value[i], type(value[0])):
                    r = False
                i += 1

    return r
