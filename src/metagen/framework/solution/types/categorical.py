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
        Initialize the categorical variable with a random category from the available categories.
        """
        _, categories = self.get_definition().get_attributes()
        random_category = random.choice(categories)

        self.set(random_category)

    def mutate(self) -> None:
        """
        Modify the value of this Categorical instance to a random category from its definition, excluding its current value.
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
