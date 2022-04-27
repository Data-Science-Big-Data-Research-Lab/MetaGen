from pycvoa.problem.ctrl import SolutionError


def is_assigned_variable(variable, solution_structure):
    if variable not in solution_structure.keys():
        raise SolutionError("The " + variable + " variable is not assigned in this solution.")


def is_assigned_element(layer_variable, element, solution_structure):
    if element not in solution_structure.get(layer_variable).keys():
        raise SolutionError("The element " + element + " is not assigned in the " + layer_variable + " variable of this solution.")


def is_assigned_component(vector_variable, index, solution_structure):
    if index < 0 or index >= len(solution_structure.get(vector_variable)):
        raise SolutionError(
            "The " + str(index) + "-nh component of " + vector_variable + " VECTOR variable is not assigned in this solution.")


def is_assigned_component_element(layer_vector_variable, element, index, solution_structure):
    if element not in solution_structure.get(layer_vector_variable)[index].keys():
        raise SolutionError("The element " + element + " in not assigned in the " + str(index) + "-nh component "
                                                                                      "of the " + layer_vector_variable + " variable in this solution.")


def vector_insertion_available(vector_variable, vector_size, domain):
    if domain.get_remaining_available_components(vector_variable, vector_size) == 0:
        raise SolutionError("The " + str(vector_variable) + " is complete.")



