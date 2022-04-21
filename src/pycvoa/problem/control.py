from pycvoa.problem import BASIC


def var_el_name_str_class(var_el):
    if type(var_el) != str:
        raise WrongParameters("The variable_name/element_name/variable/element parameter must be <str>")


def __min_max_step_int_class(min_value_size, max_value_size, step_size):
    if type(min_value_size) != int:
        raise WrongParameters("The min_value/min_size parameter must be <int>")
    if type(max_value_size) != int:
        raise WrongParameters("The max_value/max_size parameter must be <int>")
    if type(step_size) != int:
        raise WrongParameters("The step/step_size parameter must be <int>")


def __min_max_step_float_class(min_value, max_value, step):
    if type(min_value) != float:
        raise WrongParameters("The min_value parameter must be <float>")
    if type(max_value) != float:
        raise WrongParameters("The max_value parameter must be <float>")
    if type(step) != float:
        raise WrongParameters("The step parameter must be <float>")


def __categories_class(categories):
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


def __value_class_int_float(value):
    if type(value) not in (int, float):
        raise WrongParameters(
            "The value parameter must be <int> or <float>")


def __value_class_category(categories, value):
    if type(value) != type(categories[0]):
        raise WrongParameters(
            "The value parameter be the same Python type than categories (" + type(categories[0]) + ")")


# **** RANGE CONTROL ***
def __range(self, min_value, max_value, step):
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
        raise DefinitionError(
            "The minimum value/size of the variable/element (" + str(
                min_value) + ") must be less than the maximum value/size (" + str(
                max_value) + ").")
    else:
        average = (max_value - min_value) / 2
        if step > average:
            raise DefinitionError("The step value/size (" + str(
                step) + ") of the variable/element must be less or equal than (maximum "
                        "value/size - minimum value/size) / 2 (" + str(average) + ").")


# **** VARIABLE CONTROL ***

def __var_is_defined(variable,definitions):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :type variable: str
    """
    if variable not in definitions.keys():
        raise NotDefinedItem("The variable " + variable + " is not defined in this domain.")


def __var_type(variable, variable_type, definitions):
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


def __var_name_in_use(variable_name, definitions):
    """ It checks if a variable name is already used in the domain, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable_name: The variable name.
    :type variable_name: str
    """
    if variable_name in definitions.keys():
        raise DefinitionError(
            "The " + variable_name + " variable is already defined, please, select another variable "
                                     "name.")


def __var_name_in_use_range(self, variable_name, min_value, max_value, step):
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
    self.__var_name_in_use(variable_name)
    self.__range(min_value, max_value, step)


def __var_is_defined_type(self, variable, variable_type):
    """ It checks if a variable is defined in the domain, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param variable: The variable.
    :param variable_type: The variable type.
    :type variable: str
    :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    self.__var_is_defined(variable)
    self.__var_type(variable, variable_type)


# **** ELEMENT CONTROL ***

def __el_name_in_use(self, variable, element_name):
    """ It checks if an element name is already used in a **LAYER** variable definition, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param element_name: The element name.
    :type variable: str
    :type element_name: str
    """
    if element_name in self.__definitions[variable][1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER variable " + variable + ". Please, select "
                                                                                                      "another element name.")


def __el_is_defined(self, variable, element):
    """ It checks if an element is defined in a **LAYER** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param variable: The variable.
    :param element: The element.
    :type variable: str
    :type element: str
    """
    if element not in self.__definitions[variable][1].keys():
        raise NotDefinedItem(
            "The element " + element + " of the " + variable + " LAYER variable is not defined in this domain.")


def __var_is_defined_type_el_in_use(self, variable, variable_type, element_name):
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
    self.__var_is_defined(variable)
    self.__var_type(variable, variable_type)
    self.__el_name_in_use(variable, element_name)


# **** COMPONENT CONTROL ***

def __comp_type(self, vector_variable, component_type):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    if component_type is BASIC:
        if self.__definitions[vector_variable][4][0] not in component_type:
            raise WrongItemType(
                "The components of the VECTOR variable " + vector_variable + " are not defined as BASIC type.")
    else:
        if self.__definitions[vector_variable][4][0] is not component_type:
            raise WrongItemType(
                "The components of the VECTOR variable " + vector_variable + " are not defined as " + component_type
                + " type.")


def __comp_el_name_in_use(self, variable, element_name):
    """ It checks if an element name is already used in the **LAYER** components of a **VECTOR** variable, if yes,
    raise py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :param element_name: The element name.
    :type variable: str
    :type element_name: str
    """
    if element_name in self.__definitions[variable][4][1].keys():
        raise DefinitionError(
            "The " + element_name + " element is already defined in the LAYER coponents of the " + variable + " VECTOR variable, please, select "
                                                                                                              "another element name.")


def __comp_el_is_defined(self, vector_variable, element):
    """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param vector_variable: The variable.
    :param element: The element.
    :type vector_variable: str
    :type element: str
    """
    if element not in self.__definitions[vector_variable][4][1].keys():
        raise NotDefinedItem(
            "The element " + element + " is not defined in the LAYER components of the " + vector_variable + " VECTOR variable.")


def __comp_type_defined(self, vector_variable):
    """ It checks if the type of a **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    :param vector_variable: The variable.
    :type vector_variable: str
    """
    if len(self.__definitions[vector_variable][4]) == 0:
        raise NotDefinedItem(
            "The " + vector_variable + " components are not defined.")


def __comp_type_not_defined(self, vector_variable):
    """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param variable: The variable.
    :type variable: str
    """
    if len(self.__definitions[vector_variable][4]) > 0:
        raise DefinitionError(
            "The " + vector_variable + " components are already defined as " +
            self.__definitions[vector_variable][4][0] + ".")


def __comp_is_defined_type(self, vector_variable, component_type):
    """ It checks if the type of the **VECTOR** variable is defined, if not, raise
    py:class:`~pycvoa.problem.domain.NotDefinedItem`.

    If the second condition is fulfilled, it checks if the components of the **VECTOR** variable are defined as
    a concrete type, if not, raise py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The variable.
    :param component_type: The component type.
    :type vector_variable: str
    :type component_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    self.__comp_type_defined(vector_variable)
    self.__comp_type(vector_variable, component_type)


def __var_is_defined_type_comp_type_el_name_in_use(self, variable, variable_type, component_type, element_name):
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
    self.__var_is_defined(variable)
    self.__var_type(variable, variable_type)
    self.__comp_type_defined(variable)
    self.__comp_type(variable, component_type)
    self.__comp_el_name_in_use(variable, element_name)


class DomainError(Exception):
    """ It is the top level exception for :py:class:`~pycvoa.problem.domain.Domain` error management.
        """
    pass


class DefinitionError(DomainError):
    """ It is raised when the definition of a variable is wrong.

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
        """

    def __init__(self, message):
        self.message = message


class NotDefinedItem(DomainError):
    """ It is raised when a variable is not defined in the domain or when an element is not defined in a **LAYER**
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


class WrongItemType(DomainError):
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


class WrongParameters(DomainError):
    """ It is raised when the parameters of a query function are wrong.

            **Methods that can throw this exception:**

            - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
        """

    def __init__(self, message):
        self.message = message
