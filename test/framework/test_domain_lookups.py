"""
Referring to a name the domain does not know is an error that names it.

Every method of Domain that takes the name of a group, a structure or a variable
already defined goes through the same lookup.
"""
import pytest

from metagen.framework import Domain, Solution


def _domain() -> Domain:
    domain = Domain()
    domain.define_integer("n", 1, 5)
    domain.define_group("g")
    domain.define_static_structure("s", 3)
    return domain


@pytest.mark.parametrize("call", [
    lambda d: d.define_integer_in_group("nope", "a", 0, 1),
    lambda d: d.define_real_in_group("nope", "a", 0.0, 1.0),
    lambda d: d.define_categorical_in_group("nope", "a", ["x", "y"]),
    lambda d: d.link_variable_to_group("nope", "n"),
    lambda d: d.link_variable_to_group("g", "nope"),
    lambda d: d.set_structure_to_integer("nope", 0, 1),
    lambda d: d.set_structure_to_variable("s", "nope"),
    lambda d: d.define_static_structure("t", 2, var="nope"),
], ids=["integer in group", "real in group", "categorical in group", "link: group", "link: variable",
        "structure to integer", "structure to variable", "structure from variable"])
def test_an_undefined_name_is_reported_by_name(call):
    with pytest.raises(ValueError, match="nope is not defined"):
        call(_domain())


def _group_and_variable() -> Domain:
    domain = Domain()
    domain.define_integer("n", 1, 5)
    domain.define_group("g")
    return domain


def test_linking_moves_the_variable_into_the_group_by_default():
    domain = _group_and_variable()
    domain.link_variable_to_group("g", "n")
    assert not domain.get_core().is_variable("n")
    assert set(Solution(domain)["g"]) == {"n"}


def test_linking_with_remember_keeps_the_variable_at_the_top_level_too():
    domain = _group_and_variable()
    domain.link_variable_to_group("g", "n", remember=True)
    assert domain.get_core().is_variable("n")
    solution = Solution(domain)
    assert set(solution["g"]) == {"n"} and 1 <= solution["n"] <= 5
