from types import UnionType
from typing import Tuple, Any, Type, cast

from pycvoa.control.types import PYCVOA_TYPE, BASIC, BASICS, NUMERICAL, NUMERICALS, Basic, is_basic_value, Categories, \
    Layer, is_layer_vector_value, Vector, BasicVector, LayerVector


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


def check_basic_arguments(parameters: list[Tuple[Any, Type[int] | Type[float] | Type[str] | UnionType]]):
    fails = list()
    for e in parameters:
        if not isinstance(e[0], e[1]):
            fails.append(str(e[0]) + " must be " + str(e[1]))
    if len(fails) != 0:
        raise TypeError("Argument type errors: " + " , ".join(fails))


def check_basic_value(value: Basic):
    if not is_basic_value(value):
        raise TypeError("The parameter must be a BASIC value (int, float, str).")


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


def check_layer(layer: Layer | None):
    if layer is not None:
        if not isinstance(layer, dict):
            raise TypeError("The layer parameter must be a dict.")
        for k, v in layer.items():
            if not isinstance(k, str):
                raise ValueError(
                    "The element " + str(k) + " must be str.")
            if not is_basic_value(v):
                raise ValueError(
                    "The value " + str(v) + " of the element" + str(k) + " must be int, float or str.")


def __first_componet_type(vector: Any):
    if not isinstance(vector, list):
        raise TypeError("The VECTOR parameter must be a list.")
    if is_basic_value(vector[0]):
        r = "b"
    elif is_layer_vector_value(vector[0]):
        r = "l"
    else:
        raise ValueError("The 0-nh component of the VECTOR parameter must be a BASIC (int, float, str) or LAYER value")
    return r


def __process_remaining_components(vector: list, first_type: str):
    i = 1
    if first_type == "b":
        while i < len(vector):
            if not is_basic_value(vector[i]):
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
            if not is_layer_value(vector[i]):
                raise ValueError(
                    "The  " + str(i) + "-nh component of the LAYER VECTOR parameter must be a LAYER value")
            i += 1


def check_vector(vector: Vector):
    __process_remaining_components(cast(list, vector), __first_componet_type(vector[0]))


def check_basic_vector(basic_vector: BasicVector):
    ft = __first_componet_type(basic_vector[0])
    if ft != "b":
        raise ValueError("The 0-nh component of the BASIC VECTOR parameter must be a BASIC value (int, float, str)")
    __process_remaining_components(cast(list, basic_vector), ft)


def check_layer_vector(layer_vector: LayerVector):
    ft = __first_componet_type(layer_vector[0])
    if ft != "l":
        raise ValueError("The 0-nh component of the LAYER VECTOR parameter must be a LAYER")
    __process_remaining_components(cast(list, layer_vector), ft)
