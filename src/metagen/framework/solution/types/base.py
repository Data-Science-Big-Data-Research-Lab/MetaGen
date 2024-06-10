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
from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from metagen.framework import BaseConnector
    from metagen.framework.domain import Base



class BaseType(ABC):

    def __init__(self, definition: Base, connector: BaseConnector = None) -> None:
        """
        This class represents an abstraction of the types included in a Solution. Note that the class support a Domain or a Base definition and the type is initialized in the constructor.

        Attributes:
        __definition (Base): A definition or domain used to define the variable.
        value (Any): The value of the variable.

        """

        self.__definition = definition
        self.value: Any = None
        self.connector = connector
        self.initialize()

    def get_connector(self) -> BaseConnector:
        return self.connector

    @abstractmethod
    def check(self, value: Any) -> None:
        """
        Checks if the given value is a valid input for the variable. Note this class is intended to be overwritten for a specific type.
        """
        pass

    @abstractmethod
    def initialize(self) -> None:
        """
        Initializes the value of the variable. Note this class is intended to be overwritten for a specific type.
        """
        pass

    @abstractmethod
    def mutate(self, alteration_limit=None) -> None:
        """
        Modifies the value of the variable. Note this class is intended to be overwritten for a specific type.
        """
        pass

    def get_definition(self) -> Base:
        """
        Returns the definition or domain of the variable.
        """
        return self.__definition

    def get(self) -> Any:
        """
        Returns the value of the variable.
        """
        return self.value

    def set(self, value: Any) -> None:
        """
        Sets the value of the variable.
        """

        self.value = value

    def __str__(self):
        """
        Returns a string representation of the value of the variable.
        """
        return str(self.value)

    def __repr__(self):
        """
        Returns a string representation of the value of the variable.
        """
        return str(self.value)

    def _closest_number(self, value: int | float, step: int | float):
        """
        Calculates the closest number to the given value that is a multiple of the given step. This class is intended to be used as auxiliary functions.
        :param value: Value to be rounded.
        :param step: Step size of the interval.
        :type value: int, float
        :type step: int, float
        :returns: The value rounded considering the step.
        :rtype: int, float
        """
        left_value = value - (value % step)
        right_value = (value + step) - (value % step)
        if value - left_value > right_value - value:
            return right_value
        else:
            return left_value

    def _generate_numerical(self, left: int | float, right: int | float, step_size: int | float | None = None) -> int | float:
        """ From a value in an interval compute a new random value by adding (to the right) or subtracting (to the left)
        a number of steps.

        :param left: Left value of the interval.
        :param right: Right value of the interval.
        :param step_size: Step size of the interval.
        :type left: int, float
        :type right: int, float
        :type step_size: int, float
        :returns: A random value.
        :rtype: int, float
        """

        new_value = random.uniform(left, right)
        if step_size is not None:
            new_value = max(min(self._closest_number(
                new_value, step_size), right), left)

        return new_value

    def __eq__(self, other):
        """
        Compare two `BaseType` objects or a `BaseType` object and an object for equality.

        Parameters:
            other (BaseType or str): The object to compare to.

        Returns:
            bool: `True` if the objects are equal, `False` otherwise.
        """

        if isinstance(other, BaseType):
            res = self.value == other.value
        else:
            res = self.value == other

        return res

    def __add__(self, other):
        """
        Add the value of another object to the value of this `BaseType` object.

        Parameters:
            other: The object to add to this `BaseType` object's value.

        Returns:
            The sum of the two values.
        """

        return self.value + other

    def __radd__(self, other):
        return other + self.value

    def __sub__(self, other):
        """
        Subtract the value of another object from the value of this `BaseType` object.

        Parameters:
            other: The object to subtract from this `BaseType` object's value.

        Returns:
            The difference between the two values.
        """

        return self.value - other

    def __rsub__(self, other):
        return other - self.value

    def __ne__(self, other):
        """
        Compare two `BaseType` objects or a `BaseType` object and a string for inequality.

        Parameters:
            other (BaseType or str): The object to compare to.

        Returns:
            bool: `True` if the objects are not equal, `False` otherwise.
        """
        return not self.__eq__(other)

    def __mul__(self, other):
        """
        Multiply the value of this `BaseType` object by another object.

        Parameters:
            other: The object to multiply this `BaseType` object's value by.

        Returns:
            The product of the two values.
        """
        return self.value * other

    def __rmul__(self, other):
        """
        Multiply the value of another object by the value of this `BaseType` object.

        Parameters:
            other: The object to multiply by this `BaseType` object's value.

        Returns:
            The product of the two values.
        """
        return other * self.value

    def __pow__(self, other):
        """
        Exponential operation of the value of this `BaseType` object by another object.

        Parameters:
            other: The object to multiply this `BaseType` object's value by.

        Returns:
            The product of the two values.
        """
        return self.value ** other

    def __rpow__(self, other):
        """
        Exponential operation of  the value of another object by the value of this `BaseType` object.

        Parameters:
            other: The object to multiply by this `BaseType` object's value.

        Returns:
            The product of the two values.
        """
        return other ** self.value

    def __lt__(self, other):
        """ *Less than* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is less
        than another individual **B** if the fitness value of **A** is strictly less than the fitness value of **B**.
        It is necessary for set structure management.
        """
        return self.value < other

    def __le__(self, other):
        """ *Less equal* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is less or
        equal than another individual **B** if the fitness value of **A** is less or equal than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.value <= other

    def __gt__(self, other):
        """ *Greater than* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is
        greater than another individual **B** if the fitness value of **A** strictly greater than the fitness value
        of **B**. It is necessary for set structure management.
        """
        return self.value > other

    def __ge__(self, other):
        """ *Greater equal* function for :py:class:`~metagen.individual.Individual` objects. An individual **A** is
        greater or equal than another individual **B** if the fitness value of **A** greater or equal than the
        fitness value of **B**. It is necessary for set structure management.
        """
        return self.value >= other

    def __hash__(self):
        """ Hash function for :py:class:`~metagen.individual.Individual` objects. It is necessary for set structure
        management.
        """
        return hash(self.value)
