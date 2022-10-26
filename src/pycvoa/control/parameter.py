import math
from types import NoneType, UnionType
from typing import Any, Tuple, Type, Optional

from pycvoa.control.types import OptInt, OptFloat, OptStr, is_layer_value, is_layer_vector_value, \
    is_basic_vector_value, is_basic_value, Categories, LayerValue, BasicValue, BasicVectorValue, VectorValue


def check_basic_arguments(parameters: list[Tuple[Any, Type[int] | Type[float] | Type[str] | UnionType]]):
    fails = list()
    for e in parameters:
        if not isinstance(e[0], e[1]):
            fails.append(str(e[0]) + " must be " + str(e[1]))
    if len(fails) != 0:
        raise TypeError("Argument type errors: " + " , ".join(fails))


def check_basic_value(value: BasicValue):
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


def check_layer(layer: LayerValue | None):
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


def check_basic_vector(basic_vector: VectorValueI):
    if not isinstance(basic_vector, list):
        raise TypeError("The BASIC VECTOR parameter must be a list.")
    first = basic_vector[0]
    if not is_basic_value(first):
        raise ValueError("The 0-nh component of the BASIC VECTOR parameter must be a BASIC value (int, float, str)")
    i = 1
    while i < len(basic_vector):
        if not is_basic_value(basic_vector[i]):
            raise ValueError("The  " + str(i) + "-nh component of the BASIC VECTOR parameter must be a BASIC value ("
                                                "int, float, str)")
        if type(basic_vector[i]) != type(first):
            raise ValueError("The  " + str(i) + "-nh component  of the BASIC VECTOR parameter type differs from the "
                                                "rest")
        i += 1


# =========================================== VALUE CHECKERS ==========================================================#

def check_integer_range_step(min_value: int, max_value: int, step: int | None, case: str):
    check_range(min_value, max_value, case)
    return check_int_step(min_value, max_value, step, case)


def check_real_range_step(min_value: float, max_value: float, step: float | None, case: str):
    check_range(min_value, max_value, case)
    return check_float_step(min_value, max_value, step, case)


def check_range(min_value, max_value, case: str):
    """ It checks if min_value < max_value, if not, raise :py:class:`~pycvoa.problem.domain.DefinitionError`.
    If the first condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param min_value: The minimum value.
    :param max_value: The maximum value.
    :param case: The step.
    :type min_value: int, float
    :type max_value: int, float
    :type case: int, float
    """
    if min_value >= max_value:
        msg = ""
        if case == "a":
            msg = "The minimum value of the variable (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."
        elif case == "b":
            msg = "The minimum value of the element (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."
        elif case == "c":
            msg = "The minimum size of the VECTOR variable (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."
        raise ValueError(msg)


def check_int_step(min_value: int, max_value: int, step: OptInt, case: str) -> int:
    average = math.floor((max_value - min_value) / 2)
    if step is not None:
        if step > average:
            msg = ""
            if case == "a":
                msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "b":
                msg = "The step value (" + str(step) + ") of the element must be less or equal than" \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "c":
                msg = "The step size (" + str(step) + ") of the VECTOR variable must be less or equal than " \
                                                      "(maximum size - minimum size) / 2 ( " + str(average) + ")."

            raise ValueError(msg)
        else:
            r = step
    else:
        r = average
    return r


def check_float_step(min_value: float, max_value: float, step: OptFloat, case: str) -> float:
    average = (max_value - min_value) / 2
    if step is not None:
        if step > average:
            msg = ""
            if case == "a":
                msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "b":
                msg = "The step value (" + str(step) + ") of the element must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            raise ValueError(msg)
        else:
            r = step
    else:
        r = average
    return r


# ========================================== ARGUMENT CHECKERS ========================================================#

def is_none(parameter: str, value: Any):
    if value is not None:
        raise ValueError(parameter + " must be None.")


def not_none(parameter: str, value: Any):
    if value is None:
        raise ValueError(parameter + " must not be None.")


def is_basic_or_layer_value(parameter: str, value: Any):
    if type(value) not in [int, float, str, dict]:
        raise ValueError(parameter + " must be int, float, str or dict.")


def is_basic_or_layer_or_vector_value(parameter: str, value: Any):
    if type(value) not in [int, float, str, dict, list]:
        raise ValueError(parameter + " must be int, float, str, dict or list.")


# =================================== DOMAIN GENERAL CHECK VALUE METHOD ===============================================#


def check_basic_pycvoatype(element: OptStr):
    if element is not None:
        raise ValueError("You are trying to check a value of an element of a variable that is not LAYER or LAYER.")


def check_layer_pycvoatype(value: Any, element: OptStr) -> str:
    res = "f"
    if isinstance(value, (int, float, str)):
        if element is None:
            raise ValueError("You are trying to check an element's value without specifying the element name.")
        else:
            res = "a"
    elif is_layer_value(value):
        if element is not None:
            raise ValueError(
                "You are trying to check an element's value with a value different from int, float, or str.")
        else:
            res = "b"
    return res


def check_basic_vector_pycvoatype(value: Any, element: OptStr) -> str:
    res = "f"
    if isinstance(value, (int, float, str)):
        if element is not None:
            raise ValueError(
                "You are trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.")
        else:
            res = "a"
    elif is_basic_vector_value(value):
        if element is not None:
            raise ValueError(
                "You are trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.")
        else:
            res = "b"
    return res


def check_layer_vector_pycvoatype(value: Any, element: OptStr) -> str:
    res = "f"
    if isinstance(value, (int, float, str)):
        if element is None:
            raise ValueError("You are trying to check an element's value without specifying the element name.")
        else:
            res = "a"
    elif is_layer_value(value):
        if element is not None:
            raise ValueError("You are trying to check an element's value with a value different from int, float, "
                             "or str.")
        else:
            res = "b"
    elif is_layer_vector_value(value):
        if element is not None:
            raise ValueError("You are trying to check an element's value with a value different from int, float, "
                             "or str.")
        else:
            res = "c"
    return res


# =================================== SOLUTION GENERAL SET VALUE METHOD ===============================================#

def set_basic_pycvoatype(value: Any, element: OptStr, index: OptInt):
    if isinstance(value, (int, float, str)):
        if element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR.")
        elif element is not None and index is None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
    else:
        raise ValueError("The value must a BASIC value (int, float or str).")


def set_layer_pycvoatype(value: Any, element: OptStr, index: OptInt) -> str:
    if isinstance(value, (int, float, str)):
        if element is None and index is None:
            raise ValueError("You are trying to set an element's value without specifying the element name.")
        if element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
        else:
            res = "a"
    elif is_layer_value(value):
        if element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a variable that is not LAYER VECTOR")
        elif element is not None and index is None:
            raise ValueError("You are trying to set an element's value with a value different from int, float, "
                             "or str.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a component of a variable that is not "
                             "LAYER VECTOR.")
        else:
            res = "b"
    else:
        raise ValueError("The value must be a BASIC value (int, float, or str) or a well-formed LAYER value.")
    return res


def set_basic_vector_pycvoatype(value: Any, element: OptStr, index: OptInt) -> str:
    if isinstance(value, (int, float, str)):
        if element is None and index is None:
            raise ValueError("You are trying to set a component's value without specifying the target index.")
        if element is not None and index is None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
        else:
            res = "a"
    elif is_basic_vector_value(value):
        if element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a BASIC VECTOR variable with a complete "
                             "BASIC VECTOR value.")
        elif element is not None and index is None:
            raise ValueError("You are trying to set an element's value with a value different from int, float, "
                             "or str of a variable that is not LAYER.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a component of a variable that is not "
                             "LAYER VECTOR.")
        else:
            res = "b"
    else:
        raise ValueError("The value must be a BASIC value (int, float, or str) or a well-formed BASIC VECTOR value.")
    return res


def set_layer_vector_pycvoatype(value: Any, element: OptStr, index: OptInt) -> str:
    if isinstance(value, (int, float, str)):
        if element is None and index is None:
            raise ValueError("You are trying to set a LAYER VECTOR variable with a BASIC value.")
        elif element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
        elif element is not None and index is None:
            raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
        else:
            res = "a"
    elif is_layer_value(value):
        if element is None and index is None:
            raise ValueError("You are trying to set a LAYER VECTOR variable with a LAYER value without specifying "
                             "the component index.")
        elif element is not None and index is None:
            raise ValueError("You are trying to set an element's value with a value different from int, float, "
                             "or str and without specifying the component index.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a component with a value that is not "
                             "BASIC.")
        else:
            res = "b"
    elif is_layer_vector_value(value):
        if element is None and index is not None:
            raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
        elif element is not None and index is None:
            raise ValueError("You are trying to set an element's value with a value different from int, float, "
                             "or str and without specifying the component index.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to set a value of an element of a component with a value that is not "
                             "BASIC.")
        else:
            res = "c"
    else:
        raise ValueError("The value must be a BASIC value (int, float, or str) a well-formed LAYER value or a "
                         "well-formed LAYER VECTOR value.")
    return res


# =================================== SOLUTION GENERAL GET VALUE METHOD ===============================================#

def get_basic_pycvoatype(element: OptStr, index: OptInt):
    if element is None and index is not None:
        raise ValueError("You are trying to get a value of a component of a variable that is not BASIC VECTOR.")
    elif element is not None and index is None:
        raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
    elif element is not None and index is not None:
        raise ValueError("You are trying to get a value of an element of a variable that is not LAYER VECTOR.")


def get_layer_pycvoatype(element: OptStr, index: OptInt) -> str:
    if element is None and index is None:
        r = "a"
    elif element is None and index is not None:
        raise ValueError("You are trying to get a value of a component of a variable that is not BASIC VECTOR")
    elif element is not None and index is None:
        r = "b"
    else:
        raise ValueError(
            "You are trying to get an element value of a component of a variable that is not LAYER VECTOR.")
    return r


def get_basic_vector_pycvoatype(element: OptStr, index: OptInt) -> str:
    if element is None and index is None:
        r = "a"
    elif element is None and index is not None:
        r = "b"
    elif element is not None and index is None:
        raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
    else:
        raise ValueError(
            "You are trying to get an element value of a component of a variable that is not LAYER VECTOR.")
    return r


def get_layer_vector_pycvoatype(element: OptStr, index: OptInt) -> str:
    if element is None and index is None:
        r = "a"
    elif element is None and index is not None:
        r = "b"
    elif element is not None and index is None:
        raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
    else:
        r = "c"
    return r
