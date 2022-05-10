from pycvoa.problem.ctrl import DefinitionError
from pycvoa.problem.types import *


# ==================================================================================================================== #
# =========================================== VARIABLE LEVEL ========================================================= #
# ==================================================================================================================== #

def is_defined_variable(variable: str, definitions: dict):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param definitions: The definitions.
    :type variable: str
    """
    if variable not in definitions.keys():
        raise DefinitionError("The variable " + variable + " is not defined in this domain.")


def not_defined_variable(variable_name: str, definitions: dict):
    """ It checks if a variable name is already used in the domain, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable_name: The variable name.
    :param definitions: The definitions.
    :type variable_name: str
    """
    if variable_name in definitions.keys():
        raise DefinitionError(
            "The " + variable_name + " variable is already defined, please, select another variable "
                                     "name.")


def check_variable_type(variable: str, check_type: str, definitions: dict):
    if check_type is BASIC:
        if definitions[variable][0] not in check_type:
            raise DefinitionError("The variable " + variable + " is not defined as BASIC type.")
    elif check_type is NUMERICAL:
        if definitions[variable][0] not in check_type:
            raise DefinitionError("The variable " + variable + " is not defined as NUMERICAL type.")
    else:
        if definitions[variable][0] is not check_type:
            raise DefinitionError("The variable " + variable + " is not defined as " + check_type + " type.")


def is_defined_variable_as_type(variable: str, variable_type: str, definitions: dict):
    """ It checks if a variable is defined in the domain, if not, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
        py:class:`~pycvoa.problem.domain.WrongItemType`.

        :param variable: The variable.
        :param variable_type: The variable type.
        :param definitions: The definitions.
        :type variable: str
        :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
        """
    is_defined_variable(variable, definitions)
    check_variable_type(variable, variable_type, definitions)


# ==================================================================================================================== #
# ============================================= LAYER LEVEL ========================================================== #
# ==================================================================================================================== #

def is_defined_element(layer_variable: str, element: str, definitions: dict):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_variable: The variable.
    :param element: The element.
    :param definitions: The definitions.
    :type layer_variable: str
    :type element: str
    """
    if element not in definitions[layer_variable][1].keys():
        raise DefinitionError(
            "The element " + element + " is not defined in the LAYER variable " + layer_variable + " in this domain.")


def not_defined_element(layer_variable: str, element_name: str, definitions: dict):
    """ It checks if an element name is already used in a **LAYER** variable definition, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param layer_variable: The variable.
    :param element_name: The element name.
    :param definitions: The definitions.
    :type layer_variable: str
    :type element_name: str
    """
    if element_name in definitions[layer_variable][1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER variable " + layer_variable
            + ". Please, select another element name.")


def check_element_type(layer_variable: str, element: str, check_type: str, definitions: dict):
    if check_type is BASIC:
        if definitions[layer_variable][1][element][0] not in check_type:
            raise DefinitionError("The element " + element + " is not defined as BASIC type in "
                                  + layer_variable + ".")
    elif check_type is NUMERICAL:
        if definitions[layer_variable][1][element][0] not in check_type:
            raise DefinitionError("The element " + element + " is not defined as NUMERICAL type in "
                                  + layer_variable + ".")
    else:
        if definitions[layer_variable][1][element][0] is not check_type:
            raise DefinitionError("The element " + element + " is not defined as "
                                  + check_type + " type in " + layer_variable + ".")


def is_defined_layer_without_element(layer_variable: str, element: str, definitions: dict):
    is_defined_variable_as_type(layer_variable, LAYER, definitions)
    not_defined_element(layer_variable, element, definitions)


def is_defined_layer_with_element(layer_variable: str, element: str, definitions: dict):
    is_defined_variable_as_type(layer_variable, LAYER, definitions)
    is_defined_element(layer_variable, element, definitions)


def is_defined_element_as_type(layer_variable: str, element: str, check_type: str, definitions: dict):
    is_defined_element(layer_variable, element, definitions)
    check_element_type(layer_variable, element, check_type, definitions)


def is_defined_layer_and_element_as_type(layer_variable: str, element: str, check_type: str,
                                         definitions: dict):
    is_defined_variable_as_type(layer_variable, LAYER, definitions)
    is_defined_element_as_type(layer_variable, element, check_type, definitions)


# ==================================================================================================================== #
# =========================================== VECTOR LEVEL =========================================================== #
# ==================================================================================================================== #

def are_defined_components(vector_variable: str, definitions: dict):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :param definitions: The definitions.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) <= 0:
        raise DefinitionError(
            "The components of " + vector_variable + " are not defined.")


def not_defined_components(vector_variable: str, definitions: dict):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :param definitions: The definitions.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) > 0:
        raise DefinitionError(
            "The " + vector_variable + " components are already defined as " +
            definitions[vector_variable][4][0] + ".")


def check_vector_values_size(vector_variable, values, definitions: dict):
    if len(values) < definitions[vector_variable][1] or len(values) > definitions[vector_variable][2]:
        raise DefinitionError(
            "The size of the values (" + str(len(values)) + ") is not compatible with the " + str(
                vector_variable) + " definition [" + str(definitions[vector_variable][1])
            + "," + str(definitions[vector_variable][2]) + "].")


def check_component_type(vector_variable: str, check_type: str, definitions: dict):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param check_type: The component type.
    :param definitions: The definitions.
    :type vector_variable: str
    :type check_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    if check_type is BASIC:
        if definitions[vector_variable][4][0] not in check_type:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as BASIC type.")
    elif check_type is NUMERICAL:
        if definitions[vector_variable][4][0] not in check_type:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as NUMERICAL type.")
    else:
        if definitions[vector_variable][4][0] is not check_type:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as " + check_type
                + " type.")


def is_defined_vector_without_components(vector_variable: str, definitions: dict):
    is_defined_variable_as_type(vector_variable, VECTOR, definitions)
    not_defined_components(vector_variable, definitions)


def is_defined_vector_with_components(vector_variable: str, definitions: dict):
    is_defined_variable_as_type(vector_variable, VECTOR, definitions)
    are_defined_components(vector_variable, definitions)


def are_defined_components_as_type(vector_variable: str, check_type: str, definitions: dict):
    are_defined_components(vector_variable, definitions)
    check_component_type(vector_variable, check_type, definitions)


def is_defined_vector_and_components_as_type(vector_variable: str, check_type: str, definitions: dict):
    is_defined_variable_as_type(vector_variable, VECTOR, definitions)
    are_defined_components_as_type(vector_variable, check_type, definitions)


# ==================================================================================================================== #
# =========================================== LAYER VECTOR LEVEL ===================================================== #
# ==================================================================================================================== #

def is_defined_component_element(layer_vector_variable: str, element: str, definitions: dict):
    """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_vector_variable: The variable.
    :param element: The element.
    :param definitions: The definitions.
    :type layer_vector_variable: str
    :type element: str
    """
    if element not in definitions[layer_vector_variable][4][1].keys():
        raise DefinitionError(
            "The element " + str(element) + " is not defined in the LAYER components of the "
            + str(layer_vector_variable) + " VECTOR variable.")


def not_defined_component_element(layer_vector_variable: str, element: str, definitions: dict):
    """ It checks if an element name is already used in the **LAYER** components of a **VECTOR** variable, if yes,
    raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param layer_vector_variable: The variable.
    :param element_name: The element name.
    :param definitions: The definitions.
    :type layer_vector_variable: str
    :type element_name: str
    """
    if element in definitions[layer_vector_variable][4][1].keys():
        raise DefinitionError(
            "The " + element + " element is already defined in the LAYER components of the "
            + layer_vector_variable + " VECTOR variable, please, select another element name.")


def check_component_element_type(layer_vector_variable: str, element: str, check_type, definitions: dict):
    if check_type is BASIC:
        if definitions[layer_vector_variable][4][1][element][0] not in check_type:
            raise DefinitionError(
                "The element " + element + " of the LAYER VECTOR variable " + layer_vector_variable
                + " are not defined as BASIC type.")
    elif check_type is NUMERICAL:
        if definitions[layer_vector_variable][4][1][element][0] not in check_type:
            raise DefinitionError(
                "The element " + element + " of the LAYER VECTOR variable " + layer_vector_variable
                + " are not defined as NUMERICAL type.")
    else:
        if definitions[layer_vector_variable][4][1][element][0] is not check_type:
            raise DefinitionError(
                "The element " + element + " of the LAYER VECTOR variable " + layer_vector_variable
                + " are not defined as " + check_type + " type.")


def is_defined_layer_vector_without_element(layer_vector_variable: str, element: str, definitions: dict):
    is_defined_vector_and_components_as_type(layer_vector_variable, LAYER, definitions)
    not_defined_component_element(layer_vector_variable, element, definitions)


def is_defined_layer_vector_with_element(layer_vector_variable: str, element: str, definitions: dict):
    is_defined_vector_and_components_as_type(layer_vector_variable, LAYER, definitions)
    is_defined_component_element(layer_vector_variable, element, definitions)


def is_defined_component_element_as_type(layer_vector_variable: str, element: str, check_type: str, definitions: dict):
    is_defined_component_element(layer_vector_variable, element, definitions)
    check_component_element_type(layer_vector_variable, element, check_type, definitions)


def is_defined_layer_vector_and_component_element(layer_vector_variable: str, element: str, definitions: dict):
    is_defined_vector_and_components_as_type(layer_vector_variable, LAYER, definitions)
    is_defined_component_element(layer_vector_variable, element, definitions)


def is_defined_layer_vector_and_component_element_as_type(layer_vector_variable: str, element: str,
                                                          check_type: str, definitions: dict):
    is_defined_vector_and_components_as_type(layer_vector_variable, LAYER, definitions)
    is_defined_component_element_as_type(layer_vector_variable, element, check_type, definitions)


# ==================================================================================================================== #
# ================================================= OTHERS =========================================================== #
# ==================================================================================================================== #

def is_defined_element_item_definition(item_definition: dict, element: str):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param item_definition: The variable.
    :param element: The element.
    :type item_definition: str
    :type element: str
    """
    if element not in item_definition.keys():
        raise DefinitionError(
            "The element " + element + " is not defined in the LAYER variable.")


def is_a_complete_layer(layer_definition: str, layer: dict):
    if len(layer) < len(layer_definition):
        raise DefinitionError(
            "The layer " + str(layer) + " is not complete.")
