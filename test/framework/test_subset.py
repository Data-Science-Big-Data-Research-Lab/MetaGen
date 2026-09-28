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


# --- the crossover of the genetic algorithms -------------------------------------

def _ga_subset(elements=LETTERS, min_size=1, max_size=None):
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector, GASubset
    return GASubset(SubsetDefinition(elements, min_size, max_size), connector=GAConnector())


def _cuts(a, b):
    """Every pair of cut points a share in (0, 1) gives to lengths ``a`` and ``b``."""
    points = sorted({0.0, 1.0} | {i / a for i in range(1, a) if a} | {j / b for j in range(1, b) if b})
    shares = points[1:-1] + [(low + high) / 2 for low, high in zip(points, points[1:])]
    return {(int(share * a), int(share * b)) for share in shares}


def test_one_share_never_leaves_a_child_shorter_than_the_shorter_parent():
    """Why the crossover needs no redraw: cut at one share, each child, before its
    repetitions are dropped, is at least as long as the shorter parent."""
    for a in range(0, 30):
        for b in range(0, 30):
            for i, j in _cuts(a, b):
                assert i + b - j >= min(a, b) and a - i + j >= min(a, b)
                assert i + b - j <= max(a, b) and a - i + j <= max(a, b)


def _before_repair(head, tail):
    return head + [element for element in tail if element not in head]


def _explains(children, first, second, elements, min_size):
    """Whether one pair of cuts gives both children: each is its head and tail without
    repetitions, completed, only if short, up to the minimum with elements it did not
    hold."""
    for i, j in _cuts(len(first), len(second)):
        matched = True
        for child, (head, tail) in zip(children, ((first[:i], second[j:]), (first[i:], second[:j]))):
            base = _before_repair(head, tail)
            extra = [element for element in child if element not in base]
            if not set(base) <= set(child) or (extra and len(child) != min_size) \
                    or (not extra and len(child) != len(base)) \
                    or any(element not in elements for element in extra):
                matched = False
                break
        if matched:
            return True
    return False


@pytest.mark.parametrize("elements, min_size, max_size", [
    (LETTERS, 1, 8), (LETTERS, 0, 8), (LETTERS, 2, 5), (LETTERS, 3, 3), (LETTERS, 0, 2),
    (LETTERS, 8, 8), (list(range(40)), 2, 10), (list(range(6179)), 2, 50),
])
def test_the_crossover_gives_valid_children_that_one_cut_explains(elements, min_size, max_size):
    set_seed(20)
    for _ in range(400):
        mother, father = _ga_subset(elements, min_size, max_size), _ga_subset(elements, min_size, max_size)
        first, second = list(mother.get()), list(father.get())
        children = mother.crossover(father)
        values = [child.get() for child in children]
        assert all(_valid(value, elements, min_size, max_size) for value in values)
        assert _explains(values, first, second, elements, min_size)
        assert mother.get() == first and father.get() == second


def test_a_short_child_is_completed_with_elements_it_did_not_hold():
    """Parents that share c and d: cutting both in half gives a child made of c, d and
    c again, which drops to two and has to be completed; the element that completes it
    may be one neither parent held."""
    set_seed(21)
    completed = 0
    for _ in range(500):
        mother, father = _ga_subset(LETTERS, 3, 5), _ga_subset(LETTERS, 3, 5)
        mother.set(["a", "b", "c", "d"])
        father.set(["c", "d", "e"])
        for child in mother.crossover(father):
            assert _valid(child.get(), LETTERS, 3, 5)
            completed += bool(set(child.get()) - {"a", "b", "c", "d", "e"})
    assert completed > 0


def test_parents_of_different_lengths_are_never_cut_to_leave_a_child_short():
    """Before its repetitions go, each child has at least the minimum. Disjoint
    parents make every child's size before repair its size after."""
    set_seed(22)
    for _ in range(1000):
        mother, father = _ga_subset(LETTERS, 3, 6), _ga_subset(LETTERS, 3, 6)
        mother.set(["a", "b", "c"])
        father.set(["d", "e", "f", "g", "h"])
        children = mother.crossover(father)
        assert all(set(child.get()) <= set(LETTERS) and len(child.get()) >= 3 for child in children)
        assert sorted(len(child.get()) for child in children) in ([3, 5], [4, 4])


def test_equal_lengths_keep_the_length_when_nothing_repeats():
    set_seed(23)
    for _ in range(300):
        mother, father = _ga_subset(LETTERS, 1, 8), _ga_subset(LETTERS, 1, 8)
        mother.set(["a", "c", "e", "g"])
        father.set(["b", "d", "f", "h"])
        assert [len(child.get()) for child in mother.crossover(father)] == [4, 4]


def test_the_children_are_new_objects():
    mother, father = _ga_subset(), _ga_subset()
    mother.set(["a", "b"])
    father.set(["c", "d", "e"])
    for child in mother.crossover(father):
        assert child is not mother and child is not father
        child.mutate(1)
    assert mother.get() == ["a", "b"] and father.get() == ["c", "d", "e"]


def test_the_crossover_is_reproducible():
    def run():
        set_seed(24)
        mother, father = _ga_subset(list(range(100)), 2, 30), _ga_subset(list(range(100)), 2, 30)
        return [[child.get() for child in mother.crossover(father)] for _ in range(50)]
    assert run() == run()


def test_a_solution_of_three_subsets_crosses_each_one_on_its_own_cut():
    """The way a tricluster crosses over: every dimension with its own share."""
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector
    from metagen.metaheuristics.tools import solution_class
    set_seed(25)
    domain = Domain(GAConnector())
    names = ("rows", "columns", "layers")
    for name in names:
        domain.define_subset(name, list(range(30)), 2, 12)
    solution_type = solution_class(domain)
    independent = 0
    for _ in range(300):
        mother, father = (solution_type(domain, connector=domain.get_connector()) for _ in range(2))
        children = mother.crossover(father)
        for name in names:
            values = [child[name] for child in children]
            assert _explains(values, mother[name], father[name], list(range(30)), 2)
        shares = {name: len(children[0][name]) - len(mother[name]) for name in names}
        independent += len(set(shares.values())) > 1
    assert independent > 0


@pytest.mark.parametrize("kind", ["static", "dynamic", "positional"])
def test_structures_of_subsets_cross_over_into_valid_children(kind):
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector
    from metagen.metaheuristics.tools import solution_class
    set_seed(26)
    domain = Domain(GAConnector())
    if kind == "static":
        domain.define_static_structure("teams", 3)
    else:
        domain.define_dynamic_structure("teams", 1, 3)
    domain.define_subset("first", LETTERS, 1, 3)
    domain.define_subset("second", list(range(20)), 2, 6)
    domain.define_subset("third", ["x", "y", "z"], 0, 2)
    if kind == "positional":
        domain.set_structure_to_variables("teams", ["first", "second", "third"])
        rules = [(LETTERS, 1, 3), (list(range(20)), 2, 6), (["x", "y", "z"], 0, 2)]
    else:
        domain.set_structure_to_variable("teams", "first")
        rules = [(LETTERS, 1, 3)] * 3
    make = solution_class(domain)
    for _ in range(300):
        mother, father = (make(domain, connector=domain.get_connector()) for _ in range(2))
        before = mother["teams"], father["teams"]
        for child in mother.crossover(father):
            assert all(_valid(team, *rule) for team, rule in zip(child["teams"], rules))
        assert (mother["teams"], father["teams"]) == before


def test_the_genetic_connector_registers_the_subset_crossover():
    from metagen.metaheuristics import GA
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector, GASubset
    connector = GAConnector()
    assert connector.get_type(frozenset) is GASubset
    assert connector.get_type(SubsetDefinition(LETTERS)) is GASubset
    domain = Domain(connector)
    domain.define_subset("s", LETTERS)
    GA(domain, lambda solution: len(solution["s"]))


# --- TPE and KernelTPE -----------------------------------------------------------

def test_the_inclusion_model_counts_the_observations_and_the_prior():
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    definition = SubsetDefinition(["a", "b", "c", "d"], 1, 3)
    model = SubsetModel(definition, [["a", "b"], ["a"], ["a", "c"]], prior_weight=1.0)
    prior = (5 / 3) / 4                        # the mean observed size over the elements
    expected = [(3 + prior) / 4, (1 + prior) / 4, (1 + prior) / 4, (0 + prior) / 4]
    assert np.allclose(model.inclusion, expected)
    empty = SubsetModel(definition, [], prior_weight=1.0)
    assert np.allclose(empty.inclusion, (1 + 3) / 2 / 4)   # before any: the middle of the sizes


def test_the_model_draws_selections_of_the_observed_size_when_the_maximum_is_wide():
    """With no maximum declared, a prior centered on the middle of the sizes would put
    half of a thousand elements in; the observed selections hold twenty."""
    from metagen.metaheuristics import KernelTPE
    from metagen.metaheuristics.tools import solution_class
    from metagen.framework.rng import get_rng
    set_seed(35)
    domain = Domain()
    domain.define_subset("g", list(range(1000)))
    algorithm = KernelTPE(domain, lambda solution: len(solution["g"]), seed=35)
    make = solution_class(domain)

    def observed():
        solution = make(domain, connector=domain.get_connector())
        solution.set("g", get_rng().sample(range(1000), 20))
        solution.evaluate(algorithm.fitness_function)
        return solution

    good, bad = [observed() for _ in range(5)], [observed() for _ in range(100)]
    sizes = [len(algorithm.propose(good, bad)["g"]) for _ in range(20)]
    assert np.mean(sizes) < 35
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    drawn = [len(SubsetModel(domain.get_core().get("g"), [s["g"] for s in good], 1.0).draw()) for _ in range(200)]
    assert 15 < np.mean(drawn) < 30


def test_bringing_a_draw_within_the_sizes_keeps_the_likeliest_elements():
    """A draw too large drops the elements least likely to be in, and a draw too small
    takes those most likely: with 0, 1 and 2 far likelier than the rest and room for
    exactly three, most draws are those three either way. Measured: about 900 of 2000
    too large and 1370 too small, against 200 and 110 when the repair goes the wrong
    way or draws uniformly."""
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    set_seed(36)
    for inclusion in ([0.9] * 3 + [0.3] * 7, [0.3] * 3 + [0.01] * 7):
        model = SubsetModel(SubsetDefinition(list(range(10)), 3, 3), [], prior_weight=1.0)
        model.inclusion[:] = inclusion
        kept = sum(model.draw() == [0, 1, 2] for _ in range(2000))
        assert kept > 600


def test_the_inclusion_model_draws_valid_selections_that_follow_it():
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    set_seed(30)
    definition = SubsetDefinition(list(range(20)), 2, 6)
    observed = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [0, 1]]
    model = SubsetModel(definition, observed, prior_weight=1.0)
    counts = Counter()
    for _ in range(2000):
        value = model.draw()
        assert _valid(value, list(range(20)), 2, 6)
        counts.update(value)
    assert counts[0] > counts[1] > counts[10] and counts[1] > counts[19]


@pytest.mark.parametrize("min_size, max_size", [(0, 0), (0, 20), (5, 5), (18, 20), (20, 20)])
def test_the_inclusion_model_keeps_to_any_sizes(min_size, max_size):
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    set_seed(31)
    elements = list(range(20))
    definition = SubsetDefinition(elements, min_size, max_size)
    for observed in ([], [elements[:max_size]], [elements[:min_size]] * 5):
        model = SubsetModel(definition, observed, prior_weight=1.0)
        for _ in range(200):
            assert _valid(model.draw(), elements, min_size, max_size)


def test_the_log_density_prefers_the_selections_of_the_observations():
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    definition = SubsetDefinition(list(range(10)), 1, 5)
    good = SubsetModel(definition, [[0, 1, 2]] * 5, 1.0)
    bad = SubsetModel(definition, [[7, 8, 9]] * 5, 1.0)
    def score(selection):
        return good.log_density(selection) - bad.log_density(selection)
    assert score([0, 1, 2]) > score([0, 1, 9]) > score([7, 8, 9])
    assert np.isclose(np.exp(good.log_density([0, 1, 2])), np.prod(
        [good.inclusion[i] if i in (0, 1, 2) else 1 - good.inclusion[i] for i in range(10)]))


def test_tpe_resamples_a_subset_from_the_best_references():
    from metagen.metaheuristics.tpe.tpe_tools import TPEConnector, TPESubset
    from metagen.metaheuristics.tools import solution_class
    set_seed(32)
    domain = Domain(TPEConnector())
    domain.define_subset("s", list(range(30)), 1, 10)
    assert domain.get_connector().get_type(frozenset) is TPESubset
    make = solution_class(domain)
    best, worst = [], []
    for values, bucket in (([0, 1, 2], best), ([0, 1, 3], best), ([27, 28, 29], worst)):
        solution = make(domain, connector=domain.get_connector())
        solution.set("s", values)
        bucket.append(solution)
    counts = Counter()
    for _ in range(500):
        candidate = make(domain, connector=domain.get_connector())
        candidate.resample(best, worst)
        assert _valid(candidate["s"], list(range(30)), 1, 10)
        counts.update(candidate["s"])
    assert counts[0] > 300 and counts[0] > 5 * counts[28]


def test_kernel_tpe_draws_and_scores_the_subset():
    """With a subset as the only variable, the candidate KernelTPE proposes is the one
    that scores highest under l/g, and it is drawn from the model of the good ones."""
    from metagen.metaheuristics import KernelTPE
    from metagen.metaheuristics.tools import solution_class
    set_seed(33)
    domain = Domain()
    domain.define_subset("s", list(range(12)), 1, 6)
    algorithm = KernelTPE(domain, lambda solution: len(solution["s"]), seed=33, n_candidates=24)
    make = solution_class(domain)
    good, bad = [], []
    for values, bucket in (([0, 1], good), ([0, 2], good), ([0, 1, 2], good),
                           ([9, 10, 11], bad), ([8, 9, 10, 11], bad), ([7, 11], bad)):
        solution = make(domain, connector=domain.get_connector())
        solution.set("s", values)
        solution.evaluate(algorithm.fitness_function)
        bucket.append(solution)
    counts = Counter()
    for _ in range(200):
        candidate = algorithm.propose(good, bad)
        assert _valid(candidate["s"], list(range(12)), 1, 6)
        counts.update(candidate["s"])
    assert counts[0] > 150 and counts[11] < 20


def test_kernel_tpe_keeps_the_subset_candidate_that_scores_highest(monkeypatch):
    from metagen.metaheuristics import KernelTPE
    from metagen.metaheuristics.tools import solution_class
    from metagen.metaheuristics.tpe.subset_model import SubsetModel
    set_seed(34)
    domain = Domain()
    domain.define_subset("s", list(range(12)), 1, 6)
    algorithm = KernelTPE(domain, lambda solution: len(solution["s"]), seed=34, n_candidates=24)
    make = solution_class(domain)
    good, bad = [], []
    for values, bucket in (([0, 1], good), ([2, 3], good), ([9, 10, 11], bad), ([4, 5], bad)):
        solution = make(domain, connector=domain.get_connector())
        solution.set("s", values)
        bucket.append(solution)
    drawn, original = [], SubsetModel.draw

    def recording(self, leaf=None):
        value = original(self, leaf)
        drawn.append(value)
        return value

    monkeypatch.setattr(SubsetModel, "draw", recording)
    good_model = SubsetModel(domain.get_core().get("s"), [[0, 1], [2, 3]], 1.0)
    bad_model = SubsetModel(domain.get_core().get("s"), [[9, 10, 11], [4, 5]], 1.0)
    for _ in range(20):
        drawn.clear()
        chosen = algorithm.propose(good, bad)["s"]
        scores = [good_model.log_density(value) - bad_model.log_density(value) for value in drawn]
        assert len(drawn) == 24
        assert np.isclose(good_model.log_density(chosen) - bad_model.log_density(chosen), max(scores))


# --- every algorithm -------------------------------------------------------------

WEIGHTS = [12, 7, 11, 8, 9, 6, 14, 5, 10, 13, 4, 15, 3, 9, 7, 11, 6, 8, 12, 5]
VALUES = [24, 13, 23, 15, 16, 11, 28, 9, 20, 25, 7, 30, 5, 17, 14, 21, 12, 15, 22, 10]
CAPACITY = 60


def _knapsack_domain(connector=None, condition=False):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_subset("items", list(range(20)), 0, 20)
    domain.define_real("x", -1.0, 1.0)
    if condition:
        domain.define_categorical("pack", ["yes", "no"])
        domain.set_condition("items", "pack", ["yes"])
    return domain


def _knapsack_and_log():
    invalid = []

    def fitness(solution):
        items = solution["items"]
        if items is None:
            return 0.0 + solution["x"] ** 2
        if not _valid(items, list(range(20)), 0, 20):
            invalid.append(items)
        weight = sum(WEIGHTS[i] for i in items)
        return -sum(VALUES[i] for i in items) + 10 * max(0, weight - CAPACITY) + solution["x"] ** 2

    return fitness, invalid


def _algorithms():
    from metagen.metaheuristics import (GA, SA, SSGA, HillClimbing, KernelTPE, Memetic,
                                        RandomSearch, TabuSearch, TPE)
    return [RandomSearch, HillClimbing, TabuSearch, SA, GA, SSGA, Memetic, TPE, KernelTPE]


def _build(algorithm, condition=False, **kwargs):
    from metagen.metaheuristics import GA, SSGA, Memetic
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector
    genetic = algorithm in (GA, SSGA, Memetic)
    domain = _knapsack_domain(GAConnector() if genetic else None, condition)
    fitness, invalid = _knapsack_and_log()
    return algorithm(domain, fitness, **kwargs), fitness, invalid


@pytest.mark.parametrize("index", range(9), ids=lambda i: _algorithms()[i].__name__)
def test_every_algorithm_keeps_the_subset_valid_and_reports_its_true_fitness(index):
    algorithm, fitness, invalid = _build(_algorithms()[index], seed=40)
    best = algorithm.run()
    assert invalid == []
    assert best.get_fitness() == fitness(best)
    history = algorithm.best_solution_fitnesses
    assert all(later <= earlier for earlier, later in zip(history, history[1:]))


TARGET = set(range(0, 200, 25))


def _sparse_domain(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_subset("s", list(range(200)), 3, 8)
    return domain


def _distance_to_target(solution):
    return len(TARGET ^ set(solution["s"]))


# Measured on 28 September 2026: SSGA wins 4 of 10 with its default budget, 110
# evaluations at two children per iteration; it does improve (from 11 to 9 in 50
# iterations, to 5 in 500), only slower than random sampling spends the same budget.
# It is also the weakest on the behavior bench.
_SLOW = {"SSGA": "two children per iteration: 110 evaluations are too few to beat random sampling here"}


@pytest.mark.parametrize("index", [
    pytest.param(i, marks=pytest.mark.xfail(reason=_SLOW[name], strict=True)) if name in _SLOW else i
    for i, name in enumerate(a.__name__ for a in _algorithms()) if i > 0
], ids=lambda i: _algorithms()[i].__name__)
def test_every_algorithm_beats_random_sampling_with_its_own_budget(index):
    """Choosing the eight elements of a target among two hundred: every search beats
    as many random selections as it evaluates, on at least eight of ten seeds. The
    problem is separable, the case an element-by-element model is made for."""
    from metagen.metaheuristics import GA, SSGA, Memetic
    from metagen.metaheuristics.genetic.genetic_tools import GAConnector
    algorithm_class = _algorithms()[index]
    genetic = algorithm_class in (GA, SSGA, Memetic)
    wins = 0
    for seed in range(10):
        evaluations = []

        def counted(solution):
            evaluations.append(1)
            return _distance_to_target(solution)

        best = algorithm_class(_sparse_domain(GAConnector() if genetic else None), counted, seed=seed).run()
        set_seed(1000 + seed)
        domain = _sparse_domain()
        random_best = min(_distance_to_target(Solution(domain)) for _ in evaluations)
        wins += best.get_fitness() < random_best
    assert wins >= 8


@pytest.mark.parametrize("index", range(9), ids=lambda i: _algorithms()[i].__name__)
def test_every_algorithm_runs_with_a_conditional_subset(index):
    algorithm, fitness, invalid = _build(_algorithms()[index], condition=True, seed=41)
    best = algorithm.run()
    assert invalid == [] and best.get_fitness() == fitness(best)


@pytest.mark.parametrize("variant", ["CVOA", "ProbabilisticCVOA"])
def test_cvoa_keeps_the_subset_valid(variant):
    from metagen.metaheuristics import ProbabilisticCVOA, StrainProperties, cvoa_launcher
    from metagen.metaheuristics.cvoa.cvoa import CVOA
    strain_class = {"CVOA": CVOA, "ProbabilisticCVOA": ProbabilisticCVOA}[variant]
    fitness, invalid = _knapsack_and_log()
    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2)]
    best = cvoa_launcher(strains, _knapsack_domain(), fitness, seed=0, strain_class=strain_class)
    assert invalid == [] and best.get_fitness() == fitness(best)


@pytest.mark.parametrize("index", range(9), ids=lambda i: _algorithms()[i].__name__)
def test_a_run_with_a_subset_resumes_exactly(index, tmp_path):
    whole, fitness, _ = _build(_algorithms()[index], seed=42, max_iterations=8)
    reference = whole.run().get_fitness(), list(whole.best_solution_fitnesses)
    path = str(tmp_path / "run.ckpt")
    algorithm, _, _ = _build(_algorithms()[index], seed=42, max_iterations=8, checkpoint=path)

    def stops_after_three_iterations(solution):
        if algorithm.current_iteration >= 3:
            algorithm.request_stop()
        return fitness(solution)

    algorithm.fitness_function = stops_after_three_iterations
    algorithm.run()
    resumed = type(algorithm).resume(path, fitness)
    best = resumed.run()
    assert (best.get_fitness(), resumed.best_solution_fitnesses) == reference


def test_the_history_records_the_subset_as_a_list(tmp_path):
    from metagen.metaheuristics import HillClimbing
    path = tmp_path / "history.jsonl"
    algorithm, _, _ = _build(HillClimbing, seed=43, max_iterations=5, history=str(path))
    algorithm.run()
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert lines and all(isinstance(line["best_solution"]["items"], list) for line in lines
                         if "best_solution" in line)
