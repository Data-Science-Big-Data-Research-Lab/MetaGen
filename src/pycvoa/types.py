from typing import TypeAlias, Tuple, Literal, Union, List, Dict, Final

# PYCVOA literals
INTEGER: Final = "INTEGER"
REAL: Final = "REAL"
CATEGORICAL: Final = "CATEGORICAL"
LAYER: Final = "LAYER"
VECTOR: Final = "VECTOR"
BASIC: Final = ("BASIC", "INTEGER", "REAL", "CATEGORICAL")
NUMERICAL: Final = ("NUMERICAL", "INTEGER", "REAL")


# PYCVOA literals
INTEGER_TYPE = Literal["INTEGER"]
REAL_TYPE = Literal["REAL"]
CATEGORICAL_TYPE = Literal["CATEGORICAL"]
LAYER_TYPE = Literal["LAYER"]
VECTOR_TYPE = Literal["VECTOR"]


IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
NumericalDef: TypeAlias = Union[IntegerDef, RealDef]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, List[int] | List[float] | List[str]]
BasicDef: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef]
LayerDef: TypeAlias = Tuple[LAYER_TYPE, Dict[str, BasicDef]]
ComponentDef: TypeAlias = Union[BasicDef, LayerDef, None]
VectorDef: TypeAlias = List
VarDefinition: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, VectorDef]
DefStructure: TypeAlias = Dict[str, VarDefinition]

# LAYER definition type
LayerAttributes: TypeAlias = dict[str, BasicDef]
NumericalAttributes: TypeAlias = Union[Tuple[int, int, int], Tuple[float, float, float]]
VectorAttributes: TypeAlias = Tuple[int, int, int]



OptInt: TypeAlias = int | None
OptFloat: TypeAlias = float | None
OptStr: TypeAlias = str | None
OptDict: TypeAlias = dict | None
NumericaVectorValues: TypeAlias = list[int] | list[float]
IntOrIntList: TypeAlias = int | list[int]
BasicValueList: TypeAlias = list[str] | list[int] | list[float]

# VALUES types
BasicValue: TypeAlias = int | float | str
LayerValue: TypeAlias = dict[str, BasicValue]
VectorValue: TypeAlias = Union[list[int], list[float], list[str], list[LayerValue]]
SupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue]
OptSupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue, None]
VarStructureType: TypeAlias = dict[str, SupportedValues]
LayerVectorValue: TypeAlias = list[LayerValue]
OptLayerValue: TypeAlias = Union[LayerValue, None]
