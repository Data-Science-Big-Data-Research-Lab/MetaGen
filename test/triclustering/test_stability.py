"""How much the triclusters of several runs recur in the others, and the null cube."""
import math

import numpy as np
import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriGen
from metagen.triclustering import Cube, Stability, null_cube, plant, stability


def test_runs_that_find_the_same_genes_are_fully_stable_and_disjoint_runs_not_at_all():
    same = stability([[{"a", "b", "c"}], [{"a", "b", "c"}], [{"c", "b", "a"}]], population=10)
    assert all(found == Stability(1.0, found.chance, ("a", "b", "c")) for run in same for found in run)
    apart = stability([[{"a", "b", "c"}], [{"d", "e", "f"}]], population=10)
    assert apart[0][0].stability == 0.0 and apart[0][0].core == ()


def test_what_chance_would_give_is_that_of_random_genes_of_the_same_sizes():
    found = stability([[["a", "b", "c"]], [["d", "e", "f", "g"], ["h", "i"]]], population=10)[0][0]
    pairs = 10 * 9 / 2
    assert found.chance == pytest.approx(1 - (1 - 6 / pairs) * (1 - 1 / pairs))


def test_a_pair_counts_once_even_when_the_triclusters_of_a_run_overlap():
    found = stability([[["a", "b", "c", "d"]], [["a", "b", "x"], ["a", "b", "y"], ["c", "d"]]], population=20)[0][0]
    assert found.stability == pytest.approx(2 / 6)


def test_the_core_keeps_the_genes_that_turn_up_with_the_tricluster_in_enough_runs():
    runs = [[["a", "b", "c", "d", "e"]], [["a", "b", "c", "z"]], [["a", "b", "y"]], [["a", "q", "r"]], [["s", "t"]]]
    first = stability(runs, population=30)[0][0]
    assert first.core == ("a", "b")
    assert stability(runs, population=30, share=0.25)[0][0].core == ("a", "b", "c")
    assert stability(runs, population=30, share=1.0)[0][0].core == ()


def test_repeated_names_count_once_and_a_tricluster_of_one_gene_has_no_pairs():
    runs = [[["a", "a", "b"], ["p1", "p1"]], [["a", "b"]]]
    first = stability(runs, population=10)[0]
    assert first[0].stability == 1.0 and math.isnan(first[1].stability) and math.isnan(first[1].chance)


def test_what_cannot_be_compared_says_so():
    with pytest.raises(ValueError, match="at least two"):
        stability([[["a", "b"]]], population=10)
    with pytest.raises(ValueError, match="population"):
        stability([[["a", "b"]], [["a", "b"]]])
    with pytest.raises(ValueError, match="smaller than a tricluster"):
        stability([[["a", "b", "c"]], [["a", "b"]]], population=2)
    with pytest.raises(ValueError, match="share"):
        stability([[["a", "b"]], [["a", "b"]]], population=10, share=0)


def test_the_results_of_trigen_are_compared_by_the_names_of_their_genes():
    cube, planted = plant((60, 5, 8), [(15, 4, 6)], noise=0.05, seed=1)
    named = Cube(cube.values, genes=[f"gene{index}" for index in range(60)])
    settings = dict(n_triclusters=2, generations=10, population_size=20, min_sizes=(4, 2, 3), max_sizes=(20, 5, 8),
                    shuffle_genes=True)
    results = []
    for seed in range(3):
        trigen = TriGen(named, seed=seed, **settings)
        trigen.run()
        results.append(trigen.result())
    measured = stability(results)
    assert [len(run) for run in measured] == [2, 2, 2]
    by_names = stability([[names["genes"] for names in result.names] for result in results], population=60)
    assert measured == by_names


def test_a_null_cube_keeps_each_series_but_not_the_genes_across_conditions():
    values = np.random.default_rng(0).normal(size=(30, 4, 5))
    cube = Cube(values, genes=[f"g{index}" for index in range(30)])
    null = null_cube(cube, seed=3)
    assert null.genes == cube.genes and null.shape == cube.shape
    for condition in range(4):
        assert sorted(map(tuple, null.values[:, condition])) == sorted(map(tuple, values[:, condition]))
    assert not np.array_equal(null.values, values)
    assert np.array_equal(null_cube(cube, seed=3).values, null.values)
    set_seed(7)
    first = null_cube(cube)
    set_seed(7)
    assert np.array_equal(null_cube(cube).values, first.values)
