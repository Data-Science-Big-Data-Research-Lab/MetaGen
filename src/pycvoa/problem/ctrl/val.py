import pycvoa.problem.ctrl as ctrl
from pycvoa.problem.domain import Domain
from pycvoa.problem.types import *


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


def number_in_range(number, min_value, max_value):
    if number < min_value or number > max_value:
        raise ValueError(
            "The parameter " + str(number) + " must be in [" + str(min_value) + " , " + str(max_value) + "].")


def basic(basic_variable, value, domain: Domain):
    if not domain.check_basic(basic_variable, value):
        raise ValueError("The value " + str(value) + " is not compatible with the " + basic_variable + " variable "
                                                                                                       "definition.")


def layer_element(layer_variable, element, value, domain: Domain):
    if not domain.check_element(layer_variable, element, value):
        raise ValueError(
            "The value " + str(
                value) + " is not valid for the " + element + " element in the " + layer_variable + " variable.")


def list_size(vector_variable, values, domain: Domain):
    if not domain.check_vector_size(vector_variable, values):
        raise ValueError("The size of " + str(values) + " is not compatible with the " + vector_variable
                         + " definition.")


def basic_vector(basic_vector_variable, value, domain: Domain):
    if not domain.check_vector_basic_value(basic_vector_variable, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + basic_vector_variable + " variable.")


def basic_vector_list(basic_vector_variable, values, domain: Domain):
    res = domain.check_vector_basic_values(basic_vector_variable, values)
    if res[0] != -1:
        raise ValueError("The " + res[0] + "-nh value must be " + res[1] + ".")


def basic_vector_size_list(basic_vector_variable, values, domain: Domain):
    list_size(basic_vector_variable, values, domain)
    basic_vector_list(basic_vector_variable, values, domain)


def layer_vector_list(layer_vector_variable, values, domain: Domain):
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


def layer_vector_component(layer_vector_variable, layer, domain: Domain):
    for element, value in layer:
        element_definition = domain.get_component_element_definition(layer_vector_variable, element)
        if element_definition[0] is INTEGER:
            ctrl.par.is_int(value)
            if value < element_definition[1] or value > element_definition[2]:
                raise ValueError("The " + element + " element is not compatible with its definition.")
        elif element_definition[0] is REAL:
            ctrl.par.is_float(value)
            if value < element_definition[1] or value > element_definition[2]:
                raise ValueError("The " + element + " element is not compatible with its definition.")
        elif element_definition[0] is CATEGORICAL:
            ctrl.par.same_python_type(element_definition[1], value)
            if value not in element_definition[1]:
                raise ValueError("The " + element + " element is not compatible with its definition.")



def layer_vector_element(layer_vector_variable, element, value, domain: Domain):
    if not domain.check_vector_layer_element_value(layer_vector_variable, element, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + element + " element in the " + layer_vector_variable + "variable.")



def layer_vector_size_list(layer_vector_variable, values, domain: Domain):
    list_size(layer_vector_variable, values, domain)
    layer_vector_list(layer_vector_variable, values, domain)
