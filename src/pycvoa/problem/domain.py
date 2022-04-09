from pycvoa.problem import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, BASIC
from pycvoa.problem.support import definition_to_string


class Domain:
    """ This class provides the required functionality to define a domain. The user must instantiate the class into a
    variable and, next, define the variables using the member methods of the class.

    **Example:**

    .. code-block:: python

        new_domain = Domain()
        new_domain.register_categorical_variable("Categorical",["C1","C2","C3"])


    The variable definitions are internally storer in a member variable with the following TYPE-depended structure:

    **Internal structure for BASIC definition TYPES**

    - list(INTEGER, int, int, int)
    - list(REAL, float, float, float)
    - list(CATEGORICAL, list(Any)*)

    **Internal structure for the LAYER definition TYPE**

    - list(LAYER,
                list(
                        (
                        list(INTEGER, int, int, int) |
                        list(REAL, float, float, float) |
                        list(CATEGORICAL, list(Any)*)
                        )*
                    )
            )

    **Internal structure for the VECTOR definition TYPE**

    - list(VECTOR, int, int, int,
                list(INTEGER, int, int, int)
           )
    - list(VECTOR,int,int,int,
                list(REAL, float, float, float)
           )
    - list(VECTOR,int,int,int,
                list(CATEGORICAL, list(Any)*)
           )
    - list(VECTOR, int, int, int,
            list(LAYER,
                list(
                        (
                        list(INTEGER, int, int, int) |
                        list(REAL, float, float, float) |
                        list(CATEGORICAL, list(Any)*)
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

    # **** DEFINE METHODS ****

    def define_integer(self, name, min_value, max_value, step):
        """ It defines an integer variable receiving the variable name, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        :param name: Variable name.
        :param min_value: Minimum value
        :param max_value: Maximum value
        :param step: Step size
        :type name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        if min_value < max_value:
            if step < (max_value-min_value)/2:
                self.__definitions[name] = [INTEGER, min_value, max_value, step]
            else:
                raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
        else:
            raise WrongDefinition("The minimum value must be less than the maximum value")

    def define_real(self, name, min_value, max_value, step):
        """ It defines a real variable receiving the variable name, the minimum and maximum values that it will be
        able to have, and the step size to traverse the interval.

        :param name: Variable name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        if min_value < max_value:
            if step < (max_value - min_value) / 2:
                self.__definitions[name] = [REAL, min_value, max_value, step]
            else:
                raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
        else:
            raise WrongDefinition("The minimum value must be less than the maximum value")

    def define_categorical(self, name, categories):
        """ It defines a categorical variable receiving the variable name, and a list with the labels that it will be
        able to have.

        :param name: Variable name.
        :param categories: List of labels.
        :type name: str
        :type categories: list
        """
        self.__definitions[name] = [CATEGORICAL, categories]

    def define_layer(self, name):
        """ It defines a layer variable receiving the variable name. Next, the layer elements have to be defined using
        the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_layer_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_layer_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_layer_categorical`

        :param name: Variable name.
        :type name: str
        """
        self.__definitions[name] = [LAYER, {}]

    def define_vector(self, name, min_size, max_size, step_size):
        """ It defines a vector variable receiving the variable name, the minimum and maximum size that it will be able
        to have, and the step size to select the size from the :math:`[min\_size, max\_size]`. Afterwards, the vector
        type must be set using the following methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_as_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_as_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_as_categorical`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_as_layer`

        :param name: Variable name.
        :param min_size: Minimum size.
        :param max_size: Maximum size.
        :param step_size: Step size.
        :type name: str
        :type min_size: int
        :type max_size: int
        :type step_size: int
        """
        if min_size < max_size:
            if step_size < (min_size-max_size)/2:
                self.__definitions[name] = [VECTOR, min_size, max_size, step_size, {}]
            else:
                raise WrongDefinition("The step size must be less than (minimum size-maximum size)/2")
        else:
            raise WrongDefinition("The minimum size must be less than the maximum size")


    def define_integer_element(self, variable, element_name, min_value, max_value, step):
        """ It defines an integer element into the layer_name variable by receiving the element name, the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param variable: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type variable: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        if self.get_variable_type(variable) is LAYER:
            layer_elements = self.__definitions[variable][1]
            if min_value < max_value:
                if step < (max_value - min_value) / 2:
                    layer_elements[element_name] = [INTEGER, min_value, max_value, step]
                else:
                    raise WrongDefinition("The step value must be less than (maximum value-minimum value)/2")
            else:
                raise WrongDefinition("The minimum value must be less than the maximum value")
        else:
            raise WrongVariableType("The "+variable+" variable is not defined as a LAYER")


    def define_real_element(self, layer_name, element_name, min_value, max_value, step):
        """ It defines a real element into the layer_name variable by receiving the element name, the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param layer_name: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type layer_name: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def define_categorical_element(self, layer_name, element_name, categories):
        """ It defines a categorical element into the layer_name variable by receiving the element name, and a list with
        the labels that it will be able to have.

        :param layer_name: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param categories: List of labels.
        :type layer_name: str
        :type element_name: str
        :type categories: list
        """
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    def define_vector_as_integer(self, vector_variable_name, min_value, max_value, step):
        """ It set the component type of the vector variable to integer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval

        :param vector_variable_name: Vector variable name previously defined.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        self.__definitions[vector_variable_name][4] = [INTEGER, min_value, max_value, step]

    def define_vector_as_real(self, vector_variable_name, min_value, max_value, step):
        """ It set the component type of the vector variable to real by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval

        :param vector_variable_name: Vector variable name previously defined.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        self.__definitions[vector_variable_name][4] = [REAL, min_value, max_value, step]

    def define_vector_as_categorical(self, vector_variable_name, categories):
        """ It set the component type of the vector variable to categorical by receiving a list with
        the labels that it will be able to have.

        :param vector_variable_name: Vector variable name previously defined.
        :param categories: List of label.
        :type vector_variable_name: str
        :type categories: list
        """
        self.__definitions[vector_variable_name][4] = [CATEGORICAL, categories]

    def define_vector_as_layer(self, vector_variable_name):
        """ It set the component type of the vector variable to layer. Afterwards, the elements of
        the layer must be set using the methods:

        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_layer_integer`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_layer_real`
        - :py:meth:`~pycvoa.problem.domain.Domain.define_vector_layer_categorical`

        :param vector_variable_name: Vector variable name previously defined.
        :type vector_variable_name: str
        """
        self.__definitions[vector_variable_name][4] = [LAYER, {}]

    def define_vector_integer_element(self, vector_variable_name, element_name, min_value, max_value, step):
        """ It defines an integer element of a vector variable set as a layer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [INTEGER, min_value, max_value, step]

    def define_vector_real_element(self, vector_variable_name, element_name, min_value, max_value, step):
        """ It defines a real element of a vector variable set as a layer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def define_vector_categorical_element(self, vector_variable_name, element_name, categories):
        """ It defines a categorical element of a vector variable set as a layer by receiving a list with
        the labels that it will be able to have.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param categories: List of labels.
        :type vector_variable_name: str
        :type element_name: str
        :type categories: list
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    # **** IS DEFINED METHODS ***

    def is_defined_variable(self, variable):
        r = False
        if variable in self.get_variable_list():
            r = True
        return r

    def is_defined_element(self, variable, element):
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
        """ Get the definition of a variable.

        :param variable: The variable.
        :type variable: str
        :returns: Definition of a variable.
        :rtype: list
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
        """
        r = None
        if self.is_defined_variable(variable):
            r = self.__definitions[variable][0]
        else:
            raise NotDefinedVariable("The variable " + variable + " is not defined in this domain")
        return r

    def get_element_type(self, variable, element):
        """ Get the layer element type.

        :param variable: The registered layer variable.
        :type variable: str
        :param element: The element.
        :type element: str
        :returns: The variable type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**
        """
        r = None
        if self.get_variable_type(variable) is LAYER:
            r = self.__definitions[variable][1][element][0]
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as LAYER type")
        return r

    def get_component_type(self, variable):
        """ Get the type of the components of a registered **VECTOR** variable.

        :param vector_variable: The registered **VECTOR** variable.
        :type vector_variable: str
        :returns: The **VECTOR** variable component type.
        :rtype: **INTEGER**, **REAL**, **CATEGORICAL**, **LAYER**
        """
        r = None
        if self.get_variable_type(variable) is VECTOR:
            r = self.__definitions[variable][4][0]
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as VECTOR type")
        return r

    # **** GET ELEMENT DEFINITION METHODS ***

    def get_element_definition(self, variable, element):
        """ Get the layer element definition.

        :param variable: The registered layer variable.
        :type variable: str
        :param element: The element.
        :type element: str
        :returns: The element definition.
        :rtype: list
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

        :param variable: The registered layer variable.
        :type variable: str
        :returns: A list with the elements the registered **LAYER** variable.
        :rtype: list
        """
        r = None

        if self.get_variable_type(variable) is LAYER:
            r = list(self.__definitions[variable][1].keys())
        else:
            raise WrongVariableType("The variable " + variable + " is not defined as LAYER type")

        return r

    # **** GET COMPONENT DEFINITION METHODS ***

    def get_component_definition(self, variable):
        """ Get the definition of the components of a registered **VECTOR** variable.

        :param variable: The registered **VECTOR** variable.
        :type variable: str
        :returns: The **VECTOR** variable component definition.
        :rtype: list
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
        """
        r = None
        if self.get_component_type(variable) is LAYER:
            r = list(self.__definitions[variable][4][1].keys())
        else:
            raise WrongVariableType(
                "The components of the VECTOR variable " + variable + " are not defined as LAYER type")
        return r

    def get_component_element_definition(self, variable, element):
        """ Get the layer element definition for a **VECTOR** variable.

        :param variable: The registered **VECTOR** variable.
        :type variable: str
        :param element: The element.
        :type element: str
        :returns: The element definition.
        :rtype: list
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
        """


        """
        r = False
        variable_type = self.get_variable_type(variable)
        if variable_type in BASIC:
            r = self.check_basic(variable, value)
        elif variable_type is LAYER:
            if element is None:
                raise WrongVariableType(
                    "The variable " + variable + " is LAYER, therefore, an element name must be provided")
            else:
                r = self.check_element(variable, element, value)
        elif variable_type is VECTOR:
            comp_type = self.get_component_type(variable)
            if comp_type in BASIC:
                self.check_basic_component(variable, value)
            elif comp_type is LAYER:
                if element is None:
                    raise WrongVariableType(
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
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message

class NotDefinedElement(DomainError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message

class WrongVariableType(DomainError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message

class WrongComponentType(DomainError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message

class WrongDefinition(DomainError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message