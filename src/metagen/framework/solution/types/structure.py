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
import random
from typing import Any, cast, TYPE_CHECKING

from metagen.framework.domain.core import (BaseStructureDefinition,
                                           DynamicStructureDefinition,
                                           StaticStructureDefinition)
from metagen.framework.solution.literals import InputValue, SolVector
from metagen.framework.solution import Solution

from .base import BaseType

if TYPE_CHECKING:
    from metagen.framework.solution.bounds import BaseTypeClass


class Structure(BaseType):

    def __init__(self, definition: BaseStructureDefinition, connector=None):
        """
        The Real class inherits from the BaseType class and represents a Real variable.

        :param definition: An instance of `BaseStructureDefinition` class representing the definition of the categorical variable.
        :type definition: `BaseStructureDefinition`
        """

        super(Structure, self).__init__(definition, connector)

    def check(self, value: Any) -> None:
        """
        Check if the input value is a valid Real value, according to the definition of the Real instance.

        :param value: The value to check.
        :raises ValueError: if the value does not correspond to the definition.
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
        Initializes the Structure according to the definition provided. If the definition is of type DynamicStructureDefinition, a random size is chosen within the min_size and max_size range (inclusive), with an optional step size. If the definition is of type StaticStructureDefinition, the provided size value is used instead. 

        For each position in the Structure, a new instance of the BaseType class is created based on the base type provided by the definition. The `initialize()` method is then called on this instance to set a value for it, and the instance is appended to the Structure. 

        .. seealso::
            :meth:`get_definition`
        """

        self.set([])

        size = 0

        if isinstance(self.get_definition(), DynamicStructureDefinition):
            _, min_size, max_size, step_size, _ = self.get_definition().get_attributes()

            size = random.randrange(min_size, max_size, step_size or 1)

        elif isinstance(self.get_definition(), StaticStructureDefinition):
            _, size, _ = self.get_definition().get_attributes()

        for _ in range(size):
            base_type_class = self.get_connector().get_type(self.get_definition().get_base())

            base_value: BaseType = base_type_class(
                self.get_definition().get_base(), connector=self.get_connector())
            self.append(base_value)

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Modify the Structure by performing an action selected randomly from three options:
        1. Resizing: if the Structure definition is dynamic, resizes the vector to a new random size.
        2. Altering: modify the values of the vector. Note this option is the only one allowed for a static structure definition.
        3. Resizing and Altering: if the Structure definition is dynamic, resizes the vector by calling and modify a random set of values of the vector.

        .. seealso::
            :meth:`_resize`
            :meth:`_alterate`
        """

        if isinstance(self.get_definition(), DynamicStructureDefinition):
            action = random.choice([1, 2, 3])
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
        Obtains the builtin value of the Structure or an specific index builtin value.
        """

        if index is not None:
            return super().get()[index]
        else:
            return super().get()

    def _resize(self) -> None:
        """
        Resizes the vector based on the definition provided at initialization. The vector size can increase or decrease,
        depending on the minimum, maximum, and step size defined in the definition. When increasing, a random set of values are included from the defined type. 
        When decreasing, a random set of values are deleted from the structure.
        """

        current_size = len(self)
        _, min_size, max_size, step_size, _ = self.get_definition().get_attributes()
        new_size = round(self._generate_numerical(
            min_size, max_size, step_size))

        if new_size > current_size:
            n_deletions = 0
            base_type_class = self.get_connector().get_type(self.get_definition().get_base())
            for _ in range(new_size - current_size):
                new_value: BaseType = base_type_class(
                    self.get_definition().get_base(), connector=self.get_connector())
                new_value.initialize()
                self.append(new_value)
        elif current_size > new_size:
            n_deletions = current_size - new_size
        else:
            n_deletions = 0

        for _ in range(n_deletions):
            ri = random.choice(range(len(self)))
            del self[ri]

    def _alterate(self, alteration_limit: Any=None) -> None:
        """
        Randomly alters a certain number of elements in the vector by calling their `mutate` method.
        """

        current_size = len(self)
        number_of_changes = random.randint(1, current_size)
        index_to_change = random.sample(
            list(range(0, current_size)), number_of_changes)

        for i in index_to_change:
            self.get(i).mutate(alteration_limit=alteration_limit)

    def _convert(self, value: InputValue) -> BaseType:
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
        if isinstance(value, int | float | str | list | dict):
            base_type_class: type[BaseType] = self.get_connector().get_type(
                value)
            value = base_type_class(self.get_definition(
            ).get_base(), connector=self.get_connector())
        elif BaseType:  # Compatibility with already defined types
            pass
        else:
            raise ValueError(
                f"The type {type(value)} is not supported by the structure. An instance of [int, float, str, list, dict, BaseType] was expected.")

        return value

    def __len__(self) -> int:
        """
        Returns the number of values stored in the Structure.

        :return: The length of the Structure.
        :rtype: int
        """
        return len(self.value)

    def __getitem__(self, i) -> BaseType:
        """
        Returns the value at the given index in the Structure.

        :param i: The index of the value to return.
        :type i: int
        :return: The value at the given index.
        :rtype: BaseType
        """
        return self.value[i].value

    def __delitem__(self, i) -> None:
        """
        Deletes the value at the given index in the Structure.

        :param i: The index of the value to delete.
        :type i: int
        :return: None
        """
        del self.value[i]

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

        current_values = self.get()
        current_values[index] = self._convert(value)
        self.set(current_values)

    def insert(self, index: int, value: int | float | str | list | dict | BaseType) -> None:
        """
        Inserts the given value at the given index in the Structure.

        :param index: The index to insert the value at.
        :type index: int
        :param value: The value to insert.
        :type value: int | float | str | list | dict | BaseType
        :return: None
        """
        self.check(value)
        current_values = self.get()
        current_values[index].insert(index, self._convert(value))
        self.set(current_values)

    def append(self, value: int | float | str | list | dict | BaseType) -> None:
        """
        Appends the given value to the end of the Structure.

        :param value: The value to append.
        :type value: int | float | str | list | dict | BaseType
        :return: None
        """
        self.check(value)
        current_values = self.get()
        current_values.append(self._convert(value))
        self.set(current_values)

    def set(self, value: list[BaseType | Any]) -> None:

        base_type_class: type[BaseTypeClass] = self.get_connector().get_type(
            self.get_definition())

        # Transform the values inside the list if they are a builtin
        for index in range(len(value)):
            v = value[index]
            if not isinstance(v, (BaseType, Solution)):
                type_value: BaseType | Solution = base_type_class(
                    self.get_definition().get_base(), self.get_connector())
                type_value.set(v)
                value[index] = type_value

        self.value = value

    def __str__(self) -> str:
        """
        Returns a string representation of the Structure.

        :return: A string representation of the values in the Structure.
        :rtype: str
        """
        str_values = [str(v) for v in self.value]
        return str(str_values)
