from typing import Final, TypeAlias, Tuple, Literal, Union
from pycvoa.problem import Domain

INTEGER = Literal["INTEGER"]
INTEGER_TYPE: TypeAlias = Literal["INTEGER"]
REAL = Literal["REAL"]
REAL_TYPE: TypeAlias = Literal["REAL"]
CATEGORICAL_TYPE: TypeAlias = Literal["CATEGORICAL"]
CATEGORICAL = Literal["CATEGORICAL"]
LAYER_TYPE: TypeAlias = Literal["LAYER"]
LAYER = Literal["LAYER"]
VECTOR_TYPE: TypeAlias = Literal["VECTOR"]
VECTOR = Literal["VECTOR"]
BASIC_TYPE: TypeAlias = Union[INTEGER_TYPE, REAL_TYPE, CATEGORICAL_TYPE]
BASIC = Literal["INTEGER", "REAL", "CATEGORICAL"]
NUMERICAL_TYPE: TypeAlias = Union[INTEGER_TYPE, REAL_TYPE]
NUMERICAL = Literal["INTEGER", "REAL"]
PYCVOA_TYPE: TypeAlias = Union[INTEGER_TYPE, REAL_TYPE, CATEGORICAL_TYPE, LAYER_TYPE, VECTOR_TYPE]

IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, list[int] | list[float] | list[str]]
BasicDef: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef]
LayerDef: TypeAlias = Tuple[LAYER_TYPE, dict[str, Union[IntegerDef, RealDef, CategoricalDef]]]
VectorDef: TypeAlias = Tuple[VECTOR_TYPE, int, int, int, Union[IntegerDef, RealDef, CategoricalDef, LayerDef, None]]
BasicVectorDef: TypeAlias = Tuple[VECTOR_TYPE, int, int, int, Union[IntegerDef, RealDef, CategoricalDef]]
LayerVectorDef: TypeAlias = Tuple[VECTOR_TYPE, int, int, int, LayerDef]
VarDefinition: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, VectorDef]
DefStructure: TypeAlias = dict[str, VarDefinition]

OptInt: TypeAlias = int | None
OptFloat: TypeAlias = float | None
OptStr: TypeAlias = str | None
OptDict: TypeAlias = dict | None
NumericaVectorValues: TypeAlias = list[int] | list[float]
IntOrIntList: TypeAlias = int | list[int]
BasicVectorValues: TypeAlias = list[str] | list[int] | list[float]
OptDomain: TypeAlias = Union[Domain, None]

BasicValue: TypeAlias = int | float | str
LayerValue: TypeAlias = dict[str, BasicValue]
VectorValue: TypeAlias = Union[list[int], list[float], list[str], list[LayerValue]]
SupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue]
OptSupportedValues: TypeAlias = Union[BasicValue, LayerValue, VectorValue, None]
VarStructureType: TypeAlias = dict[str, SupportedValues]
LayerVectorValue: TypeAlias = list[LayerValue]
OptLayerValue: TypeAlias = Union[LayerValue, None]

