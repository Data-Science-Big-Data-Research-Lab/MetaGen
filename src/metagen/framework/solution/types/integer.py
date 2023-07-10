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

    def mutate(self) -> None:
        """
        Modify the value of this Integer instance to a random category from its definition.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        step = step or 1
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
