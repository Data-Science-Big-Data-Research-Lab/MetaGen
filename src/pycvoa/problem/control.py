import pycvoa
from pycvoa.problem import BASIC, INTEGER, REAL, CATEGORICAL, VECTOR


def ctrl_element_is_none(variable, element):
    if element is not None:
        raise WrongParameters(
            "The variable/component type of " + variable + " is BASIC, therefore, the element must not "
                                                           "be provided.")


def ctrl_element_not_none(variable, element):
    if element is None:
        raise WrongParameters(
            "The variable/component type of " + variable + " is LAYER, therefore, the element must "
                                                           "be provided.")


def ctrl_index_not_none(variable, index):
    if index is None:
        raise WrongParameters(
            "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                "must be provided")


def ctrl_index_is_none(variable, index):
    if index is not None:
        raise WrongParameters(
            "The " + variable + "variable is not defined as VECTOR, therefore, an index must not be provided")


def ctrl_index_element_is_none(variable, index, element):
    ctrl_index_is_none(variable, index)
    ctrl_element_is_none(variable, element)


def sol_ctrl_check_domain_type(variable, check_type, external_domain, internal_domain):
    current_domain = sol_ctrl_check_domain(external_domain, internal_domain)
    sol_ctrl_check_type(variable, check_type, current_domain)
    return current_domain


def sol_ctrl_check_domain(external_domain, internal_domain):
    sol_ctrl_check_domain_class(external_domain)
    current_domain = external_domain
    if current_domain is None:
        current_domain = internal_domain
    if current_domain is None:
        raise NotAvailableItem("A domain must be specified, via parameter or set_domain method.")
    return current_domain


def sol_ctrl_check_domain_class(domain):
    if domain is not None:
        if type(domain) is not pycvoa.problem.domain.Domain:
            raise WrongParameters("The " + domain + " parameter is not instantiate from <Domain> class.")


def sol_ctrl_check_type(variable, check_type, domain):
    var_type = domain.get_variable_type(variable)
    if check_type is BASIC:
        if var_type not in BASIC:
            raise WrongItemType("The " + variable + " variable is not defined as BASIC.")
    else:
        if var_type is not check_type:
            raise WrongItemType("The " + variable + " variable is not defined as " + check_type + ".")


def sol_ctrl_check_var_avail_dom_type(variable, solution_structure, check_type, external_domain,
                                      internal_domain):
    sol_ctrl_check_variable_availability(variable, solution_structure)
    current_domain = sol_ctrl_check_domain_type(variable, check_type, external_domain, internal_domain)
    return current_domain


def sol_ctrl_check_component_type(vector_variable, check_type, domain):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    comp_type = domain.get_component_type(vector_variable)
    if check_type is BASIC:
        if comp_type not in BASIC:
            raise WrongItemType("The components of " + vector_variable + " are not defined as BASIC.")
    else:
        if comp_type is not check_type:
            raise WrongItemType("The components of " + vector_variable + " are not defined as " + check_type + ".")


def sol_ctrl_check_basic_value(variable, value, domain):
    if not domain.check_basic(variable, value):
        raise WrongItemValue("The value " + str(value) + " is not compatible with the " + variable + " variable "
                                                                                                     "definition.")


def sol_ctrl_check_element_value(variable, element, value, domain):
    if not domain.check_element(variable, element, value):
        raise WrongItemValue(
            "The value " + str(
                value) + " is not valid for the " + element + " element in the " + variable + " variable.")


def sol_ctrl_check_basic_component(variable, value, domain):
    if not domain.check_vector_basic_value(variable, value):
        raise WrongItemValue(
            "The value " + value + " is not valid for the " + variable + " variable.")


def sol_ctrl_check_element_component(variable, element, value, domain):
    if not domain.check_vector_layer_element_value(variable, element, value):
        raise WrongItemValue(
            "The value " + value + " is not valid for the " + element + " element in the " + variable + " variable.")


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


# DOMAIN

def dom_ctrl_var_el_name_str_class(var_el):
    if type(var_el) != str:
        raise WrongParameters("The variable_name/element_name/variable/element parameter must be <str>.")


def dom_ctrl_min_max_step_int_class(min_value_size, max_value_size, step_size):
    if type(min_value_size) != int:
        raise WrongParameters("The min_value/min_size parameter must be <int>")
    if type(max_value_size) != int:
        raise WrongParameters("The max_value/max_size parameter must be <int>")
    if type(step_size) != int:
        raise WrongParameters("The step/step_size parameter must be <int>")


def dom_ctrl_min_max_step_float_class(min_value, max_value, step):
    if type(min_value) != float:
        raise WrongParameters("The min_value parameter must be <float>")
    if type(max_value) != float:
        raise WrongParameters("The max_value parameter must be <float>")
    if type(step) != float:
        raise WrongParameters("The step parameter must be <float>")


def dom_ctrl_categories_class(categories):
    if type(categories) != list:
        raise WrongParameters("The categories parameter must be <list>")
    if len(categories) < 2:
        raise WrongParameters("The categories parameter must have al least two elements")
    for el in categories:
        if type(el) not in (int, float, str):
            raise WrongParameters(
                "The " + str(categories.index(
                    el)) + "-nh element of the categories parameter must be <int>, <float> or <str>")
        if type(el) != type(categories[0]):
            raise WrongParameters(
                "All the elements of the categories parameter must have the same type (<int>, <float> or <str>)")


def dom_ctrl_value_class_int_float(value):
    if type(value) not in (int, float):
        raise WrongParameters(
            "The value parameter must be <int> or <float>")


def dom_ctrl_value_class_int(value):
    if type(value) != int:
        raise WrongParameters(
            "The value parameter must be <int>.")


def dom_ctrl_value_class_float(value):
    if type(value) != float:
        raise WrongParameters(
            "The value parameter must be <float>.")


def dom_ctrl_value_class_category(categories, value):
    if type(value) != type(categories[0]):
        raise WrongParameters(
            "The value parameter be the same Python type than categories (" + str(type(categories[0])) + ")")

def dom_ctrl_values_class_dict(values):
    if type(values) != dict:
        raise WrongParameters(
            "The values parameter must be <dict>.")

def dom_ctrl_vector_defined_type_comp_defined_type(variable, component_type, definitions):
    dom_ctrl_var_is_defined_type(variable, VECTOR, definitions)
    dom_ctrl_comp_is_defined_type(variable, component_type, definitions)


def dom_check_vector_values_size(vector_variable, values, definitions):
    if definitions[vector_variable][1] > len(values) > definitions[vector_variable][2]:
        raise WrongItemValue(
            "The size of " + str(values) + " is not compatible with the " + vector_variable + " variable "
                                                                                              "definition.")


def sol_check_vector_layer_values_size_class(vector_variable, values, domain):
    sol_check_vector_values_size(vector_variable, values, domain)
    sol_check_vector_layer_values(vector_variable, values, domain)


def sol_check_vector_basic_values_size_class(vector_variable, values, domain):
    sol_check_vector_values_size(vector_variable, values, domain)
    sol_check_vector_basic_values(vector_variable, values, domain)


def sol_check_vector_values_size(vector_variable, values, domain):
    if not domain.check_vector_size(vector_variable, values):
        raise WrongParameters("The size of " + str(values) + " is not compatible with the " + vector_variable
                              + " definition.")


def sol_check_vector_basic_values(vector_variable, values, domain):
    res = domain.check_vector_basic_values(vector_variable, values)
    if res[0] != -1:
        raise WrongParameters("The " + res[0] + "-nh value must be " + res[1] + ".")


def sol_check_vector_layer_values(vector_variable, values, domain):
    for layer in values:
        for element, value in layer:
            element_definition = domain.get_component_element_definition(vector_variable, element)
            if element_definition[0] is INTEGER:
                dom_ctrl_value_class_int(value)
                if value < element_definition[1] or value > element_definition[2]:
                    raise WrongParameters("The "+element+" element of the "+ str(values.index(layer)) + "-nh component "
                                                                            "is not compatible with its definition.")
            elif element_definition[0] is REAL:
                dom_ctrl_value_class_float(value)
                if value < element_definition[1] or value > element_definition[2]:
                    raise WrongParameters(
                        "The " + element + " element of the " + str(values.index(layer)) + "-nh component "
                                                                        "is not compatible with its definition.")
            elif element_definition[0] is CATEGORICAL:
                dom_ctrl_value_class_category(element_definition[1], value)
                if value not in element_definition[1]:
                    raise WrongParameters(
                        "The " + element + " element of the " + str(values.index(layer)) + "-nh component "
                                                                             "is not compatible with its definition.")


# **** RANGE CONTROL ***
def dom_ctrl_range(min_value, max_value, step):
    """ It checks if min_value < max_value, if not, raise :py:class:`~pycvoa.problem.domain.DefinitionError`.
    If the first condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param min_value: The minimum value.
    :param max_value: The maximum value.
    :param step: The step.
    :type min_value: int, float
    :type max_value: int, float
    :type step: int, float
    """
    if min_value >= max_value:
        raise WrongItemValue(
            "The minimum value/size of the variable/element (" + str(
                min_value) + ") must be less than the maximum value/size (" + str(
                max_value) + ").")
    else:
        average = (max_value - min_value) / 2
        if step > average:
            raise WrongItemValue("The step value/size (" + str(
                step) + ") of the variable/element must be less or equal than (maximum "
                        "value/size - minimum value/size) / 2 (" + str(average) + ").")


# **** VARIABLE CONTROL ***

def dom_ctrl_var_is_defined(variable, definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :type variable: str
    """
    if variable not in definitions.keys():
        raise NotAvailableItem("The variable " + variable + " is not defined in this domain.")


def dom_ctrl_var_type(variable, variable_type, definitions):
    """ It checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    :type variable: str
    """
    if variable_type is BASIC:
        if definitions[variable][0] not in variable_type:
            raise WrongItemType("The variable " + variable + " is not defined as a BASIC type.")
    else:
        if definitions[variable][0] is not variable_type:
            raise WrongItemType("The variable " + variable + " is not defined as " + variable_type + " type.")


def dom_ctrl_var_name_in_use(variable_name, definitions):
    """ It checks if a variable name is already used in the domain, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable_name: The variable name.
    :type variable_name: str
    """
    if variable_name in definitions.keys():
        raise NotAvailableItem(
            "The " + variable_name + " variable is already defined, please, select another variable "
                                     "name.")


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


# **** ELEMENT CONTROL ***

def dom_ctrl_el_name_in_use(variable, element_name, definitions):
    """ It checks if an element name is already used in a **LAYER** variable definition, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param element_name: The element name.
    :type variable: str
    :type element_name: str
    """
    if element_name in definitions[variable][1].keys():
        raise WrongItemType(
            "The " + element_name + " element is already defined in the LAYER variable " + variable + ". Please, select "
                                                                                                      "another element name.")


def dom_ctrl_el_is_defined(variable, element, definitions):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param variable: The variable.
    :param element: The element.
    :type variable: str
    :type element: str
    """
    if element not in definitions[variable][1].keys():
        raise NotAvailableItem(
            "The element " + element + " of the " + variable + " LAYER variable is not defined in this domain.")


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


# **** COMPONENT CONTROL ***

def dom_ctrl_comp_type(vector_variable, component_type, definitions):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    if component_type is BASIC:
        if definitions[vector_variable][4][0] not in component_type:
            raise WrongItemType(
                "The components of the VECTOR variable " + vector_variable + " are not defined as BASIC type.")
    else:
        if definitions[vector_variable][4][0] is not component_type:
            raise WrongItemType(
                "The components of the VECTOR variable " + vector_variable + " are not defined as " + component_type
                + " type.")


def dom_ctrl_comp_el_name_in_use(vector_variable, element_name, definitions):
    """ It checks if an element name is already used in the **LAYER** components of a **VECTOR** variable, if yes,
    raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param element_name: The element name.
    :type variable: str
    :type element_name: str
    """
    if element_name in definitions[vector_variable][4][1].keys():
        raise WrongItemType(
            "The " + element_name + " element is already defined in the LAYER components of the " + vector_variable + " VECTOR variable, please, select "
                                                                                                                      "another element name.")


def dom_ctrl_comp_el_is_defined(vector_variable, element, definitions):
    """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param vector_variable: The variable.
    :param element: The element.
    :type vector_variable: str
    :type element: str
    """
    if element not in definitions[vector_variable][4][1].keys():
        raise WrongItemType(
            "The element " + element + " is not defined in the LAYER components of the " + vector_variable + " VECTOR variable.")


def dom_ctrl_comp_type_defined(vector_variable, definitions):
    """ It checks if the type of a **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param vector_variable: The variable.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) == 0:
        raise NotAvailableItem(
            "The " + vector_variable + " components are not defined.")


def dom_ctrl_comp_type_not_defined(vector_variable, definitions):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param vector_variable: The variable.
    :type vector_variable: str
    """
    if len(definitions[vector_variable][4]) > 0:
        raise WrongItemType(
            "The " + vector_variable + " components are already defined as " +
            definitions[vector_variable][4][0] + ".")


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




class WrongParameters(Exception):
    """ It is raised when the parameters of a query function are wrong.

        **Methods that can directly throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
        - :py:meth:`~pycvoa.problem.solution.Solution.set_value`
        """

    def __init__(self, message):
        self.message = message


class WrongItemType(Exception):
    """ It is raised when the type of the variable is wrong.

         **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        self.message = message


class NotAvailableItem(Exception):
    """ It is raised when the domain is not set in the solution.

    **Methods that can directly throw this exception:**

    - :py:meth:`~pycvoa.problem.solution.Solution.check_variable_type`
    - :py:meth:`~pycvoa.problem.solution.Solution.check_component_type`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_basic`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_component_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.add_basic_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.insert_basic_component`

    **Methods that can throw this exception through auxiliary functions:**

    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_component_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_basic_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_element_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_basic_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_layer_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_size`
    - :py:meth:`~pycvoa.problem.solution.Solution.remove_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.delete_component`

    It is raised when the definition of a variable is wrong.

            **Methods that can directly throw this exception:**

           - :py:meth:`~pycvoa.problem.domain.Domain.define_integer`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_real`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_vector`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
           - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`

        It is raised when a variable is not defined in the domain or when an element is not defined in a **LAYER**
        variable of the domain.

        **Methods that can directly throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.get_variable_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_variable_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`

         **Methods that can throw this exception through auxiliary functions:**

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.is_defined_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_type`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
        - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
    """

    def __init__(self, message):
        self.message = message


class WrongItemValue(Exception):
    """ It is raised when the domain is not set in the solution.

    **Methods that can directly throw this exception:**

    - :py:meth:`~pycvoa.problem.solution.Solution.check_variable_type`
    - :py:meth:`~pycvoa.problem.solution.Solution.check_component_type`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_basic`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_component_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.set_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.add_basic_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.insert_basic_component`

    **Methods that can throw this exception through auxiliary functions:**

    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.is_available_component_element`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_basic_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_element_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_basic_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_layer_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_size`
    - :py:meth:`~pycvoa.problem.solution.Solution.remove_component`
    - :py:meth:`~pycvoa.problem.solution.Solution.delete_component`
    """

    def __init__(self, message):
        self.message = message
