"""Defining variables on a Domain: what is accepted, what is rejected, and what the
definition then reports. The cases come from the original CSV-driven tests, inlined."""
import pytest

from metagen.framework import Domain
from metagen.framework.domain.literals import C as CATEGORICAL, I as INTEGER, R as REAL

INTEGER_RANGES = [
    ("I", 0, 100, None),
    ("I", -100, 100, None),
    ("I", -999999999999999999999, 999999999999999999999999, None),
    ("I", 0, 1, None),
    ("I", -1, 0, None),
    ("I", -10, 10, 2),
    ("I", -12, 12, 3),
    ("I", -12, 12, 4),
]

REAL_RANGES = [
    ("R", 0, 100, None),
    ("R", -100, 100, None),
    ("R", -999999999999, 999999999999, None),
    ("R", 0, 1, None),
    ("R", -1, 0, None),
    ("R", -10, 10, 2),
    ("R", -12, 12, 3),
    ("R", -12, 12, 4),
]

CATEGORIES = [
    ['C1', 'C2'],
    ['C1', 'C2', 'C3', 'C4'],
    ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11'],
]


@pytest.mark.parametrize("name,minimum,maximum,step", INTEGER_RANGES)
def test_an_integer_is_defined_with_its_range(name, minimum, maximum, step):
    domain = Domain()
    domain.define_integer(name, minimum, maximum, step)

    assert domain.get_core().is_variable(name)
    definition = domain.get_core().get(name)
    kind, low, high, _ = definition.get_attributes()
    assert (kind, low, high) == (INTEGER, minimum, maximum)
    for value in (minimum, maximum, (maximum - minimum) // 2, maximum - 1, minimum + 1):
        assert definition.check_value(value)
    assert not definition.check_value(minimum - 1)
    assert not definition.check_value(maximum + 1)


@pytest.mark.parametrize("name,minimum,maximum,step", REAL_RANGES)
def test_a_real_is_defined_with_its_range(name, minimum, maximum, step):
    domain = Domain()
    domain.define_real(name, minimum, maximum, step)

    assert domain.get_core().is_variable(name)
    definition = domain.get_core().get(name)
    kind, low, high, _ = definition.get_attributes()
    assert (kind, low, high) == (REAL, minimum, maximum)
    for value in (minimum, maximum, (maximum - minimum) // 2, maximum - 1, minimum + 1):
        assert definition.check_value(value)
    assert not definition.check_value(minimum - 0.001)
    assert not definition.check_value(maximum + 0.001)


@pytest.mark.parametrize("categories", CATEGORIES)
def test_a_categorical_is_defined_with_its_categories(categories):
    domain = Domain()
    domain.define_categorical("C", categories)

    definition = domain.get_core().get("C")
    kind, allowed = definition.get_attributes()
    assert (kind, allowed) == (CATEGORICAL, categories)
    for category in categories:
        assert definition.check_value(category)
        assert not definition.check_value(category + "$random_string%")


def test_an_undefined_variable_is_not_in_the_domain():
    domain = Domain()
    assert not domain.get_core().is_variable("nothing")
    with pytest.raises(KeyError):
        domain.get_core().get("nothing")
