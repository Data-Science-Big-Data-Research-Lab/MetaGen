"""Setting values on a Solution: what each variable accepts and rejects, on the full
domain of the conftest, and the properties a fresh solution has to satisfy. The valid
and invalid values come from the original CSV-driven tests, inlined."""
import copy
import math

import pytest

from metagen.framework.rng import set_seed

# (variable, value). A group value is a dict, and reads back as one (F-37).
VALID = [
    ('I', 0),
    ('I', 1),
    ('I', 2),
    ('I', 100),
    ('I', 99),
    ('I', 50),
    ('I', 25),
    ('I', 75),
    ('R', 0.0),
    ('R', 1e-12),
    ('R', 0.75),
    ('R', 0.5),
    ('R', 0.25),
    ('R', 0.999999999999),
    ('R', 1.0),
    ('C', 'C1'),
    ('C', 'C2'),
    ('C', 'C3'),
    ('C', 'C4'),
    ('L', {'EI': 2}),
    ('L', {'EI': 0}),
    ('L', {'EI': 100}),
    ('L', {'EI': 99}),
    ('L', {'EI': 50}),
    ('L', {'EI': 25}),
    ('L', {'EI': 75}),
    ('L', {'ER': 0.0}),
    ('L', {'ER': 1e-12}),
    ('L', {'ER': 0.75}),
    ('L', {'ER': 0.5}),
    ('L', {'ER': 0.25}),
    ('L', {'ER': 0.999999999999}),
    ('L', {'ER': 1.0}),
    ('L', {'EC': 'C1'}),
    ('L', {'EC': 'C2'}),
    ('L', {'EC': 'C3'}),
    ('L', {'EC': 'C4'}),
]

INVALID = [
    ('I', -1),
    ('I', -2),
    ('I', 101),
    ('I', 102),
    ('I', 99999999),
    ('I', -9999999),
    ('R', -1e-09),
    ('R', 1.0000000001),
    ('R', 9999999999.99),
    ('R', -0.5),
    ('R', -0.25),
    ('R', 1.999999999999),
    ('C', 'C8'),
    ('C', 'FJIHBIIOJNF'),
    ('C', ''),
    ('L', {'EI': -1}),
    ('L', {'EI': -2}),
    ('L', {'EI': 101}),
    ('L', {'EI': -25}),
    ('L', {'EI': 99999999}),
    ('L', {'EI': -9999999}),
    ('L', {'ER': -1e-12}),
    ('L', {'ER': 999999999.99}),
    ('L', {'ER': -999999999.9}),
    ('L', {'ER': 1.000000000001}),
    ('L', {'EC': 'C8'}),
    ('L', {'EC': 'DFRGGFE'}),
]


@pytest.mark.parametrize("name,value", VALID)
def test_a_valid_value_is_stored_as_given(solution, name, value):
    solution.set(name, value)
    assert solution.is_available(name)
    assert solution[name] == value


@pytest.mark.parametrize("name,value", INVALID)
def test_an_invalid_value_is_rejected(solution, name, value):
    with pytest.raises(ValueError):
        solution.set(name, value)


def test_a_variable_the_domain_lacks_is_rejected(solution):
    # A bare KeyError today, from the definition lookup: the message names the
    # key and nothing else. DevSolution, which the old tests used, said "The
    # variable X does not exists in the Domain" instead.
    for name in ("THISVALUEDOESNOTEXISTS", None, -1):
        with pytest.raises(KeyError):
            solution.set(name, "EXAMPLE")
    with pytest.raises(KeyError):
        solution.set("L", {"THISVALUEDOESNOTEXISTS": "EXAMPLE"})
    with pytest.raises(ValueError):
        solution.set("L", {"ER": "EXAMPLE"})


def test_a_fresh_solution_is_consistent_with_its_domain(full_domain, solution):
    assert solution.get_definition() == full_domain.get_core()
    assert solution.get_connector() == full_domain.get_connector()
    assert solution.get_fitness() == math.inf
    for name, variable in solution.get_variables().items():
        assert solution.is_available(name)
        # get() hands out the type object; [] its plain value, valid for the domain
        # at any depth (F-37).
        assert solution.get(name) is variable
        assert full_domain.get_core().check(name, solution[name])


def test_a_copy_is_equal_until_it_is_mutated(solution):
    twin = copy.deepcopy(solution)
    assert twin == solution
    set_seed(1)
    twin.mutate(alterations_number=len(solution.get_variables()))
    assert twin != solution
