from typing import cast

from pycvoa.control import DefinitionError, DomainError, SolutionError
from pycvoa.problem.domain import Domain
from pycvoa.control.types import *
import pycvoa.control.common as cmn

OptDomain: TypeAlias = Union[Domain, None]


# ================================================== AUXILIARY ======================================================= #


def get_valid_domain(external_domain: OptDomain, internal_domain: OptDomain) -> Domain:
    current_domain = external_domain
    if current_domain is None:
        current_domain = internal_domain
    if current_domain is None:
        raise DomainError("A domain must be specified, via parameter or set_domain method.")
    return current_domain


def __list_size(vector_variable: str, values: list, domain: Domain):
    if not domain.check_vector_values_size(vector_variable, values):
        raise DomainError("The size of " + str(values) + " is not compatible with the " + vector_variable
                          + " definition.")


# ================================================== BASIC =========================================================== #

def check_basic_value(check_basic_variable: str, value: Basic, external_domain: OptDomain,
                      internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if not valid_domain.check_basic(check_basic_variable, value):
        raise DomainError("The value " + str(value) + " is not compatible with the "
                          + check_basic_variable + " variable definition.")


# ================================================== LAYER =========================================================== #

def check_layer_value(layer_variable: str, layer_value: SolLayer, external_domain: OptDomain,
                      internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    for element, value in layer_value.items():
        if not valid_domain.check_element(layer_variable, element, value):
            raise DomainError(
                "The value " + str(value) + " is not compatible for the " + element + " element in the "
                + layer_variable + " variable.")


def check_layer_element_value(layer_variable: str, element: str, value: Basic, external_domain: OptDomain,
                              internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if not valid_domain.check_element(layer_variable, element, value):
        raise DomainError(
            "The value " + str(value) + " is not compatible for the " + element + " element in the "
            + layer_variable + " variable.")


# =============================================== BASIC VECTOR ======================================================= #

def check_basic_vector_values(check_basic_vector_variable: str, value_list: Union[BasicValueList, BasicVectorInput], external_domain: OptDomain,
                              internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if not valid_domain.check_vector_basic_values(check_basic_vector_variable, value_list):
        raise DomainError(
            "The values are not compatible with the " + check_basic_vector_variable + " variable definition")


def check_basic_vector_value(check_basic_vector_variable: str, value: Basic, external_domain: OptDomain,
                             internal_domain: OptDomain) -> Domain:
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if not valid_domain.check_vector_basic_value(check_basic_vector_variable, value):
        raise DomainError(
            "The value " + str(value) + " is not valid for the " + str(check_basic_vector_variable) + " variable.")
    return valid_domain


# =============================================== LAYER VECTOR ======================================================= #


def check_layer_vector_values(layer_vector_variable: str, value_list: LayerVectorValue, external_domain: OptDomain,
                              internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    __list_size(layer_vector_variable, value_list, valid_domain)
    for layer in value_list:
        assert type(layer) is SolLayer
        for element, value in layer.items():
            if not valid_domain.check_vector_layer_element_value(layer_vector_variable, element, value):
                raise DomainError(
                    "The " + element + " element of the " + str(value_list.index(layer))
                    + "-nh component is not compatible with its definition.")


def check_layer_vector_component(layer_vector_variable: str, layer_values: SolLayer, external_domain: OptDomain,
                                 internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    for element, value in layer_values.items():
        if not valid_domain.check_vector_layer_element_value(layer_vector_variable, element, value):
            raise DomainError(
                "The " + element + " element of the is not compatible with its definition.")
    return valid_domain


# =============================================== DEF. CHECKING ====================================================== #

def is_defined_variable(variable: str, external_domain: OptDomain, internal_domain: OptDomain) -> Domain:
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if valid_domain.is_defined_variable(variable) is not True:
        raise DomainError(
            "The variable " + variable + " is not defined in this domain.")
    return valid_domain


def is_defined_as_layer(variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = is_defined_variable(variable, external_domain, internal_domain)
    if valid_domain.get_variable_type(variable) is not LAYER:
        raise DomainError("The variable " + variable + " is not defined as LAYER.")


def is_defined_as_vector_variable(variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = is_defined_variable(variable, external_domain, internal_domain)
    if valid_domain.get_variable_type(variable) is not VECTOR:
        raise DomainError("The variable " + variable + " is not defined as LAYER.")
    if not valid_domain.are_defined_components(variable):
        raise DomainError("The components of the " + variable + " VECTOR variable have not defined.")


def is_defined_as_layer_vector_variable(variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = is_defined_variable(variable, external_domain, internal_domain)
    if valid_domain.get_variable_type(variable) is not VECTOR:
        raise DomainError("The variable " + variable + " is not defined as LAYER.")
    if not valid_domain.get_vector_components_type(variable) is not LAYER:
        raise DomainError("The components of the " + variable + " VECTOR variable have not defined as LAYER.")


# =============================================== GENERAL =========================================================== #

def check_layer_vector_element(layer_vector_variable: str, element: str, value: Basic, external_domain: OptDomain,
                               internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if not valid_domain.check_vector_layer_element_value(layer_vector_variable, element, value):
        raise ValueError(
            "The value " + str(value) + " is not valid for the " + str(element) + " element in the "
            + str(layer_vector_variable) + " variable.")
    return valid_domain


def basic_variable(check_basic_variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if cmn.check_item_type(BASIC, valid_domain.get_variable_type(check_basic_variable)) is False:
        raise DefinitionError("The variable " + check_basic_variable + " is not defined as BASIC.")
    return valid_domain


def layer_variable(check_layer_variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if cmn.check_item_type(LAYER, valid_domain.get_variable_type(check_layer_variable)) is False:
        raise DefinitionError("The variable " + check_layer_variable + " is not defined as LAYER.")
    return valid_domain


def layer_variable_element(check_layer_variable: str, element: str, external_domain: OptDomain,
                           internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    if cmn.check_item_type(LAYER, valid_domain.get_variable_type(check_layer_variable)) is False:
        raise DefinitionError("The variable " + check_layer_variable + " is not defined as LAYER.")
    if valid_domain.is_defined_element(check_layer_variable, element) is False:
        raise DefinitionError(
            "The element " + element + " of the " + check_layer_variable +
            " LAYER variable is not defined in this domain.")
    return valid_domain


def basic_vector_variable(check_vector_variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    __check_component_type(check_vector_variable, BASIC, valid_domain)
    return valid_domain


def layer_vector_variable(check_vector_variable: str, external_domain: OptDomain, internal_domain: OptDomain):
    valid_domain = get_valid_domain(external_domain, internal_domain)
    __check_component_type(check_vector_variable, LAYER, valid_domain)
    return valid_domain


def __check_component_type(check_vector_variable: str, check_type: PYCVOA_TYPE, domain: Domain):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param check_vector_variable: The **VECTOR** variable.
    :param check_type: The component type.
    :param domain: The domain
    :type check_vector_variable: str
    :type check_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    comp_type = domain.get_vector_components_type(check_vector_variable)
    if check_type is BASIC:
        if comp_type not in BASICS:
            raise ValueError("The components of " + check_vector_variable + " are not defined as BASIC.")
    elif check_type is NUMERICAL:
        if comp_type not in NUMERICALS:
            raise ValueError("The components of " + check_vector_variable + " are not defined as NUMERICAL.")
    else:
        if comp_type is not check_type:
            raise ValueError("The components of " + check_vector_variable
                             + " are not defined as " + str(check_type) + ".")



def check_item_type(check_type: PYCVOA_TYPE, item_type: PYCVOA_TYPE):
    r = False
    if check_type is BASIC:
        if item_type in BASICS:
            r = True
    elif check_type is NUMERICAL:
        if check_type in NUMERICALS:
            r = True
    else:
        if item_type is check_type:
            r = True
    return r


def is_assigned_layer_element(layer_variable: str, element: str, solution_structure: VarStructureType):
    is_assigned_variable(layer_variable, solution_structure)
    layer: SolLayer = cast(SolLayer, solution_structure.get(layer_variable))
    if element not in layer.keys():
        raise SolutionError(
            "The element " + str(element) + " is not assigned in the " + str(layer_variable) + "variable of this "
                                                                                               "solution.")


def is_assigned_element(layer_variable: str, element: str, solution_structure: VarStructureType):
    layer: SolLayer = cast(SolLayer, solution_structure.get(layer_variable))
    if element not in layer.keys():
        raise SolutionError(
            "The element " + str(element) + " is not assigned in the " + str(layer_variable) + "variable of this "
                                                                                               "solution.")


def is_assigned_variable(variable: str, solution_structure: VarStructureType):
    if variable not in solution_structure.keys():
        raise SolutionError("The " + str(variable) + " variable is not assigned in this solution.")


def is_assigned_component(vector_variable: str, index: int, vector_values_size: int):
    if index < 0 or index >= vector_values_size:
        raise SolutionError(
            "The " + str(
                index) + "-nh component of " + vector_variable + " VECTOR variable is not assigned in this solution.")


def is_assigned_component_element(layer_vector_variable: str, index: int, element: str,
                                  layer_vector_value: LayerVectorValue):
    if element not in layer_vector_value[index].keys():
        raise SolutionError("The element " + str(element) + " in not assigned in the " + str(index)
                            + "-nh component of the " + str(layer_vector_variable) + " variable in this solution.")


def vector_insertion_available(vector_variable: str, domain: Domain, vector_value: VectorValue):
    if domain.get_remaining_available_complete_components(vector_variable, len(vector_value)) == 0:
        raise SolutionError("The " + str(vector_variable) + " is complete.")


def vector_adding_available(vector_variable: str, remaining: int):
    if remaining == 0:
        raise SolutionError("The " + str(vector_variable) + " is complete.")


def vector_element_adding_available(layer_vector_variable: str, layer_vector_value: LayerVectorValue, domain: Domain):
    key_sizes = len(layer_vector_value[-1].keys()
                    & domain.get_layer_components_attributes(layer_vector_variable).keys())
    if key_sizes == 0:
        v_size = len(layer_vector_value)
    else:
        v_size = len(layer_vector_value) - 1
    if domain.get_remaining_available_complete_components(layer_vector_variable, v_size) == 0:
        raise SolutionError("The " + str(layer_vector_variable) + " is complete.")


def assigned_vector_removal_available(vector_variable, vector_value_size: int, domain: Domain):
    r = domain.get_remaining_available_complete_components(vector_variable, vector_value_size - 1)
    if r < 0:
        raise SolutionError("The " + str(vector_variable) + " can not deleting.")
    return vector_value_size - r