import sys

from pycvoa.problem import LAYER, VECTOR
from pycvoa.problem.control import *


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
        >>> boosted_solution = Solution(domain=defined_domain)

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
        sol_ctrl_check_domain_class(domain)
        self.__domain = domain
        self.__variables = {}
        self.discovery_iteration = 0
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
        sol_ctrl_check_domain_class(domain)
        self.__domain = domain

    # ** BASIC SETTER ***
    def set_basic(self, variable, value, domain=None):
        """ It sets the value of variable. If the variable does not exist, it will be created with the indicated value.

         **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**. For **LAYER** and **VECTOR** variables,
        there are specific setters (:py:meth:`~pycvoa.individual.Individual.set_layer_element_value`,
        :py:meth:`~pycvoa.individual.Individual.set_vector_element_by_index` respectively and
        :py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param variable: The name of the variable to set.
        :param value: The new value of the variable.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type value: int, float, str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **BASIC** type.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as BASIC.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        """
        current_domain = sol_ctrl_check_domain_type(variable, BASIC, domain, self.__domain)
        sol_ctrl_check_basic_value(variable, value, current_domain)
        self.__variables[variable] = value

    # ** LAYER SETTER ***
    def set_element(self, variable, element, value, domain=None):
        """ It sets the element value of a **LAYER** variable. If the **LAYER** variable does not exist,
        it will be created with the indicated value.

        :param variable: The name of the variable to set.
        :param element: The new value of the variable.
        :param value: The new value of the variable.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type element: str
        :type value: int, float, str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in the domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **BASIC** type.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as LAYER.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        """
        current_domain = sol_ctrl_check_domain_type(variable, LAYER, domain, self.__domain)
        sol_ctrl_check_element_value(variable, element, value, current_domain)
        if variable not in self.__variables.keys():
            self.__variables[variable] = {element: value}
        else:
            self.__variables[variable][element] = value

    # ** VECTOR SETTERS ***
    def set_basic_vector(self, variable, values, domain=None):
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_check_vector_basic_values_size_class(variable, values, current_domain)
        self.__variables[variable] = values

    def set_layer_vector(self, variable, values, domain=None):
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_check_vector_layer_values_size_class(variable, values, current_domain)
        self.__variables[variable] = values

    def add_basic_component(self, variable, value, domain=None):
        """ It appends a value at last of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param value: The new value.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type value: int, float, str, list
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** type.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_basic_component(variable, value, current_domain)
        if variable not in self.__variables.keys():
            self.__variables[variable] = [value]
        else:
            self.__variables[variable].append(value)

    def insert_component_element(self, variable, element, index, value, domain=None):
        """ It inserts a value in the **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable
        does not exist, it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param index: The index.
        :param value: The new value.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type index: int
        :type value: int, float, str, list
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** type.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_element_component(variable, element, value, current_domain)
        if variable not in self.__variables:
            self.__variables[variable] = [{element: value}]
        else:
            self.__variables[variable].insert(index, {element: value})

    def add_component_element(self, variable, element, value, domain=None):
        """ It appends a value at last of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param value: The new value.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type value: int, float, str, list
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** type.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_element_component(variable, element, value, current_domain)
        if variable not in self.__variables.keys():
            self.__variables[variable] = [{element: value}]
        else:
            if element in self.__variables[variable][-1].keys():
                self.__variables[variable].append({element: value})
            else:
                self.__variables[variable][-1][element] = value

    def insert_basic_component(self, variable, index, value, domain=None):
        """ It inserts a value in the **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable
        does not exist, it will be created with the indicated value in the 0 position.

        :param variable: The name of the variable to set.
        :param index: The index.
        :param value: The new value.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type index: int
        :type value: int, float, str, list
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not defined as a **BASIC** type.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_basic_component(variable, value, current_domain)
        if variable not in self.__variables:
            self.__variables[variable] = [value]
        else:
            self.__variables[variable].insert(index, value)

    def set_component(self, variable, index, value, domain=None):
        """ It sets **index**-nh position of a **VECTOR** variable. If the **VECTOR** variable does not exist,
        it will be created with the indicated value in the 0 position.

         **Precondition:**

        The type of the queried **VECTOR** variable must be **INTEGER**, **REAL** or **CATEGORICAL**.
        For **VECTOR** variables defined as **LAYER**, there is a specific setter
        (:py:meth:`~pycvoa.individual.Individual.set_vector_layer_element_by_index`)

        :param variable: The name of the variable to set.
        :param index: The position to set.
        :param value: The new value of the position.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type index: int
        :type value: int, float, str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not
        defined as a **BASIC** type.
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_basic_component(variable, value, current_domain)
        if variable not in self.__variables.keys():
            self.__variables[variable] = [value]
        else:
            sol_ctrl_check_component_availability(variable, index, self.__variables)
            self.__variables[variable][index] = value

    def set_component_element(self, variable, index, element, value, domain=None):
        """ It sets an element of a **LAYER** in the **index**-nh position of a **VECTOR** variable.

        :param variable: The name of the variable to set.
        :param index: The position to set.
        :param element: The layer element name.
        :param value: The new value of the layer element.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type index: int
        :type element: str
        :type value: int, float, str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the VECTOR variable are not
        defined as LAYER.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedVectorComponentError: The **index**-nh component of the
        **VECTOR** variable is not available.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        """
        current_domain = sol_ctrl_check_domain_type(variable, VECTOR, domain, self.__domain)
        sol_ctrl_check_element_component(variable, element, value, current_domain)
        if variable not in self.__variables.keys():
            self.__variables[variable] = [{element: value}]
        else:
            sol_ctrl_check_component_availability(variable, index, self.__variables)
            self.__variables[variable][index][element] = value

    def remove_component(self, variable, domain=None):
        """ It removes the last position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as VECTOR.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        self.__variables[variable].pop()

    def delete_component(self, variable, index, domain=None):
        """ It removes a value in the **index**-nh position of a **VECTOR** variable.

        :param variable: The name of the **VECTOR** variable to modify.
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        sol_ctrl_check_component_availability(variable, index, self.__variables)
        del self.__variables[variable][index]

    def set_value(self, variable, value, index=None, element=None, domain=None):
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
        :param domain: The domain used to check the type, defaults to None.
        :type variable: str
        :type index: int
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.solution.WrongParameters: Index/element parameter must be provided.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **BASIC**/**VECTOR** type.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as BASIC/LAYER/VECTOR.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.domain.WrongComponentType: The components of the **VECTOR** variable are not
        defined as a **BASIC**/**LAYER** type.
        :raise NotDefinedVectorComponentError: The **index**-nh component of the **VECTOR** variable is not available.
        :raise :py:class:`~pycvoa.problem.solution.WrongValue: The value is not valid.
        """
        current_domain = sol_ctrl_check_domain(domain, self.__domain)
        var_type = current_domain.get_variable_type(variable)
        if var_type in BASIC:
            ctrl_index_is_none(variable, index)
            ctrl_element_is_none(variable, element)
            self.set_basic(variable, value, current_domain)
        elif var_type is LAYER:
            ctrl_index_is_none(variable, index)
            ctrl_element_not_none(variable, element)
            self.set_element(variable, element, value, current_domain)
        elif var_type is VECTOR:
            ctrl_index_not_none(variable, index)
            vector_definition = current_domain.get_component_definition(variable)
            if vector_definition in BASIC:
                ctrl_element_is_none(variable, element)
                self.set_component(variable, index, value, current_domain)
            elif vector_definition is LAYER:
                ctrl_element_not_none(variable, element)
                self.set_component_element(variable, index, element, value, current_domain)

    # ** IS METHODS ***

    def is_available(self, variable):
        """ It checks if the input variable has a value in this solution.

        :param variable: The variable to check.
        :returns: True if the variable has a value, otherwise False.
        :type variable: str
        :rtype: bool
        """
        r = False
        if variable in self.__variables.keys():
            r = True
        return r

    def check_variable_type(self, variable, variable_type, domain=None):
        """ It checks if the input variable is equal to the input variable type, taking into account the internal
        solution domain (by default) or a domain passed as parameter.

        :param variable: The variable to check.
        :param variable_type: The variable type to check.
        :param domain: The domain used to check the type, defaults to None.
        :returns: True if the variable is defined as the queried variable type, otherwise False
        :type variable: str
        :type variable_type: INTEGER, REAL, CATEGORICAL, LAYER, VECTOR
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.solution.DomainLevel: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        """
        sol_ctrl_check_variable_availability(variable, self.__variables)
        current_domain = sol_ctrl_check_domain(domain, self.__domain)
        current_type = current_domain.get_variable_type(variable)
        r = False
        if variable_type is BASIC:
            if current_type in BASIC:
                r = True
        else:
            if current_type is variable_type:
                r = True
        return r

    def check_component_type(self, variable, component_type, domain=None):
        """ It checks if the components of the input variable (defined as **VECTOR**) is equal to the input component
        type, taking into account the internal solution domain (by default) or a domain passed as parameter.

        :param variable: The **VECTOR** variable to check.
        :param component_type: The component type to check.
        :param domain: The domain used to check the type, defaults to None.
        :returns: True if the variable is defined as the queried variable type, otherwise False
        :type variable: str
        :type component_type: INTEGER, REAL, CATEGORICAL, LAYER, VECTOR
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.solution.DomainLevel: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in this domain.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        """
        current_domain = sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        current_component_type = current_domain.get_component_type(variable)
        r = False
        if component_type is BASIC:
            if current_component_type in BASIC:
                r = True
        else:
            if current_component_type is component_type:
                r = True
        return r

    def is_available_element(self, variable, element, domain=None):
        """ It checks if the input element of the input **LAYER** variable has a value in this solution, taking into
        account the internal solution domain (by default) or a domain passed as parameter.

        :param variable: The **LAYER** variable to check.
        :param element: The element to check.
        :param domain: The domain used to check the type, defaults to None.
        :returns: True if the element has a value, otherwise False.
        :type variable: str
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **LAYER**.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, LAYER, domain, self.__domain)
        r = False
        if element in self.__variables.get(variable).keys():
            r = True
        return r

    def is_available_component(self, variable, index, domain=None):
        """ It checks if the *index*-nh component of the input **VECTOR** variable has a value in this solution,
        taking into account the internal solution domain (by default) or a domain passed as parameter.

        :param variable: The **VECTOR** variable to check.
        :param index: The index of the component to check.
        :param domain: The domain used to check the type, defaults to None.
        :returns: True if the *index*-nh component has a value, otherwise False.
        :type variable: str
        :type index: int
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.solution.DomainLevel: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, LAYER, domain, self.__domain)
        r = False
        if 0 <= index < len(self.__variables.get(variable)):
            r = True
        return r

    def is_available_component_element(self, variable, index, element, domain=None):
        """ It checks if the input element of the *index*-nh component (defined as **LAYER**) of the input **VECTOR**
        variable has a value in this solution, taking into account the internal solution domain (by default) or
        a domain passed as parameter.

        :param variable: The **VECTOR** variable to check.
        :param index: The index of the component to check.
        :param element: The element to check.
        :param domain: The domain used to check the type, defaults to None.
        :returns: True if the *index*-nh component has a value, otherwise False.
        :type variable: str
        :type index: int
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: bool
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in the domain.
        :raise :py:class:`~pycvoa.problem.solution.WrongComponentType: The component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedVectorComponentError: The component is not available.
        """
        current_domain = sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        sol_ctrl_check_component_type(variable, LAYER, current_domain)
        sol_ctrl_check_component_availability(variable, index, self.__variables)
        r = False
        if element in self.__variables.get(variable)[index].keys():
            r = True
        return r

    # ** GETTERS ***
    def get_basic_value(self, variable, domain=None):
        """ It returns a variable value of a **BASIC** variable of the solution.

        **Precondition:**

        The queried variable must be **INTEGER**, **REAL** or **CATEGORICAL**.

        For **LAYER** and **VECTOR** variables, there are specific getters:

        - :py:meth:`~pycvoa.problem.solution.Solution.get_element_value`,
        - :py:meth:`~pycvoa.problem.solution.Solution.get_component_value`
        - :py:meth:`~pycvoa.problem.solution.Solution.get_component_element_value`

        :param variable: The variable.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The variable value.
        :type variable: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: int, float, str
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as BASIC.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, BASIC, domain, self.__domain)
        return self.__variables.get(variable)

    def get_element_value(self, variable, element, domain=None):
        """ It returns an element value of a **LAYER** variable of the solution.

        :param variable: The **LAYER** variable.
        :param element: The element.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The element value of the **LAYER** variable.
        :type variable: str
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: int, float, str
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedLayerElementError: The element is not defined in the
        **LAYER** variable.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, LAYER, domain, self.__domain)
        sol_ctrl_check_element_availability(variable, element, self.__variables)
        return variable[element]

    def get_basic_component_value(self, variable, index, domain=None):
        """ It returns the **index**-nh value of a **VECTOR** variable defined as **BASIC** of the solution.

        :param variable: The variable.
        :param index: The index of the element to get.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The **index**-nh value of the size **VECTOR** variable.
        :type variable: str
        :type index: int
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: float, int, str
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in the domain.
        :raise :py:class:`~pycvoa.problem.solution.WrongComponentType: The components of the **VECTOR** variable is not
        defined as **BASIC**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedVectorComponentError: The **index**-nh component of the
        **VECTOR** variable is not available.
        """
        current_domain = sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        sol_ctrl_check_component_type(variable, BASIC, current_domain)
        sol_ctrl_check_component_availability(variable, index, self.__variables)
        return self.__variables.get(variable)[index]

    def get_layer_component_value(self, variable, index, element, domain=None):
        """ It returns a **LAYER** element value of the **index**-nh component of a **VECTOR** variable
        of the solution.

        :param variable: The variable.
        :param index: The index of the element to get.
        :param element: The element.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The element value of the **index**-nh position of the **VECTOR** variable.
        :type variable: str
        :type index: int
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: float, int, str
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in the domain.
        :raise :py:class:`~pycvoa.problem.solution.WrongComponentType: The component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedComponentElementError: The element of the **index**-nh
        component of the **VECTOR** variable is not available.
        """
        current_domain = sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        sol_ctrl_check_component_type(variable, LAYER, current_domain)
        sol_ctrl_check_component_availability(variable, index, self.__variables)
        sol_ctrl_check_component_element_availability(variable, element, index, self.__variables)
        return self.__variables.get(variable)[index][element]

    def get_value(self, variable, index=None, element=None, domain=None):
        """ It returns a value of a variable.

        This member has three use cases:

        - BASIC TYPE: Only the **BASIC** variable must be provided.
        - LAYER TYPE: A **LAYER** variable and the element name must be provided.
        - VECTOR TYPE: A **VECTOR** variable and the index of the component must be provided. If the components are
        defined as **LAYER**, the element must be also provided.

        :param variable: The variable.
        :param index: The index of a position of a **VECTOR** variable, defaults to None.
        :param element: The element of a **LAYER** variable, defaults to None.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The value.
        :type variable: str
        :type index: int
        :type element: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: int, float, str
        :raise :py:class:`~pycvoa.problem.domain.NotDefinedVariable: The variable is not defined in the domain.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as BASIC.
        The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.WrongParameters: The element of a **LAYER** variable is not provided.
        The index of a component of a **VECTOR** variable is not provided. The element of component of a **VECTOR**
        variable defined as **LAYER** is not provided.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedLayerElementError: The element is not defined in the
        **LAYER** variable.
        :raise :py:class:`~pycvoa.problem.domain.WrongVariableType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.solution.WrongComponentType: The components of the **VECTOR** variable is not
        defined as **BASIC**. The component type is not defined as **LAYER**.
        :raise :py:class:`~pycvoa.problem.solution.NotDefinedVectorComponentError: The **index**-nh component of the
        **VECTOR** variable is not available.
        """
        current_domain = sol_ctrl_check_domain(domain, self.__domain)
        var_type = current_domain.get_variable_type(variable)
        r = None
        if var_type in BASIC:
            ctrl_index_is_none(variable, index)
            ctrl_element_is_none(variable, element)
            r = self.get_basic_value(variable, current_domain)
        elif var_type is LAYER:
            ctrl_index_is_none(variable, index)
            ctrl_element_not_none(variable, element)
            r = self.get_element_value(variable, element, current_domain)
        elif var_type is VECTOR:
            ctrl_index_not_none(variable, index)
            vector_definition = current_domain.get_component_definition(variable)
            if vector_definition in BASIC:
                ctrl_element_is_none(variable, element)
                r = self.get_basic_component_value(variable, index, current_domain)
            elif vector_definition is LAYER:
                ctrl_element_not_none(variable, element)
                r = self.get_layer_component_value(variable, index, element, current_domain)
        return r

    def get_vector_size(self, variable, domain=None):
        """ It returns the size of a **VECTOR** variable of the solution. It is useful to access the values
        of the **VECTOR** variable sequentially.

        :param variable: The **VECTOR** variable name.
        :param domain: The domain used to check the type, defaults to None.
        :returns: The size of the **VECTOR** variable.
        :type variable: str
        :type domain: :py:class:`~pycvoa.problem.domain.Domain
        :rtype: int
        :raise :py:class:`~pycvoa.problem.solution.NotSpecifiedDomain: The domain is not set.
        :raise :py:class:`~pycvoa.problem.solution.WrongType: The variable is not defined as **VECTOR**.
        :raise :py:class:`~pycvoa.problem.solution.NotInSolutionError: The variable is not in this solution.
        """
        sol_ctrl_check_var_avail_dom_type(variable, self.__variables, VECTOR, domain, self.__domain)
        return len(self.__variables.get(variable))

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
