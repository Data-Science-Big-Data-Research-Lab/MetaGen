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
from typing import Any, Tuple

from metagen.framework.alteration import RelativeAlteration
from metagen.framework.rng import get_rng

# What a real and an integer on a logarithmic scale share: integer.py took _log_window from
# real.py inside a function (OF-16 of the independent audit).


def _log_window(value: float, min_value: float, max_value: float, alteration_limit: Any) -> Tuple[float, float]:
    """
    The interval of the logarithm a mutation draws from, on a logarithmic scale: the
    whole domain, or the current value's logarithm give or take the alteration limit,
    itself on the logarithm (a ``RelativeAlteration`` is a share of the orders of
    magnitude of the range).

    :param value: The current value.
    :param min_value: The minimum of the domain.
    :param max_value: The maximum of the domain.
    :param alteration_limit: A number, a ``RelativeAlteration`` or None.
    :return: The lowest and highest logarithm.
    """
    low, high = math.log(min_value), math.log(max_value)
    if isinstance(alteration_limit, RelativeAlteration):
        alteration_limit = alteration_limit.of(low, high)
    if alteration_limit is None:
        return low, high
    center = math.log(value)
    return max(low, center - alteration_limit), min(high, center + alteration_limit)


def _log_draw(min_value: int, max_value: int) -> int:
    """An integer of [min_value, max_value] drawn uniformly on the logarithm, each integer
    taking the stretch of the logarithm closer to it than to its neighbors."""
    drawn = math.exp(get_rng().uniform(math.log(min_value - 0.5), math.log(max_value + 0.5)))
    return min(max(int(round(drawn)), min_value), max_value)
