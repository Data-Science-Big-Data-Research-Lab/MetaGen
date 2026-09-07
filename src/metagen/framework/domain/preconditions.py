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
from itertools import pairwise
from typing import Any, Final, Literal, Tuple, final


@final
class Primitives:

    @staticmethod
    def is_basic_value(value: Any) -> bool:
        r = False
        if isinstance(value, (int, float, str)):
            r = True
        return r

    @staticmethod
    def is_categories_value(value: Any) -> bool:
        # pairwise only compared adjacent items, so ["a", "b", "a"] passed and even
        # ["a", "b", "a", "b"] did. And len >= 2 forbade pinning a hyperparameter to a
        # single value, which is a legitimate thing to declare (F-17).
        if not isinstance(value, list) or not value:
            return False
        if not all(Primitives.is_basic_value(x) for x in value):
            return False
        if any(type(x) is not type(value[0]) for x in value):
            return False
        return len(set(value)) == len(value)

    @staticmethod
    def is_layer_value(value: Any) -> bool:
        r = False
        if isinstance(value, dict):
            r = all(isinstance(k, str) and Primitives.is_basic_value(v)
                    for k, v in list(value.items()))
        return r

    @staticmethod
    def is_basic_vector_sequence_value(value: Any) -> bool:
        r = False
        if isinstance(value, list):
            r = all(type(x) == type(y) and Primitives.is_basic_value(x)
                    for x, y in pairwise(value))
        return r

    @staticmethod
    def is_layer_vector_sequence_value(value: Any) -> bool:
        r = False
        if isinstance(value, list):
            r = all(Primitives.is_layer_value(x) for x in value)
        return r


@final
class Messages:

    @staticmethod
    def min_max(min_value: int | float, max_value: int | float, mode: Literal["i", "r", "s"]) -> str:
        context = Messages.get_context(mode)
        return context[0] + " The minimum " + context[1] + " of the variable (" + str(min_value) \
            + ") must be less than the maximum one (" + str(max_value) + ")."

    @staticmethod
    def step_zero(mode: Literal["i", "r", "s"]) -> str:
        context = Messages.get_context(mode)
        return context[0] + " The " + context[1] + " must be greater than zero."

    @staticmethod
    def step(step: int | float, avg: int | float, mode: Literal["i", "r", "s"]) -> str:
        context = Messages.get_context(mode)
        return context[0] + " The step value (" + str(step) \
            + ") of the variable must be less or equal than (maximum" \
            + context[1] + " - minimum " + context[1] + ") / 2 (" \
            + str(avg) + ")."

    @staticmethod
    def min_max_length(min_length: int, max_length: int) -> str:
        prefix, suffix = Messages.get_context("s")
        return prefix + " The minimum " + suffix + " of the variable (" + str(min_length) \
            + ") must be less than or equal to the maximum one (" + str(max_length) + ")."

    @staticmethod
    def negative_length(length: int) -> str:
        prefix, suffix = Messages.get_context("s")
        return prefix + " The minimum " + suffix + " of the variable (" \
            + str(length) + ") can not be negative."

    @staticmethod
    def not_positive_length(length: int) -> str:
        prefix, suffix = Messages.get_context("s")
        return prefix + " The " + suffix + " of the variable (" + str(length) \
            + ") must be greater than zero."

    NOT_CATEGORIES: Final = "The categories must be a list, have the same type (int, float or str) and can not " \
                            "contain repeated values"

    @staticmethod
    def definition(name: str, mode: Literal["i", "r", "s", "d_a", "d_n", "d_g", "d_s"]):
        context = Messages.get_context(mode)
        return context[0] + " The variable " + name + " is " + context[1] + "."

    BASE_TYPE_NOT_DEFINED: Final = "[STRUCTURE definition error] The Base Type is not defined yet."

    @staticmethod
    def get_context(mode: Literal["i", "r", "s", "d_a", "d_n", "d_g", "d_s"]) -> Tuple[str, str]:
        prefix: str = "[STRUCTURE definition error]"
        suffix: str = "length"
        if mode == "i":
            prefix = "[INTEGER definition error]"
            suffix = "value"
        elif mode == "r":
            prefix = "[REAL definition error]"
            suffix = "value"
        # `mode in (...)`, not `mode == (...)`: comparing a str against a tuple is
        # always false, so every definition error came out with the STRUCTURE prefix
        # and "length" as its suffix — "The variable i is length." (F-16)
        elif mode in ("d_a", "d_n", "d_g", "d_s"):
            prefix = "[DEFINITION error]"
            if mode == "d_a":
                suffix = "already defined"
            elif mode == "d_n":
                suffix = "not defined"
            elif mode == "d_g":
                suffix = "not a group"
            elif mode == "d_s":
                suffix = "not a structure"
        return prefix, suffix


@final
class Preconditions:

    @staticmethod
    def length(value: int | float, mode: Literal["i", "r", "s"]):
        if value <= 0:
            raise ValueError(Messages.step_zero(mode))

    @final
    class Integer:
        @staticmethod
        def range(min_value: int, max_value: int, step: int | None):
            if min_value >= max_value:
                raise ValueError(Messages.min_max(min_value, max_value, "i"))
            if step is not None:
                avg = math.floor((max_value - min_value) / 2)
                Preconditions.length(step, "i")
                if step > avg:
                    raise ValueError(Messages.step(step, avg, "i"))

    @final
    class Real:
        @staticmethod
        def range(min_value: float, max_value: float, step: float | None):
            if min_value >= max_value:
                raise ValueError(Messages.min_max(min_value, max_value, "r"))
            if step is not None:
                avg = (max_value - min_value) / 2
                Preconditions.length(step, "r")
                if step > avg:
                    raise ValueError(Messages.step(step, avg, "r"))

    @final
    class Categorical:
        @staticmethod
        def categories(value: Any):
            if not Primitives.is_categories_value(value):
                raise ValueError(Messages.NOT_CATEGORIES)

    @final
    class Structure:
        """
        Length checks for the two structure definitions, which had none (F-19).

        Unlike Integer and Real, a minimum equal to the maximum is allowed here:
        it declares a structure of a fixed length, and check_length already
        accepts it as ``min <= length <= max``.
        """

        @staticmethod
        def length(length: int):
            if length < 1:
                raise ValueError(Messages.not_positive_length(length))

        @staticmethod
        def range(min_length: int, max_length: int, step_length: int | None):
            if min_length < 0:
                raise ValueError(Messages.negative_length(min_length))
            if min_length > max_length:
                raise ValueError(Messages.min_max_length(min_length, max_length))
            if step_length is not None:
                Preconditions.length(step_length, "s")
