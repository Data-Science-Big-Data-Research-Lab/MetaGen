from typing import TypeAlias, Tuple, Literal, Union, List, Dict, Final

# PYCVOA literals
INTEGER: Final = "INTEGER"
REAL: Final = "REAL"
CATEGORICAL: Final = "CATEGORICAL"
LAYER: Final = "LAYER"
VECTOR: Final = "VECTOR"
BASIC: Final = "BASIC"
NUMERICAL: Final = "NUMERICAL"
BASIC_PYTYPES: Final = ("INTEGER", "REAL", "CATEGORICAL")
NUMERICAL_PYTYPES: Final = ("INTEGER", "REAL")

# PYCVOA literals
INTEGER_TYPE = Literal["INTEGER"]
REAL_TYPE = Literal["REAL"]
CATEGORICAL_TYPE = Literal["CATEGORICAL"]
LAYER_TYPE = Literal["LAYER"]
VECTOR_TYPE = Literal["VECTOR"]
PYCVOA_TYPE = Literal["INTEGER", "REAL", "CATEGORICAL", "LAYER", "VECTOR", "BASIC", "NUMERICAL"]

BasicValue: TypeAlias = int | float | str
BasicValueList: TypeAlias = List[BasicValue]

IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, BasicValueList]
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
LayerValue: TypeAlias = Dict[str, BasicValue]
VectorValue: TypeAlias = Union[BasicValueList, List[LayerValue]]
SupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue]
OptSupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue, None]
VarStructureType: TypeAlias = Dict[str, SupportedValues]
LayerVectorValue: TypeAlias = List[LayerValue]
OptLayerValue: TypeAlias = Union[LayerValue, None]
