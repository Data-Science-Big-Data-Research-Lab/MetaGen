"""Subset variables, defined with Domain.define_subset: every value is a selection of
the definition's elements, each at most once, in their order, and between the minimum
and the maximum size, whatever initializes, sets, mutates or holds it."""
import copy
import json
import pickle
from collections import Counter

import numpy as np
import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.domain import SubsetDefinition
from metagen.framework.rng import set_seed
from metagen.framework.solution.types import Subset

LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h"]


def _valid(value, elements=LETTERS, min_size=1, max_size=None):
    max_size = len(elements) if max_size is None else max_size
    positions = [elements.index(member) for member in value]
    return (isinstance(value, list) and positions == sorted(set(positions))
            and min_size <= len(value) <= max_size)


def _subset(elements=LETTERS, min_size=1, max_size=None):
    return Subset(SubsetDefinition(elements, min_size, max_size))


def _domain(elements=LETTERS, min_size=1, max_size=None):
    domain = Domain()
    domain.define_subset("s", elements, min_size, max_size)
    return domain


def _steps(before, after):
    """What one step did, read from the two values: 'add', 'remove' or 'change'."""
    gone, new = set(before) - set(after), set(after) - set(before)
    if len(new) == 1 and not gone:
        return "add"
    if len(gone) == 1 and not new:
        return "remove"
    if len(gone) == 1 and len(new) == 1:
        return "change"
    return None


# --- the definition --------------------------------------------------------------

def test_the_sizes_default_to_one_and_all_the_elements():
    assert SubsetDefinition(LETTERS).get_attributes() == ("SUBSET", LETTERS, 1, 8)
    assert SubsetDefinition(LETTERS, 0, 3).get_attributes() == ("SUBSET", LETTERS, 0, 3)


@pytest.mark.parametrize("min_size, max_size", [(0, 0), (0, 8), (3, 3), (8, 8), (0, 1), (1, 1)])
def test_every_consistent_pair_of_sizes_is_accepted(min_size, max_size):
    SubsetDefinition(LETTERS, min_size, max_size)


@pytest.mark.parametrize("min_size, max_size", [(-1, 3), (4, 3), (1, 9), (1.5, 3), (1, 2.0), ("1", 3),
                                                (True, 3), (1, np.inf)])
def test_inconsistent_sizes_are_rejected(min_size, max_size):
    with pytest.raises(ValueError, match="SUBSET"):
        SubsetDefinition(LETTERS, min_size, max_size)


def test_numpy_integers_are_valid_sizes():
    assert SubsetDefinition(LETTERS, np.int64(2), np.int32(4)).get_attributes()[2:] == (2, 4)


@pytest.mark.parametrize("elements", [[], ["a", "a"], ["a", "b", "a"], [1, "a"], "abc", None, [[1], [2]]])
def test_invalid_elements_are_rejected(elements):
    with pytest.raises(ValueError):
        Domain().define_subset("s", elements)


def test_a_single_element_is_enough():
    assert SubsetDefinition(["only"], 0, 1).get_attributes() == ("SUBSET", ["only"], 0, 1)


@pytest.mark.parametrize("value", [["a"], ("c", "a"), {"h", "b", "d"}, frozenset(LETTERS), LETTERS])
def test_check_value_accepts_a_selection_in_any_container_and_order(value):
    assert SubsetDefinition(LETTERS).check_value(value)


@pytest.mark.parametrize("value", [[], ["a", "a"], ["a", "z"], ["a", 1], "ab", "a", 3, None,
                                   {"a": 1}, [["a"]], LETTERS + ["z"]])
def test_check_value_rejects_what_is_not_a_selection(value):
    assert not SubsetDefinition(LETTERS).check_value(value)


def test_check_value_applies_the_sizes():
    definition = SubsetDefinition(LETTERS, 2, 3)
    assert [definition.check_value(LETTERS[:size]) for size in range(6)] == [
        False, False, True, True, False, False]


def test_a_bool_does_not_pass_for_an_integer_nor_the_other_way():
    assert not SubsetDefinition([0, 1, 2]).check_value([True])
    assert SubsetDefinition([True, False]).check_value([True])
    assert not SubsetDefinition([True, False]).check_value([1])


@pytest.mark.parametrize("elements, value, accepted", [
    ([0, 1, 2], [1.0], False),                 # a float is not an integer element
    ([0, 1, 2], [np.True_], False),
    ([0, 1, 2], [np.int64(1)], True),
    ([0.5, 1.0], [1], True),                   # an int stands for a float element
    ([0.5, 1.0], [np.float32(0.5)], True),
    ([0.5, 1.0], [True], False),
    ([np.float64(0.5), np.float64(1.0)], [0.5], True),
    (["1", "2"], [1], False),
    ([1, 2], ["1"], False),
])
def test_members_follow_the_rules_of_the_numeric_definitions(elements, value, accepted):
    assert SubsetDefinition(elements).check_value(value) is accepted


def test_invalid_elements_are_reported_as_a_subset_error():
    with pytest.raises(ValueError, match=r"\[SUBSET definition error\] The elements"):
        Domain().define_subset("s", [])


def test_a_permutation_in_a_structure_still_takes_only_a_list():
    domain = Domain()
    domain.define_static_structure("routes", 2)
    domain.define_permutation("route", [1, 2, 3])
    domain.set_structure_to_variable("routes", "route")
    solution = Solution(domain)
    solution.set("routes", [[3, 2, 1], [1, 2, 3]])
    for value in ([(3, 2, 1), [1, 2, 3]], [{1, 2, 3}, [1, 2, 3]]):
        with pytest.raises(ValueError, match="not supported"):
            solution.set("routes", value)


def test_the_value_is_kept_as_the_definitions_own_elements():
    subset = _subset([0.5, 1.0, 2.0])
    subset.set({2, 1})
    assert subset.get() == [1.0, 2.0] and all(type(x) is float for x in subset.get())
    subset = _subset([10, 20, 30])
    subset.set([np.int64(30), np.int64(10)])
    assert subset.get() == [10, 30] and all(type(x) is int for x in subset.get())


def test_the_domain_checks_and_shows_it():
    domain = _domain(min_size=2, max_size=3)
    assert domain.get_core().check("s", ["b", "a"])
    assert not domain.get_core().check("s", ["a"])
    assert "[SUBSET] {Elements = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], Size = [2, 3]}" in str(domain)


def test_a_long_list_of_elements_is_summarized_when_shown():
    domain = Domain()
    domain.define_subset("genes", list(range(6179)), 2, 50)
    domain.define_subset("few", list(range(20)))
    shown = str(domain)
    assert "[SUBSET] {Elements = 6179 (0 ... 6178), Size = [2, 50]}" in shown
    assert "Elements = " + str(list(range(20))) in shown


# --- initializing and setting ----------------------------------------------------

@pytest.mark.parametrize("min_size, max_size", [(1, 8), (0, 3), (2, 5), (4, 4), (0, 0), (8, 8)])
def test_initialize_draws_every_size_and_every_element(min_size, max_size):
    set_seed(0)
    sizes, members = Counter(), Counter()
    for _ in range(3000):
        value = _subset(LETTERS, min_size, max_size).get()
        assert _valid(value, LETTERS, min_size, max_size)
        sizes[len(value)] += 1
        members.update(value)
    assert set(sizes) == set(range(min_size, max_size + 1))
    # The size is uniform: every one within a fifth of its expected share.
    expected = 3000 / (max_size - min_size + 1)
    assert all(abs(count - expected) < expected / 5 for count in sizes.values())
    if max_size:
        assert set(members) == set(LETTERS)


def test_set_keeps_the_order_of_the_elements_whatever_the_order_given():
    subset = _subset()
    for given in (["h", "a", "d"], ("d", "h", "a"), {"a", "h", "d"}, frozenset({"d", "a", "h"})):
        subset.set(given)
        assert subset.get() == ["a", "d", "h"]


@pytest.mark.parametrize("value", [[], ["a", "a"], ["z"], ["a", "b", "c", "d"], "abc", 3])
def test_set_rejects_an_invalid_value_and_keeps_the_previous_one(value):
    solution = Solution(_domain(max_size=3))
    before = solution["s"]
    with pytest.raises((ValueError, TypeError)):
        solution.set("s", value)
    assert solution["s"] == before


def test_a_solution_takes_a_subset_as_a_tuple_or_a_set():
    solution = Solution(_domain())
    solution.set("s", ("c", "a"))
    assert solution["s"] == ["a", "c"]
    solution.set("s", {"b"})
    assert solution["s"] == ["b"]
    solution.set("s", frozenset({"h", "g"}))
    assert solution["s"] == ["g", "h"]


def test_other_variables_still_refuse_a_tuple_or_a_set():
    domain = Domain()
    domain.define_integer("n", 0, 10)
    domain.define_permutation("p", [1, 2, 3])
    solution = Solution(domain)
    for variable, value in (("n", (1,)), ("n", {1}), ("p", {1, 2, 3})):
        with pytest.raises(TypeError):
            solution.set(variable, value)


def test_reading_gives_a_copy_that_does_not_change_the_solution():
    domain = _domain()
    domain.define_permutation("p", [1, 2, 3])
    solution = Solution(domain)
    solution.set("s", ["a", "b"])
    before_p = solution["p"]
    read = solution["s"]
    read.append("h")
    solution["p"].reverse()
    assert solution["s"] == ["a", "b"] and solution["p"] == before_p


def test_two_solutions_with_the_same_selection_are_equal_and_hash_alike():
    domain = _domain()
    first, second = Solution(domain), Solution(domain)
    first.set("s", ["c", "a", "e"])
    second.set("s", {"e", "c", "a"})
    assert first == second and hash(first) == hash(second)
    second.set("s", ["a", "c"])
    assert first != second


# --- mutating --------------------------------------------------------------------

@pytest.mark.parametrize("limit", [None, 1, 2, 5, RelativeAlteration(0.2), RelativeAlteration(1.0)])
@pytest.mark.parametrize("min_size, max_size", [(1, 8), (0, 3), (2, 5), (4, 4), (0, 1), (7, 8)])
def test_a_mutation_always_changes_the_value_and_keeps_it_valid(limit, min_size, max_size):
    set_seed(1)
    subset = _subset(LETTERS, min_size, max_size)
    for _ in range(300):
        before = list(subset.get())
        subset.mutate(limit)
        assert _valid(subset.get(), LETTERS, min_size, max_size)
        assert subset.get() != before


@pytest.mark.parametrize("min_size, max_size, value", [(0, 0, []), (8, 8, LETTERS)])
def test_a_definition_with_a_single_value_is_left_as_it_is(min_size, max_size, value):
    subset = _subset(LETTERS, min_size, max_size)
    assert subset.get() == value
    for limit in (None, 1, 3, RelativeAlteration(0.5)):
        subset.mutate(limit)
        assert subset.get() == value


def test_a_limit_of_one_takes_exactly_one_step():
    set_seed(2)
    subset = _subset(LETTERS, 1, 8)
    for _ in range(2000):
        before = list(subset.get())
        subset.mutate(1)
        assert _steps(before, subset.get()) is not None


@pytest.mark.parametrize("size, allowed", [
    (1, {"add", "change"}),            # at the minimum nothing is removed
    (4, {"add", "remove", "change"}),
    (6, {"remove", "change"}),         # at the maximum nothing is added
])
def test_each_step_is_drawn_among_those_the_sizes_allow_and_evenly(size, allowed):
    set_seed(3)
    subset = _subset(LETTERS, 1, 6)
    seen = Counter()
    for _ in range(3000):
        subset.set(LETTERS[:size])
        subset.mutate(1)
        seen[_steps(LETTERS[:size], subset.get())] += 1
    assert set(seen) == allowed
    expected = 3000 / len(allowed)
    assert all(abs(count - expected) < expected / 5 for count in seen.values())


@pytest.mark.parametrize("min_size, max_size", [(1, 8), (0, 8), (3, 3), (1, 1), (2, 5), (7, 8)])
def test_every_single_step_changes_the_selection(min_size, max_size):
    """Each step on its own, without the rule that retries until the value changes: a
    step drawn but not allowed by the sizes, or a change that puts back the element it
    took out, would do nothing and pass unseen through a whole mutation."""
    set_seed(17)
    subset = _subset(LETTERS, min_size, max_size)
    for _ in range(3000):
        subset.initialize()
        chosen = list(subset.get())
        subset._step(chosen)
        assert set(chosen) != set(subset.get()) and len(set(chosen)) == len(chosen)
        assert min_size <= len(chosen) <= max_size


def test_a_fixed_size_changes_one_element_at_a_time():
    set_seed(4)
    subset = _subset(LETTERS, 3, 3)
    for _ in range(500):
        before = list(subset.get())
        subset.mutate(1)
        assert _steps(before, subset.get()) == "change"


def test_changing_never_puts_back_the_element_it_took_out():
    # With one element held and two in all, a change must swap it for the other.
    set_seed(5)
    subset = _subset(["x", "y"], 1, 1)
    for _ in range(200):
        before = subset.get()
        subset.mutate(1)
        assert subset.get() != before


def test_an_empty_selection_can_only_grow_and_a_full_one_only_shrink_or_change():
    set_seed(6)
    empty = _subset(LETTERS, 0, 8)
    full = _subset(LETTERS, 0, 8)
    for _ in range(300):
        empty.set([])
        empty.mutate(1)
        assert len(empty.get()) == 1
        full.set(LETTERS)
        full.mutate(1)
        assert len(full.get()) == 7


@pytest.mark.parametrize("limit, most", [(3, 3), (RelativeAlteration(0.25), 2), (RelativeAlteration(0.01), 1)])
def test_a_limit_bounds_the_number_of_steps(limit, most):
    """Each step moves the selection by one (add, remove) or two (change) elements, so
    the symmetric difference is at most twice the steps; with a relative limit the
    steps are a fraction of the maximum size, eight here."""
    set_seed(7)
    subset = _subset(LETTERS, 0, 8)
    reached = 0
    for _ in range(2000):
        before = set(subset.get())
        subset.mutate(limit)
        moved = len(before ^ set(subset.get()))
        assert moved <= 2 * most
        reached = max(reached, moved)
    assert reached > 2 * most - 2


def test_a_relative_limit_is_a_fraction_of_the_maximum_size_not_of_the_elements():
    set_seed(8)
    subset = _subset(list(range(6179)), 2, 50)
    for _ in range(300):
        before = set(subset.get())
        subset.mutate(RelativeAlteration(0.2))
        assert len(before ^ set(subset.get())) <= 2 * 10


def test_no_limit_draws_a_new_selection_of_any_size():
    set_seed(9)
    subset = _subset(LETTERS, 1, 8)
    sizes = Counter()
    for _ in range(2000):
        subset.mutate(None)
        sizes[len(subset.get())] += 1
    assert set(sizes) == set(range(1, 9))


def test_one_element_toggles_in_and_out():
    subset = _subset(["only"], 0, 1)
    for _ in range(10):
        before = subset.get()
        subset.mutate(1)
        assert subset.get() == ([] if before else ["only"])


def test_the_same_seed_gives_the_same_mutations():
    def run():
        set_seed(10)
        subset = _subset(list(range(100)), 5, 30)
        values = []
        for limit in [None, 1, 3, RelativeAlteration(0.2)] * 25:
            subset.mutate(limit)
            values.append(subset.get())
        return values
    assert run() == run()


def test_a_solution_mutates_every_kind_of_variable_and_keeps_the_subset_valid():
    set_seed(11)
    domain = _domain(min_size=2, max_size=4)
    domain.define_real("x", 0.0, 1.0)
    domain.define_permutation("p", [1, 2, 3])
    solution = Solution(domain)
    for limit in (None, 1, RelativeAlteration(0.2)) * 100:
        solution.mutate(alteration_limit=limit)
        assert _valid(solution["s"], LETTERS, 2, 4)


def test_one_variable_and_one_step_give_the_nine_moves_of_a_three_part_selection():
    """A solution of three subsets mutated with one variable and a limit of one takes
    exactly one step on exactly one of them."""
    set_seed(12)
    domain = Domain()
    for name in ("rows", "columns", "layers"):
        domain.define_subset(name, list(range(10)), 2, 6)
    solution = Solution(domain)
    moves = Counter()
    for _ in range(3000):
        before = {name: solution[name] for name in ("rows", "columns", "layers")}
        solution.mutate(alterations_number=1, alteration_limit=1)
        changed = [(name, _steps(before[name], solution[name]))
                   for name in before if solution[name] != before[name]]
        assert len(changed) == 1 and changed[0][1] is not None
        moves[changed[0]] += 1
    assert len(moves) == 9


def test_large_sets_of_elements_initialize_and_mutate():
    set_seed(13)
    elements = list(range(6179))
    subset = _subset(elements, 2, 50)
    for limit in (None, 1, RelativeAlteration(0.2)) * 100:
        subset.mutate(limit)
        assert _valid(subset.get(), elements, 2, 50)


# --- inside the rest of the framework --------------------------------------------

def test_structures_hold_subsets():
    set_seed(14)
    domain = Domain()
    domain.define_static_structure("teams", 3)
    domain.define_subset("team", LETTERS, 2, 3)
    domain.set_structure_to_variable("teams", "team")
    solution = Solution(domain)
    solution.set("teams", [{"b", "a"}, ("h", "c"), ["d", "e", "f"]])
    assert solution["teams"] == [["a", "b"], ["c", "h"], ["d", "e", "f"]]
    with pytest.raises(ValueError):
        solution.set("teams", [["a"], ["b", "c"], ["d", "e"]])
    for _ in range(100):
        solution.mutate(alteration_limit=1)
        assert all(_valid(team, LETTERS, 2, 3) for team in solution["teams"])


def test_a_dynamic_structure_of_subsets_grows_and_shrinks_with_valid_elements():
    set_seed(15)
    domain = Domain()
    domain.define_dynamic_structure("teams", 1, 4)
    domain.define_subset("team", LETTERS, 1, 2)
    domain.set_structure_to_variable("teams", "team")
    solution = Solution(domain)
    lengths = set()
    for _ in range(200):
        solution.mutate()
        lengths.add(len(solution["teams"]))
        assert all(_valid(team, LETTERS, 1, 2) for team in solution["teams"])
    assert lengths == {1, 2, 3, 4}


def test_a_positional_structure_takes_a_different_subset_per_position():
    set_seed(16)
    domain = Domain()
    domain.define_static_structure("dims", 2)
    domain.define_subset("small", ["a", "b", "c"], 1, 2)
    domain.define_subset("large", list(range(50)), 5, 10)
    domain.set_structure_to_variables("dims", ["small", "large"])
    solution = Solution(domain)
    solution.set("dims", [{"c"}, set(range(5))])
    assert solution["dims"] == [["c"], [0, 1, 2, 3, 4]]
    for _ in range(100):
        solution.mutate(alteration_limit=1)
        small, large = solution["dims"]
        assert _valid(small, ["a", "b", "c"], 1, 2) and _valid(large, list(range(50)), 5, 10)


def test_a_subset_can_depend_on_another_variable_but_not_decide_one():
    domain = _domain()
    domain.define_categorical("use", ["yes", "no"])
    domain.set_condition("s", "use", ["yes"])
    solution = Solution(domain)
    solution.set("use", "no")
    assert solution["s"] is None and not solution.is_active("s")
    solution.set("use", "yes")
    assert _valid(solution["s"])
    domain.define_real("x", 0.0, 1.0)
    with pytest.raises(ValueError):
        domain.set_condition("x", "s", [["a"]])


def test_a_subset_survives_json_pickle_and_deepcopy():
    solution = Solution(_domain())
    solution.set("s", ["b", "g"])
    assert json.loads(json.dumps(solution["s"])) == ["b", "g"]
    for clone in (pickle.loads(pickle.dumps(solution)), copy.deepcopy(solution)):
        assert clone["s"] == ["b", "g"] and clone == solution
        clone.set("s", ["a"])
        assert solution["s"] == ["b", "g"]


def test_the_connector_knows_the_subset():
    connector = Domain().get_connector()
    subset = _subset()
    assert connector.get_type(frozenset) is Subset
    assert connector.get_type(SubsetDefinition(LETTERS)) is Subset
    assert connector.get_builtin(subset) is frozenset
    assert connector.get_definition(subset) is SubsetDefinition
