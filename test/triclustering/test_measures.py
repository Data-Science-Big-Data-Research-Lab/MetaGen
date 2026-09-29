"""MSR3D, LSL and MSL: against values computed by the original implementation, against a
literal, loop-by-loop reading of their definitions, and on cases whose value is known."""
import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pytest

from metagen.triclustering import Cube, Tricluster, lsl, msl, msr3d

REFERENCE = json.loads((Path(__file__).parent / "data" / "reference.json").read_text())
SYNTHETIC = Cube(np.array(REFERENCE["synthetic"]["values"]))
TOLERANCE = 1e-12


def _close(mine, theirs):
    return abs(mine - theirs) <= TOLERANCE * max(1.0, abs(theirs))


def _tricluster(positions):
    return Tricluster(positions["genes"], positions["conditions"], positions["times"])


# --- against the reference values ------------------------------------------------

@pytest.mark.parametrize("case", REFERENCE["synthetic"]["cases"], ids=lambda case: case["id"])
def test_the_measures_match_the_reference_values(case):
    """In the reference, views 0 and 1 have the genes on the X axis and view 2 the
    times; the value is their mean. The positions are given as the case gives them,
    unsorted in some, and the tricluster sorts them."""
    tricluster = _tricluster(case["input"])
    assert tricluster == _tricluster(case["effective"])
    assert _close(msr3d(SYNTHETIC, tricluster), case["msr3d"])
    for measure, name in ((msl, "msl"), (lsl, "lsl")):
        gene_view, _, time_view = case[name]["views"]
        assert _close(measure(SYNTHETIC, tricluster, views="trlab"), case[name]["raw"])
        assert _close(measure(SYNTHETIC, tricluster, views="time"), time_view)
        assert _close(measure(SYNTHETIC, tricluster, views="trlab", normalized=True), case[name]["raw"] / (2 * math.pi))
        # The gene view alone: three times the "trlab" value is twice it plus the time view.
        assert _close((3 * measure(SYNTHETIC, tricluster, views="trlab") - time_view) / 2, gene_view)


@pytest.mark.parametrize("case", REFERENCE["spin"]["cases"], ids=lambda case: case["id"])
def test_a_slope_just_below_zero_turns_into_almost_two_pi(case):
    """Three series that look alike, flat to the eye: one rising by 1e-9 per gene, one
    falling by as much, one flat. The angle of a negative slope has 2π added, which is
    the published definition, so rising against falling is the largest difference."""
    cube = Cube(np.array(REFERENCE["spin"]["values"]))
    tricluster = _tricluster(case["effective"])
    assert _close(msl(cube, tricluster, views="trlab"), case["msl"]["raw"])
    assert _close(lsl(cube, tricluster, views="trlab"), case["lsl"]["raw"])


# --- against a literal reading of the definitions -------------------------------

ON_X = {"genes": (1, 0, 2), "times": (0, 2, 1), "conditions": (0, 1, 2)}
VIEWS = {"distinct": [("genes", 1), ("times", 1), ("conditions", 1)], "time": [("times", 1)],
         "trlab": [("genes", 2), ("times", 1)]}


def _turn(angle):
    return angle + 2 * math.pi if angle < 0 else angle


def _literal_view(values, kind):
    """values[series][x][panel]: every pair of series in a panel and every pair of
    panels of a series, one by one."""
    series, points, panels = values.shape
    x = np.arange(1, points + 1)

    def shape(s, p):
        y = values[s, :, p]
        if kind == "msl":
            return [_turn(math.atan(y[k + 1] - y[k])) for k in range(points - 1)]
        return [_turn(math.atan(np.polyfit(x, y, 1)[0]))]

    differences = []
    for s in range(series):
        for p, q in itertools.combinations(range(panels), 2):
            differences.append(np.mean(np.abs(np.subtract(shape(s, p), shape(s, q)))))
    for p in range(panels):
        for s, r in itertools.combinations(range(series), 2):
            differences.append(np.mean(np.abs(np.subtract(shape(s, p), shape(r, p)))))
    return float(np.mean(differences))


def _literal(values, kind, views):
    chosen = VIEWS[views]
    total = sum(weight * _literal_view(np.transpose(values, ON_X[axis]), kind) for axis, weight in chosen)
    return total / sum(weight for _, weight in chosen)


def _literal_msr3d(values):
    g, c, t = values.shape
    total = 0.0
    for i, j, k in itertools.product(range(g), range(c), range(t)):
        residue = (values[i, j, k] - values[i, j, :].mean() - values[i, :, k].mean() - values[:, j, k].mean()
                   + values[i].mean() + values[:, j].mean() + values[:, :, k].mean() - values.mean())
        total += residue ** 2
    return total / values.size


@pytest.mark.parametrize("shape", [(2, 2, 2), (3, 2, 4), (5, 3, 2), (7, 4, 5), (2, 6, 3)])
@pytest.mark.parametrize("views", ["distinct", "time", "trlab"])
def test_the_measures_match_a_literal_reading_of_their_definitions(shape, views):
    rng = np.random.default_rng(sum(shape))
    values = rng.normal(size=shape) * rng.choice([0.1, 1.0, 10.0])
    cube = Cube(values)
    whole = Tricluster(*(range(size) for size in shape))
    assert math.isclose(msl(cube, whole, views=views), _literal(values, "msl", views), rel_tol=1e-12)
    assert math.isclose(lsl(cube, whole, views=views), _literal(values, "lsl", views), rel_tol=1e-9)
    assert math.isclose(msr3d(cube, whole), _literal_msr3d(values), rel_tol=1e-12, abs_tol=1e-15)


def test_a_part_of_the_cube_is_measured_on_its_own_values():
    values = np.random.default_rng(1).normal(size=(9, 5, 7))
    cube = Cube(values)
    tricluster = Tricluster([8, 1, 4], [3, 0], [6, 2, 5, 0])
    part = values[np.ix_([1, 4, 8], [0, 3], [0, 2, 5, 6])]
    for views in VIEWS:
        assert math.isclose(msl(cube, tricluster, views=views), _literal(part, "msl", views), rel_tol=1e-12)


# --- values known in advance ------------------------------------------------------

def _grid(shape):
    return np.meshgrid(*(np.arange(size, dtype=float) for size in shape), indexing="ij")


def test_the_three_views_on_a_case_worked_out_by_hand():
    """Two genes, three conditions, two times, with x = gene · condition: each gene is a
    line over the conditions with slope 0 or 1, and nothing changes over time.

    - Conditions on the X axis: series gene 0 (angles 0, 0) and gene 1 (π/4, π/4) in
      each of the two panels; two pairs in panels differ by π/4, two pairs of panels by
      0: π/8.
    - Genes on the X axis: series condition 0, 1 and 2 with slopes 0, 1 and 2, one
      segment each, in each of the two panels; three pairs per panel differ by π/4,
      arctan 2 and arctan 2 − π/4, six in all, and three pairs of panels by 0:
      4 · arctan 2 / 9.
    - Times on the X axis: every series is flat: 0.
    """
    genes, conditions, _ = np.meshgrid(np.arange(2.0), np.arange(3.0), np.arange(2.0), indexing="ij")
    cube = Cube(genes * conditions)
    whole = Tricluster(range(2), range(3), range(2))
    along_conditions, along_genes = math.pi / 8, 4 * math.atan(2) / 9
    assert math.isclose(msl(cube, whole, views="distinct"), (along_conditions + along_genes + 0.0) / 3, rel_tol=1e-12)
    assert math.isclose(msl(cube, whole, views="trlab"), 2 * along_genes / 3, rel_tol=1e-12)
    assert msl(cube, whole, views="time") == 0.0
    # With straight lines, the least squares line is the line itself.
    for views in VIEWS:
        assert math.isclose(lsl(cube, whole, views=views), msl(cube, whole, views=views), rel_tol=1e-12)


def test_a_flat_series_of_any_values_has_slope_zero():
    """Rows that are flat but hold values like 0.3 or -1.7: a least squares slope worked
    out from raw sums comes out as ±1e-17, and the side of zero decides between an angle
    of 0 and one of 2π."""
    rows = np.random.default_rng(4).normal(size=(10, 1, 1))
    cube = Cube(np.broadcast_to(rows, (10, 3, 7)))
    whole = Tricluster(range(10), range(3), range(7))
    assert lsl(cube, whole, views="time") == 0.0 and msl(cube, whole, views="time") == 0.0
    assert lsl(cube, whole) < 1e-15


def test_the_residue_keeps_its_precision_far_from_zero():
    noise = np.random.default_rng(5).normal(size=(5, 3, 4)) * 1e-3
    whole = Tricluster(range(5), range(3), range(4))
    assert math.isclose(msr3d(Cube(noise + 1e6), whole), msr3d(Cube(noise), whole), rel_tol=1e-6)


def test_a_nan_comes_through_the_pair_differences():
    from metagen.triclustering.measures import _pair_sums
    assert math.isnan(_pair_sums(np.array([[[1.0, np.nan, 2.0]]]), axis=2))
    assert _pair_sums(np.full((1, 1, 4), 0.1), axis=2) == 0.0


@pytest.mark.parametrize("views", ["distinct", "time", "trlab"])
def test_a_constant_block_measures_zero(views):
    cube = Cube(np.full((4, 3, 5), 2.5))
    whole = Tricluster(range(4), range(3), range(5))
    assert msl(cube, whole, views=views) == 0.0 and lsl(cube, whole, views=views) == 0.0
    assert msr3d(cube, whole) < 1e-28


def test_an_additive_block_has_no_residue():
    genes, conditions, times = _grid((5, 3, 4))
    cube = Cube(3.0 * genes - 2.0 * conditions + 0.5 * times + 7.0)
    assert msr3d(cube, Tricluster(range(5), range(3), range(4))) < 1e-25


def test_series_that_share_one_line_over_time_measure_zero_in_the_time_view():
    genes, conditions, times = _grid((6, 3, 5))
    cube = Cube(2.0 * times + 10.0 * genes - 3.0 * conditions)        # parallel lines over time
    whole = Tricluster(range(6), range(3), range(5))
    assert msl(cube, whole, views="time") == 0.0 and lsl(cube, whole, views="time") == 0.0
    # Along the genes and the conditions the series are parallel lines too; the angles
    # there are not exact in floating point, so zero up to rounding.
    assert msl(cube, whole) < 1e-15 and lsl(cube, whole) < 1e-15


def test_the_time_view_does_not_depend_on_the_order_of_genes_or_conditions_and_the_others_do():
    rng = np.random.default_rng(2)
    values = rng.normal(size=(6, 4, 5))
    shuffled = values[rng.permutation(6)][:, rng.permutation(4)]
    whole = Tricluster(range(6), range(4), range(5))
    original, reordered = Cube(values), Cube(shuffled)
    for measure in (msl, lsl):
        assert math.isclose(measure(original, whole, views="time"), measure(reordered, whole, views="time"),
                            rel_tol=1e-12)
        assert not math.isclose(measure(original, whole), measure(reordered, whole), rel_tol=1e-6)
    assert math.isclose(msr3d(original, whole), msr3d(reordered, whole), rel_tol=1e-12)
    times_shuffled = values[:, :, rng.permutation(5)]
    assert math.isclose(msr3d(original, whole), msr3d(Cube(times_shuffled), whole), rel_tol=1e-12)


@pytest.mark.parametrize("seed", range(20))
def test_lsl_and_msl_stay_within_zero_and_two_pi(seed):
    rng = np.random.default_rng(seed)
    shape = tuple(rng.integers(2, 7, size=3))
    cube = Cube(rng.normal(size=shape) * 10 ** rng.uniform(-3, 3))
    tricluster = Tricluster(*(range(size) for size in shape))
    for measure in (msl, lsl):
        for views in VIEWS:
            assert 0.0 <= measure(cube, tricluster, views=views) <= 2 * math.pi
            assert 0.0 <= measure(cube, tricluster, views=views, normalized=True) <= 1.0


def test_an_unknown_choice_of_views_is_rejected():
    whole = Tricluster(range(2), range(2), range(2))
    for measure in (msl, lsl):
        with pytest.raises(ValueError, match="views"):
            measure(Cube(np.zeros((2, 2, 2))), whole, views="all")


def test_a_tricluster_that_does_not_fit_is_rejected():
    with pytest.raises(ValueError, match="beyond"):
        msl(SYNTHETIC, Tricluster([0, 99], [0, 1], [0, 1]))


def test_the_pair_differences_take_n_log_n_and_not_n_squared():
    """A tricluster of 200 genes: the literal reading compares every pair of the 200
    series one by one; this does it sorting, and has to be far faster."""
    values = np.random.default_rng(3).normal(size=(200, 4, 8))
    cube = Cube(values)
    tricluster = Tricluster(range(200), range(4), range(8))
    start = time.perf_counter()
    fast = msl(cube, tricluster, views="time")
    fast_seconds = time.perf_counter() - start
    start = time.perf_counter()
    slow = _literal(values, "msl", "time")
    slow_seconds = time.perf_counter() - start
    assert math.isclose(fast, slow, rel_tol=1e-12)
    assert fast_seconds * 10 < slow_seconds
