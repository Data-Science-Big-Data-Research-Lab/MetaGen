import pycvoa.problem.ctrl as ctrl
from pycvoa.problem.domain import Domain
from pycvoa.problem.types import LAYER, VECTOR


def domain_defined_as_layer_vector_assigned(layer_vector_variable, solution_structure:dict, external_domain: Domain, internal_domain: Domain) -> Domain:
    valid_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.var.component_type(layer_vector_variable, LAYER, valid_domain)
    ctrl.sol.is_assigned_variable(layer_vector_variable, solution_structure)
    return valid_domain


def domain_defined_as_vector_assigned(vector_variable, solution_structure:dict, external_domain: Domain, internal_domain: Domain) -> Domain:
    valid_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.var.variable_type(vector_variable, VECTOR, valid_domain)
    ctrl.sol.is_assigned_variable(vector_variable, solution_structure)
    return valid_domain

def domain_defined_as_layer_assigned(layer_variable, solution_structure:dict, external_domain: Domain, internal_domain: Domain) -> Domain:
    valid_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.var.variable_type(layer_variable,LAYER,valid_domain)
    ctrl.sol.is_assigned_variable(layer_variable,solution_structure)
    return valid_domain



def domain_defined_assigned(variable, solution_structure:dict, external_domain: Domain, internal_domain: Domain) -> Domain:
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    current_domain.is_defined_variable(variable)
    ctrl.sol.is_assigned_variable(variable,solution_structure)
    return current_domain



def domain_vector_type(vector_variable, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.var.variable_type(vector_variable, VECTOR, current_domain)


def domain_basic_value(basic_variable, value, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    if not current_domain.check_basic(basic_variable, value):
        raise ValueError("The value " + str(value) + " is not compatible with the " + basic_variable + " variable "
                                                                                                       "definition.")


def domain_layer_element_value(layer_variable, element, value, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    if not current_domain.check_element(layer_variable, element, value):
        raise ValueError(
            "The value " + str(
                value) + " is not valid for the " + element + " element in the " + layer_variable + " variable.")


def domain_basic_vector_list(basic_vector_variable, value_list: list, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    res = current_domain.check_vector_basic_values(basic_vector_variable, value_list)
    if res[0] != -1:
        raise ValueError("The " + res[0] + "-nh value must be " + res[1] + ".")


def domain_basic_vector_value(basic_vector_variable, value, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    if not current_domain.check_vector_basic_value(basic_vector_variable, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + basic_vector_variable + " variable.")


def domain_layer_vector_list(layer_vector_variable, value_list: list, external_domain: Domain, internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.val.list_size(layer_vector_variable, value_list, current_domain)
    ctrl.val.layer_vector_list(layer_vector_variable, value_list, current_domain)


def domain_layer_vector_component(layer_vector_variable, layer_values, external_domain: Domain,
                                  internal_domain: Domain):
    ctrl.par.is_dict(layer_values)
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    ctrl.var.component_type(layer_vector_variable, LAYER, current_domain)
    ctrl.val.layer_vector_component(layer_vector_variable, layer_values, current_domain)


def domain_layer_vector_element(layer_vector_variable, element, value, external_domain: Domain,
                                internal_domain: Domain):
    current_domain = ctrl.var.valid_domain(external_domain, internal_domain)
    if not current_domain.check_vector_layer_element_value(layer_vector_variable, element, value):
        raise ValueError(
            "The value " + value + " is not valid for the " + element + " element in the " + layer_vector_variable + "variable.")
    return current_domain


def is_assigned_variable_valid_domain_check_variable_type(variable, solution_structure, check_type, external_domain,
                                                          internal_domain):
    ctrl.sol.is_assigned_variable(variable, solution_structure)
    current_domain = ctrl.val.domain__variable_type(variable, check_type, external_domain, internal_domain)
    return current_domain


def is_defined_variable_check_range(variable_name, min_value, max_value, step, definitions):
    """ It checks if a variable name is already used in the domain, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the first condition is not fulfilled, it checks if min_value < max_value, if not,
    raise :py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the second condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable_name: The variable name.
    :param min_value: The minimum value.
    :param max_value: The maximum value.
    :param step: The step.
    :type variable_name: str
    :type min_value: int, float
    :type max_value: int, float
    :type step: int, float
    """
    ctrl.dom.is_defined_variable(variable_name, definitions)
    ctrl.val.check_range(min_value, max_value, step)
