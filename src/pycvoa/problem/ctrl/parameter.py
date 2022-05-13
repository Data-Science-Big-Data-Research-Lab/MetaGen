import math
from typing import Optional

import pycvoa


# =========================================== SINGLE TYPES ============================================================#

# def is_string(parameter_name: str, value):
#     if type(value) != str:
#         raise TypeError("The " + parameter_name + " parameter must be <str>.")

#
# def are_string(parameter_name_1: str, value_1, parameter_name_2: str, value_2):
#     if type(value_1) != str and type(value_2) == str:
#         raise TypeError("The " + parameter_name_1 + " parameter must be <str>.")
#     elif type(value_1) == str and type(value_2) != str:
#         raise TypeError("The " + parameter_name_2 + " parameter must be <str>.")
#     elif type(value_1) != str and type(value_2) != str:
#         raise TypeError("The " + parameter_name_1 + " and " + parameter_name_2 + " parameters must be <str>.")


# def is_int(parameter_name: str, value):
#     if type(value) != int:
#         raise TypeError("The " + parameter_name + " parameter must be <int>.")
#
#
# def is_optional_int(parameter_name: str, value):
#     if value is not None:
#         if type(value) != int:
#             raise TypeError("The " + parameter_name + " parameter must be <int>.")
#
#
# def are_int(parameter_name_1: str, value_1, parameter_name_2: str, value_2):
#     if type(value_1) != int and type(value_2) == int:
#         raise TypeError("The " + parameter_name_1 + " parameter must be <int>.")
#     elif type(value_1) == int and type(value_2) != int:
#         raise TypeError("The " + parameter_name_2 + " parameter must be <int>.")
#     elif type(value_1) != int and type(value_2) != int:
#         raise TypeError("The " + parameter_name_1 + " and " + parameter_name_2 + " parameters must be <int>.")
#
#
# def is_float(parameter_name: str, value):
#     if type(value) != float:
#         raise TypeError("The " + parameter_name + " parameter must be <float>.")


# def is_optional_float(parameter_name: str, value):
#     if value is not None:
#         if type(value) != float:
#             raise TypeError("The " + parameter_name + " parameter must be <float>.")


# def are_float(parameter_name_1: str, value_1, parameter_name_2: str, value_2):
#     if type(value_1) != float and type(value_2) == float:
#         raise TypeError("The " + parameter_name_1 + " parameter must be <float>.")
#     elif type(value_1) == float and type(value_2) != float:
#         raise TypeError("The " + parameter_name_2 + " parameter must be <float>.")
#     elif type(value_1) != float and type(value_2) != float:
#         raise TypeError("The " + parameter_name_1 + " and " + parameter_name_2 + " parameters must be <float>.")
#
#
# def is_basic(parameter_name: str, value):
#     if type(value) not in (int, float, str):
#         raise TypeError("The " + parameter_name + " parameter must be <int>, <float> or <str>.")


# =========================================== DICT/LIST TYPES =========================================================#

# def is_dict(parameter_name: str, values):
#     if type(values) != dict:
#         raise TypeError("The " + parameter_name + " parameter must be <dict>.")
#
#
# def not_dict(parameter_name: str, values):
#     if type(values) == dict:
#         raise TypeError("The " + parameter_name + " parameter must not be <dict>.")
#
#
# def is_list(parameter_name: str, values):
#     if type(values) != list:
#         raise TypeError("The " + parameter_name + " parameter must be <list>.")
#
#
# def not_list(parameter_name: str, values):
#     if type(values) == list:
#         raise TypeError("The " + parameter_name + " parameter must not be <list>.")
#
#
# def is_list_of_dict(parameter_name: str, values):
#     is_list(parameter_name, values)
#     for e in values:
#         if type(e) != dict:
#             raise TypeError("The " + values.index(e) + "-nh value for the "
#                             + parameter_name + " parameter must be <dict>.")


# =========================================== MULTIPLE TYPES===========================================================#

def same_class(parameter_name: str, categories: list, value):
    categories_type = type(categories[0])
    if type(value) != categories_type:
        raise TypeError("The " + parameter_name + " parameter must have the same class: "
                        + str(categories_type) + ".")


# =========================================== DOMAIN TYPES ============================================================#

def is_domain_class(parameter_name: str, domain):
    if domain is not None:
        if type(domain) is not pycvoa.problem.domain.Domain:
            raise TypeError("The " + parameter_name + " parameter must be an instance of <Domain> class.")


# =========================================== NONE TYPES ==============================================================#

def element_is_none(variable: str, element: str, case: str):
    if element is not None:
        if case == "a":
            raise ValueError(
                "The type of " + variable + " is BASIC, therefore, the element must not be provided.")
        elif case == "b":
            raise ValueError(
                "The " + variable + " is LAYER, and the type of the values are <dict>, therefore, "
                                    "the element must not be provided.")
        elif case == "c":
            raise ValueError(
                "The type of " + variable + " is VECTOR, and the type of the values are <list>, therefore, "
                                            "the element must not be provided.")
        elif case == "d":
            raise ValueError(
                "The components type of the VECTOR variable " + variable + " are BASIC, therefore, "
                                                                           "the element must not be provided.")
        elif case == "e":
            raise ValueError(
                "The " + variable + " is LAYER VECTOR, and the type of the values are <dict>, therefore, "
                                    "the element must not be provided.")


def element_not_none(variable, element, case: str):
    if element is None:
        if case == "a":
            raise ValueError(
                "The type of " + variable
                + " is LAYER and the values are not <dict>, therefore, the element must be provided.")
        elif case == "b":
            raise ValueError(
                "The " + variable
                + " is LAYER VECTOR and the values are not <dict>, therefore, the element must be provided.")


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

def check_range(min_value, max_value, case: str):
    """ It checks if min_value < max_value, if not, raise :py:class:`~pycvoa.problem.domain.DefinitionError`.
    If the first condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param min_value: The minimum value.
    :param max_value: The maximum value.
    :param step: The step.
    :type min_value: int, float
    :type max_value: int, float
    :type step: int, float
    """
    if min_value >= max_value:
        if case == "a":
            raise ValueError(
                "The minimum value of the variable (" + str(min_value)
                + ") must be less than the maximum one (" + str(max_value) + ").")
        elif case == "b":
            raise ValueError(
                "The minimum value of the element (" + str(min_value)
                + ") must be less than the maximum one (" + str(max_value) + ").")
        elif case == "c":
            raise ValueError(
                "The minimum size of the VECTOR variable (" + str(min_value)
                + ") must be less than the maximum one (" + str(max_value) + ").")


def check_int_step(min_value: int, max_value: int, step: int, case: str):
    average = math.floor((max_value - min_value) / 2)
    if step is not None:
        if step > average:
            if case == "a":
                raise ValueError("The step value (" + str(step)
                                 + ") of the variable must be less or equal than (maximum value - minimum value) / 2 ("
                                 + str(average) + ").")
            elif case == "b":
                raise ValueError("The step value (" + str(step)
                                 + ") of the element must be less or equal than (maximum value - minimum value) / 2 ("
                                 + str(average) + ").")
            elif case == "c":
                raise ValueError("The step size (" + str(step)
                                 + ") of the VECTOR variable must be less or equal than "
                                   "(maximum size - minimum size) / 2 ( " + str(average) + ").")
        else:
            r = step
    else:
        r = average
    return r


def check_float_step(min_value: float, max_value: float, step: float, case: str):
    average = (max_value - min_value) / 2
    if step is not None:
        if step > average:
            if case == "a":
                raise ValueError("The step value (" + str(step)
                                 + ") of the variable must be less or equal than (maximum value - minimum value) / 2 ("
                                 + str(average) + ").")
            elif case == "b":
                raise ValueError("The step value (" + str(step)
                                 + ") of the element must be less or equal than (maximum value - minimum value) / 2 ("
                                 + str(average) + ").")
            elif case == "c":
                raise ValueError("The step size (" + str(step)
                                 + ") of the VECTOR variable must be less or equal than "
                                   "(maximum size - minimum size) / 2 ( " + str(average) + ").")
        else:
            r = step
    else:
        r = average
    return r


def categories_length_type_values(categories: list):
    if len(categories) < 2:
        raise ValueError("The categories parameter must have al least two elements.")
    for el in categories:
        if type(el) not in (int, float, str):
            raise TypeError(
                "The " + str(categories.index(
                    el)) + "-nh element of the categories parameter must be <int>, <float> or <str>.")
        categories_type = type(categories[0])
        if type(el) != categories_type:
            raise TypeError(
                "All the elements of the categories parameter must have the same type (<int>, <float> or <str>).")
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


# =========================================== GLOBAL PROCEDURES =======================================================#

def check_integer_range_step(min_value, max_value, step, case: str):
    check_range(min_value, max_value, case)
    return check_int_step(min_value, max_value, step, case)


def check_real_range_step(min_value, max_value, step, case: str):
    are_float("min_value", min_value, "max_value", max_value)
    check_range(min_value, max_value, case)
    is_optional_float("step", step)
    return check_float_step(min_value, max_value, step, case)


def check_integer_definition(variable_name: str, min_value: int, max_value: int, step: Optional[int], case: str):
    return check_integer_range_step(min_value, max_value, step, case)


def check_real_definition(variable_name, min_value, max_value, step, case: str):
    is_string("variable_name", variable_name)
    return check_real_range_step(min_value, max_value, step, case)


def check_categorical_definition(variable_name, categories):
    is_string("variable_name", variable_name)
    is_list("categories", categories)
    categories_length_type_values(categories)


def check_integer_element_definition(layer_variable, element, min_value, max_value, step):
    are_string("layer_variable", layer_variable, "element", element)
    return check_integer_range_step(min_value, max_value, step, "b")


def check_real_element_definition(layer_variable, element, min_value, max_value, step):
    are_string("layer_variable", layer_variable, "element", element)
    return check_real_range_step(min_value, max_value, step, "b")


def check_categorical_element_definition(layer_variable, element, categories):
    are_string("layer_variable", layer_variable, "element", element)
    is_list("categories", categories)
    categories_length_type_values(categories)
