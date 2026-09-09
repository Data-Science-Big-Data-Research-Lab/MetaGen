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
from typing import Any, Callable, cast

from metagen.framework.domain.core import (BaseStructureDefinition,
                                           DynamicStructureDefinition,
                                           StaticStructureDefinition)
from metagen.framework.solution.literals import InputValue, SolVector
from metagen.framework.solution import Solution
from metagen.framework.solution.base_solution import builtin_value

from .base import BaseType
from metagen.framework.rng import get_rng


class Structure(BaseType):

    def __init__(self, definition: DynamicStructureDefinition | StaticStructureDefinition,
                 connector=None):
        """
        The Real class inherits from the BaseType class and represents a Real variable.

        :param definition: The structure's definition, static or dynamic. Declared as the
            two concrete classes and not as their mixin ``BaseStructureDefinition``,
            which is not a ``Base`` and so is not what ``BaseType`` accepts (P-11).
        :type definition: DynamicStructureDefinition or StaticStructureDefinition
        """

        super(Structure, self).__init__(definition, connector)

    def get_definition(self) -> DynamicStructureDefinition | StaticStructureDefinition:
        """
        The definition this structure was built from, static or dynamic.

        Narrows what :py:meth:`~metagen.framework.solution.types.base.BaseType.get_definition`
        declares. Two things need it: ``get_base`` lives on the structure definitions
        and not on ``Base``, and the attribute tuples of the two have different widths,
        five for the dynamic one and three for the static (P-11).

        :return: The definition of this structure.
        :rtype: DynamicStructureDefinition or StaticStructureDefinition
        """
        return cast(DynamicStructureDefinition | StaticStructureDefinition,
                    super().get_definition())

    def _new_element(self) -> BaseType | Solution:
        """
        A fresh element of this structure, built from its base definition.

        The class comes from the connector's registry, so it is a Solution when the
        base is a group and a BaseType subclass otherwise. Both are constructed the
        same way, but their declared parameter types differ and mypy cannot follow a
        runtime registry, hence the cast to the shape they share (P-11).

        :return: A new element, uninitialized.
        :rtype: BaseType or Solution
        """
        base = self.get_definition().get_base()
        element_class = cast(Callable[..., BaseType | Solution],
                             self.get_connector().get_type(base))
        return element_class(base, connector=self.get_connector())

    def check(self, value: Any) -> None:
        """
        Check that a single element is valid for the base definition of this Structure.

        This is about one element: what the whole list may hold, and how long it may
        be, is checked by set().

        :param value: The element to check.
        :raises ValueError: if the value does not correspond to the base definition.
        """

        if not isinstance(value, BaseType) and not self.get_definition().get_base().check_value(value):
            raise ValueError(
                f"The value {value} provided is not valid for definition: {self.get_definition()}")

    def is_available(self, index: int) -> bool:
        """ It checks if the *index*-nh component of the input **VECTOR** variable has a value in this solution,
        taking into account the internal solution legacy_domain (by default) or a legacy_domain passed as parameter.

        :param index: The index of the component to check.
        :returns: True if the *index*-nh component has a value, otherwise False.
        :type index: int
        :rtype: bool
        """
        r = False
        if 0 <= index < len(cast(SolVector, super().value)):
            r = True
        return r

    def initialize(self) -> None:
        """
        Initializes the Structure according to the definition provided. If the definition is of type DynamicStructureDefinition, a rs size is chosen within the min_size and max_size range (inclusive), with an optional step size. If the definition is of type StaticStructureDefinition, the provided size value is used instead.

        For each position in the Structure, a new instance of the BaseType class is created based on the base type provided by the definition. The `initialize()` method is then called on this instance to set a value for it, and the instance is appended to the Structure. 

        .. seealso::
            :meth:`get_definition`
        """

        size = 0

        # Bound to a local so that isinstance narrows it: the two definitions carry
        # attribute tuples of different widths, and asking get_definition() again
        # inside the branch throws that narrowing away (P-11).
        definition = self.get_definition()

        if isinstance(definition, DynamicStructureDefinition):
            _, min_size, max_size, step_size, _ = definition.get_attributes()

            # max_size + 1, because randrange excludes its upper bound while
            # check_length and _resize both accept min <= length <= max (F-19).
            size = get_rng().randrange(min_size, max_size + 1, step_size or 1)

        elif isinstance(definition, StaticStructureDefinition):
            _, size, _ = definition.get_attributes()

        # Built as a list and handed over whole: set() checks the length, so growing
        # from empty one append at a time would be rejected at the first element
        # (F-38). Each element is initialized by its own constructor.
        self.set([self._new_element() for _ in range(size)])

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Modify the Structure by performing an action selected randomly from three options:
        1. Resizing: if the Structure definition is dynamic, resizes the vector to a new rs size.
        2. Altering: modify the values of the vector. Note this option is the only one allowed for a static structure definition.
        3. Resizing and Altering: if the Structure definition is dynamic, resizes the vector by calling and modify a rs set of values of the vector.

        .. seealso::
            :meth:`_resize`
            :meth:`_alterate`
        """

        if isinstance(self.get_definition(), DynamicStructureDefinition):
            action = get_rng().choice([1, 2, 3])
        else:
            action = 2

        # If the action is resizing, resize the vector with resize_vector_variable
        if action == 1:
            self._resize()
        # If the action is changing, change the vector with change_vector_variable
        elif action == 2:
            self._alterate(alteration_limit=alteration_limit)
        # If the action is resizing and changing, resize the vector with resize_vector_variable
        # and change the vector with change_vector_variable
        else:
            self._resize()
            self._alterate()

    def get(self, index=None) -> Any:
        """
        The elements of the Structure as type objects, all of them or the one at the
        given index. Use [] for plain Python values instead (F-37).

        :param index: The position wanted, or None for the whole list.
        :type index: int | None
        :return: The list of type objects, or the type object at the position.
        :rtype: list | BaseType | Solution
        """

        if index is not None:
            return super().get()[index]
        else:
            return super().get()

    def _resize(self) -> None:
        """
        Resizes the vector based on the definition provided at initialization. The vector size can increase or decrease,
        depending on the minimum, maximum, and step size defined in the definition. When increasing, a rs set of values are included from the defined type.
        When decreasing, a rs set of values are deleted from the structure.
        """

        current_size = len(self)
        # Only a dynamic structure resizes; mutate() reaches here through the branch
        # that has already established that.
        definition = cast(DynamicStructureDefinition, self.get_definition())
        _, min_size, max_size, step_size, _ = definition.get_attributes()
        new_size = round(self._generate_numerical(
            min_size, max_size, step_size))

        # On a copy, handed over whole at the end: every intermediate length would
        # have to be valid otherwise, and set() checks it (F-38). The draws are the
        # ones there always were, in the same order: each new element is initialized
        # twice, once by its constructor and once here, and each deletion picks its
        # index from the list as it shrinks.
        values = list(self.get())
        if new_size > current_size:
            n_deletions = 0
            for _ in range(new_size - current_size):
                new_value = self._new_element()
                new_value.initialize()
                values.append(new_value)
        elif current_size > new_size:
            n_deletions = current_size - new_size
        else:
            n_deletions = 0
        for _ in range(n_deletions):
            ri = get_rng().choice(range(len(values)))
            del values[ri]
        self.set(values)

    def _alterate(self, alteration_limit: Any=None) -> None:
        """
        Randomly alters a certain number of elements in the vector by calling their `mutate` method.
        """

        current_size = len(self)

        # A dynamic structure whose minimum length is zero can be empty, and
        # there is nothing to alter then. randint(1, 0) raised instead (F-19).
        if current_size == 0:
            return

        number_of_changes = get_rng().randint(1, current_size)
        index_to_change = get_rng().sample(
            list(range(0, current_size)), number_of_changes)

        for i in index_to_change:
            self.get(i).mutate(alteration_limit=alteration_limit)

    def _convert(self, value: InputValue | BaseType | Solution) -> BaseType | Solution:
        """
        This method takes an input value which usually represents a builtin type and returns an instance of the corresponding BaseType. For instance:

        * int builtin type is converted to `Integer`.
        * float builtin type is converted to `Real`.
        * str builtin type is converted to `Categorical`.
        * list builtin type is converted to `Structure`.
        * dict builtin type is converted to `Solution`.
        * BaseTypes are not converted and returned without change.


        :param value: An input value to be converted to a BaseType instance.
        :type value: InputValue
        :return: A BaseType instance created from the input value.
        :raises ValueError: If the type of the input value is not supported by the Structure [int, float, str, list, dict, BaseType]. 
        """
        # Solution is not a BaseType, so both have to be named here: a structure
        # whose base is a group holds Solution instances.
        if isinstance(value, (BaseType, Solution)):  # Compatibility with already defined types
            return value

        if isinstance(value, int | float | str | list | dict):
            # From the value's own type rather than from the base, so a dict becomes
            # a group; built with the base definition all the same. Same registry mypy
            # cannot follow as in _new_element.
            element_class = cast(Callable[..., BaseType | Solution],
                                 self.get_connector().get_type(value))
            converted = element_class(self.get_definition().get_base(),
                                      connector=self.get_connector())

            # The constructor initializes the instance at random, so the input
            # value has to be applied on top of it. Without this the structure
            # kept a random element and dropped what the caller assigned (F-05).
            if isinstance(value, dict):
                # A dict base is a group, which the connector maps to Solution, whose
                # set takes (variable, value) instead of just the value.
                sub_solution = cast(Solution, converted)
                for variable, variable_value in value.items():
                    sub_solution.set(variable, variable_value)
            else:
                cast(BaseType, converted).set(value)

            return converted

        raise ValueError(
            f"The type {type(value)} is not supported by the structure. An instance of [int, float, str, list, dict, BaseType] was expected.")

    def __len__(self) -> int:
        """
        Returns the number of values stored in the Structure.

        :return: The length of the Structure.
        :rtype: int
        """
        return len(self.value)

    def __getitem__(self, i) -> Any:
        """
        Returns the value at the given index in the Structure, as a plain Python
        value at any depth (F-37). Use get(i) for the type object instead.

        :param i: The index of the value to return.
        :type i: int
        :return: The value at the given index.
        :rtype: InputValue
        """
        return builtin_value(self.value[i])

    def __delitem__(self, i) -> None:
        """
        Deletes the value at the given index in the Structure.

        :param i: The index of the value to delete.
        :type i: int
        :return: None
        :raises ValueError: if the Structure would be left with an invalid length.
        """
        values = list(self.get())
        del values[i]
        self.set(values)

    def __setitem__(self, index: int, value: int | float | str | list | dict | BaseType) -> None:
        """
        Sets the value at the given index in the Structure to the given value.

        :param index: The index of the value to set.
        :type index: int
        :param value: The new value to set.
        :type value: int | float | str | list | dict | BaseType
        :return: None
        """
        self.check(value)
        values = list(self.get())
        values[index] = value
        self.set(values)

    def insert(self, index: int, value: int | float | str | list | dict | BaseType) -> None:
        """
        Inserts the given value at the given index in the Structure.

        :param index: The index to insert the value at.
        :type index: int
        :param value: The value to insert.
        :type value: int | float | str | list | dict | BaseType
        :return: None
        :raises ValueError: if the Structure would be left with an invalid length.
        """
        self.check(value)
        # On a copy, so that a rejected length leaves the Structure as it was: get()
        # returns the list itself, and inserting into it before set() could refuse
        # would already have changed it (F-38). Was current_values[index].insert(...),
        # which asked the element at that position to insert, not the list (F-06).
        values = list(self.get())
        values.insert(index, value)
        self.set(values)

    def append(self, value: int | float | str | list | dict | BaseType | Solution) -> None:
        """
        Appends the given value to the end of the Structure.

        :param value: The value to append.
        :type value: int | float | str | list | dict | BaseType
        :return: None
        :raises ValueError: if the Structure would be left with an invalid length.
        """
        self.check(value)
        self.set(list(self.get()) + [value])

    def set(self, value: list[BaseType | Any]) -> None:
        """
        Sets the whole content of the Structure, converting any builtin in the list.

        :param value: The values to store, either builtins or already built types.
        :type value: list[BaseType | Any]
        :return: None
        :raises ValueError: if the list has a length the definition does not allow.
        """
        # The length first, against the definition's own rule: the elements were
        # validated one by one and the count never, so a static structure of ten
        # took three and a dynamic one grew past its maximum (F-38). Before
        # converting, so that a rejected list costs no draws and changes nothing.
        definition = self.get_definition()
        if not definition.check_length(value):
            raise ValueError(
                f"A structure of {len(value)} elements is not valid for definition: {definition}")
        # Each element goes through the same conversion append and __setitem__ use.
        # Asking the connector for the type of the structure's own definition, as
        # this did, answered Structure and then tried to build one out of the base
        # definition, so a plain list of builtins raised (F-06).
        self.value = [self._convert(element) for element in value]

    def __str__(self) -> str:
        """
        Returns a string representation of the Structure.

        :return: A string representation of the values in the Structure.
        :rtype: str
        """
        str_values = [str(v.value if isinstance(v, Solution) else v) for v in self.value]
        return str(str_values)
