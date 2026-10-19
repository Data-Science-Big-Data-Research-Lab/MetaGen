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
import math
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
        Initialize the Integer variable with a random integer value in the defined ranges considering the step size.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()
        if self.get_definition().log:
            self.set(_log_draw(min_value, max_value))
            return
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
            mutation can replace the current value with any within the domain. On a
            logarithmic scale both are measured on the natural logarithm of the value.
        :type alteration_limit: int or RelativeAlteration or None
        """
        # F-49: the draw included the current value, so on a two-valued domain half
        # the mutations changed nothing. F-32 brought the relative limit. F-50: the
        # window was truncated with int(), which rounds towards zero, so its lower end
        # reached one integer too far and its upper end one too short, and a limit
        # narrower than a step left the value alone: with RelativeAlteration(0.2) a
        # bit at 0 never flipped and an integer in [0, 4] could only go down.
        _, min_value, max_value, step = self.get_definition().get_attributes()
        if self.get_definition().log:
            self._mutate_on_log(min_value, max_value, alteration_limit)
            return
        step = step or 1
        # The grid is anchored on the domain's minimum, captured before the window
        # narrows it (the same rule F-01 gave Real): a window such as [13, 27] over a
        # step of 5 from 10 holds 15, 20 and 25, not 13, 18 and 23.
        origin, domain_max = int(min_value), int(max_value)

        # Resolved here rather than by the caller because the caller has one number
        # for the whole solution, and every variable has a range of its own (F-32).
        if isinstance(alteration_limit, RelativeAlteration):
            alteration_limit = alteration_limit.of(min_value, max_value)

        low, high = origin, domain_max
        if alteration_limit is not None:
            # At least one grid step, so that a neighborhood narrower than the grid
            # still moves: a bit flips, and an integer in [1, 5] moves by one.
            reach = max(alteration_limit, step)
            low = max(origin, self.get() - reach)
            high = min(domain_max, self.get() + reach)

        # The grid points inside [low, high], rounding inwards on both sides alike.
        first = origin + math.ceil((low - origin) / step) * step
        last = origin + math.floor((high - origin) / step) * step
        if first > last:
            # A hand-set value off the grid with a window too narrow to hold a grid
            # point: draw over the whole domain instead.
            first, last = origin, domain_max - (domain_max - origin) % step
        grid_size = (last - first) // step + 1

        # Mutating means changing: draw from the grid without the current value, as
        # Categorical does. Drawing over the whole window left a two-valued integer,
        # a bit, unchanged half of the time (F-49). A value off the grid, set by hand,
        # is simply redrawn. A window always holds a neighbor now, since it reaches at
        # least one step and a domain has at least three grid points; the check stays
        # for a definition built around those preconditions.
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

    def _mutate_on_log(self, min_value: int, max_value: int, alteration_limit: Any) -> None:
        """
        The mutation on a logarithmic scale: a new integer drawn on the logarithm within
        the alteration limit, which reaches at least the neighboring integers, and never
        the current value, as on a linear scale.
        """
        from .real import _log_window

        current = self.get()
        low_log, high_log = _log_window(current, min_value, max_value, alteration_limit)
        low = max(min_value, min(current - 1, math.floor(math.exp(low_log))))
        high = min(max_value, max(current + 1, math.ceil(math.exp(high_log))))
        for _ in range(100):
            drawn = _log_draw(low, high)
            if drawn != current:
                self.set(drawn)
                return
        # A window of two integers on a steep logarithm can keep drawing the current one;
        # move to a neighbor then, which every window holds.
        neighbors = [value for value in (current - 1, current + 1) if low <= value <= high]
        self.set(neighbors[get_rng().randrange(len(neighbors))])

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


def _log_draw(min_value: int, max_value: int) -> int:
    """An integer of [min_value, max_value] drawn uniformly on the logarithm, each integer
    taking the stretch of the logarithm closer to it than to its neighbors."""
    drawn = math.exp(get_rng().uniform(math.log(min_value - 0.5), math.log(max_value + 0.5)))
    return min(max(int(round(drawn)), min_value), max_value)
