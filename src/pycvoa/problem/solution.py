import sys

from pycvoa.problem import CATEGORICAL, INTEGER, REAL, LAYER, VECTOR, BASIC


class Solution:
    """ This class is an abstraction of a solution for a meta-heuristic that a third-party provides.

    The :py:class:`~pycvoa.cvoa.CVOA` algorithm uses this class to model the individuals in its emulated pandemic
    process.

    The default and unique, constructor builds an empty solution with the worst fitness value
    (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
    :py:class:`~pycvoa.problem.domain.Domain` object can be passed to check the variable definitions internally and,
    therefore boost the Solution fucntionality.

    **Example:**

    .. code-block:: python

        >>> best_solution  = Solution(best=True)
        >>> best_solution.fitness
        0.0
        >>> worst_solution  = Solution()
        >>> worst_solution.fitness
        1.7976931348623157e+308

    :param best: If true, build an individual with the best fitness value, defaults to True.
    :param domain: The domain of the solution, defaults to None.
    :type best: bool
    :type domain: :py:class:`~pycvoa.problem.domain.Domain`
    """

    def __init__(self, best=False, domain=None):
        """ It is the default and unique, constructor builds an empty solution with the worst fitness value
        (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
        :py:class:`~pycvoa.problem.domain.Domain` object can be passed to check the variable definitions internally and,
        therefore boost the Solution fucntionality.

        :param best: If True the individual will be built with the best fitness function;
        otherwise the worst, defaults to False.
        :param domain: The domain of the solution, defaults to None.
        :ivar __domain: Domain associated with the solution.
        :ivar __variables: Data structure where the variables of a solution are stored.
        :ivar discovering_iteration_time: Pandemic time when a solution is discovered.
        :ivar fitness: Fitness value.
        :type best: bool
        :type domain: :py:class:`~pycvoa.problem.domain.Domain`
        :vartype __domain: :py:class:`~pycvoa.problem.domain.Domain`
        :vartype __variables: dict
        :vartype discovering_iteration_time: int
        :vartype fitness: float
        """
        self.__domain = domain
        self.__variables = {}
        self.discovering_iteration_time = 0
        if best:
            self.fitness = 0.0
        else:
            self.fitness = sys.float_info.max

    # ** DOMAIN AVAILABILITY INTERFACE ***
    def set_domain(self, domain):
        """ It sets the domain of the solution.

        :param domain: The domain of the solution.
        :type domain: :py:class:`~pycvoa.problem.domain.Domain`
        """
        self.__domain = domain

    def domain_type(self, variable):
        r = None
        if self.__domain is not None:
            r = self.__domain.get_variable_type(variable)
        return r

    def domain_is_defined_element (self,variable,element):
        r = None
        if self.__domain is not None:
            r = self.__domain.is_defined_element(variable, element)
        return r

    def domain_component_definition(self,variable):
        r = None
        if self.__domain is not None:
            r = self.__domain.get_component_definition(variable)
        return r

    # ** AVAILABILITY CHECKERS ***

    def is_avialable(self, variable):
        r = False
        if variable in self.__variables.keys():
            r = True
        return r

    def is_avialable_element(self, variable, element):
        r = False
        if self.is_avialable(variable):
            if element in self.__variables.get(variable).keys():
                r = True
        else:
            raise NotInSolutionError("The " + variable + " variable is not in this solution")
        return r

    def is_available_component(self, variable, index):
        r = False
        if self.check_variable_type(variable, VECTOR):
            if 0 <= index < len(self.__variables.get(variable)):
                r = True
        else:
            raise WrongType("The variable " + variable + " is not defined as VECTOR.")
        return r

    def is_available_component_element(self, variable, index, element):
        r = False
        if self.is_available_component(variable, index):
            if self.check_component_type(variable, LAYER):
                if element in self.__variables.get(variable)[index].keys():
                    r = True
            else:
                raise WrongComponentType("The component type is not LAYER")
        else:
            raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                 + variable + " is not available")
        return r

    # ** TYPE CHECKERS ***

    def check_variable_type(self, variable, type):
        r = False
        if self.is_avialable(variable):
            if type is BASIC:
                if self.__domain.get_variable_type(variable) in BASIC:
                    r = True
            else:
                if self.__domain.get_variable_type(variable) is type:
                    r = True
        else:
            raise NotInSolutionError("The " + variable + " variable is not in this solution")
        return r

    def check_component_type(self, variable, type):
        r = False
        if self.is_avialable(variable):
            if self.check_variable_type(variable, VECTOR):
                if type is BASIC:
                    if self.__domain.get_component_type(variable) in BASIC:
                        r = True
                else:
                    if self.__domain.get_component_type(variable) is type:
                        r = True
            else:
                raise WrongType("The " + variable + " variable is not defined as VECTOR")
        else:
            raise NotInSolutionError("The " + variable + " variable is not in this solution")
        return r

    # ** GETTERS ***

    def get_basic_value(self, variable):
        """ It returns a variable value of a **BASIC** variable of the solution.

        **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**.

        For **LAYER** and **VECTOR** variables, there are specific getters:

        - :py:meth:`~pycvoa.problem.solution.Solution.get_element_value`,
        - :py:meth:`~pycvoa.problem.solution.Solution.get_component_value`
        - :py:meth:`~pycvoa.problem.solution.Solution.get_component_element_value`

        :param variable: The variable.
        :returns: The variable value.
        :type variable: str
        :rtype: int, float, str
        :raise NotDefinedVariableError: The variable is not in the solution.
        :raise WrongType: The variable is not defined as BASIC.
        """
        r = None
        if self.check_variable_type(variable, BASIC):
            r = self.__variables.get(variable)
        else:
            raise WrongType("The variable " + variable + " is not defined as BASIC.")
        return r

    def get_element_value(self, variable, element):
        """ It returns an element value of a **LAYER** variable of the solution.

        :param variable: The **LAYER** variable.
        :param element: The element.
        :returns: The element value of the **LAYER** variable.
        :type variable: str
        :type element: str
        :rtype: int, float, str
        :raise NotInSolutionError: The variable is not in this solution.
        :raise WrongType: The variable is not defined as **LAYER**.
        :raise NotDefinedLayerElementError: The element is not defined in the **LAYER** variable.
        """
        r = None
        if self.check_variable_type(variable, LAYER):
            if self.is_avialable_element(element):
                r = variable[element]
            else:
                raise NotDefinedLayerElementError(
                    "The element " + element + " is not defined in the " + variable + " variable.")
        else:
            raise WrongType("The variable " + variable + " is not defined as LAYER.")
        return r

    def get_basic_component_value(self, variable, index):
        """ It returns the **index**-nh value of a **VECTOR** variable defined as **BASIC** of the solution.

        :param variable: The variable.
        :param index: The index of the element to get.
        :type variable: str
        :type index: int
        :returns: The **index**-nh value of the size **VECTOR** variable.
        :rtype: float, int, str
        :raise NotInSolutionError: The variable is not in the solution.
        :raise WrongType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the **VECTOR** variable is not defined as **BASIC**.
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        """
        r = None
        if self.check_component_type(variable, BASIC):
            if self.is_available_component(variable, index):
                r = self.__variables.get(variable)[index]
            else:
                raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                     + variable + " is not available")
        else:
            raise WrongComponentType("The component type is not BASIC")
        return r

    def get_layer_component_value(self, variable, index, element):
        """ It returns a **LAYER** element value of the **index**-nh component of a **VECTOR** variable
        of the solution.

        :param variable: The variable.
        :param index: The index of the element to get.
        :param element: The element.
        :returns: The element value of the **index**-nh position of the **VECTOR** variable.
        :type variable: str
        :type index: int
        :type element: str
        :rtype: float, int, str
        :raise NotInSolutionError: The variable is not in the solution.
        :raise WrongType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the **VECTOR** variable are not defined as **LAYER**.
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        :raise NotDefinedComponentElementError: The element of the **index**-nh component of the **VECTOR** variable
        is not available.
        """
        r = None
        if self.is_available_component_element(variable, index, element):
            r = self.__variables.get(variable)[index][element]
        else:
            raise NotDefinedComponentElementError("The element " + element + " in not in the " + index + " component "
                                                                                "of the " + variable + " variable.")
        return r

    def get_value(self, variable, index=None, element=None):
        """ It returns a value of a variable.

        This member has three use cases:

        - BASIC TYPE: Only the **BASIC** variable must be provided.
        - LAYER TYPE: A **LAYER** variable and the element name must be provided.
        - VECTOR TYPE: A **VECTOR** variable and the index of the component must be provided. If the components are
        defined as **LAYER**, the element must be also provided.

        :param variable: The variable.
        :param index: The index of a position of a **VECTOR** variable, defaults to None.
        :param element: The element of a **LAYER** variable, defaults to None.
        :returns: The value.
        :type variable: str
        :type index: int
        :type element: str
        :rtype: int, float, str
        :raise NotInSolutionError: The variable is not in this solution.
        :raise WrongParameters: The element of a **LAYER** variable is not provided. The index of a component of a
        **VECTOR** variable is not provided. The element of component of a **VECTOR** variable defined as **LAYER**
        is not provided.
        :raise WrongType: The variable is not defined as **VECTOR**.
        :raise WrongComponentType: The components of the **VECTOR** variable are not defined as **LAYER**.
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        :raise NotDefinedComponentElementError: The element of the **index**-nh component of the **VECTOR** variable
        is not available.
        """

        var_type = self.__domain.get_variable_type(variable)

        if var_type in BASIC:
            r = self.get_basic_value(variable)

        elif var_type is LAYER:
            if element is None:
                raise WrongParameters(
                    "The " + variable + "variable is defined as LAYER, therefore an element name must be "
                                        "provided")
            else:
                r = self.get_element_value(variable, element)

        elif var_type is VECTOR:
            if index is None:
                raise WrongParameters(
                    "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                        "must be provided")
            else:

                vector_definition = self.__domain.get_component_definition(variable)

                if vector_definition in BASIC:
                    r = self.get_basic_component_value(variable, index)
                elif vector_definition is LAYER:
                    if element is None:
                        raise WrongParameters(
                            "The components of the VECTOR variable " + variable + " are defined as LAYER, "
                                                                                  "therefore an element name must be "
                                                                                  "provided")
                    else:
                        r = self.get_layer_component_value(variable, index, element)

        return r

    def get_vector_size(self, variable):
        """ It returns the size of a **VECTOR** variable of the solution. It is useful to access the values
        of the **VECTOR** variable sequentially.

        :param variable: The **VECTOR** variable name.
        :returns: The size of the **VECTOR** variable.
        :type variable: str
        :rtype: int
        :raise NotInSolutionError: The variable is not in this solution.
        :raise WrongType: The variable is not defined as **VECTOR**.
        """
        r = None
        if self.check_variable_type(variable,VECTOR):
            r = len(self.__variables.get(variable))
        else:
            raise WrongType("The "+variable+" is not defined as VECTOR")
        return r

    # ** SETTERS ***

    def set_basic(self, variable, value):
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
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type in BASIC:
                self.__variables[variable] = value
            else:
                raise WrongType("The variable is not defined as BASIC")
        else:
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
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is LAYER:
                if variable not in self.__variables:
                    self.__variables[variable] = {element: value}
                else:
                    self.__variables[variable][element] = value
            else:
                raise WrongType("The variable is not defined as LAYER")
        else:
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
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        """
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is VECTOR:
                if variable not in self.__variables:
                    self.__variables[variable] = [value]
                else:
                    if self.is_available_component(variable,index):
                        self.__variables[variable][index] = value
                    else:
                        raise NotDefinedVectorComponentError("The"+index+"-nh component of the **VECTOR** variable "
                                                                         "is not available.")
            else:
                raise WrongType("The variable is not defined as VECTOR")
        else:
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
        is_el = self.domain_is_defined_element(variable,element)
        if is_el is not None:
            if is_el is True:
                if self.is_available_component(variable, index):
                    self.__variables[variable][index][element] = value
                else:
                    raise NotDefinedVectorComponentError("The" + index + "-nh component of the **VECTOR** variable "
                                                                         "is not available.")
            else:
                raise NotDefinedLayerElementError("The variable is not defined as VECTOR")
        else:
           self.__variables[variable][index][element] = value

    def set_value(self, variable, value, index=None, element=None):
        """ It sets a value of a variable.

             This member has three use cases:

             - BASIC TYPE: Only the variable name must be provided.
             - LAYER TYPE: The variable type and the element name must be provided.
             - VECTOR TYPE: The variable name and the index of the component must be provided.
                 - If the components are defined as a LAYER TYPE: The element must be also provided.

        :param variable: The variable name.
        :param value: The new value.
        :param index: Index position of a **VECTOR** variable, defaults to None.
        :param element: Element of a **LAYER** variable, defaults to None.
        :type variable: str
        :type index: int
        :type element: str
        :raise SolutionError:
        """

        var_type = self.domain_type(variable)

        if var_type is not None:

            if var_type in BASIC:
                self.set_basic(variable, value)

            elif var_type is LAYER:
                if element is None:
                    raise SolutionError(
                        "The " + variable + "variable is defined as LAYER, therefore an element name must be "
                                            "provided")
                else:
                    self.set_element(variable, element, value)

            elif var_type is VECTOR:
                if index is None:
                    raise SolutionError(
                        "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                            "must be provided")
                else:

                    vector_definition = self.domain_component_definition(variable)

                    if vector_definition in BASIC:
                        self.set_component(variable, index, value)
                    elif vector_definition is LAYER:
                        if element is None:
                            raise SolutionError(
                                "The components of the VECTOR variable " + variable + " are defined as LAYER, "
                                                                                      "therefore an element name must be "
                                                                                      "provided")
                        else:
                            self.set_component_element(variable, index, element, value)

        else:
            raise NotSetDomain("The domain is not set for this solution")

    # ** VECTOR TYPE MODIFIERS **

    def add_component(self, variable, value):
        """ It appends a value at last of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param value: The new value.
        :type variable: str
        :type value: int, float, str, list
        """
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is VECTOR:
                if variable not in self.__variables:
                    self.__variables[variable] = [value]
                else:
                    self.__variables[variable].append(value)
            else:
                raise WrongType("The variable is not defined as VECTOR")
        else:
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
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is VECTOR:
                if variable not in self.__variables:
                    self.__variables[variable] = [value]
                else:
                    self.__variables[variable].insert(index, value)
            else:
                raise WrongType("The variable is not defined as VECTOR")
        else:
            if variable not in self.__variables:
                self.__variables[variable] = [value]
            else:
                self.__variables[variable].insert(index, value)

    def remove_component(self, variable):
        """ It removes the last position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :type variable: str
        """
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is VECTOR:
                self.__variables[variable].pop()
            else:
                raise WrongType("The variable is not defined as VECTOR")
        else:
            self.__variables[variable].pop()

    def delete_component(self, variable, index):
        """ It removes a value in the **index**-nh position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :param index: The position to be removed.
        :type variable: str
        :type index: int
        """
        var_type = self.domain_type(variable)
        if var_type is not None:
            if var_type is VECTOR:
                if self.is_available_component(variable, index):
                    del self.__variables[variable][index]
                else:
                    raise NotDefinedVectorComponentError("The" + index + "-nh component of the **VECTOR** variable "
                                                                         "is not available.")
            else:
                raise WrongType("The variable is not defined as VECTOR")
        else:
            del self.__variables[variable][index]

    # ** TO STRING **

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

    # ** SET INTERNAL METHODS **

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
    """ It is raised when a queried variable is not in the solution.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_size`
    """

    def __init__(self, message):
        self.message = message


class WrongType(SolutionError):
    """ It is raised when a variable is queried with the wrong method.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_size`
    """

    def __init__(self, message):
        self.message = message


class NotDefinedLayerElementError(SolutionError):
    """ It is raised when a non defined element of a **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_layer_element_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class NotDefinedComponentElementError(SolutionError):
    """ It is raised when a non defined element of a **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_layer_element_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class NotLayerError(SolutionError):
    """ It is raised when an element of a non defined **LAYER** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_layer_element_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class NotVectorError(SolutionError):
    """ It is raised when there is an access to a position of a variable that it does not has defined as a **VECTOR**.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_size`
    """

    def __init__(self, message):
        self.message = message


class NotDefinedVectorComponentError(SolutionError):
    """ It is raised when a not existing position of a **VECTOR** variable is accessed.

    **Methods that can throw this exception:**
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_component_value`
    - :py:meth:`~pycvoa.problem.solution.Solution.get_vector_layer_component_value`
    """

    def __init__(self, message):
        self.message = message


class WrongParameters(SolutionError):
    """ It is raised when the parameters of a query function are wrong.

        **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    """

    def __init__(self, message):
        self.message = message


class WrongComponentType(SolutionError):
    """ It is raised when the parameters of a query function are wrong.

        **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    """

    def __init__(self, message):
        self.message = message


class NotSetDomain(SolutionError):
    """ It is raised when the parameters of a query function are wrong.

        **Methods that can throw this exception:**

        - :py:meth:`~pycvoa.problem.solution.Solution.get_value`
    """

    def __init__(self, message):
        self.message = message