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
from typing import Any, Dict, Optional, Tuple, TypeAlias, Union, cast

import metagen.framework.domain as definitions
import metagen.framework.solution as types


#: What the registry stores for a solution type. Usually the class itself; for a
#: structure, the class paired with a discriminator, because one builtin -- a list --
#: maps to both the static and the dynamic definition.
SolutionEntry: TypeAlias = Union[
    type[Union[types.BaseType, types.Solution]],
    Tuple[type[Union[types.BaseType, types.Solution]], str]]

#: The Python types a domain variable can be expressed as.
BuiltinType: TypeAlias = type[Union[int, float, str, list, dict]]


def _solution_class(entry: SolutionEntry) -> type[types.BaseType | types.Solution]:
    """The class an entry stands for, dropping the structure discriminator."""
    return entry[0] if isinstance(entry, tuple) else entry


class BaseConnector:
    """
    A connector class that maps domain types to solution types and provides type conversion functions.

    :param _domain_to_solution: A dictionary mapping domain types to solution types.
    :type _domain_to_solution: Dict[definitions.Base, types.BaseType]
    :param _solution_to_domain: A dictionary mapping solution types to domain types.
    :type _solution_to_domain: Dict[types.BaseType, definitions.Base]
    :param _solution_to_builtin: A dictionary mapping solution types to built-in types.
    :type _solution_to_builtin: Dict[types.BaseType, Any]
    :param _builtin_to_solution: A dictionary mapping built-in types to solution types.
    :type _builtin_to_solution: Dict[Any, types.BaseType]
    """

    def __init__(self) -> None:
        """
        Initializes the BaseConnector object.

        :return: None
        """

        # Classes mapped to classes, not instances to instances. The annotations said
        # the latter, and the unbound type variables that used to stand in for them
        # turned everything into Any, so nothing checked (P-11).
        self._domain_to_solution: Dict[type[definitions.Base], SolutionEntry] = {}
        self._solution_to_domain: Dict[SolutionEntry, type[definitions.Base]] = {}
        self._solution_to_builtin: Dict[SolutionEntry, BuiltinType] = {}
        self._builtin_to_solution: Dict[BuiltinType, SolutionEntry] = {}

        self.register(definitions.BaseDefinition, types.Solution, dict)
        self.register(definitions.IntegerDefinition, types.Integer, int)
        self.register(definitions.RealDefinition, types.Real, float)
        self.register(definitions.CategoricalDefinition,
                      types.Categorical, str)
        self.register(definitions.DynamicStructureDefinition,
                      (types.Structure, 'dynamic'), list)
        self.register(definitions.StaticStructureDefinition,
                      (types.Structure, 'static'), list)

    def register(self, domain_type: type[definitions.Base], solution_type: SolutionEntry,
                 builtin_type: BuiltinType) -> None:
        """
        Registers a domain type, solution type, and built-in type.

        :param domain_type: The domain type to register.
        :type domain_type: type[`definitions.Base`]
        :param solution_type: The solution type to register.
        :type solution_type: type[types.BaseType | `types.Solution`] or Tuple[type[types.BaseType | `types.Solution`], str]
        :param builtin_type: The built-in type to register.
        :type builtin_type: type[int | float | str | list | dict]
        :return: None
        """

        self._domain_to_solution[domain_type] = solution_type
        self._solution_to_domain[solution_type] = domain_type
        self._solution_to_builtin[solution_type] = builtin_type
        self._builtin_to_solution[builtin_type] = solution_type

    def get_type(self, definition: definitions.Base | int | float | str | list | dict | type[definitions.Base | int | float | str | list | dict]) -> type[types.BaseType | types.Solution]:
        """
        Retrieves the solution type based on the input definition.

        :param definition: The definition object or type for which to retrieve the solution type.
        :type definition: definitions.Base or int or float or str or list or dict or type[definitions.Base or int or float or str or list or dict]
        :return: The corresponding solution type.
        :rtype: type[`types.BaseType` | `types.Solution`]
        :raises ValueError: If the definition is not registered in the connector.
        """
        try:
            definition_class: type = definition if inspect.isclass(definition) else type(definition)
            # Structures used to need a branch of their own to drop the discriminator
            # with [0]; _solution_class does that for every entry, so the structure
            # case and the list case stopped being different from the general ones.
            # Every registered structure definition is a Base as well: the mixin
            # BaseStructureDefinition is not, but nothing is registered under it.
            if issubclass(definition_class, definitions.Base):
                return _solution_class(self._domain_to_solution[definition_class])
            elif issubclass(definition_class, (int, float, str, list, dict)):
                return _solution_class(self._builtin_to_solution[definition_class])
            else:
                raise ValueError(
                    f"The object {definition} must be an instance of Base definition or builtin.")
        except KeyError:
            raise ValueError(
                f"The class {definition} has not been registered in the connector.")

    def get_definition(self, solution_type: types.BaseType | types.Solution | SolutionEntry) -> type[definitions.Base]:
        """
        Retrieves the domain type based on the input solution type.

        Takes an instance, a class, or a class paired with its discriminator. A
        structure is registered under a discriminator, because a list stands for both
        the static and the dynamic definition, and this used to look an instance up by
        its bare class and fail on every structure (F-36). An instance carries its own
        definition, which says which of the entries registered for its class is the
        right one; a bare class alone cannot, so it has to come with its discriminator.

        :param solution_type: The solution type or type object for which to retrieve the domain type.
        :type solution_type: `types.BaseType` | `types.Solution` | type[`types.BaseType` | `types.Solution`] |
                             Tuple[type[`types.BaseType`], str]
        :return: The corresponding domain type.
        :rtype: type[definitions.Base]
        :raises ValueError: If the solution type is not registered in the connector, or
            if a bare class is registered under several discriminators.
        """
        # A local rather than reassigning the parameter, which arrives as an
        # instance or as a class and would otherwise hold both types at once.
        # The cast says what inspect.isclass established and mypy cannot follow: what
        # is left here is an instance, or nothing.
        instance = cast(Optional[Union[types.BaseType, types.Solution]],
                        None if inspect.isclass(solution_type) or isinstance(solution_type, tuple)
                        else solution_type)
        key: SolutionEntry = cast(SolutionEntry, (
            solution_type if instance is None else type(instance)))

        if not issubclass(_solution_class(key), (types.BaseType, types.Solution)):
            raise ValueError(
                f"The class {solution_type} must be an instance of BaseType.")

        if key in self._solution_to_domain:
            return self._solution_to_domain[key]

        # Not a key on its own: look at what is registered under a discriminator
        # for this class. Only reachable with a bare class or an instance, since a
        # tuple key that is missing is simply unregistered.
        registered = {entry: domain for entry, domain in self._solution_to_domain.items()
                      if _solution_class(entry) is key}
        if instance is not None:
            # The instance knows: its own definition is an instance of one of them.
            definition_class = type(instance.get_definition())
            if definition_class in registered.values():
                return definition_class
        elif len(registered) == 1:
            return next(iter(registered.values()))
        elif registered:
            raise ValueError(
                f"The class {key} is registered under discriminators that map to "
                f"different definitions, {sorted(d.__name__ for d in registered.values())}: "
                f"pass the class paired with its discriminator, or an instance.")
        raise ValueError(
            f"The object {key} has not been registered in the connector.")

    def get_builtin(self, solution_type: types.BaseType | types.Solution | SolutionEntry) -> BuiltinType:
        """
        Retrieves the built-in type based on the input solution type.

        Takes an instance, a class, or a class paired with its discriminator. A
        structure is registered under a discriminator, because a list stands for both
        the static and the dynamic definition, and this used to look a structure up by
        its bare class and fail on every one (F-34). When the bare class is not a key,
        the entries registered under a discriminator for that class are consulted:
        they all map to the same builtin, so no discriminator is needed to answer.

        :param solution_type: The solution type for which to retrieve the built-in type.
        :type solution_type: `types.BaseType` | `types.Solution` | type | Tuple[type, str]
        :return: The corresponding built-in type.
        :rtype: type[int | float | str | list | dict]
        :raises ValueError: If the solution type is not registered in the connector,
            or if it is registered under discriminators that map to different builtins.
        """
        # Same cast as in get_definition: the parameter arrives as an instance or as
        # a class, and mypy cannot tell which of the two type() is applied to.
        key: SolutionEntry
        if isinstance(solution_type, tuple):
            key = cast(SolutionEntry, (
                solution_type[0] if inspect.isclass(solution_type[0])
                else type(solution_type[0]), solution_type[1]))
        else:
            key = cast(SolutionEntry, (
                solution_type if inspect.isclass(solution_type)
                else type(solution_type)))

        if not issubclass(_solution_class(key), (types.BaseType, types.Solution)):
            raise ValueError(
                f"The object {solution_type} must be an instance of BaseType.")

        if key in self._solution_to_builtin:
            return self._solution_to_builtin[key]

        # Not a key on its own: look at what is registered under a discriminator
        # for this class. Only reachable with a bare class, since a tuple key that
        # is missing is simply unregistered.
        registered = {builtin for entry, builtin in self._solution_to_builtin.items()
                      if _solution_class(entry) is key}
        if len(registered) == 1:
            return registered.pop()
        if registered:
            raise ValueError(
                f"The class {key} is registered under discriminators that map to "
                f"different builtins, {sorted(b.__name__ for b in registered)}: pass "
                f"the class paired with its discriminator.")
        raise ValueError(
            f"The object {key} has not been registered in the connector.")
