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
from typing import Any, List, cast

from metagen.framework.alteration import RelativeAlteration
from metagen.framework.domain import PermutationDefinition
from metagen.framework.rng import get_rng

from .base import BaseType


class Permutation(BaseType):
    """
    An ordering of the elements of a :py:class:`~metagen.framework.domain.core.PermutationDefinition`:
    every value holds each element exactly once. It reads as a list.

    :param definition: The definition of the permutation.
    :type definition: PermutationDefinition
    """

    def __init__(self, definition: PermutationDefinition, connector=None) -> None:
        super(Permutation, self).__init__(definition, connector)

    def get_definition(self) -> PermutationDefinition:
        """
        The definition this variable was built from.

        :return: The definition of this variable.
        :rtype: PermutationDefinition
        """
        return cast(PermutationDefinition, super().get_definition())

    def check(self, value: Any) -> None:
        """
        Check that a value is an ordering of the elements of the definition.

        :param value: The value to check.
        :raises ValueError: if it is not.
        """
        if not self.get_definition().check_value(value):
            _, elements = self.get_definition().get_attributes()
            raise ValueError(f"The value {value} must hold each of {elements} exactly once.")

    def initialize(self) -> None:
        """
        Initialize the permutation with an ordering drawn at random.
        """
        _, elements = self.get_definition().get_attributes()
        self.set(get_rng().sample(list(elements), len(elements)))

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Change the ordering, always to a different one.

        :param alteration_limit: How far the ordering may move, counted in swaps of two
            positions. A number is the most swaps, a
            :py:class:`~metagen.framework.alteration.RelativeAlteration` a fraction of the
            length (at least one swap), and None, the default, draws a new ordering at
            random.
        :type alteration_limit: int or RelativeAlteration or None
        """
        current: List[Any] = list(self.get())
        size = len(current)
        if alteration_limit is None:
            candidate = current
            while candidate == current:
                candidate = get_rng().sample(current, size)
            self.set(candidate)
            return

        if isinstance(alteration_limit, RelativeAlteration):
            most = max(1, round(alteration_limit.fraction * size))
        else:
            most = max(1, int(alteration_limit))
        candidate = list(current)
        for _ in range(get_rng().randint(1, most)):
            self._swap(candidate)
        # Swaps can undo each other; a mutation always changes the ordering.
        while candidate == current:
            self._swap(candidate)
        self.set(candidate)

    @staticmethod
    def _swap(values: List[Any]) -> None:
        first, second = get_rng().sample(range(len(values)), 2)
        values[first], values[second] = values[second], values[first]

    def set(self, value: Any) -> None:
        """
        Set the ordering, after checking it.

        :param value: A list or tuple holding each element exactly once.
        :raises ValueError: if it does not.
        """
        self.check(value)
        super().set(list(value))
