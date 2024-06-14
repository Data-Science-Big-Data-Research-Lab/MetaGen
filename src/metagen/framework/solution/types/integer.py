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
from typing import Any

from metagen.framework.domain.core import IntegerDefinition

from .base import BaseType


class Integer(BaseType):

    def __init__(self, definition: IntegerDefinition, connector=None) -> None:
        """
        The Integer class inherits from the BaseType class and represents an integer variable.

        :param definition: An instance of `IntegerDefinition` class representing the definition of the categorical variable.
        :type definition: `IntegerDefinition`
        """

        super(Integer, self).__init__(definition, connector)

    def check(self, value: Any) -> None:
        """
        Check if the input value is a valid Integer value, according to the definition of the Integer instance.

        :param value: The value to check.

        :raises ValueError: if the value does not correspond to the definition.
        """

        definition = self.get_definition()

        if not definition.check_value(value):
            _, min_value, max_value, _ = definition.get_attributes()
            raise ValueError(
                f"The value provided must be a int in the range [{min_value}, {max_value}]")

    def initialize(self) -> None:
        """
        Initialize the Integer variable with a random integer value in the defined ranges considering the step size.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        step = step or 1
        random_integer = random.randrange(min_value, max_value + 1, step)
        self.set(random_integer)

    def mutate(self, alteration_limit: int=None) -> None:
        """
        Modify the value of this Integer instance to a random category from its definition.

        :param alteration_limit: The determined how much the mutation will alter the current value. If not provided, the mutation can replace the current value with any within the domain.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        step = step or 1

        if alteration_limit != None:
            limited_min_value = self.get() - alteration_limit
            limited_max_value = self.get() + alteration_limit

            min_value = limited_min_value if max_value > limited_min_value > min_value else min_value
            max_value = limited_max_value if max_value > limited_max_value > min_value else max_value
            

        random_integer = random.randrange(min_value, max_value + 1, step)
        self.set(random_integer)

    def set(self, value: Any) -> None:
        """
        Sets the value of the Integer variable, after checking if the value is valid.

        Args:
            value (Any): The value to be set for the Integer variable.

        """
        self.check(value)
        super().set(value)
