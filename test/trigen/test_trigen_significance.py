"""TriGen scoring a tricluster by its significance: how unlikely its quality is among random
triclusters of its same size, with no size term, so that the best score is the whole of a
pattern and the largest sizes are not needed to keep the triclusters to it."""
import numpy as np
import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriclusterFitness, TriGen
from metagen.metaheuristics.trigen.trigen import grow
from metagen.triclustering import Tricluster, cell_precision, plant, recovery, relevance

CUBE, (BLOCK, OTHER) = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
OUTSIDE = [gene for gene in range(100) if gene not in BLOCK.genes and gene not in OTHER.genes]


def _fitness(seed=0, **arguments):
    set_seed(seed)
    fitness = TriclusterFitness(CUBE, scoring="significance", **arguments)
    fitness.fit_chance()
    return fitness


def test_the_whole_pattern_is_more_significant_than_its_parts_and_than_with_noise():
    fitness = _fitness()
    whole = fitness.significance(BLOCK)
    parts = [Tricluster(BLOCK.genes[:n], BLOCK.conditions[:c], BLOCK.times[:t]) for n, c, t in ((5, 2, 3), (10, 3, 4), (15, 4, 5))]
    noisy = [Tricluster(list(BLOCK.genes) + OUTSIDE[:n], BLOCK.conditions, BLOCK.times) for n in (2, 5, 20)]
    assert all(fitness.significance(part) < whole for part in parts)
    assert all(fitness.significance(tricluster) < whole for tricluster in noisy)
    assert [fitness.significance(t) for t in parts] == sorted(fitness.significance(t) for t in parts)
    assert whole > 20


def test_noise_and_the_whole_cube_are_about_as_significant_as_chance():
    fitness = _fitness()
    assert abs(fitness.significance(Tricluster(OUTSIDE[:20], range(4), range(6)))) < 3
    assert abs(fitness.significance(Tricluster(range(100), range(10), range(12)))) < 3


def test_only_the_significance_not_already_found_counts():
    """The fitness is minus the significance of the tricluster less the largest it shares
    with one found: the tricluster found scores 0, and padded with noise it scores worse,
    while a new pattern that shares only conditions and times keeps its whole score."""
    fitness = _fitness()
    z = fitness.significance(BLOCK)
    assert fitness.terms(BLOCK)["z"] == z and fitness.terms(BLOCK)["z_found"] == 0.0
    assert fitness.evaluate(BLOCK) == -z
    fitness.found.append(BLOCK)
    assert fitness.evaluate(BLOCK) == 0.0
    others = [time for time in range(12) if time not in BLOCK.times][:2]
    padded = [Tricluster(list(BLOCK.genes) + OUTSIDE[:5], BLOCK.conditions, BLOCK.times),
              Tricluster(BLOCK.genes, list(BLOCK.conditions) + [c for c in range(10) if c not in BLOCK.conditions][:2],
                         list(BLOCK.times) + others)]
    assert all(fitness.evaluate(tricluster) > 0.0 for tricluster in padded)
    sharing = Tricluster(OTHER.genes, OTHER.conditions, OTHER.times)
    assert not set(sharing.genes) & set(BLOCK.genes)
    assert fitness.evaluate(sharing) == -fitness.significance(sharing) < 0.0


def test_a_tricluster_no_better_than_chance_scores_above_zero():
    fitness = _fitness()
    noise = Tricluster(OUTSIDE[:20], range(4), range(6))
    assert fitness.evaluate(noise) == -fitness.significance(noise)
    assert fitness.evaluate(noise) > fitness.evaluate(BLOCK)


def test_the_model_of_chance_comes_from_the_seed():
    assert _fitness(seed=1).significance(BLOCK) == _fitness(seed=1).significance(BLOCK)
    assert _fitness(seed=1).significance(BLOCK) != _fitness(seed=2).significance(BLOCK)


def test_each_run_fits_the_model_of_chance_anew():
    """A model fitted before, from another seed, does not change what a run finds."""
    arguments = dict(n_triclusters=2, generations=5, population_size=12, min_sizes=(3, 2, 2), max_sizes=(30, 6, 8),
                     scoring="significance", seed=4)
    expected = TriGen(CUBE, **arguments).run()
    trigen = TriGen(CUBE, **arguments)
    set_seed(99)
    trigen.fitness.fit_chance()
    assert trigen.run() == expected


def test_pruning_removes_what_does_not_follow_the_pattern():
    """From the block with five genes of noise and a time it lacks, growing by the
    significance with pruning ends at the block; without pruning it cannot remove them."""
    fitness = _fitness()
    times = list(BLOCK.times) + [time for time in range(12) if time not in BLOCK.times][:1]
    start = Tricluster(list(BLOCK.genes) + OUTSIDE[:5], BLOCK.conditions, times)
    sizes = ((2, 100), (2, 10), (2, 12))
    pruned, _ = grow(start, fitness.evaluate, sizes, CUBE.shape, pruning=True)
    assert pruned == BLOCK
    kept, _ = grow(start, fitness.evaluate, sizes, CUBE.shape)
    assert set(start.genes) <= set(kept.genes)


def test_pruning_stops_when_no_step_lowers_the_score():
    """With every step leaving the score equal, pruning takes none: it never cycles."""
    start = Tricluster(range(6), range(3), range(4))
    pruned, evaluations = grow(start, lambda tricluster: 1.0, ((2, 10), (2, 5), (2, 6)), CUBE.shape, pruning=True)
    assert pruned == start and evaluations > 1


def test_pruning_stops_at_the_smallest_sizes():
    shrinking = lambda tricluster: float(sum(tricluster.size))   # noqa: E731
    start = Tricluster(range(8), range(5), range(6))
    pruned, _ = grow(start, shrinking, ((3, 8), (2, 5), (4, 6)), CUBE.shape, pruning=True)
    assert pruned.size == (3, 2, 4)


def test_pruning_is_on_with_the_significance_unless_said_otherwise():
    assert TriGen(CUBE, scoring="significance").pruning is True
    assert TriGen(CUBE).pruning is False
    assert TriGen(CUBE, scoring="significance", pruning=False).pruning is False
    assert TriGen(CUBE, pruning=True).pruning is True
    assert TriGen(CUBE, scoring="significance", growth="quality").pruning is False


@pytest.mark.parametrize("arguments", [{"scoring": "pareto"},
                                       {"scoring": "significance", "weights": {"quality": 1.0}}])
def test_options_out_of_range_are_rejected(arguments):
    with pytest.raises(ValueError):
        TriclusterFitness(CUBE, **arguments)


def test_the_same_seed_gives_the_same_triclusters_and_running_again_starts_over():
    trigen = TriGen(CUBE, n_triclusters=2, generations=5, population_size=12, min_sizes=(3, 2, 2),
                    max_sizes=(30, 6, 8), scoring="significance", seed=4)
    first = trigen.run()
    assert first == trigen.run()
    assert all("z" in record["terms"] for record in trigen.history)


def test_without_largest_sizes_it_recovers_the_planted_triclusters():
    """Two additive triclusters planted in noise, a population of 100 over 50 generations,
    and no largest sizes: the significance keeps the triclusters to the patterns."""
    # On these five seeds: recovery (Jaccard) 0.83 on average, from 0.50 to 1.0, and
    # precision 0.88. Over 30 seeds without largest sizes the weighted fitness recovers
    # 0.03, taking in nearly the whole cube (bench block 6).
    found_recovery, found_precision = [], []
    for seed in range(5):
        cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=seed)
        found = TriGen(cube, n_triclusters=2, generations=50, population_size=100, min_sizes=(5, 2, 3),
                       scoring="significance", seed=seed).run()
        found_recovery.append(recovery(found, planted))
        found_precision.append(relevance(found, planted, cell_precision))
    assert np.mean(found_recovery) >= 0.6 and np.mean(found_precision) >= 0.7
