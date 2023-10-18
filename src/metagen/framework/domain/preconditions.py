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
    def is_categories_value(value: Any):
        r = False
        if isinstance(value, list):
            if len(value) >= 2:
                r = all(type(x) == type(y) and Primitives.is_basic_value(x) and x != y
                        for x, y in pairwise(value))
        return r

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
        return context[0] + " The  " + context[1] + " must be greater than zero."

    @staticmethod
    def step(step: int | float, avg: int | float, mode: Literal["i", "r", "s"]) -> str:
        context = Messages.get_context(mode)
        return context[0] + " The step value (" + str(step) \
            + ") of the variable must be less or equal than (maximum" \
            + context[1] + " - minimum " + context[1] + ") / 2 (" \
            + str(avg) + ")."

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
        elif mode == ("d_a", "d_g"):
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
