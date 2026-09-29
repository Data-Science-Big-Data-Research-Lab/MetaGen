"""Cubes with planted triclusters: each planted block has the pattern it says, none
share a cell, the rest is standard normal noise, and a seed reproduces the cube."""
import numpy as np
import pytest

from metagen.framework.rng import set_seed
from metagen.triclustering import Cube, Tricluster, cell_jaccard, lsl, msl, msr3d, plant

SIZES = [(12, 3, 4), (8, 4, 5), (10, 2, 6)]


def _log_block(cube, tricluster):
    block = cube.subcube(tricluster)
    assert (block > 0).all()
    return Cube(np.log(block))


def test_the_triclusters_have_the_sizes_asked_for_fit_and_share_no_cell():
    cube, planted = plant((60, 6, 8), SIZES, seed=0)
    assert cube.shape == (60, 6, 8)
    assert [tricluster.size for tricluster in planted] == SIZES
    for tricluster in planted:
        tricluster.check(cube)
    for first, second in zip(planted, planted[1:]):
        assert cell_jaccard(first, second) == 0.0 and not set(first.genes) & set(second.genes)


@pytest.mark.parametrize("seed", range(5))
def test_a_constant_block_is_one_value(seed):
    cube, planted = plant((40, 5, 6), SIZES[:2], pattern="constant", seed=seed)
    for tricluster in planted:
        block = cube.subcube(tricluster)
        assert np.ptp(block) == 0.0 and -3.0 <= block.flat[0] <= 3.0
        assert msr3d(cube, tricluster) < 1e-28 and msl(cube, tricluster) == 0.0 and lsl(cube, tricluster) == 0.0


@pytest.mark.parametrize("seed", range(5))
def test_an_additive_block_has_no_residue_and_a_multiplicative_one_none_on_its_logarithm(seed):
    cube, planted = plant((40, 5, 6), SIZES[:2], pattern="additive", seed=seed)
    for tricluster in planted:
        assert msr3d(cube, tricluster) < 1e-25
    cube, planted = plant((40, 5, 6), SIZES[:2], pattern="multiplicative", seed=seed)
    for tricluster in planted:
        logarithm = _log_block(cube, tricluster)
        assert msr3d(logarithm, Tricluster(*(range(n) for n in tricluster.size))) < 1e-25
        assert msr3d(cube, tricluster) > 1e-6


def test_noise_moves_the_block_off_its_pattern_by_about_as_much():
    for noise in (0.01, 0.1, 1.0):
        cube, planted = plant((200, 10, 12), [(100, 8, 10)], pattern="constant", noise=noise, seed=1)
        assert np.std(cube.subcube(planted[0])) == pytest.approx(noise, rel=0.1)


def test_outside_the_triclusters_the_values_are_standard_normal():
    cube, planted = plant((300, 10, 12), SIZES, pattern="additive", seed=2)
    outside = np.ones(cube.shape, dtype=bool)
    for tricluster in planted:
        outside[np.ix_(tricluster.genes, tricluster.conditions, tricluster.times)] = False
    values = cube.values[outside]
    assert abs(values.mean()) < 0.03 and abs(values.std() - 1.0) < 0.03


def test_the_same_seed_gives_the_same_cube_and_another_seed_another():
    first, planted_first = plant((50, 6, 8), SIZES, seed=7)
    second, planted_second = plant((50, 6, 8), SIZES, seed=7)
    third, _ = plant((50, 6, 8), SIZES, seed=8)
    assert np.array_equal(first.values, second.values) and planted_first == planted_second
    assert not np.array_equal(first.values, third.values)


def test_without_a_seed_it_follows_metagens_generator_and_leaves_numpys_global_one_alone():
    np.random.seed(123)
    expected_global = np.random.random()
    np.random.seed(123)
    set_seed(5)
    first, _ = plant((50, 6, 8), SIZES)
    set_seed(5)
    second, _ = plant((50, 6, 8), SIZES)
    assert np.array_equal(first.values, second.values)
    assert np.random.random() == expected_global


@pytest.mark.parametrize("arguments, message", [
    ({"shape": (10, 5)}, "three integers"),
    ({"shape": (10, 1, 5)}, "three integers"),
    ({"shape": (10.0, 5, 5)}, "three integers"),
    ({"sizes": [(3, 2)]}, "three integers"),
    ({"sizes": [(3, 1, 2)]}, "three integers"),
    ({"sizes": [(3, 9, 2)]}, "does not fit"),
    ({"sizes": [(6, 2, 2), (5, 2, 2)]}, "genes"),
    ({"pattern": "shifting"}, "pattern"),
    ({"noise": -0.1}, "negative"),
])
def test_what_cannot_be_planted_is_rejected(arguments, message):
    call = {"shape": (10, 5, 5), "sizes": [(3, 2, 2)], **arguments}
    with pytest.raises(ValueError, match=message):
        plant(**call)


def test_a_search_can_tell_a_planted_tricluster_from_the_rest():
    """The reason for planting them: the planted block is far more coherent than a
    block of the same size elsewhere."""
    cube, planted = plant((80, 6, 10), [(15, 3, 6)], pattern="additive", noise=0.05, seed=3)
    target = planted[0]
    others = [g for g in range(80) if g not in target.genes][:15]
    elsewhere = Tricluster(others, target.conditions, target.times)
    assert msr3d(cube, target) < 0.01 < msr3d(cube, elsewhere)
