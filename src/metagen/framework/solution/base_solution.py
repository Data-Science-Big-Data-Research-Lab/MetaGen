from __future__ import annotations

import random
import sys
from collections.abc import Callable
from typing import TYPE_CHECKING, KeysView, ValuesView, Dict

import metagen.framework.solution as types

if TYPE_CHECKING:
    from metagen.framework import BaseConnector, Domain
    from metagen.framework.domain import Base, BaseDefinition
    from metagen.framework.solution.literals import (InputValue, SolLayer)
    from metagen.framework.solution.bounds import BaseTypeClass, SolutionClass


class Solution:

    def __init__(self, definition: Domain | BaseDefinition, best=False, connector=None):
        """ 
        It is the default and unique, constructor builds an empty solution with the worst fitness value
        (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
        :py:class:`~metagen.problem.facades.Domain` object can be passed to check the variable definitions internally and,
        therefore boost the Solution fucntionality.

        **Example:**

        .. code-block:: python

            >>> from metagen.framework import Domain, Solution
            >>> domain = Domain()
            >>> domain.define_integer('example', 0, 10)
            >>> best_solution  = Solution(domain, best=True)
            >>> best_solution.fitness
            0.0
            >>> best_solution
            F = 0     {example = 3}
            >>> worst_solution  = Solution(domain)
            >>> worst_solution.fitness
            1.7976931348623157e+308
            >>> worst_solution
            F = 1.7976931348623157e+308     {example = 5}
            >>> boosted_solution = Solution(domain)
            >>> boosted_solution
            F = 1.7976931348623157e+308     {example = 1}

        :param definition: The Domain of the solution. If the definition is an instance of Base the connector must be provided.
        :param best: If True the individual will be built with the best fitness function; otherwise the worst, defaults to False.
        :param connector: The connector to be used by the class, if None the definition must be a Domain instance.
        :type definition: :py:class:`~metagen.framework.Domain`
        :type best: bool
        :type connector: :py:class:`~metagen.framework.BaseConnector`
        :vartype __definition: :py:class:`~metagen.problem.facades.Domain`
        :vartype value: dict
        :vartype fitness: float
        """
        self.connector = connector or definition.get_connector()
        self.__definition: BaseDefinition = definition.get_core(
        ) if definition.__class__.__name__ == 'Domain' else definition

        self.value: Dict[str, types.BaseType] = {}
        self.fitness: float = sys.float_info.min if best else sys.float_info.max

        self.initialize()

    def get_variables(self) -> Dict[str, types.BaseType]:
        """ It obtains the defined variables which constitutes the solution.

        :returns: The defined variables.
        :rtype: :py:class:`~metagen.control.legacy.SolStructure`
        """
        return self.value

    def get_definition(self) -> BaseDefinition:
        """ It obtains the defined Domain from the solution.

        :returns: The defined Domain.
        :rtype: :py:class:`~metagen.problem.facades.Domain`
        """
        return self.__definition

    def set(self, variable: str, value: InputValue | types.BaseType) -> None:
        """
        Sets the value of a variable in the solution.

        :param variable: The name of the variable to set.
        :type variable: str
        :param value: The value to set the variable to.
        :type value: InputValue
        :raises TypeError: If the value's type is not supported by the solution.

        .. note::
            This method sets the value of a variable in the solution. The type of the value determines how the variable is stored internally. If the value is an integer, it is stored as an integer variable. If it is a float, it is stored as a real variable. If it is a string, it is stored as a categorical variable. If it is a list, it is stored as a vector variable. If it is a dictionary, it is stored as a sub-solution variable. If it is any other type, it must be a pre-defined type for compatibility with previously defined solutions.

        .. seealso::
            :func:`_set_sub_solution`
            :func:`_set_value`
        """

        if isinstance(value, (int, float, str, list)):
            base_type_class: type[BaseTypeClass] = self.get_connector().get_type(
                value)
            variable_definition: Base = self.get_definition().get(variable)

            variable_definition.check_value(value)

            type_value: types.BaseType = base_type_class(
                variable_definition, self.get_connector())
            type_value.set(value)
            self._set_value(variable, type_value)
        elif isinstance(value, dict):
            self._set_sub_solution(variable, value)
        elif types.BaseType:  # Compatibility with already defined types
            self._set_value(variable, value)
        else:
            raise TypeError(
                f"The type {type(value)} is not supported by the solution.")

    def get(self, variable: str) -> types.BaseType:
        """
        Returns the value of a variable in the solution.

        :param variable: The name of the variable to get.
        :type variable: str
        :return: The value of the variable.
        :rtype: InputValue

        .. note::
            This method returns the value of a variable in the solution. The type of the value depends on how the variable is stored internally. If it is an integer variable, the method returns an integer. If it is a real variable, it returns a float. If it is a categorical variable, it returns a string. If it is a vector variable, it returns a list. If it is a sub-solution variable, it returns a dictionary.

        .. seealso::
            :func:`set`
        """

        return self.value[variable]

    def get_connector(self) -> BaseConnector:
        """
        Get the connector used by the Solution.

        :return: The connector object.
        :rtype: BaseConnector
        """
        return self.connector

    def evaluate(self, fitness_func: Callable[[Solution], float]) -> None:
        """
        Evaluate the fitness of the Solution using the provided fitness function.

        :param fitness_func: The fitness function to evaluate the object's fitness.
        :type fitness_func: Callable[[Solution], float]
        :return: None
        """
        self.set_fitness(fitness_func(self))

    def set_fitness(self, fitness: float) -> None:
        """
        Set the fitness of the Solution to the given value.

        :param fitness: The fitness value to set.
        :type fitness: float
        :return: None
        """
        self.fitness = fitness

    def get_fitness(self) -> float:
        """
        Get the fitness value of the Solution.

        :return: The fitness value.
        :rtype: float
        """

        return self.fitness

    def is_available(self, variable: str) -> bool:
        """
        Checks if a variable is available in the solution.

        :param variable: The name of the variable to check.
        :type variable: str
        :return: True if the variable is available, False otherwise.
        :rtype: bool

        .. note::
            This method checks if a variable is available in the solution. It returns True if the variable is present in the solution's variables, and False otherwise.

        .. seealso::
            :func:`get_variables`
            :func:`get`
        """

        return variable in self.get_variables()

    def keys(self) -> KeysView:
        """
        Get the keys of the solution value dict.

        :return: A KeysView with the keys of the solution
        """

        return self.get_variables().keys()

    def values(self) -> ValuesView:
        """
        Get the values of the solution value dict.

        :return: A ValuesView with the keys of the solution
        """
        return self.get_variables().values()

    def initialize(self):
        """
        Initializes the solution with random values defined in its domain.

        .. note::
            This method initializes the solution with random values within its domain. It iterates through all the variables in the domain and generates a random value according to their definition. The generated value is then set as the initial value of the variable in the solution.

        .. seealso::
            :func:`_initialize`
            :func:`get_definition`
            :func:`set`
        """
        domain: BaseDefinition = self.get_definition()
        for variable in domain.variable_list():
            definition = domain.get(variable)
            self._initialize(variable, definition)

    def mutate(self, alterations_number: int = None):
        """
        Modify a random subset of the solution's variables calling its mutate method.

        :param alterations_number: The number of variables to mutate at the first level. If not specified, a random number between 1 and the total number of variables will be chosen.
        :type alterations_number: int, optional

        .. seealso::
            :func:`get_variables`
            :func:`initialize`
        """
        variables = self.get_variables().keys()
        alterations_number = alterations_number or random.randint(
            1, len(variables))
        altered_variables = set(random.sample(
            list(variables), alterations_number))

        for variable in altered_variables:
            value = self.get(variable)
            value.mutate()

            self.set(variable, value)

    # ** PRIVATE FUNCTIONS ***

    def _set_value(self, key: str, value: types.BaseType | Solution):
        """
        Sets the value of a variable in the object's internal dictionary.

        :param key: The key of the variable to set.
        :type key: str
        :param value: The value to set the variable to.
        :type value: types.BaseType
        :return: None
        :raises: None

        .. note::
            This method is intended for internal use only and should not be called directly from outside the object.
        """
        self.value[key] = value

    # ** LAYER TYPE METHODS ***
    def _set_sub_solution(self, variable: str, value: SolLayer):
        """
        Sets the value of a sub-solution variable.

        :param variable: The name of the sub-solution variable to set.
        :type variable: str
        :param value: A dictionary containing the values of the sub-solution variables.
        :type value: SolLayer

        .. note::
            This method sets the value of a sub-solution variable in the solution. It creates a new `Solution` object for the sub-solution and iterates through the key-value pairs in the input dictionary to set the values of the sub-solution variables. The sub-solution is then set as the value of the sub-solution variable in the current solution.

        .. seealso::
            :func:`_set_value`
            :func:`set`
        """
        variable_definition = self.get_definition().get(variable)

        solution_definition: type[SolutionClass] = self.get_connector().get_type(
            value)
        subsolution: Solution = solution_definition(
            variable_definition, connector=self.get_connector())
        subsolution.value = {}

        for k, v in value.items():
            subsolution.set(k, v)

        self._set_value(variable, subsolution)

    def _initialize(self, variable: str, definition: Base) -> None:
        """
        Initializes a variable with depending upon its definition.

        :param variable: The name of the variable to initialize.
        :type variable: str
        :param definition: The definition object for the variable.
        :type definition: BaseDefinition
        :return: None

        .. note::
            This method initializes a variable with the given definition object. It first converts the definition object into a corresponding variable type object, then calls the :meth:`initialize` method of the variable type object to initialize it, and finally sets the value of the variable using the :meth:`set` method.

        .. seealso::
            :meth:`initialize`
            :meth:`set`
        """
        type_class: type[BaseTypeClass] = self.get_connector().get_type(
            definition)
        variable_definition = self.get_definition().get(variable)
        self.set(variable, type_class(
            variable_definition, connector=self.get_connector()))

    # ** SET VALUE METHOD

    def __str__(self):
        """ String representation of a :py:class:`~metagen.individual.Individual` object.
        """
        res = "F = " + str(self.fitness) + "\t{"
        count = 1
        for variable in sorted(self.value):
            res += str(variable) + " = " + str(self.value[variable])
            if count < len(self.get_variables()):
                res += " , "
            count += 1
        res += "}"
        return res

    def __repr__(self):
        return str(self)

    # ** SET INTERNAL METHODS **

    def __setitem__(self, variable, value):
        """
        Sets the value of a variable given its name.
        :param variable: The name of the variable.
        :type variable: str
        :param value: The new value of the variable.
        :type value: InputValue
        """
        self.set(variable, value)

    def __getitem__(self, variable):
        """
        Returns the value of a variable given its name.
        :param variable: The name of the variable.
        :type variable: str
        :return: The value of the variable.
        :rtype: InputValue
        """
        return self.value[variable].value

    def __iter__(self):
        """
        Returns an iterator over the names of the variables in the solution.
        :return: An iterator over the variable names.
        :rtype: Iterator[str]
        """
        return iter(self.get_variables())

    def __eq__(self, other):
        """ Equity function of the :py:class:`~metagen.framework.Solution` class. An
        :py:class:`~metagen.individual.Individual` object is equal to another :py:class:`~metagen.framework.Solution`
        object if they have the same variables with the same values.
        """
        res = True

        if not isinstance(other, Solution):
            res = False
        else:
            i = 0
            if self.get_variables().keys() != other.get_variables().keys():
                res = False
            else:
                keys = list(self.get_variables().keys())
                while i < len(keys) and res:
                    vf = self.get(keys[i])
                    vo = other.get(keys[i])
                    res = vf == vo
                    i += 1
        return res

    def __ne__(self, other):
        """ Non Equity function of the :py:class:`~metagen.individual.Individual` class. An
        :py:class:`~metagen.individual.Individual` object is not equal to another :
        py:class:`~metagen.individual.Individual` object if they do not have the same variables with the same values.
        """
        return not self.__eq__(other)

    def __hash__(self):
        """ Hash function for :py:class:`~metagen.individual.Individual` objects. It is necessary for set structure
        management.
        """
        return hash((self.get_variables().__hash__, self.fitness))

    def __lt__(self, other):
        """ *Less than* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is less
        than another individual **B** if the fitness value of **A** is strictly less than the fitness value of **B**.
        It is necessary for set structure management.
        """
        return self.fitness < other.fitness

    def __le__(self, other):
        """ *Less equal* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is less or
        equal than another individual **B** if the fitness value of **A** is less or equal than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.fitness <= other.fitness

    def __gt__(self, other):
        """ *Greater than* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is
        greater than another individual **B** if the fitness value of **A** strictly greater than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.fitness > other.fitness

    def __ge__(self, other):
        """ *Greater equal* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is
        greater or equal than another individual **B** if the fitness value of **A** greater or equal than the
        fitness value of **B**. It is necessary for set structure management.
        """
        return self.fitness >= other.fitness
