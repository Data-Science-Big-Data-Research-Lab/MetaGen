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
from typing import Any, cast

from metagen.framework.domain.core import IntegerDefinition

from .base import BaseType
from metagen.framework.alteration import RelativeAlteration
from metagen.framework.rng import get_rng


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

    def get_definition(self) -> IntegerDefinition:
        """
        The definition this variable was built from.

        Narrows what :py:meth:`~metagen.framework.solution.types.base.BaseType.get_definition`
        declares, which is the union of every definition and whose ``get_attributes``
        is therefore a union of tuples of two to five elements. Every unpacking here
        is of a fixed width, so without the narrowing none of them type-checks.

        :return: The definition of this variable.
        :rtype: IntegerDefinition
        """
        return cast(IntegerDefinition, super().get_definition())

    def initialize(self) -> None:
        """
        Initialize the Integer variable with a rs integer value in the defined ranges considering the step size.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        step = step or 1
        random_integer = get_rng().randrange(min_value, max_value + 1, step)
        self.set(random_integer)

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Modify the value of this Integer instance to another value of its definition,
        never the current one: a mutation always changes the variable, as it
        does for a Categorical.

        :param alteration_limit: How far the mutation may move the current value. A
            number is an absolute amount; a :py:class:`~metagen.framework.alteration.RelativeAlteration`
            is a fraction of this variable's own range. If not provided, the
            mutation can replace the current value with any within the domain.
        :type alteration_limit: int or RelativeAlteration or None
        """
        # F-49: the draw included the current value, so on a two-valued domain half
        # the mutations changed nothing. F-32 brought the relative limit.
        _, min_value, max_value, step = self.get_definition().get_attributes()
        step = step or 1
        # The grid is anchored on the domain's minimum, captured before the window
        # narrows it (the same rule F-01 gave Real): a window such as [13, 27] over a
        # step of 5 from 10 holds 15, 20 and 25, not 13, 18 and 23.
        origin, domain_max = int(min_value), int(max_value)

        # Resolved here rather than by the caller because the caller has one number
        # for the whole solution, and every variable has a range of its own (F-32).
        if isinstance(alteration_limit, RelativeAlteration):
            alteration_limit = alteration_limit.of(min_value, max_value)

        if alteration_limit is not None:
            limited_min_value = self.get() - alteration_limit
            limited_max_value = self.get() + alteration_limit

            min_value = limited_min_value if max_value > limited_min_value > min_value else min_value
            max_value = limited_max_value if max_value > limited_max_value > min_value else max_value

        low, high = int(min_value), int(max_value)
        first = low + (origin - low) % step
        last = high - (high - origin) % step
        if first > last:
            # A hand-set value off the grid with a window too narrow to hold a grid
            # point: draw over the whole domain instead.
            first, last = origin, domain_max - (domain_max - origin) % step
        grid_size = (last - first) // step + 1

        # Mutating means changing: draw from the grid without the current value, as
        # Categorical does. Drawing over the whole window left a two-valued integer,
        # a bit, unchanged half of the time (F-49). A value off the grid, set by hand,
        # is simply redrawn; a window with a single grid point has nothing to move to.
        current = self.get()
        on_grid = first <= current <= last and (current - first) % step == 0
        if on_grid:
            if grid_size == 1:
                return
            index = get_rng().randrange(grid_size - 1)
            if index >= (current - first) // step:
                index += 1
        else:
            index = get_rng().randrange(grid_size)
        self.set(first + index * step)

    def set(self, value: Any) -> None:
        """
        Sets the value of the Integer variable, after checking if the value is valid.

        Args:
            value (Any): The value to be set for the Integer variable.

        """
        self.check(value)

        # Normalized: the definition accepts anything numbers.Integral/Real since A-08,
        # so 1 into a real variable or a numpy scalar would otherwise be stored as it
        # came in. What the user reads back is always a native int.
        super().set(int(value))
