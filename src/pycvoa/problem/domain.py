import copy
from typing import cast, Type, Optional
from pycvoa.control import parameter as ctrl_par
from pycvoa.control import definition as ctrl_def
from pycvoa.control.types import *


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
        self.__definitions: DefStructure = {}

    # **** DEFINE BASIC VARIABLE METHODS ****
    def define_integer(self, variable_name: str, min_value: int, max_value: int, step: int | None = None):
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
        ctrl_par.check_basic_arguments([(variable_name, str), (min_value, int), (max_value, int), (step, int | None)])
        valid_step: int = ctrl_par.check_integer_range_step(min_value, max_value, step, "a")
        ctrl_def.not_defined_variable(variable_name, self.__definitions)
        self.__definitions[variable_name] = (INTEGER, min_value, max_value, valid_step)

    def define_real(self, variable_name: str, min_value: float, max_value: float, step: float | None = None):
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
        ctrl_par.check_basic_arguments([(variable_name, str), (min_value, float), (max_value, float),
                                        (step, float | None)])
        valid_step = ctrl_par.check_real_range_step(min_value, max_value, step, "a")
        ctrl_def.not_defined_variable(variable_name, self.__definitions)
        self.__definitions[variable_name] = (REAL, min_value, max_value, valid_step)

    def define_categorical(self, variable_name: str, categories: Categories):
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
        ctrl_par.check_categories(categories)
        ctrl_def.not_defined_variable(variable_name, self.__definitions)
        self.__definitions[variable_name] = (CATEGORICAL, copy.deepcopy(categories))

    # **** DEFINE LAYER VARIABLE METHODS ****

    def define_layer(self, variable_name: str):
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
        ctrl_par.check_basic_arguments([(variable_name, str)])
        ctrl_def.not_defined_variable(variable_name, self.__definitions)
        self.__definitions[variable_name] = (LAYER, {})

    def define_integer_element(self, layer_variable: str, element_name: str, min_value: int, max_value: int,
                               step: int | None = None):
        """ It defines an **INTEGER** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param layer_variable: The **LAYER** variable where the new element will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type layer_variable: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        ctrl_par.check_basic_arguments(
            [(layer_variable, str), (element_name, str), (min_value, int), (max_value, int), (step, int | None)])
        valid_step = ctrl_par.check_integer_range_step(min_value, max_value, step, "b")
        ctrl_def.is_defined_layer_without_element(layer_variable, element_name, self.__definitions)
        cast(LayerAttributes, self.__definitions[layer_variable][1])[element_name] = \
            (INTEGER, min_value, max_value, valid_step)

    def define_real_element(self, layer_variable: str, element_name: str, min_value: float, max_value: float,
                            step: float | None = None):
        """ It defines a **REAL** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param layer_variable: The **LAYER** variable where the new element will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type layer_variable: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        ctrl_par.check_basic_arguments(
            [(layer_variable, str), (element_name, str), (min_value, float), (max_value, float), (step, float | None)])
        valid_step = ctrl_par.check_real_range_step(min_value, max_value, step, "b")
        ctrl_def.is_defined_layer_without_element(layer_variable, element_name, self.__definitions)
        cast(LayerAttributes, self.__definitions[layer_variable][1])[element_name] = \
            (REAL, min_value, max_value, valid_step)

    def define_categorical_element(self, layer_variable: str, element_name: str, categories: Categories):
        """ It defines a **CATEGORICAL** element into a **LAYER** variable by receiving a list with
        the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is not already defined.

        :param layer_variable: The **LAYER** variable where the new element will be inserted.
        :param element_name: The element name.
        :param categories: The list with the categories.
        :type layer_variable: str
        :type element_name: str
        :type categories: list of int, float or str
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str), (element_name, str)])
        ctrl_par.check_categories(categories)
        ctrl_def.is_defined_layer_without_element(layer_variable, element_name, self.__definitions)
        cast(LayerAttributes, self.__definitions[layer_variable][1])[element_name] = \
            (CATEGORICAL, copy.deepcopy(categories))

    # **** DEFINE BASIC VECTOR VARIABLE METHODS ****

    def define_vector(self, variable_name: str, min_size: int, max_size: int, step_size: int | None = None):
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
        ctrl_par.check_basic_arguments([(variable_name, str), (min_size, int), (max_size, int),
                                        (step_size, int | None)])
        valid_step_size = ctrl_par.check_integer_range_step(min_size, max_size, step_size, "c")
        ctrl_def.not_defined_variable(variable_name, self.__definitions)
        self.__definitions[variable_name] = (VECTOR, min_size, max_size, valid_step_size, None)

    def define_components_as_integer(self, vector_variable: str, min_value: int, max_value: int,
                                     step: int | None = None):
        """ It defines the components of a **VECTOR** variable as **INTEGER** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param vector_variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type vector_variable: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str), (min_value, int), (max_value, int),
                                        (step, int | None)])
        valid_step: int = ctrl_par.check_integer_range_step(min_value, max_value, step, "a")
        ctrl_def.is_defined_vector_without_components(vector_variable, self.__definitions)
        Domain.__set_components_definition(vector_variable, self.__definitions,
                                           (INTEGER, min_value, max_value, valid_step))

    def define_components_as_real(self, vector_variable: str, min_value: float, max_value: float,
                                  step: float | None = None):
        """ It defines the components of a **VECTOR** variable as **REAL** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param vector_variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type vector_variable: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined,
         min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str), (min_value, float), (max_value, float),
                                        (step, float | None)])
        valid_step = ctrl_par.check_real_range_step(min_value, max_value, step, "a")
        ctrl_def.is_defined_vector_without_components(vector_variable, self.__definitions)
        Domain.__set_components_definition(vector_variable, self.__definitions,
                                           (REAL, min_value, max_value, valid_step))

    def define_components_as_categorical(self, vector_variable: str, categories: Categories):
        """ It defines the components of a **VECTOR** variable as **CATEGORICAL** by receiving a list with
        the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.

        :param vector_variable: The **VECTOR** variable where its components will be defined.
        :param categories: List of label.
        :type vector_variable: str
        :type categories: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_par.check_categories(categories)
        ctrl_def.is_defined_vector_without_components(vector_variable, self.__definitions)
        Domain.__set_components_definition(vector_variable, self.__definitions,
                                           (CATEGORICAL, copy.deepcopy(categories)))

    # **** DEFINE LAYER VECTOR VARIABLE METHODS ****

    def define_components_as_layer(self, vector_variable: str):
        """ It defines the components of a **VECTOR** variable as **LAYER**. Afterwards, the elements of
        the layer must be set using the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_categorical_element`

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** variable is not already defined.

        :param vector_variable: The **VECTOR** variable where its components will be defined.
        :type vector_variable: str
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The component type is already defined.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_def.is_defined_vector_without_components(vector_variable, self.__definitions)
        Domain.__set_components_definition(vector_variable, self.__definitions, (LAYER, {}))

    def define_layer_vector_integer_element(self, layer_vector_variable: str, element_name: str, min_value: int,
                                            max_value: int, step: int | None = None):
        """ It defines an **INTEGER** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param layer_vector_variable: The **VECTOR** variable where its components will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type layer_vector_variable: str
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
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (element_name, str),
                                        (min_value, int), (max_value, int), (step, int | None)])
        valid_step = ctrl_par.check_integer_range_step(min_value, max_value, step, "b")
        ctrl_def.is_defined_layer_vector_without_element(layer_vector_variable, element_name, self.__definitions)
        cast(LayerAttributes,
             cast(LayerDef,
                  cast(VectorDef,
                       self.__definitions[layer_vector_variable])[4])[1])[element_name] = \
            (INTEGER, min_value, max_value, valid_step)

    def define_layer_vector_real_element(self, layer_vector_variable: str, element_name: str, min_value: float,
                                         max_value: float, step: float | None = None):
        """ It defines a **REAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.
        - min_value < max_value and step < (max_value-min_value) / 2.

        :param layer_vector_variable: The **VECTOR** variable where its components will be defined.
        :param element_name: The element name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type layer_vector_variable: str
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
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (element_name, str),
                                        (min_value, float), (max_value, float), (step, int | None)])
        valid_step = ctrl_par.check_real_range_step(min_value, max_value, step, "b")
        ctrl_def.is_defined_layer_vector_without_element(layer_vector_variable, element_name, self.__definitions)
        cast(LayerAttributes,
             cast(LayerDef,
                  cast(VectorDef,
                       self.__definitions[layer_vector_variable])[4])[1])[element_name] = \
            (REAL, min_value, max_value, valid_step)

    def define_layer_vector_categorical_element(self, layer_vector_variable: str, element_name: str,
                                                categories: Categories):
        """ It defines a **CATEGORICAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving a list with the categories that it will be able to have.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The component type of the **VECTOR** is defined as **LAYER**.
        - The element is not already defined.

        :param layer_vector_variable: The Vector variable name previously defined.
        :param element_name: The element name.
        :param categories: List of categories.
        :type layer_vector_variable: str
        :type element_name: str
        :type categories: list(int, float, str)
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**,
        the component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.domain.DefinitionError`: The element name is already used.
        """
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (element_name, str)])
        ctrl_par.check_categories(categories)
        ctrl_def.is_defined_layer_vector_without_element(layer_vector_variable, element_name, self.__definitions)
        cast(LayerAttributes,
             cast(LayerDef,
                  cast(VectorDef,
                       self.__definitions[layer_vector_variable])[4])[1])[element_name] = \
            (CATEGORICAL, copy.deepcopy(categories))

    # **** IS DEFINED METHODS ***

    def is_defined_variable(self, variable: str) -> bool:
        """ It checks if the variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: True if the variable is defined in the domain, otherwise False.
        :rtype: bool
        """
        ctrl_par.check_basic_arguments([(variable, str)])
        if variable in self.__definitions.keys():
            r = True
        else:
            r = False
        return r

    def is_defined_element(self, layer_variable: str, element: str) -> bool:
        """ It checks if an element is defined in a **LAYER** variable of the domain.

         **Preconditions:**

        - The variable is defined as **LAYER** type.

        :param layer_variable: The **LAYER** variable.
        :param element: The element.
        :type layer_variable: str
        :type element: str
        :returns: True if the element is defined in the **LAYER** variable, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str), (element, str)])
        ctrl_def.is_defined_variable_as_type(layer_variable, self.__definitions, LAYER)
        r = False
        if element in cast(LayerDef, self.__definitions[layer_variable])[1].keys():
            r = True
        return r

    def are_defined_components(self, vector_variable: str) -> bool:
        """ It checks if the components of a **VECTOR** variable are already defined.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.

        :param vector_variable: The **LAYER** variable.
        :type vector_variable: str
        :returns: True if the components of the **VECTOR** variable are already defined, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_def.is_defined_variable_as_type(vector_variable, self.__definitions, VECTOR)
        r = False
        if cast(VectorDef, self.__definitions[vector_variable])[4] is not None:
            r = True
        return r

    # **** GET TYPE METHODS **

    def get_variable_type(self, variable: str) -> PYCVOA_TYPE:
        """ Get the variable type.

        **Preconditions:**

        - The variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER** or **VECTOR**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        """
        ctrl_par.check_basic_arguments([(variable, str)])
        ctrl_def.is_defined_variable(variable, self.__definitions)
        return self.__definitions[variable][0]

    def get_layer_element_type(self, layer_variable: str, element: str) -> PYCVOA_TYPE:
        """ Get an element type of a **LAYER** variable.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param layer_variable: The **LAYER** variable.
        :param element: The element.
        :type layer_variable: str
        :type element: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain, the
        element is not defined in the **LAYER** variable.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str), (element, str)])
        ctrl_def.is_defined_layer_with_element(layer_variable, element, self.__definitions)
        return cast(LayerDef, self.__definitions[layer_variable])[1][element][0]

    def get_vector_components_type(self, vector_variable: str) -> PYCVOA_TYPE:
        """ Get the type of the components of a **VECTOR** variable.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined.

        :param vector_variable: The defined **VECTOR** variable.
        :type vector_variable: str
        :returns: The **VECTOR** variable component type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER**
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_def.is_defined_vector_with_components(vector_variable, self.__definitions)
        return cast(ComponentDef, cast(VectorDef, self.__definitions[vector_variable])[4])[0]

    def get_layer_vector_component_element_type(self, layer_vector_variable: str, element: str) -> PYCVOA_TYPE:
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (element, str)])
        ctrl_def.is_defined_layer_vector_with_element(layer_vector_variable, element, self.__definitions)
        return cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1][element][0]

    # **** GET VARIABLE DEFINITION METHODS ***

    def get_definitions(self) -> DefStructure:
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

    def get_variable_list(self) -> list[str]:
        """ Get a list with the defined variables. It is useful to iterate throw the registered variables
        using a for loop.

        :returns: A list with the registered variables.
        :rtype: list
        """
        return list(self.__definitions.keys())

    def get_variable_definition(self, variable: str) -> VarDefinition:
        """ Get the definition structure of a variable.

        **Preconditions:**

        - The variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: Definition of a variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        """
        ctrl_par.check_basic_arguments([(variable, str)])
        ctrl_def.is_defined_variable(variable, self.__definitions)
        return self.__definitions[variable]

    # **** GET ELEMENT DEFINITION METHODS ***

    def get_element_list(self, layer_variable: str) -> list[str]:
        """ Get a list with the elements of a registered **LAYER** variable. It is useful to iterate throw
        the elements of a registered **LAYER** variable using a for loop.

         **Preconditions:**

        - The variable is defined as **LAYER** type.

        :param layer_variable: The defined **LAYER** variable.
        :type layer_variable: str
        :returns: A list with the elements the registered **LAYER** variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str)])
        ctrl_def.is_defined_variable_as_type(layer_variable, self.__definitions, LAYER)
        return list(cast(LayerDef, self.__definitions[layer_variable])[1].keys())

    def get_element_definition(self, layer_variable: str, element: str) -> BasicDef:
        """ Get an element definition of a **LAYER** variable.

         **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param layer_variable: The defined **LAYER** variable.
        :param element: The element.
        :type layer_variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str), (element, str)])
        ctrl_def.is_defined_layer_with_element(layer_variable, element, self.__definitions)
        return cast(LayerDef, self.__definitions[layer_variable])[1][element]

    # **** GET COMPONENT DEFINITION METHODS ***

    def get_vector_component_definition(self, vector_variable: str) -> ComponentDef:
        """ Get the definition of the components of a defined **VECTOR** variable.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined.

        :param vector_variable: The defined **VECTOR** variable.
        :type vector_variable: str
        :returns: The **VECTOR** variable component definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_def.is_defined_vector_with_components(vector_variable, self.__definitions)
        return cast(ComponentDef, (cast(VectorDef, self.__definitions[vector_variable])[4]))

    def get_component_element_list(self, layer_vector_variable: str) -> list[str]:
        """ Get a list with the elements of a registered **VECTOR** variable registered as **LAYER**. It is useful to
        iterate throw the elements of the layers in a registered **LAYER** variable using a for loop.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.

        :param layer_vector_variable: The registered **VECTOR** variable.
        :type layer_vector_variable: str
        :returns: A list with the elements of the **LAYER** defined in the **VECTOR** variable.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_vector_variable, str)])
        ctrl_def.is_defined_vector_and_components_as_type(layer_vector_variable, self.__definitions, LAYER)
        return list(cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1].keys())

    def get_component_element_definition(self, layer_vector_variable: str, element: str) -> BasicDef:
        """ Get the layer element definition for a **VECTOR** variable.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.
        - The element is defined in the **LAYER** components.

        :param layer_vector_variable: The registered **VECTOR** variable.
        :param element: The element.
        :type layer_vector_variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain,
        the component type is not defined. The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (element, str)])
        ctrl_def.is_defined_layer_vector_and_component_element(layer_vector_variable, element, self.__definitions)
        return cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1][element]

    # **** GET DEFINITION ITEMS ***

    def get_numerical_variable_attributes(self, numerical_variable: str) -> NumericalAttributes:
        ctrl_par.check_basic_arguments([(numerical_variable, str)])
        ctrl_def.is_defined_variable_as_type(numerical_variable, self.__definitions, NUMERICAL)
        return (cast(NumericalDef, self.__definitions[numerical_variable])[1],
                cast(NumericalDef, self.__definitions[numerical_variable])[2],
                cast(NumericalDef, self.__definitions[numerical_variable])[3])

    def get_categorical_variable_attributes(self, categorical_variable: str) -> Categories:
        ctrl_par.check_basic_arguments([(categorical_variable, str)])
        ctrl_def.is_defined_variable_as_type(categorical_variable, self.__definitions, CATEGORICAL)
        return copy.deepcopy(cast(CategoricalDef, self.__definitions[categorical_variable])[1])

    def get_numerical_element_attributes(self, layer_variable: str, numerical_element: str) -> NumericalAttributes:
        ctrl_par.check_basic_arguments([(layer_variable, str), (numerical_element, str)])
        ctrl_def.is_defined_layer_and_element_as_type(layer_variable, numerical_element, self.__definitions, NUMERICAL)
        layer_attr = cast(LayerAttributes, cast(LayerDef, self.__definitions[layer_variable])[1])
        return (cast(NumericalDef, layer_attr[numerical_element])[1],
                cast(NumericalDef, layer_attr[numerical_element])[2],
                cast(NumericalDef, layer_attr[numerical_element])[3])

    def get_categorical_element_attributes(self, layer_variable: str, categorical_element: str) -> Categories:
        ctrl_par.check_basic_arguments([(layer_variable, str), (categorical_element, str)])
        ctrl_def.is_defined_layer_and_element_as_type(layer_variable, categorical_element,
                                                      self.__definitions, CATEGORICAL)
        layer_attr = cast(LayerAttributes, cast(LayerDef, self.__definitions[layer_variable])[1])
        return copy.deepcopy(cast(CategoricalDef, layer_attr[categorical_element])[1])

    def get_vector_variable_attributes(self, vector_variable: str) -> VectorAttributes:
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_def.is_defined_variable_as_type(vector_variable, self.__definitions, VECTOR)
        return (cast(VectorDef, self.__definitions[vector_variable])[1],
                cast(VectorDef, self.__definitions[vector_variable])[2],
                cast(VectorDef, self.__definitions[vector_variable])[3])

    def get_numerical_components_attributes(self, numerical_vector_variable: str) -> NumericalAttributes:
        ctrl_par.check_basic_arguments([(numerical_vector_variable, str)])
        ctrl_def.is_defined_vector_and_components_as_type(numerical_vector_variable, self.__definitions, NUMERICAL)
        return (cast(NumericalDef, cast(VectorDef, self.__definitions[numerical_vector_variable])[4])[1],
                cast(NumericalDef, cast(VectorDef, self.__definitions[numerical_vector_variable])[4])[2],
                cast(NumericalDef, cast(VectorDef, self.__definitions[numerical_vector_variable])[4])[3])

    def get_categorical_components_attributes(self, categorical_vector_variable: str) -> Categories:
        ctrl_par.check_basic_arguments([(categorical_vector_variable, str)])
        ctrl_def.is_defined_vector_and_components_as_type(categorical_vector_variable, self.__definitions,
                                                          CATEGORICAL)
        return copy.deepcopy(cast(CategoricalDef,
                                  cast(VectorDef, self.__definitions[categorical_vector_variable])[4])[1])

    def get_layer_components_attributes(self, layer_vector_variable: str) -> LayerAttributes:
        ctrl_par.check_basic_arguments([(layer_vector_variable, str)])
        ctrl_def.is_defined_vector_and_components_as_type(layer_vector_variable, self.__definitions, LAYER)
        return copy.deepcopy(cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1])

    def get_layer_vector_numerical_element_attributes(self, layer_vector_variable: str,
                                                      numerical_element: str) -> NumericalAttributes:
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (numerical_element, str)])
        ctrl_def.is_defined_layer_vector_and_component_element_as_type(layer_vector_variable, numerical_element,
                                                                       self.__definitions, NUMERICAL)
        layer_attributes = cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1]
        return (cast(NumericalDef, layer_attributes[numerical_element])[1],
                cast(NumericalDef, layer_attributes[numerical_element])[2],
                cast(NumericalDef, layer_attributes[numerical_element])[3])

    def get_layer_vector_categorical_attributes(self, layer_vector_variable: str,
                                                categorical_element: str) -> Categories:
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (categorical_element, str)])
        ctrl_def.is_defined_layer_vector_and_component_element_as_type(layer_vector_variable, categorical_element,
                                                                       self.__definitions, CATEGORICAL)
        layer_attributes = cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1]
        return copy.deepcopy(cast(CategoricalDef, layer_attributes[categorical_element])[1])

    # **** GET AVAILABLE COMPONENTS ***

    def get_remaining_available_complete_components(self, basic_vector_variable: str, current_vector_size: int) -> int:
        ctrl_par.check_basic_arguments([(basic_vector_variable, str), (current_vector_size, int)])
        ctrl_def.is_defined_vector_with_components(basic_vector_variable, self.__definitions)
        return Domain.__available_size(basic_vector_variable, current_vector_size, self.__definitions)

    def get_remaining_available_layer_components(self, layer_vector_variable: str, current_vector_size: int,
                                                 layer_value: LayerValue) -> Tuple[int, int]:
        ctrl_par.check_basic_arguments([(layer_vector_variable, str), (current_vector_size, int)])
        ctrl_par.check_layer(layer_value)
        ctrl_def.is_defined_vector_and_components_as_type(layer_vector_variable, self.__definitions, "LAYER")
        layer_attributes: LayerAttributes = cast(LayerDef,
                                                 cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1]
        e_s = len(layer_value.keys() & layer_attributes.keys())
        if e_s == 0:
            valid_vector_size = current_vector_size
        else:
            valid_vector_size = current_vector_size - 1
        v_s = Domain.__available_size(layer_vector_variable, valid_vector_size, self.__definitions)
        return v_s, len(layer_attributes.keys()) - e_s

    def get_remaining_available_components(self, vector_variable: str, current_vector_size: int,
                                           layer_value: Union[LayerValue, None]) -> int | Tuple[int, int]:
        ctrl_par.check_basic_arguments([(vector_variable, str), (current_vector_size, int)])
        ctrl_par.check_layer(layer_value)
        ctrl_def.is_defined_vector_with_components(vector_variable, self.__definitions)
        cmp_type = cast(ComponentDef, cast(VectorDef, self.__definitions[vector_variable])[4])[0]
        r: int | Tuple[int, int] = 0
        if cmp_type in BASICS:
            ctrl_par.is_none("layer_value", layer_value)
            r = Domain.__available_size(vector_variable, current_vector_size, self.__definitions)
        elif cmp_type is LAYER:
            ctrl_par.not_none("layer_value", layer_value)
            if not Domain.__check_layer_element_values(vector_variable,
                                                       cast(LayerDef,
                                                            cast(VectorDef, self.__definitions[vector_variable])[4]),
                                                       cast(dict, layer_value),
                                                       False):
                raise ValueError("The layer values are not compatible with the LAYER VECTOR component definition")
            else:
                layer_attributes: LayerAttributes = cast(LayerDef,
                                                         cast(VectorDef,
                                                              self.__definitions[vector_variable])[4])[1]
                e_s = len(cast(dict, layer_value).keys() & layer_attributes.keys())
                if e_s == 0:
                    valid_vector_size = current_vector_size
                else:
                    valid_vector_size = current_vector_size - 1
                v_s = Domain.__available_size(vector_variable, valid_vector_size, self.__definitions)
                r = (v_s, e_s)
        return r

    # **** CHECK METHODS ***

    def check_basic(self, basic_variable: str, value: BasicValue) -> bool:
        """ It checks if a value of a **BASIC** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **BASIC** type.

        :param basic_variable: The defined **BASIC** variable.
        :param value: The value to check.
        :type basic_variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the variable definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **BASIC**.
        """
        ctrl_par.check_basic_arguments([(basic_variable, str)])
        ctrl_par.check_basic_value(value)
        ctrl_def.is_defined_variable_as_type(basic_variable, self.__definitions, BASIC)
        return Domain.__check_basic_value_item(cast(BasicDef, self.__definitions[basic_variable]), value)

    def check_layer(self, layer_variable: str, layer_value: LayerValue) -> bool:
        ctrl_par.check_basic_arguments([(layer_variable, str)])
        ctrl_par.check_layer(layer_value)
        ctrl_def.is_defined_variable_as_type(layer_variable, self.__definitions, LAYER)
        return Domain.__check_layer_element_values(layer_variable, cast(LayerDef, self.__definitions[layer_variable]),
                                                   layer_value)

    def check_element(self, layer_variable: str, element: str, value: BasicValue) -> bool:
        """ It checks if a value for an element of a **LAYER** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **LAYER** type.
        - The element is defined in the **LAYER** variable.

        :param layer_variable: The defined **LAYER** variable.
        :param element: The defined element in the variable.
        :param value: The element value to check.
        :type layer_variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **BASIC**.
        """
        ctrl_par.check_basic_arguments([(layer_variable, str), (element, str)])
        ctrl_par.check_basic_value(value)
        ctrl_def.is_defined_layer_with_element(layer_variable, element, self.__definitions)
        return Domain.__check_basic_value_item(cast(LayerDef, self.__definitions[layer_variable])[1][element], value)

    # **** CHECK VECTOR METHODS ***

    def check_vector_basic_value(self, basic_vector_variable: str, value: BasicValue) -> bool:
        """ It checks if a value of a component a **VECTOR** variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **BASIC**.

        :param basic_vector_variable: The defined **VECTOR** variable.
        :param value: The element value to check.
        :type basic_vector_variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the component definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The component type is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not **BASIC**.
        """
        ctrl_par.check_basic_arguments([(basic_vector_variable, str)])
        ctrl_par.check_basic_value(value)
        ctrl_def.is_defined_vector_and_components_as_type(basic_vector_variable, self.__definitions, BASIC)
        return Domain.__check_basic_value_item(cast(BasicDef,
                                                    cast(VectorDef,
                                                         self.__definitions[basic_vector_variable])[4]),
                                               value)

    def check_vector_values_size(self, vector_variable: str, values: VectorValueI) -> bool:
        """ It checks if the components of a **VECTOR** variable are already defined.

        **Preconditions:**

        - The variable is defined as **VECTOR** type.

        :param vector_variable: The **LAYER** variable.
        :param values: The values.
        :type vector_variable: str
        :returns: True if the components of the **VECTOR** variable are already defined, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **LAYER**.
        """
        ctrl_par.check_basic_arguments([(vector_variable, str)])
        ctrl_par.check_basic_vector(values)
        ctrl_def.is_defined_variable_as_type(vector_variable, self.__definitions, "VECTOR")
        r = False
        vector_definition = cast(VectorDef, self.__definitions[vector_variable])
        if vector_definition[1] <= len(values) <= vector_definition[2]:
            r = True
        return r

    def check_vector_basic_values(self, basic_vector_variable: str, values: Union[BasicValueList, BasicVectorInput]) -> bool:
        ctrl_def.is_defined_vector_and_components_as_type(basic_vector_variable, self.__definitions, BASIC)
        ctrl_def.check_vector_values_size(basic_vector_variable, cast(VectorDef,
                                                                      self.__definitions[basic_vector_variable]),
                                          values)
        return Domain.__check_vector_basic_values(cast(VectorDef, self.__definitions[basic_vector_variable]), values)

    def check_vector_layer_element_value(self, layer_vector_variable: str, element: str, value: BasicValue) -> bool:
        """ It checks if a value for an element in a defined **VECTOR** variable fulfills its definition in the domain.

         **Preconditions:**

        - The variable is defined as **VECTOR** type.
        - The components of the **VECTOR** variable are defined as **LAYER** type.
        - The element is defined in the **LAYER** components.

        :param layer_vector_variable: The defined **VECTOR** variable.
        :param element: The defined element in the **VECTOR** variable where its components are defined as **LAYER**.
        :param value: The element value to check.
        :type layer_vector_variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedItem`: The variable is not the defined in the domain.
        The component type is not defined. The element is not defined.
        :raise :py:class:`~pycvoa.problem.domain.WrongItemType`: The variable is not defined as **VECTOR**.
        The component type is not defined as **LAYER**.
        """
        ctrl_def.is_defined_layer_vector_with_element(layer_vector_variable, element, self.__definitions)
        layer_vector_attributes = cast(LayerDef, cast(VectorDef, self.__definitions[layer_vector_variable])[4])[1]
        return Domain.__check_basic_value_item(layer_vector_attributes[element], value)

    def check_vector_layer_elements_values(self, layer_vector_variable: str, layer_values: LayerInput) -> bool:
        ctrl_def.is_defined_vector_and_components_as_type(layer_vector_variable, self.__definitions, LAYER)
        return Domain.__check_layer_element_values(layer_vector_variable,
                                                   cast(LayerDef,
                                                        cast(VectorDef, self.__definitions[layer_vector_variable])[4]),
                                                   layer_values)

    def check_vector_layer_values(self, layer_vector_variable: str, values: LayerVectorInput) -> bool:
        ctrl_def.is_defined_vector_and_components_as_type(layer_vector_variable, self.__definitions, LAYER)
        vector_def = cast(VectorDef, self.__definitions[layer_vector_variable])
        ctrl_def.check_vector_values_size(layer_vector_variable, vector_def, values)
        return Domain.__check_vector_layer_element_values(vector_def, values)

    def check_value(self, variable: str, values: SupportedInput, element: OptStr = None) -> bool:
        """ It checks if a value of a defined variable fulfills its definition in the domain.

        **Preconditions:**

        - The variable is defined in the domain.
        - In case of checking elements, the element is defined in the **LAYER** variable.
        - In case of checking components, the component of the **VECTOR** variable are defined.

        :param variable: The defined variable.
        :param values: The value to check.
        :param element: The defined element, defaults to None.
        :type variable: str
        :type values: int, float, str
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
        ctrl_def.is_defined_variable(variable, self.__definitions)
        var_type = self.__definitions[variable][0]
        r = False

        if var_type in BASICS:  # Basic variable, Basic value, None element
            ctrl_par.check_basic_pycvoatype(element)
            r = Domain.__check_basic_value_item(cast(BasicDef, self.__definitions[variable]),
                                                cast(BasicValue, values))
        elif var_type is LAYER:
            case = ctrl_par.check_layer_pycvoatype(values, element)
            layer_def = cast(LayerDef, self.__definitions[variable])
            if case == "a":  # LAYER variable, BASIC value, NOT NONE element
                ctrl_def.is_defined_element(variable, element, layer_def)
                r = Domain.__check_basic_value_item(cast(BasicDef,
                                                         layer_def[1][cast(str, element)]), cast(BasicValue, values))
            elif case == "b":  # LAYER variable, LAYER value, NONE element
                r = Domain.__check_layer_element_values(variable, layer_def, cast(LayerValue, values))

        elif var_type is VECTOR:
            vector_def = cast(VectorDef, self.__definitions[variable])
            ctrl_def.are_defined_components(variable, vector_def)
            comp_type = cast(ComponentDef, vector_def[4])[0]

            if comp_type in BASICS:
                case = ctrl_par.check_basic_vector_pycvoatype(values, element)
                if case == "a":  # BASIC-VECTOR variable, BASIC value, NONE element
                    r = Domain.__check_basic_value_item(cast(BasicDef, vector_def[4]), cast(BasicValue, values))
                elif case == "b":  # BASIC-VECTOR variable, BASIC-VECTOR value, NONE element
                    valid_values = cast(VectorInput, values)
                    ctrl_def.check_vector_values_size(variable, vector_def, valid_values)
                    r = Domain.__check_vector_basic_values(vector_def, cast(BasicVectorInput, values))

            elif comp_type is LAYER:
                case = ctrl_par.check_layer_vector_pycvoatype(values, element)
                if case == "a":  # LAYER-VECTOR variable, BASIC value, NOT NONE element
                    ctrl_def.is_defined_component_element(variable, cast(str, element), vector_def)
                    layer_vector_attributes = cast(LayerDef, vector_def[4])[1]
                    r = Domain.__check_basic_value_item(layer_vector_attributes[cast(str, element)],
                                                        cast(BasicValue, values))
                elif case == "b":  # LAYER-VECTOR variable, LAYER value, NONE element
                    r = Domain.__check_layer_element_values(variable, cast(LayerDef, vector_def[4]),
                                                            cast(LayerValue, values))
                elif case == "c":  # LAYER-VECTOR variable, LAYER-VECTOR value, NONE element
                    ctrl_def.check_component_type(variable, vector_def, LAYER)
                    r = Domain.__check_vector_layer_element_values(vector_def, cast(LayerVectorValue, values))

        return r

    def str_variable_definition(self, variable: str) -> str:
        ctrl_def.is_defined_variable(variable, self.__definitions)
        if self.__definitions[variable][0] is VECTOR:
            res = Domain.__vector_definition_to_string(variable, cast(VectorDef, self.__definitions[variable]))
        elif self.__definitions[variable][0] is LAYER:
            res = Domain.__layer_definition_to_string(variable, cast(LayerDef, self.__definitions[variable]))
        else:
            res = Domain.__basic_definition_to_string(variable, cast(BasicDef, self.__definitions[variable]))
        return res

    def str_element_definition(self, layer_variable: str, element: str) -> str:
        ctrl_def.is_defined_layer_with_element(layer_variable, element, self.__definitions)
        return Domain.__basic_definition_to_string(element,
                                                   cast(LayerDef, self.__definitions[layer_variable])[1][element])

    def str_layer_vector_element_definition(self, layer_vector_variable: str, element: str) -> str:
        ctrl_def.is_defined_layer_vector_and_component_element(layer_vector_variable, element, self.__definitions)
        return Domain.__basic_definition_to_string(element,
                                                   cast(LayerDef,
                                                        cast(VectorDef,
                                                             self.__definitions[layer_vector_variable])[4])[1][element])

    def __str__(self):
        """ String representation of a py:class:`~pycvoa.problem.domain.Domain` object
        """
        res = ""
        count = 1
        for variable, definition in self.__definitions.items():
            if definition[0] is VECTOR:
                res += Domain.__vector_definition_to_string(variable, cast(VectorDef, definition))
            elif definition[0] is LAYER:
                res += Domain.__layer_definition_to_string(variable, cast(LayerDef, definition))
            else:
                res += Domain.__basic_definition_to_string(variable, cast(BasicDef, definition))
            if count != len(self.__definitions.items()):
                res += "\n"
            count += 1

        return res

    @staticmethod
    def __basic_definition_to_string(variable: str, definition: BasicDef):
        """ Get a string representation of the definition of a **REAL**, **INTEGER** or **CATEGORICAL** variable.

            :param variable: Variable name.
            :param definition: Definition of the variable.
            :type variable: str
            :type definition: list
            :returns: A string representation of the input REAL, INTEGER or CATEGORICAL variable.
            :rtype: str
            """
        res = "[" + definition[0] + "] " + variable + " "
        if definition[0] is not CATEGORICAL:
            num_def = cast(NumericalDef, definition)
            res += "{Minimum = " + str(num_def[1]) + ", Maximum = " + str(num_def[2]) + ", Step = " + str(
                num_def[3]) + "}"
        else:
            res += "{Values = " + str(definition[1]) + "}"
        return res

    @staticmethod
    def __layer_definition_to_string(variable: str, definition: LayerDef):
        """ Get a string representation of the definition of a **LAYER** variable.

            :param variable: Variable name.
            :param definition: Definition of the variable.
            :type variable: str
            :type definition: list
            :returns: A string representation of the input LAYER variable.
            :rtype: str
            """
        res = "[" + definition[0] + "] " + variable + " "
        res += "\n"
        cnt = 1
        for element, element_definition in definition[1].items():
            res += "\t" + Domain.__basic_definition_to_string(element, element_definition)
            if cnt != len(definition[1].items()):
                res += "\n"
            cnt += 1
        return res

    @staticmethod
    def __vector_definition_to_string(variable: str, definition: VectorDef):
        """ Get a string representation of the definition of a **VECTOR** variable.

        :param variable: Variable name.
        :param definition: Definition of the variable.
        :type variable: str
        :type definition: list
        :returns: A string representation of the input VECTOR variable.
        :rtype: str
        """
        res = "[" + definition[0] + "] " + variable + " {Minimum size = " + str(definition[1]) + \
              ", Maximum size = " + str(definition[2]) + ", Step size = " \
              + str(definition[3]) + "}"

        component_definition = definition[4]

        if component_definition is not None:
            res += "  Component definition: [" + component_definition[0] + "] "
            if component_definition[0] in NUMERICALS:
                num_def = cast(NumericalDef, component_definition)
                res += "{Minimum = " + str(num_def[1]) + ", Maximum = " + str(num_def[2]) \
                       + ", Step = " + str(
                    num_def[3]) + "}"
            elif component_definition[0] is CATEGORICAL:
                res += "{Values = " + str(component_definition[1]) + "}"
            elif component_definition[0] is LAYER:
                layer_definition = cast(LayerAttributes, component_definition[1])
                res += "\n"
                cnt = 1
                for k, v in layer_definition.items():
                    res += "\t" + Domain.__basic_definition_to_string(k, v)
                    if cnt != len(layer_definition.items()):
                        res += "\n"
                    cnt += 1
        return res

    @staticmethod
    def __check_basic_value_item(basic_item_definition: BasicDef, value: BasicValue) -> bool:
        r = False
        if basic_item_definition[0] in NUMERICALS:
            if not isinstance(value, str):
                num_def = cast(NumericalDef, basic_item_definition)
                if basic_item_definition[0] is INTEGER:
                    if not isinstance(value, int):
                        r = False
                    else:
                        if num_def[1] <= value <= num_def[2]:
                            r = True
                else:
                    if not isinstance(value, float):
                        r = False
                    else:
                        if num_def[1] <= value <= num_def[2]:
                            r = True
        elif basic_item_definition[0] is CATEGORICAL:
            cat_def = cast(CategoricalDef, basic_item_definition)
            if value in cat_def[1]:
                r = True
        return r

    @staticmethod
    def __check_layer_element_values(layer_variable: str, layer_definition: LayerDef, values: LayerInput,
                                     check_complete: bool = True) -> bool:
        if check_complete:
            ctrl_def.is_a_complete_layer(layer_definition, values)
        r = True
        i = 0
        key_list = list(values.keys())
        while r and i < len(key_list):
            element = key_list[i]
            value = values.get(element)
            if value is None:
                raise ValueError("value must not be None.")
            ctrl_def.is_defined_element_item_definition(layer_variable, element, layer_definition)
            if not Domain.__check_basic_value_item(layer_definition[1][element], value):
                r = False
            else:
                i += 1
        return r

    @staticmethod
    def __check_vector_basic_values(vector_basic_definition: VectorDef,
                                    values: Union[BasicValueList, BasicVectorInput]) -> bool:
        r = True
        i = 0
        while r and i < len(values):
            if not Domain.__check_basic_value_item(cast(BasicDef, vector_basic_definition[4]), values[i]):
                r = False
            else:
                i += 1
        return r

    @staticmethod
    def __check_vector_layer_element_values(vector_layer_definition: VectorDef, values: LayerVectorInput,
                                            complete: bool = True) -> bool:
        r = True
        i = 0
        layer_def = cast(LayerDef, vector_layer_definition[4])
        while r and i < len(values):
            layer = values[i]
            # Falla la variable en la llamada "-"
            if not Domain.__check_layer_element_values("-", layer_def, layer, complete):
                r = False
            else:
                i += 1
        return r

    @staticmethod
    def __available_size(vector_variable: str, current_size: int, definitions: DefStructure) -> int:
        vec_def = cast(VectorDef, definitions[vector_variable])
        if current_size < vec_def[1]:
            r = current_size - vec_def[1]
        elif vec_def[1] <= current_size < vec_def[2]:
            r = vec_def[2] - current_size
        else:
            r = 0
        return r

    @staticmethod
    def __set_components_definition(vector_variable: str, definitions: DefStructure,
                                    component_definition: ComponentDef):
        vector_definition = cast(VectorDef, definitions[vector_variable])
        definitions[vector_variable] = (vector_definition[0], vector_definition[1],
                                        vector_definition[2], vector_definition[3],
                                        component_definition)
