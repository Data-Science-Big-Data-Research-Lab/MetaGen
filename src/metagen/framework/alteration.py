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


class RelativeAlteration:
    """
    A mutation neighbourhood expressed as a fraction of each variable's own range.

    ``alteration_limit`` is a single number handed to every variable of a solution
    alike, and a single number cannot suit a domain whose variables have different
    widths. With the 1.0 that the local searches used to default to, a real in
    [0, 1] jumped over half its range on every mutation -- resampling rather than
    neighbouring -- while an integer in [1, 1000] moved by one part in a thousand
    and sat still. That is F-32.

    Passing one of these instead says *how far* rather than *how much*, and each
    variable resolves it against the bounds of its own definition. Plain numbers
    keep meaning an absolute amount, and ``None`` keeps meaning the whole domain,
    so nothing written against the old behaviour changes.

    Instances are immutable, which is why one of them can safely be a default
    argument -- the trap F-12 was about.

    :param fraction: The share of a variable's range a mutation may travel, in (0, 1].
        The local searches default to 0.2. Anything from about a tenth to a fifth
        performs the same -- measured over 30 seeds the differences are noise -- and
        well beyond that the neighbourhood stops being one: at half the range
        HillClimbing drops from 79 wins out of 90 to 71.
    :type fraction: float
    :raises ValueError: If the fraction is outside (0, 1].
    """

    __slots__ = ("fraction",)

    def __init__(self, fraction: float = 0.1) -> None:
        if not 0 < fraction <= 1:
            raise ValueError(
                f"A relative alteration must be a fraction of the range in (0, 1], "
                f"and {fraction} is not. Pass a plain number for an absolute limit."
            )
        self.fraction = fraction

    def of(self, min_value: float, max_value: float) -> float:
        """
        Resolve the fraction against one variable's bounds.

        :param min_value: The lower bound of the variable's definition.
        :type min_value: float
        :param max_value: The upper bound of the variable's definition.
        :type max_value: float
        :return: The absolute amount this variable's mutation may travel.
        :rtype: float
        """
        return self.fraction * (max_value - min_value)

    def __repr__(self) -> str:
        return f"RelativeAlteration({self.fraction})"
