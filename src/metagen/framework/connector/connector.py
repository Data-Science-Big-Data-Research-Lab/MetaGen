"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import inspect
from typing import Any, Dict, Tuple

import metagen.framework.domain as definitions
import metagen.framework.solution as types
from metagen.framework.domain.bounds import BaseClass
from metagen.framework.solution.bounds import BaseTypeClass


class BaseConnector:

    """
    A connector class that maps domain types to solution types and provides type conversion functions.

    :ivar _domain_to_solution: A dictionary mapping domain types to solution types.
    :vartype _domain_to_solution: Dict[BaseClass, BaseTypeClass]
    :ivar _solution_to_domain: A dictionary mapping solution types to domain types.
    :vartype _solution_to_domain: Dict[BaseTypeClass, BaseClass]
    :ivar _solution_to_builtin: A dictionary mapping solution types to built-in types.
    :vartype _solution_to_builtin: Dict[BaseTypeClass, Any]
    :ivar _builtin_to_solution: A dictionary mapping built-in types to solution types.
    :vartype _builtin_to_solution: Dict[Any, BaseTypeClass]

    :meth:`__init__`:
        Initializes the BaseConnector object.

    :meth:`register`:
        Registers a domain type, solution type, and built-in type.

    :meth:`get_type`:
        Retrieves the solution type based on the input definition.

    :meth:`get_definition`:
        Retrieves the domain type based on the input solution type.

    :meth:`get_builtin`:
        Retrieves the built-in type based on the input solution type.
    """

    def __init__(self) -> None:

        self._domain_to_solution: Dict[BaseClass, BaseTypeClass] = {}
        self._solution_to_domain: Dict[BaseTypeClass, BaseClass] = {}
        self._solution_to_builtin: Dict[BaseTypeClass, Any] = {}
        self._builtin_to_solution: Dict[Any, BaseTypeClass] = {}

        self.register(definitions.BaseDefinition, types.Solution, dict)
        self.register(definitions.IntegerDefinition, types.Integer, int)
        self.register(definitions.RealDefinition, types.Real, float)
        self.register(definitions.CategoricalDefinition,
                      types.Categorical, str)
        self.register(definitions.DynamicStructureDefinition,
                      (types.Structure, 'dynamic'), list)
        self.register(definitions.StaticStructureDefinition,
                      (types.Structure, 'static'), list)

    def register(self, domain_type: type[BaseClass], solution_type: type[BaseTypeClass | types.Solution] | Tuple[type[BaseTypeClass | types.Solution], str], builtin_type: type[int | float | str | list | dict]):
        """
        Registers a domain type, solution type, and built-in type.

        :param domain_type: The domain type to register.
        :type domain_type: type[`BaseClass`]
        :param solution_type: The solution type to register.
        :type solution_type: type[BaseTypeClass | `types.Solution`] or Tuple[type[BaseTypeClass | `types.Solution`], str]
        :param builtin_type: The built-in type to register.
        :type builtin_type: type[int | float | str | list | dict]
        """

        self._domain_to_solution[domain_type] = solution_type
        self._solution_to_domain[solution_type] = domain_type
        self._solution_to_builtin[solution_type] = builtin_type
        self._builtin_to_solution[builtin_type] = solution_type

    def get_type(self, definition: definitions.Base | int | float | str | list | dict | type[definitions.Base | int | float | str | list | dict]) -> type[BaseTypeClass]:
        """
        Retrieves the solution type based on the input definition.

        :param definition: The definition object or type for which to retrieve the solution type.
        :type definition: definitions.Base or int or float or str or list or dict or type[definitions.Base or int or float or str or list or dict]
        :return: The corresponding solution type.
        :rtype: type[`BaseTypeClass`]
        :raises ValueError: If the definition is not registered in the connector.
        """
        try:
            definition_class: type[definitions.Base | int | float | str | list | dict] = definition if inspect.isclass(definition) else definition.__class__
            if issubclass(definition_class, definitions.BaseStructureDefinition):
                return self._domain_to_solution[definition_class][0]
            if issubclass(definition_class, definitions.Base):
                return self._domain_to_solution[definition_class]
            elif issubclass(definition_class, (int, float, str, dict)):
                return self._builtin_to_solution[definition_class]
            elif issubclass(definition_class, list):
                return self._builtin_to_solution[definition_class][0]
            else:
                raise ValueError(
                    f"The object {definition} must be an instance of Base definition or builtin.")
        except KeyError:
            raise ValueError(
                f"The class {definition} has not been registered in the connector.")

    def get_definition(self, solution_type: types.BaseType | types.Solution | type[types.BaseType | types.Solution] | Tuple[type[types.BaseType], str]) -> type[BaseClass]:
        """
        Retrieves the domain type based on the input solution type.

        :param solution_type: The solution type or type object for which to retrieve the domain type.
        :type solution_type: `types.BaseType` | `types.Solution` | type[`types.BaseType` | `types.Solution`] |
                             Tuple[type[`types.BaseType`], str]
        :return: The corresponding domain type.
        :rtype: type[BaseClass]
        :raises ValueError: If the solution type is not registered in the connector.
        """
        try:
            solution_type = solution_type if inspect.isclass(
                solution_type) or isinstance(solution_type, tuple) else solution_type.__class__

            if isinstance(solution_type, tuple) or issubclass(solution_type, types.BaseType) or issubclass(
                    solution_type, types.Solution): 
                return self._solution_to_domain[solution_type]
            else:
                raise ValueError(
                    f"The class {solution_type} must be an instance of BaseType.")
        except KeyError:
            raise ValueError(
                f"The object {solution_type} has not been registered in the connector.")

    def get_builtin(self, solution_type: types.BaseType) -> type[int | float | str | list | dict]:
        """
        Retrieves the built-in type based on the input solution type.

        :param solution_type: The solution type for which to retrieve the built-in type.
        :type solution_type: `types.BaseType`
        :return: The corresponding built-in type.
        :rtype: type[int | float | str | list | dict]
        :raises ValueError: If the solution type is not registered in the connector.
        """
        try:
            solution_type = solution_type if inspect.isclass(
                solution_type) else solution_type.__class__
            if issubclass(solution_type, types.BaseType):
                return self._solution_to_builtin[solution_type]
            else:
                raise ValueError(
                    f"The object {solution_type} must be an instance of BaseType.")
        except KeyError:
            raise ValueError(
                f"The object {solution_type} has not been registered in the connector.")
