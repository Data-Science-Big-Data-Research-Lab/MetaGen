import pycvoa.problem.ctrl as ctrl
from pycvoa.problem.types import *


def valid_domain(external_domain, internal_domain):
    ctrl.par.is_domain_class(external_domain)
    current_domain = external_domain
    if current_domain is None:
        current_domain = internal_domain
    if current_domain is None:
        raise ValueError("A domain must be specified, via parameter or set_domain method.")
    return current_domain


def check_basic_value(basic_variable, value, domain):
    if not domain.check_basic(basic_variable, value):
        raise ValueError("The value " + str(value) + " is not compatible with the " + basic_variable + " variable "
                                                                                                       "definition.")


def check_layer_element_value(layer_variable, element, value, domain):
    if not domain.check_element(layer_variable, element, value):
        raise ValueError(
            "The value " + str(
                value) + " is not valid for the " + element + " element in the " + layer_variable + " variable.")


def check_vector_basic_component(basic_vector_variable, value, domain):
    if not domain.check_vector_basic_value(basic_vector_variable, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + basic_vector_variable + " variable.")


def check_vector_layer_element_component(layer_vector_variable, element, value, domain):
    if not domain.check_vector_layer_element_value(layer_vector_variable, element, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + element + " element in the " + layer_vector_variable + " variable.")


def check_vector_values_size(vector_variable, values, domain):
    if not domain.check_vector_size(vector_variable, values):
        raise ValueError("The size of " + str(values) + " is not compatible with the " + vector_variable
                         + " definition.")


def check_vector_basic_values(basic_vector_variable, values, domain):
    res = domain.check_vector_basic_values(basic_vector_variable, values)
    if res[0] != -1:
        raise ValueError("The " + res[0] + "-nh value must be " + res[1] + ".")


def check_vector_layer_values(layer_vector_variable, values, domain):
    for layer in values:
        for element, value in layer:
            element_definition = domain.get_component_element_definition(layer_vector_variable, element)
            if element_definition[0] is INTEGER:
                ctrl.par.is_int(value)
                if value < element_definition[1] or value > element_definition[2]:
                    raise ValueError(
                        "The " + element + " element of the " + str(values.index(layer)) + "-nh component "
                                                                                           "is not compatible with its definition.")
            elif element_definition[0] is REAL:
                ctrl.par.is_float(value)
                if value < element_definition[1] or value > element_definition[2]:
                    raise ValueError(
                        "The " + element + " element of the " + str(values.index(layer)) + "-nh component "
                                                                                           "is not compatible with its definition.")
            elif element_definition[0] is CATEGORICAL:
                ctrl.par.same_python_type(element_definition[1], value)
                if value not in element_definition[1]:
                    raise ValueError(
                        "The " + element + " element of the " + str(values.index(layer)) + "-nh component "
                                                                                           "is not compatible with its definition.")


def check_range(min_value, max_value, step):
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
    else:
        average = (max_value - min_value) / 2
        if step > average:
            raise ValueError("The step value/size (" + str(
                step) + ") of the variable/element must be less or equal than (maximum "
                        "value/size - minimum value/size) / 2 (" + str(average) + ").")


def is_number_in_range(number, min_value, max_value):
    if number < min_value or number > max_value:
        raise ValueError(
            "The parameter " + str(number) + " must be in [" + str(min_value) + " , " + str(max_value) + "].")


def check_variable_type(variable, variable_type, domain):
    var_type = domain.get_variable_type(variable)
    if variable_type is BASIC:
        if var_type not in BASIC:
            raise ValueError("The " + variable + " variable is not defined as BASIC.")
    else:
        if var_type is not variable_type:
            raise ValueError("The " + variable + " variable is not defined as " + variable_type + ".")


def check_component_type(vector_variable, component_type, domain):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    comp_type = domain.get_vector_components_type(vector_variable)
    if component_type is BASIC:
        if comp_type not in BASIC:
            raise ValueError("The components of " + vector_variable + " are not defined as BASIC.")
    else:
        if comp_type is not component_type:
            raise ValueError("The components of " + vector_variable + " are not defined as " + component_type + ".")


def valid_domain_check_variable_type(variable, check_type, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    check_variable_type(variable, check_type, current_domain)
    return current_domain


def check_vector_values_size_basic_values(basic_vector_variable, values, domain):
    ctrl.val.check_vector_values_size(basic_vector_variable, values, domain)
    ctrl.val.check_vector_basic_values(basic_vector_variable, values, domain)


def check_vector_values_size_layer_values(layer_vector_variable, values, domain):
    ctrl.val.check_vector_values_size(layer_vector_variable, values, domain)
    ctrl.val.check_vector_layer_values(layer_vector_variable, values, domain)
