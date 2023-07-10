import random
from typing import Any

from metagen.framework.domain import RealDefinition

from .base import BaseType


class Real(BaseType):

    def __init__(self, definition: RealDefinition, connector=None) -> None:
        """
        The Real class inherits from the BaseType class and represents a Real variable.

        :param definition: An instance of `RealDefinition` class representing the definition of the categorical variable.
        :type definition: `RealDefinition`
        """
        super(Real, self).__init__(definition, connector)

    def check(self, value: Any) -> None:
        """
        Check if the input value is a valid Real value, according to the definition of the Real instance.

        :param value: The value to check.
        :raises ValueError: if the value does not correspond to the definition.
        """

        definition = self.get_definition()

        if not definition.check_value(value):
            _, min_value, max_value, _ = definition.get_attributes()
            raise ValueError(
                f"The value provided must be a float in the range [{min_value}, {max_value}]")

    def initialize(self) -> None:
        """
        Initialize the Real variable with a random float value in the defined ranges considering the step size.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        random_real = random.uniform(min_value, max_value)
        if step is not None:
            random_real = self._closest_number(random_real, step)
        self.set(random_real)

    def mutate(self) -> None:
        """
        Modify the value of this Real instance to a random value from its definition.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        self.set(self._generate_numerical(min_value, max_value, step))

    def set(self, value: Any) -> None:
        """
        Sets the value of the Real variable, after checking if the value is valid.

        Args:
            value (Any): The value to be set for the Real variable.

        """
        self.check(value)
        super().set(value)
