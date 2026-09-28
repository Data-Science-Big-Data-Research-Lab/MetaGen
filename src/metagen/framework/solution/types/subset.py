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
from typing import TYPE_CHECKING, Any, Callable, List, Optional, cast

from metagen.framework.alteration import RelativeAlteration
from metagen.framework.domain import SubsetDefinition
from metagen.framework.rng import get_rng

from .base import BaseType

if TYPE_CHECKING:
    from metagen.framework import BaseConnector


class Subset(BaseType):
    """
    A selection of some of the elements of a
    :py:class:`~metagen.framework.domain.core.SubsetDefinition`, between its minimum
    and maximum number of them. It reads as a list without repetitions, in the order
    the elements were given.

    It moves by three steps: adding an element it does not hold, removing one it
    holds, and changing one for another it did not hold.

    :param definition: The definition of the subset.
    :type definition: SubsetDefinition
    """

    def __init__(self, definition: SubsetDefinition, connector: Optional['BaseConnector'] = None) -> None:
        super(Subset, self).__init__(definition, connector)

    def get_definition(self) -> SubsetDefinition:
        """
        The definition this variable was built from.

        :return: The definition of this variable.
        :rtype: SubsetDefinition
        """
        return cast(SubsetDefinition, super().get_definition())

    def check(self, value: Any) -> None:
        """
        Check that a value is a valid selection of the elements of the definition.

        :param value: The value to check.
        :raises ValueError: if it is not.
        """
        if not self.get_definition().check_value(value):
            _, elements, min_size, max_size = self.get_definition().get_attributes()
            raise ValueError(f"The value {value!r} must hold between {min_size} and {max_size} "
                             f"distinct elements of the subset's elements.")

    def initialize(self) -> None:
        """
        Initialize the subset with a size drawn at random between the minimum and the
        maximum, both included, and that many elements drawn at random.
        """
        self.set(self._draw())

    def _draw(self) -> List[Any]:
        _, elements, min_size, max_size = self.get_definition().get_attributes()
        size = get_rng().randint(min_size, max_size)
        return get_rng().sample(list(elements), size)

    def _has_one_value(self) -> bool:
        _, elements, min_size, max_size = self.get_definition().get_attributes()
        return min_size == max_size and max_size in (0, len(elements))

    def mutate(self, alteration_limit: Any = None) -> None:
        """
        Change the selection, always to a different one, unless the definition allows
        a single one.

        :param alteration_limit: How far the selection may move, counted in steps, each
            of them adding, removing or changing one element, drawn among those the
            sizes allow. A number is the most steps, a
            :py:class:`~metagen.framework.alteration.RelativeAlteration` a fraction of the
            maximum size (at least one step; with no maximum declared, the maximum is
            all the elements), and None, the default, draws a new selection at random.
        :type alteration_limit: int or RelativeAlteration or None
        """
        if self._has_one_value():
            return
        current: List[Any] = list(self.get())
        if alteration_limit is None:
            candidate = current
            while self.get_definition().canonical(candidate) == current:
                candidate = self._draw()
            self.set(candidate)
            return

        _, _, _, max_size = self.get_definition().get_attributes()
        if isinstance(alteration_limit, RelativeAlteration):
            most = max(1, round(alteration_limit.fraction * max_size))
        else:
            most = max(1, int(alteration_limit))
        candidate = list(current)
        for _ in range(get_rng().randint(1, most)):
            self._step(candidate)
        # Steps can undo each other; a mutation always changes the selection. One step
        # always does, so this ends.
        while self.get_definition().canonical(candidate) == current:
            self._step(candidate)
        self.set(candidate)

    def _step(self, chosen: List[Any]) -> None:
        """Add, remove or change one element of ``chosen``, in place: one of the three
        the sizes allow, drawn at random."""
        _, elements, min_size, max_size = self.get_definition().get_attributes()
        steps: List[Callable[[List[Any]], None]] = []
        if len(chosen) < max_size:
            steps.append(self._add)
        if len(chosen) > min_size:
            steps.append(self._remove)
        # Changing keeps the size, so it is allowed at the minimum and at the maximum;
        # it needs an element to take out and one not held to put in.
        if 1 <= len(chosen) < len(elements):
            steps.append(self._change)
        get_rng().choice(steps)(chosen)

    def _unused(self, chosen: List[Any]) -> List[Any]:
        _, elements, _, _ = self.get_definition().get_attributes()
        held = set(chosen)
        return [element for element in elements if element not in held]

    def _add(self, chosen: List[Any]) -> None:
        chosen.append(get_rng().choice(self._unused(chosen)))

    def _remove(self, chosen: List[Any]) -> None:
        chosen.pop(get_rng().randrange(len(chosen)))

    def _change(self, chosen: List[Any]) -> None:
        # The new element is drawn among those not held before the change, so the one
        # taken out cannot come straight back and leave the step without effect.
        incoming = get_rng().choice(self._unused(chosen))
        chosen[get_rng().randrange(len(chosen))] = incoming

    def set(self, value: Any) -> None:
        """
        Set the selection, after checking it. It is kept in the order of the elements.

        :param value: A list, tuple, set or frozenset of distinct elements, between the
            minimum and the maximum number of them.
        :raises ValueError: if it is not.
        """
        self.check(value)
        super().set(self.get_definition().canonical(value))
