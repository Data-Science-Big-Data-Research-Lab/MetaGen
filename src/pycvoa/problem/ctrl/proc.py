import pycvoa.problem.ctrl as ctrl


def is_assigned_variable_valid_domain_check_variable_type(variable, solution_structure, check_type, external_domain,
                                                          internal_domain):
    ctrl.sol.is_assigned_variable(variable, solution_structure)
    current_domain = ctrl.val.valid_domain_check_variable_type(variable, check_type, external_domain, internal_domain)
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
