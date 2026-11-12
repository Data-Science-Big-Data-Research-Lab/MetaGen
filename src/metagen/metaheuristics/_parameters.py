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
import numbers
from typing import Any, Optional

from metagen.framework import RelativeAlteration

# The parameters of the metaheuristics were taken as given, so a wrong one failed far from
# its cause (tournament_size=0: "min() arg is an empty sequence" in the first iteration;
# initial_temp=-5: a comparison with a complex number) or, worse, ran a search that does not
# search and said nothing (a negative alteration_limit, cooling_rate=1.5, mutation_rate=7).
# F-75, metagen-auditoria/AUDIT.md; X-12 and Y-15 of the independent audit.


def require_integer(name: str, value: Any, minimum: int, optional: bool = False) -> None:
    """
    Check that a parameter is an integer of at least ``minimum``, or None when it is optional.

    :param name: The name of the parameter, for the message.
    :type name: str
    :param value: Its value.
    :type value: Any
    :param minimum: The least value it may take.
    :type minimum: int
    :param optional: Whether None is accepted.
    :type optional: bool
    :raises ValueError: If it is not.
    """
    if optional and value is None:
        return
    if isinstance(value, bool) or not isinstance(value, numbers.Integral) or int(value) < minimum:
        what = "a positive integer" if minimum == 1 else f"an integer of at least {minimum}"
        raise ValueError(f"{name} must be {what}{' or None' if optional else ''}, not {value!r}.")


def require_number(name: str, value: Any, above: Optional[float] = None, at_least: Optional[float] = None,
                   at_most: Optional[float] = None, optional: bool = False) -> None:
    """
    Check that a parameter is a finite number within the bounds given, or None when it is
    optional.

    :param name: The name of the parameter, for the message.
    :type name: str
    :param value: Its value.
    :type value: Any
    :param above: A bound it must exceed.
    :type above: float, optional
    :param at_least: A bound it may reach from above.
    :type at_least: float, optional
    :param at_most: A bound it may reach from below.
    :type at_most: float, optional
    :param optional: Whether None is accepted.
    :type optional: bool
    :raises ValueError: If it is not.
    """
    if optional and value is None:
        return
    number = float(value) if isinstance(value, numbers.Real) and not isinstance(value, bool) else math.nan
    valid = (math.isfinite(number) and (above is None or number > above)
             and (at_least is None or number >= at_least) and (at_most is None or number <= at_most))
    if not valid:
        if above is not None and at_most is not None:
            what = f"a number in ({above}, {at_most}]"
        elif at_least is not None and at_most is not None:
            what = f"a number in [{at_least}, {at_most}]"
        elif above is not None:
            what = f"a finite number greater than {above}"
        elif at_least is not None:
            what = f"a finite number of at least {at_least}"
        else:
            what = "a finite number"
        raise ValueError(f"{name} must be {what}{' or None' if optional else ''}, not {value!r}.")


def require_probability(name: str, value: Any) -> None:
    """
    Check that a parameter is a probability, a number in [0, 1].

    :param name: The name of the parameter, for the message.
    :type name: str
    :param value: Its value.
    :type value: Any
    :raises ValueError: If it is not.
    """
    require_number(name, value, at_least=0, at_most=1)


def require_alteration(name: str, value: Any, zero: bool = False) -> None:
    """
    Check that a parameter is how far a solution may move: None, the whole domain; a
    :py:class:`~metagen.framework.RelativeAlteration`; or a positive number, an absolute
    amount (or zero, when ``zero`` says it means something).

    :param name: The name of the parameter, for the message.
    :type name: str
    :param value: Its value.
    :type value: Any
    :param zero: Whether zero is accepted.
    :type zero: bool
    :raises ValueError: If it is not.
    """
    if value is None or isinstance(value, RelativeAlteration):
        return
    number = float(value) if isinstance(value, numbers.Real) and not isinstance(value, bool) else math.nan
    valid = math.isfinite(number) and (number >= 0 if zero else number > 0)
    if not valid:
        amount = "a number of at least 0" if zero else "a positive number"
        raise ValueError(f"{name} must be None, a RelativeAlteration or {amount}, not {value!r}.")
