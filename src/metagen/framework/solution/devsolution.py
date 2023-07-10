from typing import Any

from .base_solution import Solution
from .types.base import BaseType


class DevSolution(Solution):
    """ This class is an abstraction of a solution for a meta-heuristic that a third party provides.

    The default and unique, constructor builds an empty solution with the worst fitness value
    (:math:`best=False`, by default) or the best fitness value (:math:`best=False`). Furthermore, a
    :py:class:`~metagen.framework.Domain` object can be passed to check the variable definitions internally and,
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
    """

    def check(self, variable, value=None):
        """Check if a variable is defined in the domain and if the value is valid.

        :param variable: Name of the variable to check.
        :type variable: str
        :param value: Value to check for the variable. Optional.
        :type value: int | float | str | list | dict | Base | None
        :raises ValueError: If the variable is not available in the solution or not defined in the domain or the assigned value is not valid.
        """

        if not self.get_definition().is_variable(variable):
            raise ValueError(
                f"The variable {variable} does not exists in the Domain.")

        if not isinstance(value, BaseType) and value is not None and not self.get_definition().get(variable).check_value(value):
            raise ValueError(
                f"The value {value} assigned to the variable {variable} is not valid. {self.get_definition().get(variable)}")

    def get(self, variable: str) -> Any:
        """
        Returns the value of a variable in the solution.

        :param variable: The name of the variable to get.
        :type variable: str
        :return: The value of the variable.
        :rtype: InputValue

        :raises ValueError: If the variable does not exist in the solution or is not defined in the definition.

        .. note::
            This method returns the value of a variable in the solution. The type of the value depends on how the variable is stored internally. If it is an integer variable, the method returns an integer. If it is a real variable, it returns a float. If it is a categorical variable, it returns a string. If it is a vector variable, it returns a list. If it is a sub-solution variable, it returns a dictionary.

        .. seealso::
            :func:`_get_value`
            :func:`set`
        """
        self.check(variable)

        return super().get(variable)

    def set(self, variable: str, value: Any):
        """
        Sets the value of a variable in the solution.

        :param variable: The name of the variable to set.
        :type variable: str
        :param value: The value to set the variable to.
        :type value: InputValue
        :raises ValueError: If the variable does not exist in the solution, the variable is not defined in the definition or the value does not meets the definition conditions.

        .. note::
            This method sets the value of a variable in the solution. The type of the value determines how the variable is stored internally. If the value is an integer, it is stored as an integer variable. If it is a float, it is stored as a real variable. If it is a string, it is stored as a categorical variable. If it is a list, it is stored as a vector variable. If it is a dictionary, it is stored as a sub-solution variable. If it is any other type, it must be a pre-defined type for compatibility with previously defined solutions.

        .. seealso::
            :func:`_set_integer`
            :func:`_set_real`
            :func:`_set_categorical`
            :func:`_set_vector`
            :func:`_set_sub_solution`
            :func:`_set_value`
        """
        self.check(variable, value)

        return super().set(variable, value)
