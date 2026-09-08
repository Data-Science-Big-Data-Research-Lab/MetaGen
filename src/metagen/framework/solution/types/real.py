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
from typing import Any

from metagen.framework.domain import RealDefinition

from .base import BaseType
from metagen.framework.alteration import RelativeAlteration
from metagen.framework.rng import get_rng


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
        Initialize the Real variable with a rs float value in the defined ranges considering the step size.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()

        # Delegated instead of rounding here: this used to skip the clipping that
        # _generate_numerical does, and could hand set() a value its own check()
        # rejects (F-01).
        self.set(self._generate_numerical(min_value, max_value, step))

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Modify the value of this Real instance to a rs value from its definition.

        :param alteration_limit: How far the mutation may move the current value. A
            number is an absolute amount; a :py:class:`~metagen.framework.alteration.RelativeAlteration`
            is a fraction of this variable's own range (F-32). If not provided, the
            mutation can replace the current value with any within the domain.
        :type alteration_limit: float or RelativeAlteration or None
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        # Kept before the alteration limit narrows the interval: the grid belongs to
        # the domain, so anchoring it at a narrowed bound would put the mutated value
        # off the grid every other call (F-01).
        domain_min_value = min_value

        # Resolved here rather than by the caller because the caller has one number
        # for the whole solution, and every variable has a range of its own (F-32).
        if isinstance(alteration_limit, RelativeAlteration):
            alteration_limit = alteration_limit.of(min_value, max_value)

        if alteration_limit is not None:
            limited_min_value = self.get() - alteration_limit
            limited_max_value = self.get() + alteration_limit

            min_value = limited_min_value if max_value > limited_min_value > min_value else min_value
            max_value = limited_max_value if max_value > limited_max_value > min_value else max_value

        self.set(self._generate_numerical(min_value, max_value, step,
                                          origin=domain_min_value))

    def set(self, value: Any) -> None:
        """
        Sets the value of the Real variable, after checking if the value is valid.

        Args:
            value (Any): The value to be set for the Real variable.

        """
        self.check(value)

        # Normalized: the definition accepts anything numbers.Integral/Real since A-08,
        # so 1 into a real variable or a numpy scalar would otherwise be stored as it
        # came in. What the user reads back is always a native float.
        super().set(float(value))
