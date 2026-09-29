"""The data a triclustering works on: a Cube of values without gaps, read-only, and a
Tricluster of sorted, distinct positions that has to fit in it."""
import copy
import pickle

import numpy as np
import pytest

from metagen.framework import Domain, Solution
from metagen.triclustering import Cube, Tricluster


def _values(shape=(6, 4, 5), seed=0):
    return np.random.default_rng(seed).normal(size=shape)


# --- the cube --------------------------------------------------------------------

def test_a_cube_keeps_its_values_as_floats_and_names_its_positions_by_default():
    values = np.arange(24).reshape(2, 3, 4)
    cube = Cube(values)
    assert cube.shape == (2, 3, 4) and cube.values.dtype == np.float64
    assert np.array_equal(cube.values, values)
    assert (cube.genes, cube.conditions, cube.times) == ((0, 1), (0, 1, 2), (0, 1, 2, 3))


def test_a_cube_takes_the_names_given():
    cube = Cube(_values((2, 2, 3)), genes=["g1", "g2"], conditions=("a", "b"), times=[0, 4, 8])
    assert cube.genes == ("g1", "g2") and cube.conditions == ("a", "b") and cube.times == (0, 4, 8)


def test_a_cube_is_read_only_and_a_copy_of_what_it_was_given():
    values = _values()
    cube = Cube(values)
    values[0, 0, 0] = 99.0
    assert cube.values[0, 0, 0] != 99.0
    with pytest.raises(ValueError):
        cube.values[0, 0, 0] = 1.0


@pytest.mark.parametrize("values, message", [
    (np.zeros((3, 3)), "three dimensions"),
    (np.zeros((3, 3, 3, 3)), "three dimensions"),
    (np.zeros((1, 3, 3)), "two genes"),
    (np.zeros((3, 1, 3)), "two conditions"),
    (np.zeros((3, 3, 1)), "two times"),
    ([[["a", "b"], ["c", "d"]], [["e", "f"], ["g", "h"]]], "numbers"),
])
def test_a_cube_rejects_values_of_the_wrong_shape_or_kind(values, message):
    with pytest.raises(ValueError, match=message):
        Cube(values)


@pytest.mark.parametrize("names", [{"genes": ["a"]}, {"conditions": ["a", "b", "c"]}, {"times": list(range(6))}])
def test_a_cube_rejects_names_that_do_not_match_the_shape(names):
    with pytest.raises(ValueError, match="names"):
        Cube(_values((2, 2, 5)), **names)


@pytest.mark.parametrize("gap", [np.nan, np.inf, -np.inf])
def test_a_cube_rejects_missing_values_and_says_where_they_are(gap):
    values = _values()
    values[4, 1, 2] = gap
    values[5, 1, 0] = gap
    with pytest.raises(ValueError) as error:
        Cube(values)
    message = str(error.value)
    assert "2 missing or infinite values" in message
    assert "genes [4, 5]" in message and "conditions [1]" in message and "times [0, 2]" in message
    assert "without_missing" in message


def test_the_message_lists_at_most_ten_positions_per_dimension():
    values = _values((30, 2, 2))
    values[:, 0, 0] = np.nan
    with pytest.raises(ValueError, match=r"genes \[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, \.\.\.\]"):
        Cube(values)


@pytest.mark.parametrize("axis, index, expected_shape", [
    ("genes", 0, (4, 4, 5)), ("conditions", 1, (6, 2, 5)), ("times", 2, (6, 4, 3))])
def test_without_missing_drops_the_positions_with_gaps_along_one_axis(axis, index, expected_shape):
    values = _values()
    gaps = [(1, 1, 1), (3, 2, 4)]
    for gap in gaps:
        values[gap] = np.nan
    cube, kept = Cube.without_missing(values, axis=axis)
    dropped = {gap[index] for gap in gaps}
    assert cube.shape == expected_shape
    assert kept == tuple(p for p in range(values.shape[index]) if p not in dropped)
    assert np.array_equal(cube.values, np.take(values, kept, axis=index))


def test_without_missing_keeps_the_names_of_what_it_keeps():
    values = _values((4, 2, 3))
    values[1, 0, 0] = np.nan
    cube, kept = Cube.without_missing(values, genes=["a", "b", "c", "d"], times=[0, 1, 2])
    assert kept == (0, 2, 3) and cube.genes == ("a", "c", "d") and cube.times == (0, 1, 2)


def test_without_missing_on_values_without_gaps_keeps_everything():
    cube, kept = Cube.without_missing(_values())
    assert kept == tuple(range(6)) and cube.shape == (6, 4, 5)


@pytest.mark.parametrize("axis, message", [("rows", "axis"), ("genes", "two genes")])
def test_without_missing_rejects_an_unknown_axis_or_leaving_too_little(axis, message):
    values = _values((3, 2, 2))
    values[0:2, 0, 0] = np.nan
    with pytest.raises(ValueError, match=message):
        Cube.without_missing(values, axis=axis)


# --- the tricluster --------------------------------------------------------------

def test_a_tricluster_sorts_its_positions():
    tricluster = Tricluster([17, 3, 42], (2, 0), iter([3, 1, 2]))
    assert (tricluster.genes, tricluster.conditions, tricluster.times) == ((3, 17, 42), (0, 2), (1, 2, 3))
    assert tricluster.size == (3, 2, 3)


def test_numpy_integers_are_positions():
    tricluster = Tricluster(np.array([4, 1]), [np.int64(0), np.int32(2)], range(3))
    assert tricluster.genes == (1, 4) and all(type(p) is int for p in tricluster.conditions)


@pytest.mark.parametrize("genes", [[1, 1], [-1, 2], [1.0, 2], [True, 2], ["a", "b"], [None]])
def test_a_tricluster_rejects_positions_that_are_not_distinct_non_negative_integers(genes):
    with pytest.raises(ValueError):
        Tricluster(genes, [0, 1], [0, 1])


def test_equality_and_hash_go_by_the_positions_and_not_the_fitness():
    first = Tricluster([1, 2], [0, 1], [0, 1], fitness=0.5)
    second = Tricluster([2, 1], [1, 0], [1, 0], fitness=0.9)
    assert first == second and hash(first) == hash(second)
    assert first != Tricluster([1, 3], [0, 1], [0, 1])
    assert len({first, second}) == 1


def test_a_tricluster_is_immutable_and_survives_pickle_and_deepcopy():
    tricluster = Tricluster([1, 2], [0, 1], [0, 1], fitness=0.25)
    with pytest.raises(AttributeError):
        tricluster.genes = (5, 6)  # type: ignore[misc]
    for clone in (pickle.loads(pickle.dumps(tricluster)), copy.deepcopy(tricluster)):
        assert clone == tricluster and clone.fitness == 0.25


def test_check_accepts_a_tricluster_that_fits():
    Tricluster([0, 5], [0, 3], [0, 4]).check(Cube(_values()))


@pytest.mark.parametrize("tricluster, message", [
    (Tricluster([0, 6], [0, 1], [0, 1]), r"genes \[6\] are beyond the 6 genes"),
    (Tricluster([0, 1], [0, 4, 7], [0, 1]), r"conditions \[4, 7\] are beyond the 4"),
    (Tricluster([0, 1], [0, 1], [5]), "two times"),
    (Tricluster([2], [0, 1], [0, 1]), "two genes"),
    (Tricluster([0, 1], [], [0, 1]), "two conditions"),
])
def test_check_rejects_what_does_not_fit_or_is_too_small(tricluster, message):
    cube = Cube(_values())
    with pytest.raises(ValueError, match=message):
        tricluster.check(cube)
    with pytest.raises(ValueError, match=message):
        cube.subcube(tricluster)


def test_the_subcube_holds_the_values_of_the_tricluster_in_the_order_of_the_cube():
    values = _values()
    cube = Cube(values)
    tricluster = Tricluster([5, 1, 3], [2, 0], [4, 1, 0])
    expected = values[[1, 3, 5]][:, [0, 2]][:, :, [0, 1, 4]]
    assert np.array_equal(cube.subcube(tricluster), expected)


def test_labels_give_the_names_of_the_positions():
    cube = Cube(_values((3, 2, 2)), genes=["x", "y", "z"], conditions=["a", "b"])
    assert Tricluster([2, 0], [1, 0], [0, 1]).labels(cube) == {
        "genes": ("x", "z"), "conditions": ("a", "b"), "times": (0, 1)}


def test_a_tricluster_comes_from_a_solution_of_three_subsets():
    domain = Domain()
    domain.define_subset("genes", list(range(10)), 2, 5)
    domain.define_subset("conditions", list(range(4)), 2, 3)
    domain.define_subset("times", list(range(6)), 2, 4)
    solution = Solution(domain)
    solution.set("genes", {7, 2})
    solution.set("conditions", [3, 1])
    solution.set("times", (0, 5, 2))
    unevaluated = Tricluster.from_solution(solution)
    assert unevaluated == Tricluster([2, 7], [1, 3], [0, 2, 5]) and unevaluated.fitness is None
    solution.evaluate(lambda s: 0.125)
    assert Tricluster.from_solution(solution).fitness == 0.125


def test_the_repr_is_readable():
    assert repr(Cube(_values((3, 2, 4)))) == "Cube(3 genes, 2 conditions, 4 times)"
    assert "genes=(1, 2)" in repr(Tricluster([2, 1], [0, 1], [0, 1]))
