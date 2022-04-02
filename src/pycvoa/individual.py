import sys


class Individual:
    """ This class provides the abstraction of an individual for the :py:class:`~pycvoa.cvoa.CVOA` algorithm or any
    meta-heuristic that third-party provides. The default and unique, constructor builds an empty individual with
    the best fitness value (:math:`best=True`, by default) or the worst fitness value (:math:`best=False`).

    **Example:**

    .. code-block:: python

        >>> best_individual  = Individual()
        >>> best_individual.fitness
        0.0
        >>> worst_individual  = Individual(False)
        >>> worst_individual.fitness
        1.7976931348623157e+308

    :param best: If true, build an individual with the best fitness value, defaults to True.
    :type best: bool
    """

    def __init__(self, best=True):
        """ It is the default, and unique, constructor. It builds an empty individual with
        the best fitness value (:math:`best=True`, by default) or the worst fitness value (:math:`best=False`)

        :ivar __variables: Data structure where the variables of an individual are stored.
        :vartype __variables: dict
        :ivar discovering_iteration_time: Pandemic time when a solution is discovered.
        :vartype discovering_iteration_time: int
        :ivar fitness: Fitness value.
        :vartype fitness: float
        """
        self.__variables = {}
        self.discovering_iteration_time = 0
        if best:
            self.fitness = 0.0
        else:
            self.fitness = sys.float_info.max

    def get_variable_value(self, variable_name):
        """ It returns a variable value of the individual.

        **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**. For **LAYER** and **VECTOR** variables,
        there are specific getters (:py:meth:`~pycvoa.individual.Individual.get_layer_element_value`,
        :py:meth:`~pycvoa.individual.Individual.get_vector_component_value` and
        :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`)

        :param variable_name: The variable name.
        :type variable_name: str
        :returns: The variable value.
        :rtype: int, float, str
        :raise NotDefinedVariableError: The variable is not defined in the individual.
        """
        if variable_name in self.__variables:
            return self.__variables.get(variable_name)
        else:
            raise NotDefinedVariableError("The variable " + variable_name + " is not defined")

    def get_layer_element_value(self, layer_name, element_name):
        """ It returns an element value of a **LAYER** variable of the individual.

        :param layer_name: The **LAYER** variable name.
        :param element_name: The **LAYER** element name.
        :type layer_name: str
        :type element_name: str
        :returns: The element value of the **LAYER** variable.
        :rtype: int, float, str
        :raise NotDefinedLayerElementError: The element of the layer is not defined in the individual.
        :raise NotLayerError: The layer variable is not defined as a **LAYER** type.
        """
        if layer_name in self.__variables:
            layer = self.__variables.get(layer_name)
            if type(layer) is dict:
                if element_name in layer.keys():
                    return layer[element_name]
                else:
                    raise NotDefinedLayerElementError("The element " + element_name + " of the layer " +
                                                      layer_name + " is not defined")
            else:
                raise NotLayerError("The variable " + layer_name + " is not a layer")
        else:
            raise NotDefinedLayerElementError("The variable " + layer_name + " is not defined")

    def get_vector_component_value(self, vector_name, index):
        """ It returns the **index**-nh value of a **VECTOR** variable of the individual.

        :param vector_name: The **VECTOR** variable name.
        :param index: The index of the element to get.
        :type vector_name: str
        :type index: int
        :returns: The **index**-nh value of the size **VECTOR** variable.
        :rtype: float, int, str
        """
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    return vector[index]
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                         + vector_name + " is not defined")
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    def get_vector_layer_component_value(self, vector_name, index, layer_element):
        """ It returns a **LAYER** element value of the **index**-nh component of a **VECTOR** variable
        of the individual.

        :param vector_name: The **VECTOR** variable name.
        :param index: The index of the element to get.
        :param layer_element: The **LAYER** element name.
        :type vector_name: str
        :type index: int
        :type layer_element: str
        :returns: The element value of the **LAYER** in the **index**-nh position of the **VECTOR** variable.
        :rtype: float, int, str
        """
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    layer = vector[index]
                    if type(layer) is dict:
                        if layer_element in vector[index].keys():
                            return vector[index][layer_element]
                        else:
                            raise NotDefinedLayerElementError("The layer element " + layer_element +
                                                              " is not defined for the vector " + vector_name)
                    else:
                        raise NotLayerError(
                            "The element " + str(index) + " of the vector " + vector_name + " is not a layer")
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector " +
                                                         vector_name + " is not defined")
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    def get_vector_size(self, vector_name):
        """ It returns the size of a **VECTOR** variable of the individual. It is useful to access the values
        of the **VECTOR** variable sequentially.

        :param vector_name: The **VECTOR** variable name.
        :type vector_name: str
        :returns: The size of the **VECTOR** variable.
        :rtype: int
        """
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                return len(self.__variables.get(vector_name))
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    def set_variable_value(self, variable_name, value):
        """ It sets the value of variable. If the variable does not exist, it will be created with the indicated value.

         **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**. For **LAYER** and **VECTOR** variables,
        there are specific setters (:py:meth:`~pycvoa.individual.Individual.set_layer_element_value`,
        :py:meth:`~pycvoa.individual.Individual.set_vector_element_by_index` respectively and
        :py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param variable_name: The name of the variable to set.
        :param value: The new value of the variable.
        :type variable_name: str
        :type value: int, float, str
        """
        self.__variables[variable_name] = value

    def set_layer_element_value(self, layer_name, element_name, value):
        """ It sets the element value of a **LAYER** variable. If the **LAYER** variable does not exist,
        it will be created with the indicated value.

        :param layer_name: The name of the variable to set.
        :param element_name: The new value of the variable.
        :param value: The new value of the variable.
        :type layer_name: str
        :type element_name: str
        :type value: int, float, str
        """
        if layer_name not in self.__variables:
            self.__variables[layer_name] = {element_name: value}
        else:
            self.__variables[layer_name][element_name] = value

    def set_vector_element_by_index(self, vector_name, index, value):
        """ It sets **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

         **Precondition:**

        The type of the queried **VECTOR** variable must be **INTEGER**, **REAL** or **CATEGORICAL**.
        For **VECTOR** variables defined as **LAYER**, there is a specific setter
        (:py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param vector_name: The name of the variable to set.
        :param index: The position to set.
        :param value: The new value of the position.
        :type vector_name: str
        :type index: int
        :type value: int, float, str
        """
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name][index] = value

    def set_vector_layer_element_by_index(self, vector_name, index, layer_element, value):
        """ It sets an element of a **LAYER** in the **index**-nh position of a **VECTOR** variable.

        :param vector_name: The name of the variable to set.
        :param index: The position to set.
        :param layer_element: The layer element name.
        :param value: The new value of the layer element.
        :type vector_name: str
        :type index: int
        :type layer_element: str
        :type value: int, float, str
        """
        if vector_name in self.__variables:
            self.__variables[vector_name][index][layer_element] = value

    def add_vector_element(self, vector_name, value):
        """ It appends a value at last of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

        :param vector_name: The name of the variable to set.
        :param value: The new value.
        :type vector_name: str
        :type value: int, float, str, list
        """
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name].append(value)

    def add_vector_element_by_index(self, vector_name, index, value):
        """ It inserts a value in the **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable
        does not exist, it will be created with the indicated value in the 0 position.

        :param vector_name: The name of the variable to set.
        :param index: The position where the new value will be inserted.
        :param value: The new value.
        :type vector_name: str
        :type index: int
        :type value: int, float, str, list
        """
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name].insert(index, value)

    def remove_vector_element(self, vector_name):
        """ It removes the last position of a **VECTOR** variable.

        :param vector_name: The name of the **VECTOR** variable to modify.
        :type vector_name: str
        """
        self.__variables[vector_name].pop()

    def remove_vector_element_by_index(self, vector_name, index):
        """ It removes a value in the **index**-nh position of a **VECTOR** variable.

        :param vector_name: The name of the **VECTOR** variable to modify.
        :param index: The position to be removed.
        :type vector_name: str
        :type index: int
        """
        del self.__variables[vector_name][index]

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

        if not isinstance(other, Individual):
            res = False
        else:
            i = 0
            keys = list(self.__variables.keys())
            while i < len(keys) & res:
                vf = self.get_variable_value(keys[i])
                vo = other.get_variable_value(keys[i])
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


class IndividualError(Exception):
    """ It is the top level exception for :py:class:`~pycvoa.individual.Individual` error management.
    """
    pass


class NotDefinedVariableError(IndividualError):
    """ It is raised when a non defined variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_variable_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_size`
    """
    def __init__(self, message):
        self.message = message


class NotDefinedLayerElementError(IndividualError):
    """ It is raised when a non defined element of a **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_layer_element_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """
    def __init__(self, message):
        self.message = message


class NotLayerError(IndividualError):
    """ It is raised when an element of a non defined **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_layer_element_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """
    def __init__(self, message):
        self.message = message


class NotVectorError(IndividualError):
    """ It is raised when there is an access to a position of a variable that it does not has defined as a **VECTOR**.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_size`
    """
    def __init__(self, message):
        self.message = message


class NotDefinedVectorComponentError(IndividualError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.individual.Individual.get_vector_component_value`
    - :py:meth:`~pycvoa.individual.Individual.get_vector_layer_component_value`
    """
    def __init__(self, message):
        self.message = message
