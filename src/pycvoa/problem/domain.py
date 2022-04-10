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

    # **** DEFINE VARIABLE METHODS ****

    def define_integer(self, variable_name, min_value, max_value, step):
        """ It defines an **INTEGER** variable receiving the variable name, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

        :param variable_name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise WrongDefinition: If min_value >= max_value or step >= (max_value - min_value) / 2.
        """
        if min_value < max_value:
            if step < (max_value - min_value) / 2:
                self.__definitions[variable_name] = [INTEGER, min_value, max_value, step]
            else:
                raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
        else:
            raise WrongDefinition("The minimum value must be less than the maximum value")

    def define_real(self, variable_name, min_value, max_value, step):
        """ It defines a **REAL** variable receiving the variable name, the minimum and maximum values that it will be
        able to have, and the step size to traverse the interval.

        **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

        :param variable_name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise WrongDefinition: If min_value >= max_value or step >= (max_value - min_value) / 2.
        """
        if min_value < max_value:
            if step < (max_value - min_value) / 2:
                self.__definitions[variable_name] = [REAL, min_value, max_value, step]
            else:
                raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
        else:
            raise WrongDefinition("The minimum value must be less than the maximum value")

    def define_categorical(self, variable_name, categories):
        """ It defines a **CATEGORICAL** variable receiving the variable name, and a list with the categories that it
        will be able to have.

        :param variable_name: The variable name.
        :param categories: The list of categories.
        :type variable_name: str
        :type categories: list(int,float,str)
        """
        self.__definitions[variable_name] = [CATEGORICAL, categories]

    def define_layer(self, variable_name):
        """ It defines a **LAYER** variable receiving the variable name. Next, the layer elements have to be defined using
        the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_categorical_element`

        :param variable_name: The variable name.
        :type variable_name: str
        """
        self.__definitions[variable_name] = [LAYER, {}]

    def define_vector(self, variable_name, min_size, max_size, step_size):
        """ It defines a **VECTOR** variable receiving the variable name, the minimum and maximum size that it will be able
        to have, and the step size to select the size from the :math:`[min\_size, max\_size]`. Afterwards, the type of
        the components of the **VECTOR** variable must be set using the following methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_components_layer`

        **Preconditions:**

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
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if min_size < max_size:
            if step_size < (min_size - max_size) / 2:
                self.__definitions[variable_name] = [VECTOR, min_size, max_size, step_size, {}]
            else:
                raise WrongDefinition("The step size must be less than (minimum size-maximum size)/2")
        else:
            raise WrongDefinition("The minimum size must be less than the maximum size")

    # **** DEFINE ELEMENT METHODS ****

    def define_integer_element(self, variable, element_name, min_value, max_value, step):
        """ It defines an **INTEGER** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2


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
        :raise NotDefinedVariable: The **LAYER** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where the new element will be defined is not defined as **LAYER**.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_variable_type(variable) is LAYER:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][1][element_name] = [INTEGER, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as LAYER")

    def define_real_element(self, variable, element_name, min_value, max_value, step):
        """ It defines a **REAL** element into a **LAYER** variable by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

          **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2


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
        :raise NotDefinedVariable: The **LAYER** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where the new element will be defined is not defined as **LAYER**.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_variable_type(variable) is LAYER:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][1][element_name] = [REAL, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a LAYER")

    def define_categorical_element(self, variable, element_name, categories):
        """ It defines a **CATEGORICAL** element into a **LAYER** variable by receiving a list with
        the categories that it will be able to have.

        :param variable: The **LAYER** variable where the new element will be inserted.
        :param element_name: The element name.
        :param categories: The list with the categories.
        :type layer_name: str
        :type element_name: str
        :type categories: list(int, float, str)
        :raise NotDefinedVariable: The **LAYER** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where the new element will be defined is not defined as **LAYER**.
        """
        if self.get_variable_type(variable) is LAYER:
            self.__definitions[variable][1][element_name] = [CATEGORICAL, categories]
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a LAYER")

    # **** DEFINE COMPONENT METHODS ****

    def define_components_integer(self, variable, min_value, max_value, step):
        """ It defines the components of a **VECTOR** variable as **INTEGER** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

        :param variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type min_value: int
        :type max_value: int
        :type step: int
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_variable_type(variable) is VECTOR:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][4] = [INTEGER, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a VECTOR")

    def define_components_real(self, variable, min_value, max_value, step):
        """ It defines the components of a **VECTOR** variable as **REAL** by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

        :param variable: The **VECTOR** variable where its components will be defined.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step.
        :type variable: str
        :type min_value: float
        :type max_value: float
        :type step: float
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_variable_type(variable) is VECTOR:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][4] = [REAL, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a VECTOR")

    def define_components_categorical(self, variable, categories):
        """ It defines the components of a **VECTOR** variable as **CATEGORICAL** by receiving a list with
        the categories that it will be able to have.

        :param variable: The **VECTOR** variable where its components will be defined.
        :param categories: List of label.
        :type variable: str
        :type categories: list
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        """
        if self.get_variable_type(variable) is VECTOR:
            self.__definitions[variable][4] = [CATEGORICAL, categories]
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a VECTOR")

    def define_components_layer(self, variable):
        """ It defines the components of a **VECTOR** variable as **LAYER**. Afterwards, the elements of
        the layer must be set using the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_integer_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_real_element`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_component_categorical_element`

        :param variable: The **VECTOR** variable where its components will be defined.
        :type variable: str
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        """
        if self.get_variable_type(variable) is VECTOR:
            self.__definitions[variable][4] = [LAYER, {}]
        else:
            raise WrongVariableType("The " + variable + " variable is not defined as a VECTOR")

    # **** DEFINE COMPONENT ELEMENT METHODS ****

    def define_vector_integer_element(self, variable, element_name, min_value, max_value, step):
        """ It defines an **INTEGER** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

         **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

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
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        :raise WrongComponentType: The component of the **VECTOR** variable is not defined as LAYER.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_component_type(variable) is LAYER:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][4][1][element_name] = [INTEGER, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongComponentType("The components of the VECTOR variable " + variable + " are not defined as LAYER")

    def define_vector_real_element(self, variable, element_name, min_value, max_value, step):
        """ It defines a **REAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving the minimum and maximum values that it will be able to have, and the step
        size to traverse the interval.

         **Preconditions:**

        - min_value < max_value
        - step < (max_value-min_value) / 2

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
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        :raise WrongComponentType: The component of the **VECTOR** variable is not defined as LAYER.
        :raise WrongDefinition: If min_size >= max_size or step_size >= (min_size - max_size) / 2.
        """
        if self.get_component_type(variable) is LAYER:
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    self.__definitions[variable][4][1][element_name] = [REAL, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The components of the VECTOR variable " + variable + " are not defined as LAYER")

    def define_vector_categorical_element(self, variable, element_name, categories):
        """ It defines a **CATEGORICAL** element of a **VECTOR** variable where its components are defined as **LAYER**.
        The element is defined by receiving a list with the categories that it will be able to have.

        :param variable: The Vector variable name previously defined.
        :param element_name: The element name.
        :param categories: List of categories.
        :type variable: str
        :type element_name: str
        :type categories: list(int, float, str)
        :raise NotDefinedVariable: The **VECTOR** variable is not the defined in the domain.
        :raise WrongVariableType: The variable where its components will be defined is not defined as **VECTOR**.
        :raise WrongComponentType: The component of the **VECTOR** variable is not defined as LAYER.
        """
        if self.get_component_type(variable) is LAYER:
            self.__definitions[variable][4][1][element_name] = [CATEGORICAL, categories]
        else:
            raise WrongVariableType("The components of the VECTOR variable " + variable + " are not defined as LAYER")

    # **** IS DEFINED METHODS ***

    def is_defined_variable(self, variable):
        """ It checks if the variable is defined in the domain.

        :param variable: The variable.
        :type variable: str
        :returns: True if the variable is defined in the domain, otherwise False.
        :rtype: bool
        """
        r = False
        if variable in self.get_variable_list():
            r = True
        return r

    def is_defined_element(self, variable, element):
        """ It checks if the element is defined in the **LAYER** variable defined in the domain.

        :param variable: The **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: True if the element is defined in the **LAYER** variable of the domain, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The **LAYER** variable is not defined in this domain.
        """
        if self.is_defined_variable(variable):
            r = False
            if element in self.get_element_list():
                r = True
        else:
            raise NotDefinedVariable("The variable " + variable + " is not defined in this domain")
        return r

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

        :param variable: The variable.
        :type variable: str
        :returns: Definition of a variable.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        """
        r = None
        if self.is_defined_variable(variable):
            r = self.__definitions[variable]
        else:
            raise NotDefinedVariable("The variable " + variable + " is not defined in this domain")
        return r

    # **** GET TYPE METHODS **
    def get_variable_type(self, variable):
        """ Get the variable type.

        :param variable: The variable.
        :type variable: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER**, **VECTOR**
        :raise NotDefinedVariable: The variable is not defined in this domain.
        """
        r = None
        if self.is_defined_variable(variable):
            r = self.__definitions[variable][0]
        else:
            raise NotDefinedVariable("The variable " + variable + " is not defined in this domain")
        return r

    def get_element_type(self, variable, element):
        """ Get an element type of a **LAYER** variable.

        :param variable: The defined **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **LAYER**.
        """
        r = None
        if self.get_variable_type(variable) is LAYER:
            r = self.__definitions[variable][1][element][0]
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as LAYER type")
        return r

    def get_component_type(self, variable):
        """ Get the type of the components of a **VECTOR** variable.

        :param variable: The defined **VECTOR** variable.
        :type variable: str
        :returns: The **VECTOR** variable component type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER**
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        """
        r = None
        if self.get_variable_type(variable) is VECTOR:
            r = self.__definitions[variable][4][0]
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as VECTOR type")
        return r

    # **** GET ELEMENT DEFINITION METHODS ***

    def get_element_definition(self, variable, element):
        """ Get an element definition of a **LAYER** variable.

        :param variable: The defined **LAYER** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **LAYER**.
        :raise NotDefinedElement: The element is not defined in the **LAYER** variable.
        """
        r = None
        if self.get_variable_type(variable) is LAYER:
            if self.is_defined_element(variable, element):
                r = self.__definitions[variable][1][element]
            else:
                raise NotDefinedElement(
                    "The element " + element + " is not defined in the " + variable + " LAYER variable")
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as LAYER type")
        return r

    def get_element_list(self, variable):
        """ Get a list with the elements of a registered **LAYER** variable. It is useful to iterate throw
        the elements of a registered **LAYER** variable using a for loop.

        :param variable: The defined **LAYER** variable.
        :type variable: str
        :returns: A list with the elements the registered **LAYER** variable.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **LAYER**.
        """
        r = None

        if self.get_variable_type(variable) is LAYER:
            r = list(self.__definitions[variable][1].keys())
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as LAYER type")

        return r

    # **** GET COMPONENT DEFINITION METHODS ***

    def get_component_definition(self, variable):
        """ Get the definition of the components of a defined **VECTOR** variable.

        :param variable: The defined **VECTOR** variable.
        :type variable: str
        :returns: The **VECTOR** variable component definition.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        """
        r = None
        if self.get_variable_type(variable) is VECTOR:
            r = self.__definitions[variable][4]
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as VECTOR type")
        return r

    def get_component_element_list(self, variable):
        """ Get a list with the elements of a registered **VECTOR** variable registered as **LAYER**. It is useful to
        iterate throw the elements of the layers in a registered **LAYER** variable using a for loop.

        :param variable: The registered **VECTOR** variable.
        :type variable: str
        :returns: A list with the elements of the **LAYER** defined in the **VECTOR** variable.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the VECTOR variable are not defined as LAYER.
        """
        r = None
        if self.get_component_type(variable) is LAYER:
            r = list(self.__definitions[variable][4][1].keys())
        else:
            raise WrongComponentType(
                "The components of the VECTOR variable " + variable + " are not defined as LAYER type")
        return r

    def get_component_element_definition(self, variable, element):
        """ Get the layer element definition for a **VECTOR** variable.

        :param variable: The registered **VECTOR** variable.
        :param element: The element.
        :type variable: str
        :type element: str
        :returns: The element definition.
        :rtype: list
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the VECTOR variable are not defined as LAYER.
        """
        r = None
        if self.get_component_type(variable) is LAYER:
            r = self.__definitions[variable][4][1][element]
        else:
            raise WrongVariableType(
                "The components of the VECTOR variable " + variable + " are not defined as LAYER type")
        return r

    # **** CHECK METHODS ***

    def check_basic(self, variable, value):
        """ It checks if a value of a **BASIC** variable fulfills its definition in the domain.

        :param variable: The defined **BASIC** variable.
        :param value: The value to check.
        :type variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the variable definition, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **BASIC** type.
        """
        r = False
        definition = self.get_variable_definition(variable)
        if definition[0] in (INTEGER, REAL):
            if definition[1] <= value <= definition[2]:
                r = True
        elif definition[0] is CATEGORICAL:
            if value in definition[1]:
                r = True
        else:
            raise WrongVariableType(
                "The variable " + variable + " is defined as " + definition[0] + ", not as BASIC type")
        return r

    def check_element(self, variable, element, value):
        """ It checks if a value for an element of a **LAYER** variable fulfills its definition in the domain.

        :param variable: The defined **LAYER** variable.
        :param element: The defined element in the variable.
        :param value: The element value to check.
        :type variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **LAYER** type.
        """
        r = False
        element_definition = self.get_element_definition(variable, element)
        if element_definition[0] in (INTEGER, REAL):
            if element_definition[1] <= value <= element_definition[2]:
                r = True
        elif element_definition[0] is CATEGORICAL:
            if value in element_definition[1]:
                r = True
        return r

    def check_basic_component(self, variable, value):
        """ It checks if a value of a component a **VECTOR** variable fulfills its definition in the domain.

        :param variable: The defined **VECTOR** variable.
        :param value: The element value to check.
        :type variable: str
        :type value: int, float, str
        :returns: True if the value fulfills the component definition, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** type.
        """
        r = False
        position_definition = self.get_component_definition(variable)
        if position_definition[0] in BASIC:
            if position_definition[0] in (INTEGER, REAL):
                if position_definition[1] <= value <= position_definition[2]:
                    r = True
            elif position_definition[0] is CATEGORICAL:
                if value in position_definition[1]:
                    r = True
            else:
                raise WrongComponentType(
                    "The components of the " + variable + " VECTOR variable are defined as " + position_definition[
                        0] + ", not as BASIC type")
        return r

    def check_element_component(self, variable, element, value):
        """ It checks if a value for an element in a defined **VECTOR** variable fulfills its definition in the domain.

        :param variable: The defined **VECTOR** variable.
        :param element: The defined element in the **VECTOR** variable where its components are defined as **LAYER**.
        :param value: The element value to check.
        :type variable: str
        :type element: str
        :type value: int, float, str
        :returns: True if the value fulfills the element definition, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongVariableType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the VECTOR variable are not defined as LAYER.
        """
        r = False
        element_definition = self.get_component_element_definition(variable, element)
        if element_definition[0] in (INTEGER, REAL):
            if element_definition[1] <= value <= element_definition[2]:
                r = True
        elif element_definition[0] is CATEGORICAL:
            if value in element_definition[1]:
                r = True
        return r

    def check_value(self, variable, value, element=None):
        """ It checks if a value of a defined variable fulfills its definition in the domain.

        :param variable: The defined variable.
        :param value: The value to check.
        :param element: The defined element, defaults to None.
        :type variable: str
        :type value: int, float, str
        :type element: str
        :returns: True if the value fulfills the variable definition, otherwise False.
        :rtype: bool
        :raise NotDefinedVariable: The variable is not defined in this domain.
        :raise WrongParameters: The variable is **LAYER** type, therefore, an element name must be provided.
        The components of the **VECTOR** variable are defined as **LAYER**, therefore, an element name must be provided.
        :raise WrongVariableType: The variable is not defined as **BASIC**, **LAYER** or **VECTOR** type.
        :raise WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** or
        **LAYER** type.
        """
        r = False
        variable_type = self.get_variable_type(variable)
        if variable_type in BASIC:
            r = self.check_basic(variable, value)
        elif variable_type is LAYER:
            if element is None:
                raise WrongParameters(
                    "The variable " + variable + " is LAYER, therefore, an element name must be provided")
            else:
                r = self.check_element(variable, element, value)
        elif variable_type is VECTOR:
            comp_type = self.get_component_type(variable)
            if comp_type in BASIC:
                self.check_basic_component(variable, value)
            elif comp_type is LAYER:
                if element is None:
                    raise WrongParameters(
                        "The components of " + variable + " VECTOR variable are defined as LAYER, therefore,"
                                                          " an element name must be provided")
                else:
                    r = self.check_element_component(variable, element, value)
        return r

    # **** TO STRING ***

    def __str__(self):
        """ String representation of a :py:class:`~pycvoa.definition.ProblemDefinition` object
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


class NotDefinedVariable(DomainError):
    """ It is raised when a variable is not defined in the domain.

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
    - :py:meth:`~pycvoa.problem.domain.Domain.get_variable_definition`
    - :py:meth:`~pycvoa.problem.domain.Domain.get_variable_type`
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


class NotDefinedElement(DomainError):
    """ It is raised when an element is not defined in a **LAYER** variable of the domain.

    **Methods that can throw this exception:**

    - :py:meth:`~pycvoa.problem.domain.Domain.get_element_definition`
    """
    def __init__(self, message):
        self.message = message


class WrongVariableType(DomainError):
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


class WrongComponentType(DomainError):
    """ It is raised when the type of the component of a **VECTOR** variable is wrong.

     **Methods that can throw this exception:**

    - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_integer_element`
    - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_real_element`
    - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_categorical_element`
    - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_list`
    - :py:meth:`~pycvoa.problem.domain.Domain.get_component_element_definition`
    - :py:meth:`~pycvoa.problem.domain.Domain.check_basic_component`
    - :py:meth:`~pycvoa.problem.domain.Domain.check_element_component`
    - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
    """
    def __init__(self, message):
        self.message = message


class WrongDefinition(DomainError):
    """ It is raised when the definition of a variable is wrong.

        **Methods that can throw this exception:**

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


class WrongParameters(DomainError):
    """ It is raised when the parameters of a query function are wrong.

        **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.domain.Domain.check_value`
     """

    def __init__(self, message):
        self.message = message