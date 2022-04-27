def ctrl_index_element_is_none(variable, index, element):
    ctrl_index_is_none(variable, index)
    ctrl_element_is_none(variable, element)


def sol_ctrl_check_domain_type(variable, check_type, external_domain, internal_domain):
    current_domain = sol_ctrl_check_domain(external_domain, internal_domain)
    sol_ctrl_check_type(variable, check_type, current_domain)
    return current_domain


def sol_ctrl_check_var_avail_dom_type(variable, solution_structure, check_type, external_domain,
                                      internal_domain):
    sol_ctrl_check_variable_availability(variable, solution_structure)
    current_domain = sol_ctrl_check_domain_type(variable, check_type, external_domain, internal_domain)
    return current_domain


def dom_ctrl_vector_defined_type_comp_defined_type(variable, component_type, definitions):
    dom_ctrl_var_is_defined_type(variable, VECTOR, definitions)
    dom_ctrl_comp_is_defined_type(variable, component_type, definitions)


def sol_check_vector_layer_values_size_class(vector_variable, values, domain):
    sol_check_vector_values_size(vector_variable, values, domain)
    sol_check_vector_layer_values(vector_variable, values, domain)


def sol_check_vector_basic_values_size_class(vector_variable, values, domain):
    sol_check_vector_values_size(vector_variable, values, domain)
    sol_check_vector_basic_values(vector_variable, values, domain)


def dom_ctrl_var_name_in_use_range(variable_name, min_value, max_value, step, definitions):
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
    dom_ctrl_var_name_in_use(variable_name, definitions)
    dom_ctrl_range(min_value, max_value, step)


def dom_ctrl_var_is_defined_type(variable, variable_type, definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :type variable: str
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    dom_ctrl_var_is_defined(variable, definitions)
    dom_ctrl_var_type(variable, variable_type, definitions)


def dom_ctrl_var_is_defined_type_el_in_use(variable, variable_type, element_name, definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    If the second condition is fulfilled, it checks if an element name is already used in the **LAYER** variable
    definition, if yes, raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :param element_name: The element.
    :type variable: str
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    :type element_name: str
    """
    dom_ctrl_var_is_defined(variable, definitions)
    dom_ctrl_var_type(variable, variable_type, definitions)
    dom_ctrl_el_name_in_use(variable, element_name, definitions)


def dom_ctrl_comp_is_defined_type(vector_variable, component_type, definitions):
    """ It checks if the type of the **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    If the second condition is fulfilled, it checks if the components of the **VECTOR** variable are defined as
    a concrete type, if not, raise py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    dom_ctrl_comp_type_defined(vector_variable, definitions)
    dom_ctrl_comp_type(vector_variable, component_type, definitions)


def dom_ctrl_var_is_defined_type_comp_type_el_name_in_use(vector_variable, variable_type, component_type, element_name,
                                                          definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    If the second condition is fulfilled, it checks if the type of the **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    If the third condition is fulfilled, it checks if the components of the **VECTOR** variable are defined as
    a concrete type, if not, raise py:class:`~pycvoa.problem.domain.WrongItemType`.

    If the fourth condition is fulfilled, it checks if an element name is already used in the **LAYER** components
    of the **VECTOR** variable, if yes, raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :param component_type: The component type.
    :param element_name: The element name.
    :type variable: str
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    :type element_name: str
    """
    dom_ctrl_var_is_defined(vector_variable, definitions)
    dom_ctrl_var_type(vector_variable, variable_type, definitions)
    dom_ctrl_comp_type_defined(vector_variable, definitions)
    dom_ctrl_comp_type(vector_variable, component_type, definitions)
    dom_ctrl_comp_el_name_in_use(vector_variable, element_name, definitions)

