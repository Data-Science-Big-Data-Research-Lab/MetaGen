from pycvoa.problem import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, BASIC
from pycvoa.problem.support import definition_to_string


class Domain:
    """ This class provides the required functionality to define a domain. The user must instantiate the class, then,
    define the variables using the member methods of the class.

    **Example:**

    .. code-block:: python

        new_domain = Domain()
        new_domain.define_categorical("V1",["C1","C2","C3"])


    The variable definitions are internally stored in a member variable with the following TYPE-depended structure:

    **Internal structure for BASIC definition TYPES**

    - list(INTEGER, Maximum value [int], Minimum value [int], Step[int])
    - list(REAL, Maximum value [float], Minimum value [float], Step[float])
    - list(CATEGORICAL, Categories[list(Any)*])

    **Internal structure for the LAYER definition TYPE**

    - list(LAYER,
                list(
                        (
                        list(INTEGER, Maximum value [int], Minimum value [int], Step[int]) |
                        list(REAL, Maximum value [float], Minimum value [float], Step[float]) |
                        list(CATEGORICAL, Categories[list(Any)*])
                        )*
                    )
            )

    **Internal structure for the VECTOR definition TYPE**

    - list(VECTOR, Maximum size [int], Minimum size [int], Step size [int],
                list(INTEGER, Maximum value [int], Minimum value [int], Step[int])
           )
     - list(VECTOR, Maximum size [int], Minimum size [int], Step size [int],
                list(REAL, Maximum value [float], Minimum value [float], Step[float])
           )
   - list(VECTOR, Maximum size [int], Minimum size [int], Step size [int],
                list(CATEGORICAL, Categories[list(Any)*])
           )
    - list(VECTOR, Maximum size [int], Minimum size [int], Step size [int],
            list(LAYER,
                list(
                        (
                        list(INTEGER, Maximum value [int], Minimum value [int], Step[int]) |
                        list(REAL, Maximum value [float], Minimum value [float], Step[float]) |
                        list(CATEGORICAL, Categories[list(Any)*])
                        )*
                    )
                )
            )

    """

    def __init__(self):
        """ It is the default, and unique, constructor without parameters.

        :ivar __definitions: Data structure where the variable definitions of the domains will be stored.
        :vartype __definitions: dict
        """
        self.__definitions = {}

    # **** DEFINE BASIC VARIABLE METHODS ****

    def define_integer(self, variable_name, min_value, max_value, step):
        """ It defines an **INTEGER** variable receiving the variable name, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable_name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The variable name is already used,
         min_value >= max_value or step >= (max_value - min_value) / 2.
        """
        self.__var_el_name_str_class(variable_name)
        self.__min_max_step_int_class(min_value, max_value, step)
        self.__var_name_in_use_range(variable_name, min_value, max_value, step)
        self.__definitions[variable_name] = [INTEGER, min_value, max_value, step]

    def define_real(self, variable_name, min_value, max_value, step):
        """ It defines a **REAL** variable receiving the variable name, the minimum and maximum values that it will be
        able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable_name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The variable name is already used,
         min_value >= max_value or step >= (max_value - min_value) / 2.
        """
        self.__var_el_name_str_class(variable_name)
        self.__min_max_step_float_class(min_value, max_value, step)
        self.__var_name_in_use_range(variable_name, min_value, max_value, step)
        self.__definitions[variable_name] = [REAL, min_value, max_value, step]

    def define_categorical(self, variable_name, categories):
        """ It defines a **CATEGORICAL** variable receiving the variable name, and a list with the categories that it
        will be able to have.

         **Preconditions:**

        - The variable is not already defined.

        :param variable_name: The variable name.
        :param categories: The list of categories.
        :type variable_name: str
        :type categories: list of int, float or str
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The variable name is already used.
        """
        self.__var_el_name_str_class(variable_name)
        self.__categories_class(categories)
        self.__var_name_in_use(variable_name)
        self.__definitions[variable_name] = [CATEGORICAL, categories]

    # **** DEFINE LAYER VARIABLE METHODS ****

    def define_layer(self, variable_name):
        """ It defines a **LAYER** variable receiving the variable name. Next, the elements have to be defined
        using the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`

        **Preconditions:**

        - The variable is not already defined.

        :param variable_name: The variable name.
        :type variable_name: str
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The variable name is already used.
        """
        self.__var_el_name_str_class(variable_name)
        self.__var_name_in_use(variable_name)
        self.__definitions[variable_name] = [LAYER, {}]

    def define_integer_element(self, variable, element_name, min_value, max_value, step):
        """ It defines an **INTEGER** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **LAYER** variable where the new element will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element_name)
        self.__min_max_step_int_class(min_value, max_value, step)
        self.__var_is_defined_type_el_in_use(variable, LAYER, element_name)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][1][element_name] = [INTEGER, min_value, max_value, step]

    def define_real_element(self, variable, element_name, min_value, max_value, step):
        """ It defines a **REAL** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **LAYER** variable where the new element will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element_name)
        self.__min_max_step_float_class(min_value, max_value, step)
        self.__var_is_defined_type_el_in_use(variable, LAYER, element_name)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][1][element_name] = [REAL, min_value, max_value, step]

    def define_categorical_element(self, variable, element_name, categories):
        """ It defines a **CATEGORICAL** element into a **LAYER** variable by receiving a list with
        the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.

        :param variable: The **LAYER** variable where the new element will be inserted.
        :param element_name: The element name.
        :param categories: The list with the categories.
        :type variable: str
        :type element_name: str
        :type categories: list of int, float or str
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element_name)
        self.__categories_class(categories)
        self.__var_is_defined_type_el_in_use(variable, LAYER, element_name)
        self.__definitions[variable][1][element_name] = [CATEGORICAL, categories]

    # **** DEFINE VECTOR VARIABLE METHODS ****

    def define_vector(self, variable_name, min_size, max_size, step_size):
        """ It defines a **VECTOR** variable receiving the variable name, the minimum and maximum size that it will be
        able to have, and the step size to select the size from the :math:`[min\_size, max\_size]`. Afterwards,
        the type of the components of the **VECTOR** variable must be set using the following methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`

        **Preconditions:**

        - The variable is not already defined.
        - min_size < max_size
        - step_size < (min_size - max_size) / 2

        :param variable_name: The variable name.
        :param min_size: The minimum size.
        :param max_size: The maximum size.
        :param step_size: The step size.
        :type variable_name: str
        :type min_size: int
        :type max_size: int
        :type step_size: int
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The variable name is already used,
         min_value >= max_value or step >= (max_value - min_value) / 2.
        """
        self.__var_el_name_str_class(variable_name)
        self.__min_max_step_int_class(min_size, max_size, step_size)
        self.__var_name_in_use_range(variable_name, min_size, max_size, step_size)
        self.__definitions[variable_name] = [VECTOR, min_size, max_size, step_size, {}]

    def define_components_integer(self, variable, min_value, max_value, step):
        """ It defines the components of a **VECTOR** variable as **INTEGER** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__min_max_step_int_class(min_value, max_value, step)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_not_defined(variable)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][4] = [INTEGER, min_value, max_value, step]

    def define_components_real(self, variable, min_value, max_value, step):
        """ It defines the components of a **VECTOR** variable as **REAL** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__min_max_step_float_class(min_value, max_value, step)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_not_defined(variable)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][4] = [REAL, min_value, max_value, step]

    def define_components_categorical(self, variable, categories):
        """ It defines the components of a **VECTOR** variable as **CATEGORICAL** by receiving a list with
        the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param categories: List of label.
        :type variable: str
        :type categories: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined.
        """
        self.__var_el_name_str_class(variable)
        self.__categories_class(categories)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_not_defined(variable)
        self.__definitions[variable][4] = [CATEGORICAL, categories]

    def define_components_layer(self, variable):
        """ It defines the components of a **VECTOR** variable as **LAYER**. Afterwards, the elements of
        the layer must be set using the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_categorical_element`

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.

        :param variable: The **VECTOR** variable where its components will be defined.
        :type variable: str
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_not_defined(variable)
        self.__definitions[variable][4] = [LAYER, {}]

    def define_vector_integer_element(self, variable, element_name, min_value, max_value, step):
        """ It defines an **INTEGER** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**,
        the component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element_name)
        self.__min_max_step_int_class(min_value, max_value, step)
        self.__var_is_defined_type_comp_type_el_name_in_use(variable, VECTOR, LAYER, element_name)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][4][1][element_name] = [INTEGER, min_value, max_value, step]

    def define_vector_real_element(self, variable, element_name, min_value, max_value, step):
        """ It defines a **REAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**,
        the component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element_name)
        self.__min_max_step_float_class(min_value, max_value, step)
        self.__var_is_defined_type_comp_type_el_name_in_use(variable, VECTOR, LAYER, element_name)
        self.__range(min_value, max_value, step)
        self.__definitions[variable][4][1][element_name] = [REAL, min_value, max_value, step]

    def define_vector_categorical_element(self, variable, element_name, categories):
        """ It defines a **CATEGORICAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving a list with the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.

        :param variable: The Vector variable name previously defined.
        :param element_name: The element name.
        :param categories: List of categories.
        :type variable: str
        :type element_name: str
        :type categories: list(int, float, str)
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**,
        the component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used.
        """
        self.__var_el_name_str_class(variable)
        self.__categories_class(categories)
        self.__var_is_defined_type_comp_type_el_name_in_use(variable, VECTOR, LAYER, element_name)
        self.__definitions[variable][4][1][element_name] = [CATEGORICAL, categories]

    # **** IS DEFINED METHODS ***

    def is_defined_variable(self, variable):
        """ It checks if the variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: True if the variable is defined in the domain, otherwise False.
        :rtype: bool
        """
        self.__var_el_name_str_class(variable)
        r = False
        if variable in self.__definitions.keys():
            r = True
        return r

    def is_defined_element(self, variable, element):
        """ It checks if an element is defined in a **LAYER** variable of the domain.

         **Preconditions:**

        - The variable is defined as **LAYER** type.

        :param variable: The **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: True if the element is defined in the **LAYER** variable, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, LAYER)
        r = False
        if element in self.__definitions[variable][1].keys():
            r = True
        return r

    def is_defined_components(self, variable):
        """ It checks if the components of a **VECTOR** variable are already defined.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.

        :param variable: The **LAYER** variable.
        :type variable: str
        :returns: True if the components of the **VECTOR** variable are already defined, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        r = False
        if len(self.__definitions[variable][4]) > 0:
            r = True
        return r

    # **** GET TYPE METHODS **

    def get_variable_type(self, variable):
        """ Get the variable type.

        **Preconditions:**

        - The variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER** or **VECTOR**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined(variable)
        return self.__definitions[variable][0]

    def get_element_type(self, variable, element):
        """ Get an element type of a **LAYER** variable.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param variable: The **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain, the
        element is not defined in the **LAYER** variable.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, LAYER)
        self.__el_is_defined(variable, element)
        return self.__definitions[variable][1][element][0]

    def get_component_type(self, variable):
        """ Get the type of the components of a **VECTOR** variable.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined.

        :param variable: The defined **VECTOR** variable.
        :type variable: str
        :returns: The **VECTOR** variable component type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_defined(variable)
        return self.__definitions[variable][4][0]

    # **** GET VARIABLE DEFINITION METHODS ***

    def get_definitions(self):
        """ Get the internal data structure for the :py:class:`~pycvoa.problem.domain.Domain`.

        :returns: Internal structure of the Problem Definition.
        :rtype: dict
        """
        return self.__definitions

    def get_definition_list(self):
        """ Get a list with the defined variables and its definitions in a (key, value) form. It is useful to
        iterate throw the registered variables using a for loop.

        :returns: A (key, value) list with the registered variables.
        :rtype: list
        """
        return self.__definitions.items()

    def get_variable_list(self):
        """ Get a list with the defined variables. It is useful to iterate throw the registered variables
        using a for loop.

        :returns: A list with the registered variables.
        :rtype: list
        """
        return list(self.__definitions.keys())

    def get_variable_definition(self, variable):
        """ Get the definition structure of a variable.

        **Preconditions:**

        - The variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: Definition of a variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined(variable)
        return self.__definitions[variable]

    # **** GET ELEMENT DEFINITION METHODS ***

    def get_element_list(self, variable):
        """ Get a list with the elements of a registered **LAYER** variable. It is useful to iterate throw
        the elements of a registered **LAYER** variable using a for loop.

         **Preconditions:**

        - The variable is defined as **LAYER** type.

        :param variable: The defined **LAYER** variable.
        :type variable: str
        :returns: A list with the elements the registered **LAYER** variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, LAYER)
        return list(self.__definitions[variable][1].keys())

    def get_element_definition(self, variable, element):
        """ Get an element definition of a **LAYER** variable.

         **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param variable: The defined **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, LAYER)
        self.__el_is_defined(variable, element)
        return self.__definitions[variable][1][element]

    # **** GET COMPONENT DEFINITION METHODS ***

    def get_component_definition(self, variable):
        """ Get the definition of the components of a defined **VECTOR** variable.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined.

        :param variable: The defined **VECTOR** variable.
        :type variable: str
        :returns: The **VECTOR** variable component definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_type_defined(variable)
        return self.__definitions[variable][4]

    def get_component_element_list(self, variable):
        """ Get a list with the elements of a registered **VECTOR** variable registered as **LAYER**. It is useful to
        iterate throw the elements of the layers in a registered **LAYER** variable using a for loop.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.

        :param variable: The registered **VECTOR** variable.
        :type variable: str
        :returns: A list with the elements of the **LAYER** defined in the **VECTOR** variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_is_defined_type(variable, LAYER)
        return list(self.__definitions[variable][4][1].keys())

    def get_component_element_definition(self, variable, element):
        """ Get the layer element definition for a **VECTOR** variable.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.
        - The element is defined in the **LAYER** components.

        :param variable: The registered **VECTOR** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined. The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_is_defined_type(variable, LAYER)
        self.__comp_el_is_defined(variable, element)
        return self.__definitions[variable][4][1][element]

    # **** CHECK METHODS ***

    def check_basic(self, variable, value):
        """ It checks if a value of a **BASIC** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **BASIC** type.

        :param variable: The defined **BASIC** variable.
        :param value: The value to check.
        :type variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the variable definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **BASIC**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, BASIC)
        r = False
        if self.__definitions[variable][0] in (INTEGER, REAL):
            self.__value_class_int_float(value)
            if self.__definitions[variable][1] <= value <= self.__definitions[variable][2]:
                r = True
        elif self.__definitions[variable][0] is CATEGORICAL:
            self.__value_class_category(self.__definitions[variable][1], value)
            if value in self.__definitions[variable][1]:
                r = True
        return r

    def check_element(self, variable, element, value):
        """ It checks if a value for an element of a **LAYER** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param variable: The defined **LAYER** variable.
        :param element: The defined element in the variable.
        :param value: The element value to check.
        :type variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **BASIC**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, LAYER)
        self.__el_is_defined(variable, element)
        r = False
        if self.__definitions[variable][1][element][0] in (INTEGER, REAL):
            self.__value_class_int_float(value)
            if self.__definitions[variable][1][element][1] <= value <= self.__definitions[variable][1][element][2]:
                r = True
        elif self.__definitions[variable][1][element][0] is CATEGORICAL:
            self.__value_class_category(self.__definitions[variable][1][element][1], value)
            if value in self.__definitions[variable][1][element][1]:
                r = True
        return r

    def check_basic_component(self, variable, value):
        """ It checks if a value of a component a **VECTOR** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **BASIC**.

        :param variable: The defined **VECTOR** variable.
        :param value: The element value to check.
        :type variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the component definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not **BASIC**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_is_defined_type(variable, BASIC)
        r = False
        if self.__definitions[variable][4][0] in (INTEGER, REAL):
            self.__value_class_int_float(value)
            if self.__definitions[variable][4][1] <= value <= self.__definitions[variable][4][2]:
                r = True
        elif self.__definitions[variable][4][0] is CATEGORICAL:
            self.__value_class_category(self.__definitions[variable][4][1], value)
            if value in self.__definitions[variable][4][1]:
                r = True
        return r

    def check_element_component(self, variable, element, value):
        """ It checks if a value for an element in a defined **VECTOR** variable fulfills its definition in the domain.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.
        - The element is defined in the **LAYER** components.

        :param variable: The defined **VECTOR** variable.
        :param element: The defined element in the **VECTOR** variable where its components are defined as **LAYER**.
        :param value: The element value to check.
        :type variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The component type is not defined. The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        self.__var_el_name_str_class(variable)
        self.__var_el_name_str_class(element)
        self.__var_is_defined_type(variable, VECTOR)
        self.__comp_is_defined_type(variable, LAYER)
        self.__comp_el_is_defined(variable, element)
        r = False
        if self.__definitions[variable][4][1][element][0] in (INTEGER, REAL):
            self.__value_class_int_float(value)
            if self.__definitions[variable][4][1][element][1] <= value <= self.__definitions[variable][4][1][element][
                2]:
                r = True
        elif self.__definitions[variable][4][1][element][0] is CATEGORICAL:
            self.__value_class_category(self.__definitions[variable][4][1][element][1], value)
            if value in self.__definitions[variable][4][1][element][1]:
                r = True
        return r

    def check_value(self, variable, value, element=None):
        """ It checks if a value of a defined variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined in the domain.
        - In case of checking elements, the element is defined in the **LAYER** variable.
        - In case of checking components, the component of the **VECTOR** variable are defined.

        :param variable: The defined variable.
        :param value: The value to check.
        :param element: The defined element, defaults to None.
        :type variable: str
        :type value: int, float, str
        :type element: str
        :returns: True if the value fulfills the variable definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The component type is not defined. The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongParameters`: An element name in provided when the variable is
        defined as **BASIC**. An element name in provided when the components of the **VECTOR** variable is defined
        as **BASIC**. An element name is not provided when a **LAYER** variable is checked.
        An element name is not provided when a **VECTOR** variable, whose components are defined as ***LAYER**,
        are checked.
        """
        self.__var_el_name_str_class(variable)
        self.__var_is_defined(variable)
        r = False
        if self.__definitions[variable][0] in BASIC:
            if element is not None:
                raise WrongParameters(
                    "The " + variable + " type is BASIC, therefore, the element must not be provided.")
            r = self.check_basic(variable, value)
        elif self.__definitions[variable][0] is LAYER:
            if element is None:
                raise WrongParameters(
                    "The variable " + variable + " is LAYER, therefore, an element name must be provided")
            else:
                r = self.check_element(variable, element, value)
        elif self.__definitions[variable][0] is VECTOR:
            self.__comp_type_defined(variable)
            if self.__definitions[variable][4][0] in BASIC:
                if element is not None:
                    raise WrongParameters(
                        "The component type of the " + variable + "variable is BASIC, therefore, the element must not "
                                                                  "be provided.")
                r = self.check_basic_component(variable, value)
            elif self.__definitions[variable][4][0] is LAYER:
                if element is None:
                    raise WrongParameters(
                        "The components of " + variable + " VECTOR variable are defined as LAYER, therefore,"
                                                          " an element name must be provided")
                else:
                    r = self.check_element_component(variable, element, value)
        return r

    # **** MEMBER PARAMETERS CONTROL ***

    def __var_el_name_str_class(self, var_el):
        if type(var_el) != str:
            raise WrongParameters("The variable_name/element_name/variable/element parameter must be <str>")

    def __min_max_step_int_class(self, min_value_size, max_value_size, step_size):
        if type(min_value_size) != int:
            raise WrongParameters("The min_value/min_size parameter must be <int>")
        if type(max_value_size) != int:
            raise WrongParameters("The max_value/max_size parameter must be <int>")
        if type(step_size) != int:
            raise WrongParameters("The step/step_size parameter must be <int>")

    def __min_max_step_float_class(self, min_value, max_value, step):
        if type(min_value) != float:
            raise WrongParameters("The min_value parameter must be <float>")
        if type(max_value) != float:
            raise WrongParameters("The max_value parameter must be <float>")
        if type(step) != float:
            raise WrongParameters("The step parameter must be <float>")

    def __categories_class(self, categories):
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

    def __value_class_int_float(self, value):
        if type(value) not in (int, float):
            raise WrongParameters(
                "The value parameter must be <int> or <float>")

    def __value_class_category(self, categories, value):
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

    def __var_is_defined(self, variable):
        """ It checks if a variable is defined in the domain, if not, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param variable: The variable.
        :type variable: str
        """
        if variable not in self.__definitions.keys():
            raise NotDefinedItem("The variable " + variable + " is not defined in this domain.")

    def __var_type(self, variable, variable_type):
        """ It checks if a variable is defined as a variable type, if not, raise
        py:class:`~pycvoa.problem.domain.WrongItemType`.

        :param variable: The variable.
        :param variable_type: The variable type.
        :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
        :type variable: str
        """
        if variable_type is BASIC:
            if self.__definitions[variable][0] not in variable_type:
                raise WrongItemType("The variable " + variable + " is not defined as a BASIC type.")
        else:
            if self.__definitions[variable][0] is not variable_type:
                raise WrongItemType("The variable " + variable + " is not defined as " + variable_type + " type.")

    def __var_name_in_use(self, variable_name):
        """ It checks if a variable name is already used in the domain, if yes, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param variable_name: The variable name.
        :type variable_name: str
        """
        if variable_name in self.__definitions.keys():
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

    # **** TO STRING ***

    def __str__(self):
        """ String representation of a py:class:`~pycvoa.problem.domain.Domain` object
        """
        res = ""
        count = 1
        for k, v in self.__definitions.items():
            res += definition_to_string(k, v)
            if count != len(self.__definitions.items()):
                res += "\n"
            count += 1

        return res


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
