from pycvoa.problem.types import *

def sol_ctrl_check_variable_availability(variable, solution_structure):
    if variable not in solution_structure.keys():
        raise NotAvailableItem("The " + variable + " variable is not in this solution.")


def sol_ctrl_check_element_availability(layer_variable, element, solution_structure):
    if element not in solution_structure.get(layer_variable).keys():
        raise NotAvailableItem("The element " + element + " is not available in the " + layer_variable + " variable.")


def sol_ctrl_check_component_availability(variable, index, solution_structure):
    if index < 0 or index >= len(solution_structure.get(variable)):
        raise NotAvailableItem(
            "The " + str(index) + "-nh component of " + variable + " VECTOR variable is not available.")


def sol_ctrl_check_component_element_availability(vector_variable, element, index, solution_structure):
    if element not in solution_structure.get(vector_variable)[index].keys():
        raise NotAvailableItem("The element " + element + " in not in the " + index + " component "
                                                                                      "of the " + vector_variable + " variable.")


def sol_ctrl_can_insert_in_vector(vector_variable, vector_size, domain):
    if domain.get_remaining_components(vector_variable,vector_size) == 0:
        raise NotAvailableItem("The " + str(vector_variable) + " is complete.")


def check_variable_type(variable, variable_type, domain):
    var_type = domain.get_variable_type(variable)
    if variable_type is BASIC:
        if var_type not in BASIC:
            raise WrongItemType("The " + variable + " variable is not defined as BASIC.")
    else:
        if var_type is not variable_type:
            raise WrongItemType("The " + variable + " variable is not defined as " + variable_type + ".")


def check_component_type(vector_variable, component_type, domain):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    comp_type = domain.get_component_type(vector_variable)
    if component_type is BASIC:
        if comp_type not in BASIC:
            raise WrongItemType("The components of " + vector_variable + " are not defined as BASIC.")
    else:
        if comp_type is not component_type:
            raise WrongItemType("The components of " + vector_variable + " are not defined as " + component_type + ".")



