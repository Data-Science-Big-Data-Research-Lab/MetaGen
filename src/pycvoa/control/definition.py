from typing import cast

from pycvoa.control import DefinitionError
from pycvoa.control.types import *
import pycvoa.control.common as cmn


# ========== VARIABLE LEVEL ========== #

def is_defined_variable(variable: str, definitions: DefStructure):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param definitions: The definitions.
    :type variable: str
    """
    if variable not in definitions.keys():
        raise DefinitionError("The variable " + variable + " is not defined in this domain.")


def not_defined_variable(variable_name: str, definitions: DefStructure):
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


def check_variable_type(variable: str, definitions: DefStructure, check_type: PYCVOA_TYPE):
    if cmn.check_item_type(check_type, definitions[variable][0]) is False:
        raise DefinitionError("The " + variable + " variable is not defined as " + str(check_type) + ".")


def is_defined_variable_as_type(variable: str, definitions: DefStructure, variable_type: PYCVOA_TYPE):
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
    check_variable_type(variable, definitions, variable_type)


# ==================================================================================================================== #
# ============================================= LAYER LEVEL ========================================================== #
# ==================================================================================================================== #

def is_defined_element(layer_variable: str, element: OptStr, layer_definition: LayerDef):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_variable: The variable.
    :param element: The element.
    :param layer_definition: The definitions.
    :type layer_variable: str
    :type element: str
    """
    if element not in layer_definition[1].keys():
        raise DefinitionError(
            "The element " + str(element) + " is not defined in the LAYER variable " + layer_variable + ".")


def not_defined_element(layer_variable: str, element_name: str, layer_definition: LayerDef):
    """ It checks if an element name is already used in a **LAYER** variable definition, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param layer_variable: The variable.
    :param element_name: The element name.
    :param layer_definition: The definitions.
    :type layer_variable: str
    :type element_name: str
    """
    if element_name in layer_definition[1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER variable " + layer_variable
            + ". Please, select another element name.")


def check_element_type(layer_variable: str, element: str, layer_definition: LayerDef, check_type: PYCVOA_TYPE):
    if cmn.check_item_type(check_type, cast(LayerAttributes, layer_definition[1])[element][0]) is False:
        raise DefinitionError("The element " + element + " is not defined as "
                              + str(check_type) + " type in " + layer_variable + ".")


def is_defined_layer_without_element(layer_variable: str, element: str, definitions: DefStructure):
    is_defined_variable_as_type(layer_variable, definitions, LAYER)
    not_defined_element(layer_variable, element, cast(LayerDef, definitions[layer_variable]))


def is_defined_layer_with_element(layer_variable: str, element: str, definitions: DefStructure):
    is_defined_variable_as_type(layer_variable, definitions, LAYER)
    is_defined_element(layer_variable, element, cast(LayerDef, definitions[layer_variable]))


def is_defined_element_as_type(layer_variable: str, element: str, layer_definition: LayerDef, check_type: PYCVOA_TYPE):
    is_defined_element(layer_variable, element, layer_definition)
    check_element_type(layer_variable, element, layer_definition, check_type)


def is_defined_layer_and_element_as_type(layer_variable: str, element: str, definitions: DefStructure,
                                         check_type: PYCVOA_TYPE):
    is_defined_variable_as_type(layer_variable, definitions, LAYER)
    is_defined_element_as_type(layer_variable, element, cast(LayerDef, definitions[layer_variable]), check_type)


# ==================================================================================================================== #
# =========================================== VECTOR LEVEL =========================================================== #
# ==================================================================================================================== #

def are_defined_components(vector_variable: str, vector_definition: VectorDef):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :param vector_definition: The definitions.
    :type vector_variable: str
    """
    if vector_definition[4] is None:
        raise DefinitionError(
            "The components of " + vector_variable + " are not defined.")


def not_defined_components(vector_variable: str, vector_definition: VectorDef):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :param vector_definition: The definitions.
    :type vector_variable: str
    """
    if vector_definition[4] is not None:
        raise DefinitionError(
            "The " + vector_variable + " components are already defined as " + vector_definition[4][0] + ".")


def check_vector_values_size(vector_variable: str, vector_definition: VectorDef,
                             values: Union[VectorValue, VectorInput]):
    if len(values) < vector_definition[1] or len(values) > vector_definition[2]:
        raise DefinitionError(
            "The size of the values (" + str(len(values)) + ") is not compatible with the " + str(
                vector_variable) + " definition [" + str(vector_definition[1])
            + "," + str(vector_definition[2]) + "].")


def check_component_type(vector_variable: str, vector_definition: VectorDef, check_type: PYCVOA_TYPE):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param check_type: The component type.
    :param vector_definition: The definitions.
    :type vector_variable: str
    :type check_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    assert vector_definition[4] is not None
    if cmn.check_item_type(check_type, vector_definition[4][0]) is False:
        raise DefinitionError(
            "The components of the VECTOR variable " + vector_variable + " are not defined as " + str(check_type)
            + " type.")


def is_defined_vector_without_components(vector_variable: str, definitions: DefStructure):
    is_defined_variable_as_type(vector_variable, definitions, VECTOR)
    not_defined_components(vector_variable, cast(VectorDef, definitions[vector_variable]))


def is_defined_vector_with_components(vector_variable: str, definitions: DefStructure):
    is_defined_variable_as_type(vector_variable, definitions, VECTOR)
    are_defined_components(vector_variable, cast(VectorDef, definitions[vector_variable]))


def are_defined_components_as_type(vector_variable: str, vector_definition: VectorDef, check_type: PYCVOA_TYPE):
    are_defined_components(vector_variable, vector_definition)
    check_component_type(vector_variable, vector_definition, check_type)


def is_defined_vector_and_components_as_type(vector_variable: str, definitions: DefStructure, check_type: PYCVOA_TYPE):
    is_defined_variable_as_type(vector_variable, definitions, VECTOR)
    are_defined_components_as_type(vector_variable, cast(VectorDef, definitions[vector_variable]), check_type)


# ==================================================================================================================== #
# =========================================== LAYER VECTOR LEVEL ===================================================== #
# ==================================================================================================================== #

def is_defined_component_element(layer_vector_variable: str, element: str, layer_vector_definition: VectorDef):
    """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_vector_variable: The variable.
    :param element: The element.
    :param layer_vector_definition: The definitions.
    :type layer_vector_variable: str
    :type element: str
    """
    if element not in cast(LayerDef, layer_vector_definition[4])[1].keys():
        raise DefinitionError(
            "The element " + str(element) + " is not defined in the LAYER components of the "
            + str(layer_vector_variable) + " VECTOR variable.")


def not_defined_component_element(layer_vector_variable: str, element: str, layer_vector_definition: VectorDef):
    """ It checks if an element name is already used in the **LAYER** components of a **VECTOR** variable, if yes,
    raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param layer_vector_variable: The variable.
    :param element: The element name.
    :param layer_vector_definition: The definitions.
    :type layer_vector_variable: str
    :type element: str
    """
    if element in cast(LayerDef, layer_vector_definition[4])[1].keys():
        raise DefinitionError(
            "The " + element + " element is already defined in the LAYER components of the "
            + layer_vector_variable + " VECTOR variable, please, select another element name.")


def check_component_element_type(layer_vector_variable: str, element: str, layer_vector_definition: VectorDef,
                                 check_type: PYCVOA_TYPE):
    if cmn.check_item_type(check_type, cast(LayerDef, layer_vector_definition[4])[1][element][0]) is False:
        raise DefinitionError(
            "The element " + element + " of the LAYER VECTOR variable " + layer_vector_variable
            + " are not defined as " + check_type + " type.")


def is_defined_layer_vector_without_element(layer_vector_variable: str, element: str, definitions: DefStructure):
    is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
    not_defined_component_element(layer_vector_variable, element, cast(VectorDef, definitions[layer_vector_variable]))


def is_defined_layer_vector_with_element(layer_vector_variable: str, element: str, definitions: DefStructure):
    is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
    is_defined_component_element(layer_vector_variable, element, cast(VectorDef, definitions[layer_vector_variable]))


def is_defined_component_element_as_type(layer_vector_variable: str, element: str,
                                         layer_vector_definition: VectorDef, check_type: PYCVOA_TYPE):
    is_defined_component_element(layer_vector_variable, element, layer_vector_definition)
    check_component_element_type(layer_vector_variable, element, layer_vector_definition, check_type)


def is_defined_layer_vector_and_component_element(layer_vector_variable: str, element: str, definitions: DefStructure):
    is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
    is_defined_component_element(layer_vector_variable, element, cast(VectorDef, definitions[layer_vector_variable]))


def is_defined_layer_vector_and_component_element_as_type(layer_vector_variable: str, element: str,
                                                          definitions: DefStructure, check_type: PYCVOA_TYPE):
    is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
    is_defined_component_element_as_type(layer_vector_variable, element,
                                         cast(VectorDef, definitions[layer_vector_variable]), check_type)


# ==================================================================================================================== #
# ================================================= OTHERS =========================================================== #
# ==================================================================================================================== #

def is_defined_element_item_definition(layer_variable: str, element: str, layer_definition: LayerDef):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param layer_variable: The variable.
    :param element: The element.
    :param layer_definition: The definition
    :type layer_variable: str
    :type element: str
    """
    if element not in layer_definition[1].keys():
        raise DefinitionError(
            "The element " + element + " is not defined in the " + layer_variable + " LAYER variable.")


def is_a_complete_layer(layer_definition: LayerDef, layer_values: LayerInput):
    # print("layer_definition[1] = " + str(layer_definition[1]))
    # print("len = " + str(len(layer_definition[1])))
    if len(layer_values) < len(layer_definition[1]):
        raise DefinitionError(
            "The layer " + str(layer_values) + " is not complete.")
