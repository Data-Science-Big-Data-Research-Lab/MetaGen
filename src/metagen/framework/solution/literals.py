from typing import Dict, Final, List, Literal, Tuple, TypeAlias, Union

INTEGER: Final = "INTEGER"
REAL: Final = "REAL"
CATEGORICAL: Final = "CATEGORICAL"
LAYER: Final = "LAYER"
VECTOR: Final = "VECTOR"
SEQUENCE: Final = "SEQUENCE"
BASIC: Final = "BASIC"
NUMERICAL: Final = "NUMERICAL"
BASICS: Final = ("INTEGER", "REAL", "CATEGORICAL")
NUMERICALS: Final = ("INTEGER", "REAL")
INTEGER_TYPE = Literal["INTEGER"]
REAL_TYPE = Literal["REAL"]
CATEGORICAL_TYPE = Literal["CATEGORICAL"]
LAYER_TYPE = Literal["LAYER"]
VECTOR_TYPE = Literal["VECTOR"]
SEQUENCE_TYPE = Literal["SEQUENCE"]
METAGEN_TYPE = Literal["INTEGER", "REAL", "CATEGORICAL", "LAYER", "VECTOR", "SEQUENCE", "BASIC", "NUMERICAL"]

Basic: TypeAlias = Union[int, float, str]
Categories: TypeAlias = Union[List[int], List[float], List[str]]
BasicVector: TypeAlias = Union[List[int], List[float], List[str]]

SolLayer: TypeAlias = Dict[str, Basic]
SolLayerVector: TypeAlias = List[SolLayer]
SolVector: TypeAlias = Union[BasicVector, SolLayerVector]
InputValue: TypeAlias = Union[Basic, SolLayer, SolVector]
OutputValue: TypeAlias = Union[None, Basic, SolLayer, SolVector]

SolStructure: TypeAlias = Dict[str, InputValue]
IntegerDef: TypeAlias = Tuple[INTEGER_TYPE, int, int, int]
RealDef: TypeAlias = Tuple[REAL_TYPE, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL_TYPE, Categories]
BasicDef: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef]
NumericalDef: TypeAlias = Union[IntegerDef, RealDef]
NumericalAttributes: TypeAlias = Union[Tuple[int, int, int], Tuple[float, float, float]]
LayerAttributes: TypeAlias = Union[Dict[str, BasicDef], Dict]
BasicAttributes: TypeAlias = Union[NumericalAttributes, Categories]
LayerDef: TypeAlias = Tuple[LAYER_TYPE, LayerAttributes]
ComponentDef: TypeAlias = Union[BasicDef, LayerDef]
VectorDef: TypeAlias = Tuple[VECTOR_TYPE, int, int, int, Union[ComponentDef, None]]
SequenceDef: TypeAlias = Tuple[SEQUENCE_TYPE, int, Union[ComponentDef, None]]
VectorAttributes: TypeAlias = Tuple[int, int, int]
VarDefinition: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, VectorDef, SequenceDef]
DefStructure: TypeAlias = Dict[str, VarDefinition]
