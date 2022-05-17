import math
from pycvoa.types import OptInt, OptFloat, BasicValueList


# =========================================== NONE TYPES ==============================================================#



def element_is_none(variable: str, element: str, case: str):
    if element is not None:
        msg = ""

        if case == "a":
            msg = "The type of " + variable + " is BASIC, therefore, the element must not be provided."
        elif case == "b":
            msg = "The " + variable + "is LAYER, and the type of the values are <dict>, therefore, the element must not " \
                                      "be provided. "
        elif case == "c":
            msg = "The type of " + variable + "is VECTOR, and the type of the values are <list>, therefore, the element " \
                                              "must not be provided. "
        elif case == "d":
            msg = "The components type of the VECTOR variable " + variable + "are BASIC, therefore, the element must " \
                                                                             "not be provided. "
        elif case == "e":
            msg = "The " + variable + "is LAYER VECTOR, and the type of the values are <dict>, therefore, the element " \
                                      "must not be provided. "
        raise ValueError(msg)


def element_not_none(variable, element, case: str):
    if element is None:
        msg = ""

        if case == "a":
            msg = "The type of " + variable + "is LAYER and the values are not <dict>, therefore, the element must be " \
                                              "provided. "
        elif case == "b":
            msg = "The " + variable + "is LAYER VECTOR and the values are not <dict>, therefore, the element must be " \
                                      "provided. "

        raise ValueError(msg)


def index_is_none(variable, index):
    if index is not None:
        raise ValueError(
            "The " + variable + "variable is not defined as VECTOR, therefore, an index must not be provided.")


def index_not_none(variable, index):
    if index is None:
        raise ValueError(
            "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                "must be provided.")


def assigned_elements_is_none(variable, assigned_elements):
    if assigned_elements is None:
        raise ValueError(
            "The " + variable + "must not be provided, since the VECTOR components are not defined as LAYER.")


def assigned_elements_not_none(variable, assigned_elements):
    if assigned_elements is None:
        raise ValueError(
            "The " + variable + "must be provided, since the VECTOR components are defined as LAYER.")


# =========================================== VALUE CHECKERS ==========================================================#

def check_integer_range_step(min_value, max_value, step: OptInt, case: str):
    check_range(min_value, max_value, case)
    return check_int_step(min_value, max_value, step, case)


def check_real_range_step(min_value, max_value, step: OptFloat, case: str):
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


def check_categories(categories: BasicValueList):
    if len(categories) < 2:
        raise ValueError("The categories parameter must have al least two elements.")
    i = 0
    while i < len(categories) - 1:
        j = i + 1
        while j < len(categories):
            if categories[i] == categories[j]:
                raise ValueError(
                    "The categories list can not contain repeated values.")
            else:
                j += 1
        i += 1
