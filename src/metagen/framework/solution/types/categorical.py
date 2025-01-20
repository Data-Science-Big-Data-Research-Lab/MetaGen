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

from metagen.framework.domain import CategoricalDefinition

from .base import BaseType


class Categorical(BaseType):

    def __init__(self, definition: CategoricalDefinition, connector=None) -> None:
        """
        The Categorical class inherits from the BaseType class and represents a categorical variable.

        :param definition: An instance of CategoricalDefinition class representing the definition of the categorical variable.
        :type definition: CategoricalDefinition
        """

        super(Categorical, self).__init__(definition, connector)

    def check(self, value: Any) -> None:
        """
        Check if the input value is a valid Categorical value, according to the definition of the Categorical instance.

        :param value: The value to check.
        """

        definition = self.get_definition()

        if not definition.check_value(value):
            _, categories = definition.get_attributes()
            raise ValueError(
                f"The value provided must be a str in: {categories}")

    def initialize(self) -> None:
        """
        Initialize the categorical variable with a rs category from the available categories.
        """
        _, categories = self.get_definition().get_attributes()
        random_category = random.choice(categories)

        self.set(random_category)

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Modify the value of this Categorical instance to a rs category from its definition, excluding its current value.
        """
        _, categories = self.get_definition().get_attributes()
        current_category = self.get()
        random_category = random.choice(
            [category for category in categories if category != current_category])
        self.set(random_category)

    def set(self, value: Any) -> None:
        """
        Sets the value of the categorical variable, after checking if the value is valid.

        Args:
            value (Any): The value to be set for the categorical variable.

        """
        self.check(value)
        super().set(value)
