import math

import pycvoa


# =========================================== SINGLE TYPES ============================================================#

def is_string(variable_element_name):
    if type(variable_element_name) != str:
        raise TypeError("The variable_name/element_name/variable/element parameter must be <str>.")


def is_int(value):
    if type(value) != int:
        raise TypeError("The value parameter must be <int>.")


def is_optional_int(value):
    if value is not None:
        if type(value) != int:
            raise TypeError("The size/step_size parameter must be <int>.")


def is_float(value):
    if type(value) != float:
        raise TypeError("The value parameter must be <float>.")


def is_optional_float(value):
    if value is not None:
        if type(value) != float:
            raise TypeError("The size/step_size parameter must be <int>.")


# =========================================== DICT TYPES ==============================================================#

def is_dict(values):
    if type(values) != dict:
        raise TypeError("The values parameter must be <dict>.")


def not_dict(values):
    if type(values) == dict:
        raise TypeError("The values parameter must not be <dict>.")


# =========================================== LIST TYPES ==============================================================#

def is_list(values):
    if type(values) != list:
        raise TypeError("The values parameter must be <list>.")


def not_list(values):
    if type(values) == list:
        raise TypeError("The values parameter must not be <list>.")


# =========================================== LIST OF DICT ============================================================#

def is_list_of_dict(values):
    is_list(values)
    for e in values:
        if type(e) != dict:
            raise TypeError("The " + values.index(e) + "-nh value must be <dict>.")


# =========================================== MULTIPLE TYPES===========================================================#

def are_int(min_value_size, max_value_size):
    if type(min_value_size) != int:
        raise TypeError("The min_value/min_size parameter must be <int>.")
    if type(max_value_size) != int:
        raise TypeError("The max_value/max_size parameter must be <int>.")


def are_string(param1, param2):
    is_string(param1)
    is_string(param2)


def are_float(min_value, max_value):
    if type(min_value) != float:
        raise TypeError("The min_value parameter must be <float>.")
    if type(max_value) != float:
        raise TypeError("The max_value parameter must be <float>.")


def same_python_type(categories, value):
    categories_type = type(categories[0])
    if type(value) != categories_type:
        raise TypeError(
            "The value parameter be the same Python type than categories (" + str(categories_type) + ").")


# =========================================== DOMAIN TYPES ============================================================#

def is_domain_class(domain):
    if domain is not None:
        if type(domain) is not pycvoa.problem.domain.Domain:
            raise TypeError("The " + domain + " parameter is not instantiate from <Domain> class.")


# =========================================== NONE TYPES ==============================================================#

def element_is_none(variable, element):
    if element is not None:
        raise ValueError(
            "The variable/component type of " + variable + " is BASIC, therefore, the element must not "
                                                           "be provided.")


def element_not_none(variable, element_index):
    if element_index is None:
        raise ValueError(
            "The variable/component type of " + variable + " is LAYER, therefore, the element must "
                                                           "be provided.")


def index_is_none(variable, index):
    if index is not None:
        raise ValueError(
            "The " + variable + "variable is not defined as VECTOR, therefore, an index must not be provided.")


def index_not_none(variable, index):
    if index is None:
        raise ValueError(
            "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                "must be provided.")


# =========================================== VALUE CHECKERS ==========================================================#

def check_range(min_value, max_value):
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
        raise ValueError(
            "The minimum value/size of the variable/element (" + str(
                min_value) + ") must be less than the maximum value/size (" + str(
                max_value) + ").")


def check_int_step(min_value, max_value, step):
    average = math.floor((max_value - min_value) / 2)
    if step is not None:
        if step > average:
            raise ValueError("The step value/size (" + str(
                step) + ") of the variable/element must be less or equal than (maximum "
                        "value/size - minimum value/size) / 2 (" + str(average) + ").")
        else:
            r = step
    else:
        r = average
    return r


def check_float_step(min_value, max_value, step):
    average = (max_value - min_value) / 2
    if step is not None:
        if step > average:
            raise ValueError("The step value/size (" + str(
                step) + ") of the variable/element must be less or equal than (maximum "
                        "value/size - minimum value/size) / 2 (" + str(average) + ").")
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

def check_integer_range_step(min_value, max_value, step):
    are_int(min_value, max_value)
    check_range(min_value, max_value)
    is_optional_int(step)
    return check_int_step(min_value, max_value, step)


def check_real_range_step(min_value, max_value, step):
    are_float(min_value, max_value)
    check_range(min_value, max_value)
    is_optional_float(step)
    return check_float_step(min_value, max_value, step)


def check_integer_definition(variable_name, min_value, max_value, step):
    is_string(variable_name)
    return check_integer_range_step(min_value, max_value, step)


def check_real_definition(variable_name, min_value, max_value, step):
    is_string(variable_name)
    return check_real_range_step(min_value, max_value, step)


def check_categorical_definition(variable_name, categories):
    is_string(variable_name)
    is_list(categories)
    categories_length_type_values(categories)


def check_integer_element_definition(layer_variable, element, min_value, max_value, step):
    are_string(layer_variable, element)
    return check_integer_range_step(min_value, max_value, step)


def check_real_element_definition(layer_variable, element, min_value, max_value, step):
    are_string(layer_variable, element)
    return check_real_range_step(min_value, max_value, step)


def check_categorical_element_definition(variable_name, element, categories):
    are_string(variable_name, element)
    is_list(categories)
    categories_length_type_values(categories)
