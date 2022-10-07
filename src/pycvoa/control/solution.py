from pycvoa.problem import Domain
from pycvoa.control import SolutionError
from pycvoa.control.types import VarStructureType, OptSupportedValues, VectorValue, LayerVectorValue


def is_assigned_layer_element(layer_variable: str, element: str, solution_structure: VarStructureType):
    is_assigned_variable(layer_variable, solution_structure)
    layer: OptSupportedValues = solution_structure.get(layer_variable)
    assert type(layer) is dict
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


def is_assigned_component_element(layer_vector_variable: str, index: int, element:str,
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
