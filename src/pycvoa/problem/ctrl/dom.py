from pycvoa.problem.ctrl import DefinitionError
from pycvoa.problem.types import *


def is_defined_variable(variable, definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :type variable: str
    """
    if variable not in definitions.keys():
        raise DefinitionError("The variable " + variable + " is not defined in this domain.")


def is_defined_element(layer_variable, element, definitions):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_variable: The variable.
    :param element: The element.
    :type layer_variable: str
    :type element: str
    """
    if element not in definitions[layer_variable][1].keys():
        raise DefinitionError(
            "The element " + element + " of the " + layer_variable + " LAYER variable is not defined in this domain.")


def are_defined_components(vector_variable, definitions):
    """ It checks if the type of a **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param vector_variable: The variable.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) == 0:
        raise DefinitionError(
            "The " + vector_variable + " components are not defined.")


def is_defined_component_element(layer_vector_variable, element, definitions):
    """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_vector_variable: The variable.
    :param element: The element.
    :type layer_vector_variable: str
    :type element: str
    """
    if element not in definitions[layer_vector_variable][4][1].keys():
        raise DefinitionError(
            "The element " + element + " is not defined in the LAYER components of the " + layer_vector_variable + " VECTOR variable.")


def not_defined_variable(variable_name, definitions):
    """ It checks if a variable name is already used in the domain, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable_name: The variable name.
    :type variable_name: str
    """
    if variable_name in definitions.keys():
        raise DefinitionError(
            "The " + variable_name + " variable is already defined, please, select another variable "
                                     "name.")


def not_defined_element(layer_variable, element_name, definitions):
    """ It checks if an element name is already used in a **LAYER** variable definition, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param layer_variable: The variable.
    :param element_name: The element name.
    :type layer_variable: str
    :type element_name: str
    """
    if element_name in definitions[layer_variable][1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER variable " + layer_variable + ". Please, select another element name.")


def not_defined_components(vector_variable, definitions):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) > 0:
        raise DefinitionError(
            "The " + vector_variable + " components are already defined as " +
            definitions[vector_variable][4][0] + ".")


def not_defined_component_element(layer_vector_variable, element_name, definitions):
    """ It checks if an element name is already used in the **LAYER** components of a **VECTOR** variable, if yes,
    raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param element_name: The element name.
    :type variable: str
    :type element_name: str
    """
    if element_name in definitions[layer_vector_variable][4][1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER components of the " + layer_vector_variable + " VECTOR variable, please, select "
                                                                                                                            "another element name.")


def check_variable_type(variable, variable_type, definitions):
    """ It checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    :type variable: str
    """
    if variable_type is BASIC:
        if definitions[variable][0] not in variable_type:
            raise DefinitionError("The variable " + variable + " is not defined as a BASIC type.")
    else:
        if definitions[variable][0] is not variable_type:
            raise DefinitionError("The variable " + variable + " is not defined as " + variable_type + " type.")


def check_component_type(vector_variable, component_type, definitions):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    if component_type is BASIC:
        if definitions[vector_variable][4][0] not in component_type:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as BASIC type.")
    else:
        if definitions[vector_variable][4][0] is not component_type:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as " + component_type
                + " type.")


def check_vector_values_size(vector_variable, values, definitions):
    if definitions[vector_variable][1] <= len(values) <= definitions[vector_variable][2]:
        raise DefinitionError(
            "The size of the values ("+str(len(values))+") is not compatible with the "+str(vector_variable)+" definition.")

def is_defined_variable_as_type(variable, variable_type, definitions):
    """ It checks if a variable is defined in the domain, if not, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
        py:class:`~pycvoa.problem.domain.WrongItemType`.

        :param variable: The variable.
        :param variable_type: The variable type.
        :type variable: str
        :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
        """
    is_defined_variable(variable, definitions)
    check_variable_type(variable, variable_type, definitions)

def are_defined_variable_component_check_component_type(vector_variable, component_type, definitions):
    is_defined_variable_as_type(vector_variable, VECTOR, definitions)
    are_defined_components(vector_variable, definitions)
    check_component_type(vector_variable, component_type, definitions)

