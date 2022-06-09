import math
from pycvoa.types import OptInt, OptFloat, BasicValueList, CategoryList


# =========================================== VALUE CHECKERS ==========================================================#

def check_integer_range_step(min_value, max_value, step: OptInt, case: str):
    check_range(min_value, max_value, case)
    return check_int_step(min_value, max_value, step, case)


def check_real_range_step(min_value, max_value, step: OptFloat, case: str):
    check_range(min_value, max_value, case)
    return check_float_step(min_value, max_value, step, case)


def check_range(min_value, max_value, case: str):
    """ It checks if min_value < max_value, if not, raise :py:class:`~pycvoa.problem.domain.DefinitionError`.
    If the first condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
    py:class:`~pycvoa.problem.domain.DefinitionError`.

    :param min_value: The minimum value.
    :param max_value: The maximum value.
    :param case: The step.
    :type min_value: int, float
    :type max_value: int, float
    :type case: int, float
    """
    if min_value >= max_value:

        msg = ""

        if case == "a":
            msg = "The minimum value of the variable (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."
        elif case == "b":
            msg = "The minimum value of the element (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."
        elif case == "c":
            msg = "The minimum size of the VECTOR variable (" + str(min_value) \
                  + ") must be less than the maximum one (" + str(max_value) + ")."

        raise ValueError(msg)


def check_int_step(min_value: int, max_value: int, step: OptInt, case: str) -> int:
    average = math.floor((max_value - min_value) / 2)
    if step is not None:
        if step > average:
            msg = ""
            if case == "a":
                msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "b":
                msg = "The step value (" + str(step) + ") of the element must be less or equal than" \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "c":
                msg = "The step size (" + str(step) + ") of the VECTOR variable must be less or equal than " \
                                                      "(maximum size - minimum size) / 2 ( " + str(average) + ")."

            raise ValueError(msg)
        else:
            r = step
    else:
        r = average
    return r


def check_float_step(min_value: float, max_value: float, step: OptFloat, case: str) -> float:
    average = (max_value - min_value) / 2
    if step is not None:
        if step > average:
            msg = ""
            if case == "a":
                msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            elif case == "b":
                msg = "The step value (" + str(step) + ") of the element must be less or equal than " \
                                                       "(maximum value - minimum value) / 2 (" + str(average) + ")."
            raise ValueError(msg)
        else:
            r = step
    else:
        r = average
    return r


def check_categories(categories: CategoryList):
    if len(categories) < 2:
        raise ValueError("The categories parameter must have al least two elements.")
    i = 0
    cat_type = type(categories[0])
    while i < len(categories) - 1:
        if categories[i] is not cat_type:
            raise TypeError(
                "The categories must have the same type (int, float or str).")
        j = i + 1
        while j < len(categories):
            if categories[i] == categories[j]:
                raise ValueError(
                    "The categories list can not contain repeated values.")
            else:
                j += 1
        i += 1