from typing import TypeAlias, Tuple, Literal, Union, List, Dict

BASIC = ("BASIC", "INTEGER", "REAL", "CATEGORICAL")
NUMERICAL = ("NUMERICAL", "INTEGER", "REAL")

# PYCVOA literals
INTEGER = Literal["INTEGER"]
REAL = Literal["REAL"]
CATEGORICAL = Literal["CATEGORICAL"]
LAYER = Literal["LAYER"]
VECTOR = Literal["VECTOR"]

IntegerDef: TypeAlias = Tuple[INTEGER, int, int, int]
RealDef: TypeAlias = Tuple[REAL, float, float, float]
CategoricalDef: TypeAlias = Tuple[CATEGORICAL, List[int] | List[float] | List[str]]
LayerDef: TypeAlias = Tuple[LAYER, Dict[str, Union[IntegerDef]]]
ComponentDef: TypeAlias = Union[IntegerDef, RealDef, CategoricalDef, LayerDef, None]
VectorDef: TypeAlias = Tuple[VECTOR, int, int, int, ComponentDef]


entero_1: IntegerDef = ("INTEGER", 1, 1, 1)
layer: LayerDef = ("LAYER", {"e1": ("INTEGER", 1, 1, 1)})


def t1(el: str, p1: int, p2: int, p3: int):
    r = layer[1]
    r[el] = ("INTEGER", p1, p2, p3)
