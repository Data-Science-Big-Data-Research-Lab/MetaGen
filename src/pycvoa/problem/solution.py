import sys

from pycvoa.problem import CATEGORICAL, INTEGER, REAL, LAYER, VECTOR


class Solution:
    """ This class is an abstraction of a solution for a meta-heuristic that a third-party provides.

    The :py:class:`~pycvoa.cvoa.CVOA` algorithm uses this class to model the individuals in its emulated pandemic
    process.

    The default and unique, constructor builds an empty individual with the worst fitness value
    (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
    :py:class:`~pycvoa.problem.domain.Domain` object can be passed to check the variable definitions internally.

    **Example:**

    .. code-block:: python

        >>> best_solution  = Solution(best=True)
        >>> best_solution.fitness
        0.0
        >>> worst_solution  = Solution()
        >>> worst_solution.fitness
        1.7976931348623157e+308

    :param best: If true, build an individual with the best fitness value, defaults to True.
    :type best: bool
    :param domain: The domain of the solution, defaults to None.
    :type domain: :py:class:`~pycvoa.problem.domain.Domain`
    """

    def __init__(self, best=False, domain=None):
        """ It is the default and unique, constructor builds an empty individual with the worst fitness value
        (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
        :py:class:`~pycvoa.problem.domain.Domain` object can be passed to check the variable definitions internally.

        :param best: If True the individual will be built with the best fitness function;
        otherwise the worst, defaults to False.
        :type best: bool
        :param domain: The domain of the solution, defaults to None.
        :type domain: :py:class:`~pycvoa.problem.domain.Domain`
        :ivar __definition: Problem definition associated with the individual.
        :vartype __definition: :py:class:`~pycvoa.definition.ProblemDefinition`
        :ivar __variables: Data structure where the variables of an individual are stored.
        :vartype __variables: dict
        :ivar discovering_iteration_time: Pandemic time when a solution is discovered.
        :vartype discovering_iteration_time: int
        :ivar fitness: Fitness value.
        :vartype fitness: float
        """
        self.__domain = domain
        self.__variables = {}
        self.discovering_iteration_time = 0
        if best:
            self.fitness = 0.0
        else:
            self.fitness = sys.float_info.max

    def set_definition(self, domain):
        """ It sets the domain of the solution.

        :param domain: The domain of the solution, defaults to None.
        :type domain: :py:class:`~pycvoa.problem.domain.Domain`
        """
        self.__domain = domain

    def get_value(self, variable, index=None, element=None):
        """ It returns a value of a variable.

        This member has three use cases:

        - BASIC TYPE: Only the variable name must be provided.
        - LAYER TYPE: The variable type and the element name must be provided.
        - VECTOR TYPE: The variable name and the index of the component must be provided.
            - If the components are defined as a LAYER TYPE: The element must be also provided.

        :param variable: The variable name.
        :param index: Index position of a **VECTOR** variable, defaults to None.
        :param element: Element of a **LAYER** variable, defaults to None.
        :type variable: str
        :type index: int
        :type element: str
        :returns: The value.
        :rtype: int, float, str
        :raise SolutionError:
        """

        var_type = self.__domain.get_variable_type(variable)

        if var_type in (INTEGER, REAL, CATEGORICAL):
            r = self.get_basic_value(variable)

        elif var_type is LAYER:
            if element is None:
                raise SolutionError(
                    "The " + variable + "variable is defined as LAYER, therefore an element name must be "
                                        "provided")
            else:
                r = self.get_layer_value(variable, element)

        elif var_type is VECTOR:
            if index is None:
                raise SolutionError(
                    "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                        "must be provided")
            else:

                vector_definition = self.__domain.get_vector_component_definition(variable)

                if vector_definition in (INTEGER, REAL, CATEGORICAL):
                    r = self.get_vector_value(variable, index)
                elif vector_definition is LAYER:
                    if element is None:
                        raise SolutionError(
                            "The components of the VECTOR variable " + variable + " are defined as LAYER, "
                                                                                  "therefore an element name must be "
                                                                                  "provided")
                    else:
                        r = self.get_vector_layer_component_value(variable, index, element)

        return r

    def get_basic_value(self, variable):
        """ It returns a variable value of the solution.

        **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**.

        For **LAYER** and **VECTOR** variables, there are specific getters:

        - :py:meth:`~pycvoa.individual.Individual.get_layer_element_value`,
        - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value` and
        - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`

        :param variable: The variable name.
        :type variable: str
        :returns: The variable value.
        :rtype: int, float, str
        :raise NotDefinedVariableError: The variable is not in the solution.
        """
        if variable in self.__variables:
            return self.__variables.get(variable)
        else:
            raise NotInSolutionError("The variable " + variable + " is not in this solution")

    def get_layer_value(self, variable, element):
        """ It returns an element value of a **LAYER** variable of the individual.

        :param variable: The **LAYER** variable name.
        :param element: The **LAYER** element name.
        :type variable: str
        :type element: str
        :returns: The element value of the **LAYER** variable.
        :rtype: int, float, str
        :raise NotDefinedLayerElementError: The element of the layer is not defined in the individual.
        :raise NotLayerError: The layer variable is not defined as a **LAYER** type.
        """
        if variable in self.__variables:
            variable = self.__variables.get(variable)
            if type(variable) is dict:
                if element in variable.keys():
                    return variable[element]
                else:
                    raise NotDefinedLayerElementError("The element " + element + " of the layer " +
                                                      variable + " is not defined")
            else:
                raise NotLayerError("The variable " + variable + " is not a layer")
        else:
            raise NotDefinedLayerElementError("The variable " + variable + " is not defined")

    def get_vector_value(self, variable, index):
        """ It returns the **index**-nh value of a **VECTOR** variable of the individual.

        :param variable: The **VECTOR** variable name.
        :param index: The index of the element to get.
        :type variable: str
        :type index: int
        :returns: The **index**-nh value of the size **VECTOR** variable.
        :rtype: float, int, str
        """
        if variable in self.__variables:
            vector = self.__variables.get(variable)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    return vector[index]
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                         + variable + " is not defined")
            else:
                raise NotVectorError("The variable " + variable + " is not a vector")
        else:
            raise NotInSolutionError("The variable " + variable + " is not defined")

    def get_vector_layer_component_value(self, variable, index, element):
        """ It returns a **LAYER** element value of the **index**-nh component of a **VECTOR** variable
        of the individual.

        :param variable: The **VECTOR** variable name.
        :param index: The index of the element to get.
        :param element: The **LAYER** element name.
        :type variable: str
        :type index: int
        :type element: str
        :returns: The element value of the **LAYER** in the **index**-nh position of the **VECTOR** variable.
        :rtype: float, int, str
        """
        if variable in self.__variables:
            vector = self.__variables.get(variable)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    layer = vector[index]
                    if type(layer) is dict:
                        if element in vector[index].keys():
                            return vector[index][element]
                        else:
                            raise NotDefinedLayerElementError("The layer element " + element +
                                                              " is not defined for the vector " + variable)
                    else:
                        raise NotLayerError(
                            "The element " + str(index) + " of the vector " + variable + " is not a layer")
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector " +
                                                         variable + " is not defined")
            else:
                raise NotVectorError("The variable " + variable + " is not a vector")
        else:
            raise NotInSolutionError("The variable " + variable + " is not defined")

    def get_vector_size(self, variable):
        """ It returns the size of a **VECTOR** variable of the individual. It is useful to access the values
        of the **VECTOR** variable sequentially.

        :param variable: The **VECTOR** variable name.
        :type variable: str
        :returns: The size of the **VECTOR** variable.
        :rtype: int
        """
        if variable in self.__variables:
            vector = self.__variables.get(variable)
            if type(vector) is list:
                return len(self.__variables.get(variable))
            else:
                raise NotVectorError("The variable " + variable + " is not a vector")
        else:
            raise NotInSolutionError("The variable " + variable + " is not defined")

    def set_value(self, variable, value, index=None, element=None):
        return 1

    def set_variable(self, variable, value):
        """ It sets the value of variable. If the variable does not exist, it will be created with the indicated value.

         **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**. For **LAYER** and **VECTOR** variables,
        there are specific setters (:py:meth:`~pycvoa.individual.Individual.set_layer_element_value`,
        :py:meth:`~pycvoa.individual.Individual.set_vector_element_by_index` respectively and
        :py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param variable: The name of the variable to set.
        :param value: The new value of the variable.
        :type variable: str
        :type value: int, float, str
        """
        self.__variables[variable] = value

    def set_element(self, variable, element, value):
        """ It sets the element value of a **LAYER** variable. If the **LAYER** variable does not exist,
        it will be created with the indicated value.

        :param variable: The name of the variable to set.
        :param element: The new value of the variable.
        :param value: The new value of the variable.
        :type variable: str
        :type element: str
        :type value: int, float, str
        """
        if variable not in self.__variables:
            self.__variables[variable] = {element: value}
        else:
            self.__variables[variable][element] = value

    def set_component(self, variable, index, value):
        """ It sets **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

         **Precondition:**

        The type of the queried **VECTOR** variable must be **INTEGER**, **REAL** or **CATEGORICAL**.
        For **VECTOR** variables defined as **LAYER**, there is a specific setter
        (:py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param variable: The name of the variable to set.
        :param index: The position to set.
        :param value: The new value of the position.
        :type variable: str
        :type index: int
        :type value: int, float, str
        """
        if variable not in self.__variables:
            self.__variables[variable] = [value]
        else:
            self.__variables[variable][index] = value

    def set_component_element(self, variable, index, element, value):
        """ It sets an element of a **LAYER** in the **index**-nh position of a **VECTOR** variable.

        :param variable: The name of the variable to set.
        :param index: The position to set.
        :param element: The layer element name.
        :param value: The new value of the layer element.
        :type variable: str
        :type index: int
        :type element: str
        :type value: int, float, str
        """
        if variable in self.__variables:
            self.__variables[variable][index][element] = value

    def add_component(self, variable, value):
        """ It appends a value at last of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param value: The new value.
        :type variable: str
        :type value: int, float, str, list
        """
        if variable not in self.__variables:
            self.__variables[variable] = [value]
        else:
            self.__variables[variable].append(value)

    def insert_component(self, variable, index, value):
        """ It inserts a value in the **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable
        does not exist, it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param index: The position where the new value will be inserted.
        :param value: The new value.
        :type variable: str
        :type index: int
        :type value: int, float, str, list
        """
        if variable not in self.__variables:
            self.__variables[variable] = [value]
        else:
            self.__variables[variable].insert(index, value)

    def remove_component(self, variable):
        """ It removes the last position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :type variable: str
        """
        self.__variables[variable].pop()

    def delete_component(self, variable, index):
        """ It removes a value in the **index**-nh position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :param index: The position to be removed.
        :type variable: str
        :type index: int
        """
        del self.__variables[variable][index]

    def __str__(self):
        """ String representation of a :py:class:`~pycvoa.individual.Individual` object
        """
        res = "F = " + str(self.fitness) + "\t{"
        count = 1
        for variable in sorted(self.__variables):
            res += str(variable) + " = " + str(self.__variables[variable])
            if count < len(self.__variables):
                res += " , "
            count += 1
        res += "}"
        return res

    def __eq__(self, other):
        """ Equity function of the :py:class:`~pycvoa.individual.Individual` class. An
        :py:class:`~pycvoa.individual.Individual` object is equal to another :py:class:`~pycvoa.individual.Individual`
        object if they have the same variables with the same values.
        """
        res = True

        if not isinstance(other, Solution):
            res = False
        else:
            i = 0
            keys = list(self.__variables.keys())
            while i < len(keys) & res:
                vf = self.get_basic_value(keys[i])
                vo = other.get_basic_value(keys[i])
                if vf != vo:
                    res = False
                i += 1

        return res

    def __ne__(self, other):
        """ Non Equity function of the :py:class:`~pycvoa.individual.Individual` class. An
        :py:class:`~pycvoa.individual.Individual` object is not equal to another :
        py:class:`~pycvoa.individual.Individual` object if they do not have the same variables with the same values.
        """
        return not self.__eq__(other)

    def __hash__(self):
        """ Hash function for :py:class:`~pycvoa.individual.Individual` objects. It is necessary for set structure
        management.
        """
        return hash((self.__variables.__hash__, self.fitness))

    def __lt__(self, other):
        """ *Less than* function for :py:class:`~pycvoa.individual.Individual` objects. An individual **A** is less
        than another individual **B** if the fitness value of **A** is strictly less than the fitness value of **B**.
        It is necessary for set structure management.
        """
        return self.fitness < other.fitness

    def __le__(self, other):
        """ *Less equal* function for :py:class:`~pycvoa.individual.Individual` objects. An individual **A** is less or
        equal than another individual **B** if the fitness value of **A** is less or equal than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.fitness <= other.fitness

    def __gt__(self, other):
        """ *Greater than* function for :py:class:`~pycvoa.individual.Individual` objects. An individual **A** is
        greater than another individual **B** if the fitness value of **A** strictly greater than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.fitness > other.fitness

    def __ge__(self, other):
        """ *Greater equal* function for :py:class:`~pycvoa.individual.Individual` objects. An individual **A** is
        greater or equal than another individual **B** if the fitness value of **A** greater or equal than the
        fitness value of **B**. It is necessary for set structure management.
        """
        return self.fitness >= other.fitness


class SolutionError(Exception):
    """ It is the top level exception for :py:class:`~pycvoa.individual.Individual` error management.
    """
    pass


class NotInSolutionError(SolutionError):
    """ It is raised when a non defined variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_variable_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_size`
    """

    def __init__(self, message):
        self.message = message


class NotDefinedLayerElementError(SolutionError):
    """ It is raised when a non defined element of a **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_layer_element_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class NotLayerError(SolutionError):
    """ It is raised when an element of a non defined **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_layer_element_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class NotVectorError(SolutionError):
    """ It is raised when there is an access to a position of a variable that it does not has defined as a **VECTOR**.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_size`
    """

    def __init__(self, message):
        self.message = message


class NotDefinedVectorComponentError(SolutionError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message
