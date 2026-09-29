"""GRQ, PEQ, SPQ and TRIQ: against values computed by the original implementation,
against scipy's correlations pair by pair, and on cases whose value is known."""
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import pearsonr, spearmanr

import metagen.triclustering.quality as quality
from metagen.triclustering import Cube, Tricluster, grq, msl, peq, spq, triq

REFERENCE = json.loads((Path(__file__).parent / "data" / "reference.json").read_text())
SYNTHETIC = Cube(np.array(REFERENCE["synthetic"]["values"]))


def _close(mine, theirs, tolerance=1e-12):
    return abs(mine - theirs) <= tolerance * max(1.0, abs(theirs))


def _whole(shape):
    return Tricluster(*(range(size) for size in shape))


# --- against the reference values ------------------------------------------------

@pytest.mark.parametrize("case", REFERENCE["synthetic"]["cases"], ids=lambda case: case["id"])
def test_the_qualities_match_the_reference_values(case):
    """The reference counts a pair with a flat profile as 0 and uses the gene view twice
    and the time view once: flat_profiles="zero" and views="trlab"."""
    given = case["input"]
    tricluster = Tricluster(given["genes"], given["conditions"], given["times"])
    expected = case["triq"]
    assert _close(grq(SYNTHETIC, tricluster, views="trlab"), expected["grq"])
    assert _close(peq(SYNTHETIC, tricluster, flat_profiles="zero"), expected["peq"])
    assert _close(spq(SYNTHETIC, tricluster, flat_profiles="zero"), expected["spq"])
    assert _close(triq(SYNTHETIC, tricluster, views="trlab", flat_profiles="zero"), expected["triq_common"])


# --- against scipy, pair by pair --------------------------------------------------

def _literal(values, rank, flat_profiles):
    """Every pair of (gene, condition) profiles over time, one by one, with scipy."""
    genes, conditions, _ = values.shape
    profiles = [values[g, c, :] for g in range(genes) for c in range(conditions)]
    correlate = spearmanr if rank else pearsonr
    scores = []
    for first, second in itertools.combinations(profiles, 2):
        if np.ptp(first) == 0 or np.ptp(second) == 0:
            if flat_profiles == "zero":
                scores.append(0.0)
            continue
        scores.append(abs(correlate(first, second)[0]))
    return float(np.mean(scores)) if scores else math.nan


def _with_flat_profiles(shape, seed):
    rng = np.random.default_rng(seed)
    values = rng.normal(size=shape)
    values[0, 0, :] = 1.5                                      # a flat profile
    values[-1, -1, :] = np.round(rng.normal(size=shape[2]))    # ties, for Spearman
    return values


@pytest.mark.parametrize("shape", [(2, 2, 3), (3, 2, 4), (5, 3, 6), (4, 4, 2), (6, 2, 5)])
@pytest.mark.parametrize("flat_profiles", ["exclude", "zero"])
def test_peq_and_spq_match_scipy_pair_by_pair(shape, flat_profiles):
    values = _with_flat_profiles(shape, seed=sum(shape))
    cube, whole = Cube(values), _whole(shape)
    assert math.isclose(peq(cube, whole, flat_profiles), _literal(values, False, flat_profiles), rel_tol=1e-12)
    assert math.isclose(spq(cube, whole, flat_profiles), _literal(values, True, flat_profiles), rel_tol=1e-12)


def test_the_correlations_are_worked_out_by_blocks_the_same(monkeypatch):
    values = _with_flat_profiles((9, 4, 7), seed=3)
    cube, whole = Cube(values), _whole((9, 4, 7))
    at_once = [peq(cube, whole), spq(cube, whole), peq(cube, whole, "zero")]
    monkeypatch.setattr(quality, "_BLOCK", 5)
    by_blocks = [peq(cube, whole), spq(cube, whole), peq(cube, whole, "zero")]
    assert np.allclose(at_once, by_blocks, rtol=1e-12)


# --- values known in advance ------------------------------------------------------

def test_profiles_that_are_straight_lines_of_one_another_are_perfectly_correlated():
    times = np.arange(6.0)
    values = np.stack([times, 3 * times - 2, -0.5 * times + 7, 10 - times]).reshape(2, 2, 6)
    cube, whole = Cube(values), _whole((2, 2, 6))
    assert math.isclose(peq(cube, whole), 1.0) and math.isclose(spq(cube, whole), 1.0)


def test_spearman_counts_profiles_that_move_together_without_being_lines():
    times = np.arange(1.0, 7.0)
    values = np.stack([times, times ** 3, np.exp(times), np.sqrt(times)]).reshape(2, 2, 6)
    cube, whole = Cube(values), _whole((2, 2, 6))
    assert math.isclose(spq(cube, whole), 1.0)
    assert peq(cube, whole) < 0.99


def test_flat_profiles_are_left_out_or_counted_as_zero():
    """Three profiles that rise and one flat, under two conditions: six of the eight
    profiles vary, 15 pairs of 28."""
    rising = np.arange(5.0)
    values = np.stack([rising, 2 * rising + 1, -rising, np.full(5, 3.0)]).reshape(4, 1, 5).repeat(2, axis=1)
    cube, whole = Cube(values), _whole((4, 2, 5))
    assert peq(cube, whole) == 1.0 and spq(cube, whole) == 1.0
    assert math.isclose(peq(cube, whole, flat_profiles="zero"), 15 / 28)


def _one_varying():
    values = np.full((3, 2, 4), 2.0)
    values[1, 0] = [1.0, 5.0, 2.0, 3.0]
    return values


@pytest.mark.parametrize("values", [np.full((3, 2, 4), 2.0), _one_varying()], ids=["all flat", "one varies"])
def test_with_fewer_than_two_varying_profiles_the_correlation_is_not_defined(values):
    cube, whole = Cube(values), _whole(values.shape)
    assert math.isnan(peq(cube, whole)) and math.isnan(spq(cube, whole))
    assert peq(cube, whole, flat_profiles="zero") == 0.0 and spq(cube, whole, flat_profiles="zero") == 0.0


def test_reordering_genes_conditions_or_all_the_times_changes_nothing_and_one_profile_does():
    """A correlation does not depend on the order of the observations as long as every
    profile is reordered alike; reordering the times of one profile alone changes it."""
    rng = np.random.default_rng(4)
    values = rng.normal(size=(6, 3, 7))
    whole = _whole((6, 3, 7))
    one_profile = values.copy()
    one_profile[2, 1] = one_profile[2, 1, rng.permutation(7)]
    for measure in (peq, spq):
        original = measure(Cube(values), whole)
        assert math.isclose(original, measure(Cube(values[rng.permutation(6)][:, rng.permutation(3)]), whole),
                            rel_tol=1e-12)
        assert math.isclose(original, measure(Cube(values[:, :, rng.permutation(7)]), whole), rel_tol=1e-12)
        assert not math.isclose(original, measure(Cube(one_profile), whole), rel_tol=1e-6)


@pytest.mark.parametrize("seed", range(15))
def test_every_quality_is_between_zero_and_one(seed):
    rng = np.random.default_rng(seed)
    shape = tuple(int(n) for n in rng.integers(2, 7, size=3))
    values = rng.normal(size=shape) * 10 ** rng.uniform(-3, 3)
    cube, whole = Cube(values), _whole(shape)
    for value in (grq(cube, whole), peq(cube, whole), spq(cube, whole), triq(cube, whole),
                  triq(cube, whole, bioq=0.3), peq(cube, whole, "zero")):
        assert 0.0 <= value <= 1.0


def test_grq_is_one_minus_msl_over_two_pi():
    whole = Tricluster(range(5), range(3), range(4))
    for views in ("distinct", "time", "trlab"):
        assert grq(SYNTHETIC, whole, views=views) == 1.0 - msl(SYNTHETIC, whole, views=views) / (2 * math.pi)


def test_triq_is_the_weighted_mean_of_the_qualities():
    tricluster = Tricluster(range(4), range(3), range(5))
    g, p, s = grq(SYNTHETIC, tricluster), peq(SYNTHETIC, tricluster), spq(SYNTHETIC, tricluster)
    assert math.isclose(triq(SYNTHETIC, tricluster), 0.8 * g + 0.1 * p + 0.1 * s)
    assert math.isclose(triq(SYNTHETIC, tricluster, bioq=0.002), 0.4 * g + 0.05 * p + 0.05 * s + 0.5 * 0.002)
    assert math.isclose(triq(SYNTHETIC, tricluster, weights={"grq": 2, "peq": 1, "spq": 1}), (2 * g + p + s) / 4)


def test_triq_leaves_out_a_quality_that_is_not_defined():
    values = np.full((3, 2, 4), 2.0)
    values[0, 0] = [1.0, 2.0, 3.0, 4.0]          # one profile varies: no pair to correlate
    cube, whole = Cube(values), _whole((3, 2, 4))
    assert math.isnan(peq(cube, whole))
    assert triq(cube, whole) == grq(cube, whole)
    assert math.isclose(triq(cube, whole, bioq=0.5), (0.4 * grq(cube, whole) + 0.5 * 0.5) / 0.9)


@pytest.mark.parametrize("arguments", [
    {"weights": {"grq": 1, "peq": 1}},
    {"weights": {"grq": 1, "peq": 1, "spq": 1, "bioq": 1}},
    {"bioq": 0.1, "weights": {"grq": 1, "peq": 1, "spq": 1}},
    {"weights": {"grq": 1, "peq": -1, "spq": 1}},
    {"weights": {"grq": 0, "peq": 0, "spq": 0}},
    {"flat_profiles": "drop"},
    {"views": "all"},
])
def test_triq_rejects_weights_or_options_that_do_not_fit(arguments):
    with pytest.raises(ValueError):
        triq(SYNTHETIC, Tricluster(range(4), range(3), range(5)), **arguments)
