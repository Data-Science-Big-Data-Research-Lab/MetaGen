from itertools import pairwise
from types import UnionType
from typing import TypeAlias, Tuple, Literal, Union, List, Dict, Final, Any, Mapping, Sequence, final, Type, cast

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
INTEGER_TYPE = Literal["INTEGER"]
REAL_TYPE = Literal["REAL"]
CATEGORICAL_TYPE = Literal["CATEGORICAL"]
LAYER_TYPE = Literal["LAYER"]
VECTOR_TYPE = Literal["VECTOR"]
PYCVOA_TYPE = Literal["INTEGER", "REAL", "CATEGORICAL", "LAYER", "VECTOR", "BASIC", "NUMERICAL"]

# PYCVOA BASICS
Basic: TypeAlias = Union[int, float, str]
Categories: TypeAlias = Union[List[int], List[float], List[str]]
BasicVector: TypeAlias = Union[List[int], List[float], List[str]]

# PYCVOA DOMAIN
DomLayer: TypeAlias = Mapping[str, Basic]
DomLayerVector: TypeAlias = Sequence[DomLayer]
DomVector: TypeAlias = Union[BasicVector, DomLayerVector]
DomInput: TypeAlias = Union[Basic, DomLayer, DomVector]

# PYCVOA SOLUTION
SolLayer: TypeAlias = Dict[str, Basic]
SolLayerVector: TypeAlias = List[SolLayer]
SolVector: TypeAlias = Union[BasicVector, SolLayerVector]
Value: TypeAlias = Union[Basic, SolLayer, SolVector]

# PYCVOA GLOBAL
Layer: TypeAlias = Union[DomLayer, SolLayer]
LayerVector: TypeAlias = Union[DomLayerVector, SolLayerVector]
Vector: TypeAlias = Union[DomVector, SolVector]

# STRUCTURES
SolStructure: TypeAlias = Dict[str, Value]
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

# METHODS

@final
class Primitives:
    @staticmethod
    def is_basic_value(value: Any) -> bool:
        r = False
        if isinstance(value, (int, float, str)):
            r = True
        return r

    @staticmethod
    def is_categories_value(value: Any):
        r = False
        if isinstance(value, list):
            if len(value) >= 2:
                r = all(type(x) == type(y) and Primitives.is_basic_value(x) and x != y
                        for x, y in pairwise(value))
        return r

    @staticmethod
    def is_layer_value(value: Any) -> bool:
        r = False
        if isinstance(value, dict):
            r = all(isinstance(k, str) and Primitives.is_basic_value(v)
                    for k, v in list(value.items()))
        return r

    @staticmethod
    def is_basic_vector_value(value: Any) -> bool:
        r = False
        if isinstance(value, list):
            r = all(type(x) == type(y) and Primitives.is_basic_value(x)
                    for x, y in pairwise(value))
        return r

    @staticmethod
    def is_layer_vector_value(value: Any) -> bool:
        r = False
        if isinstance(value, list):
            r = all(Primitives.is_layer_value(x) for x in value)
        return r


@final
class ArgChk:
    @staticmethod
    def check_basic_arguments(parameters: list[Tuple[Any, Type[int] | Type[float] | Type[str] | UnionType]]):
        fails = list()
        for e in parameters:
            if not isinstance(e[0], e[1]):
                fails.append(str(e[0]) + " must be " + str(e[1]))
        if len(fails) != 0:
            raise TypeError("Argument type errors: " + " , ".join(fails))

    @staticmethod
    def is_none(parameter: str, value: Any):
        if value is not None:
            raise ValueError(parameter + " must be None.")

    @staticmethod
    def not_none(parameter: str, value: Any):
        if value is None:
            raise ValueError(parameter + " must not be None.")

    @staticmethod
    def check_item_type(check_type: PYCVOA_TYPE, actual_type: PYCVOA_TYPE) -> bool:
        r = True
        if check_type is BASIC:
            if actual_type not in BASICS:
                r = False
        elif check_type is NUMERICAL:
            if actual_type not in NUMERICALS:
                r = False
        else:
            if actual_type is not check_type:
                r = False
        return r


@final
class ValChk:

    @staticmethod
    def check_basic_value(value: Basic):
        if not Primitives.is_basic_value(value):
            raise TypeError("The parameter must be a BASIC value (int, float, str).")

    @staticmethod
    def check_categories(categories: Categories):
        if not isinstance(categories, list):
            raise TypeError("The categories parameter must be a list.")
        if len(categories) < 2:
            raise ValueError("The categories parameter must have al least two elements.")
        i = 0
        cat_type = type(categories[len(categories) - 1])
        while i < len(categories) - 1:
            if type(categories[i]) is not cat_type:
                raise TypeError(
                    "The categories must have the same type (int, float or str).")
            j = i + 1
            while j < len(categories):
                if categories[i] == categories[j]:
                    raise ValueError(
                        "The categories list can not contain repeated values.")
                else:
                    j += 1
            i += 1

    @staticmethod
    def check_layer(layer: Layer | None):
        if layer is not None:
            if not isinstance(layer, dict):
                raise TypeError("The layer parameter must be a dict.")
            for k, v in layer.items():
                if not isinstance(k, str):
                    raise ValueError(
                        "The element " + str(k) + " must be str.")
                if not Primitives.is_basic_value(v):
                    raise ValueError(
                        "The value " + str(v) + " of the element" + str(k) + " must be int, float or str.")

    @staticmethod
    def __first_componet_type(vector: Any):
        if not isinstance(vector, list):
            raise TypeError("The VECTOR parameter must be a list.")
        if Primitives.is_basic_value(vector[0]):
            r = "b"
        elif Primitives.is_layer_vector_value(vector[0]):
            r = "l"
        else:
            raise ValueError(
                "The 0-nh component of the VECTOR parameter must be a BASIC (int, float, str) or LAYER value")
        return r

    @staticmethod
    def __process_remaining_components(vector: list, first_type: str):
        i = 1
        if first_type == "b":
            while i < len(vector):
                if not Primitives.is_basic_value(vector[i]):
                    raise ValueError(
                        "The  " + str(i) + "-nh component of the BASIC VECTOR parameter must be a BASIC value ("
                                           "int, float, str)")
                if type(vector[i]) != type(vector[0]):
                    raise ValueError(
                        "The  " + str(i) + "-nh component  of the BASIC VECTOR parameter type differs from the "
                                           "rest")
                i += 1
        elif first_type == "l":
            while i < len(vector):
                if not Primitives.is_layer_value(vector[i]):
                    raise ValueError(
                        "The  " + str(i) + "-nh component of the LAYER VECTOR parameter must be a LAYER value")
                i += 1

    @staticmethod
    def check_vector(vector: Vector):
        ValChk.__process_remaining_components(cast(list, vector), ValChk.__first_componet_type(vector[0]))

    @staticmethod
    def check_basic_vector(basic_vector: BasicVector):
        ft = ValChk.__first_componet_type(basic_vector[0])
        if ft != "b":
            raise ValueError("The 0-nh component of the BASIC VECTOR parameter must be a BASIC value (int, float, str)")
        ValChk.__process_remaining_components(cast(list, basic_vector), ft)

    @staticmethod
    def check_layer_vector(layer_vector: LayerVector):
        ft = ValChk.__first_componet_type(layer_vector[0])
        if ft != "l":
            raise ValueError("The 0-nh component of the LAYER VECTOR parameter must be a LAYER")
        ValChk.__process_remaining_components(cast(list, layer_vector), ft)
