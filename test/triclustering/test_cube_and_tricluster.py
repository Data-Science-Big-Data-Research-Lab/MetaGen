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

def test_integer_and_float32_values_become_floats():
    assert Cube(np.ones((2, 2, 2), dtype=np.int8)).values.dtype == np.float64
    assert Cube(np.ones((2, 2, 2), dtype=np.float32)).values.dtype == np.float64
    assert Cube(np.ones((2, 2, 2), dtype=np.uint16)).values.dtype == np.float64


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
    with pytest.raises(ValueError):
        cube.values.setflags(write=True)
    assert not np.shares_memory(cube.values, values)


@pytest.mark.parametrize("values, message", [
    (np.zeros((3, 3)), "three dimensions"),
    (np.zeros((3, 3, 3, 3)), "three dimensions"),
    (np.zeros((1, 3, 3)), "two genes"),
    (np.zeros((3, 1, 3)), "two conditions"),
    (np.zeros((3, 3, 1)), "two times"),
    ([[["a", "b"], ["c", "d"]], [["e", "f"], ["g", "h"]]], "numbers"),
    ([[["1.5", "2"], ["3", "4"]], [["5", "6"], ["7", "8"]]], "numbers"),
    (np.ones((2, 2, 2), dtype=bool), "numbers"),
    (np.ones((2, 2, 2), dtype=complex), "numbers"),
    ([[[1, 2j], [3, 4]], [[5, 6], [7, 8]]], "numbers"),
    (np.array([[[1, 2], [3, 4]], [[5, 6], [7, None]]], dtype=object), "numbers"),
    ([[[1, 2], [3]], [[4, 5], [6, 7]]], "numbers"),
])
def test_a_cube_rejects_values_of_the_wrong_shape_or_kind(values, message):
    with pytest.raises(ValueError, match=message):
        Cube(values)


@pytest.mark.parametrize("names", [{"genes": ["a"]}, {"conditions": ["a", "b", "c"]}, {"times": list(range(6))},
                                   {"times": "abcde"}])
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


@pytest.mark.parametrize("genes", [[1, 1], [-1, 2], [1.0, 2], [True, 2], ["a", "b"], [None], 5, None,
                                   [np.True_, 2], [np.float64(1), 2], [2], []])
def test_a_tricluster_rejects_positions_that_are_not_two_or_more_distinct_non_negative_integers(genes):
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
    (Tricluster([0, 1], [0, 1], [3, 5]), r"times \[5\] are beyond the 5 times"),
])
def test_check_rejects_what_does_not_fit(tricluster, message):
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


# --- triclusters of any shape ----------------------------------------------------

def _free(seed=0, shape=(6, 4, 5), count=12):
    """A set of cells drawn at random, few enough that it is not a cube."""
    rng = np.random.default_rng(seed)
    flat = rng.choice(int(np.prod(shape)), size=count, replace=False)
    return Tricluster.from_cells(*np.unravel_index(flat, shape))


def test_cells_that_make_up_a_cube_are_that_cube():
    cube = Tricluster([4, 1, 3], [0, 2], [1, 2, 3])
    genes, conditions, times = cube.cells()
    order = np.random.default_rng(0).permutation(cube.n_cells)
    again = Tricluster.from_cells(genes[order], conditions[order], times[order])
    assert again.is_cube and again == cube and hash(again) == hash(cube)
    assert (again.genes, again.conditions, again.times) == ((1, 3, 4), (0, 2), (1, 2, 3))


def test_a_cube_keeps_the_hash_of_its_three_lists():
    cube = Tricluster([4, 1, 3], [0, 2], [1, 2, 3])
    assert hash(cube) == hash((cube.genes, cube.conditions, cube.times))


def test_a_tricluster_of_any_shape_keeps_its_cells_sorted():
    steps = Tricluster.from_cells([2, 0, 1], [0, 0, 0], [2, 0, 1])
    assert not steps.is_cube and steps.n_cells == 3
    assert (steps.genes, steps.conditions, steps.times) == ((0, 1, 2), (0,), (0, 1, 2))
    assert [column.tolist() for column in steps.cells()] == [[0, 1, 2], [0, 0, 0], [0, 1, 2]]
    assert steps == Tricluster.from_cells([0, 1, 2], [0, 0, 0], [0, 1, 2])
    assert steps != Tricluster([0, 1, 2], [0, 1], [0, 1, 2])


@pytest.mark.parametrize("seed", range(6))
def test_the_cells_two_triclusters_share_are_counted_as_a_direct_count(seed):
    rng = np.random.default_rng(seed)
    shape = (6, 4, 5)
    cubes = [Tricluster(rng.choice(6, 3, replace=False), rng.choice(4, 2, replace=False),
                        rng.choice(5, 3, replace=False)) for _ in range(2)]
    triclusters = cubes + [_free(seed, shape), _free(seed + 10, shape, count=30)]
    for first in triclusters:
        for second in triclusters:
            expected = int((first.mask(shape) & second.mask(shape)).sum())
            assert first.shared_cells(second) == expected


def test_the_mask_and_the_index_mark_its_cells():
    values = _values()
    for tricluster in (Tricluster([0, 2, 5], [1, 3], [0, 4]), _free(1)):
        mask = tricluster.mask(values.shape)
        assert int(mask.sum()) == tricluster.n_cells
        assert sorted(values[tricluster.cell_index()].ravel().tolist()) == sorted(values[mask].tolist())


@pytest.mark.parametrize("cells, message", [
    (([0, 1], [0], [0, 1]), "a gene, a condition and a time each"),
    (([0, 0], [1, 1], [2, 2]), "repeat"),
    (([0], [0], [0]), "at least two cells"),
    (([0, -1], [0, 0], [0, 0]), "non-negative"),
])
def test_cells_that_are_not_a_tricluster_are_refused(cells, message):
    with pytest.raises(ValueError, match=message):
        Tricluster.from_cells(*cells)


def test_a_tricluster_of_any_shape_is_immutable_and_survives_pickle_and_deepcopy():
    steps = _free(2)
    assert pickle.loads(pickle.dumps(steps)) == steps and copy.deepcopy(steps) == steps
    with pytest.raises(AttributeError):
        steps.genes = (0, 1)
    with pytest.raises(ValueError):
        steps.cells()[0][0] = 3


def test_what_is_only_defined_on_cubes_says_so():
    from metagen.triclustering import coordinate_recall, msl
    cube, steps = Cube(_values()), _free(3)
    for call in (lambda: cube.subcube(steps), lambda: msl(cube, steps),
                 lambda: coordinate_recall(steps, Tricluster([0, 1], [0, 1], [0, 1]))):
        with pytest.raises(ValueError, match="defined for a tricluster that is a cube"):
            call()


def test_the_measures_by_cells_take_any_shape():
    from metagen.triclustering import cell_jaccard, cell_precision, cell_recall
    cube = Tricluster([0, 1, 2, 3], [0, 1], [0, 1])
    genes, conditions, times = cube.cells()
    half = Tricluster.from_cells(genes[:8], conditions[:8], times[:8])     # the cells of genes 0 and 1
    assert not half.is_cube or half.size == (2, 2, 2)
    assert cell_recall(half, cube) == 0.5 and cell_precision(half, cube) == 1.0 and cell_jaccard(half, cube) == 0.5
    corner = Tricluster.from_cells([0, 0, 1], [0, 1, 0], [0, 0, 0])
    assert cell_precision(corner, cube) == 1.0 and cell_recall(corner, cube) == 3 / 16
