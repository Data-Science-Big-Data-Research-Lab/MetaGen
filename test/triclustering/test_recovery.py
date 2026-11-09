"""How much a triclustering recovers of what was planted: the similarities between two
triclusters, against a count of their cells one by one, and the recovery and relevance
of a list of triclusters found against a list planted."""
import itertools
import math

import numpy as np
import pytest

from metagen.triclustering import (Tricluster, cell_jaccard, cell_precision, cell_recall, coordinate_jaccard,
                                   coordinate_recall, recovery, relevance)


def _cells(tricluster):
    return set(itertools.product(tricluster.genes, tricluster.conditions, tricluster.times))


def _random_tricluster(rng):
    return Tricluster(*(rng.choice(size, size=int(rng.integers(2, size + 1)), replace=False)
                        for size in (12, 5, 6)))


@pytest.mark.parametrize("seed", range(40))
def test_the_similarities_match_a_count_of_cells_and_coordinates_one_by_one(seed):
    rng = np.random.default_rng(seed)
    found, planted = _random_tricluster(rng), _random_tricluster(rng)
    cells_found, cells_planted = _cells(found), _cells(planted)
    common = len(cells_found & cells_planted)
    assert math.isclose(cell_jaccard(found, planted), common / len(cells_found | cells_planted))
    assert math.isclose(cell_recall(found, planted), common / len(cells_planted))
    assert math.isclose(cell_precision(found, planted), common / len(cells_found))
    dimensions = list(zip((found.genes, found.conditions, found.times),
                          (planted.genes, planted.conditions, planted.times)))
    shared = sum(len(set(a) & set(b)) for a, b in dimensions)
    assert math.isclose(coordinate_jaccard(found, planted), shared / sum(len(set(a) | set(b)) for a, b in dimensions))
    assert math.isclose(coordinate_recall(found, planted), shared / sum(len(b) for _, b in dimensions))


def test_worked_out_by_hand():
    """a: genes 0-3, conditions 0-1, times 0-1, 16 cells; b: genes 2-5, the same
    conditions and times, 16 cells, 8 of them in a."""
    a = Tricluster([0, 1, 2, 3], [0, 1], [0, 1])
    b = Tricluster([2, 3, 4, 5], [0, 1], [0, 1])
    assert cell_jaccard(a, b) == 8 / 24
    assert cell_recall(a, b) == 8 / 16 and cell_precision(a, b) == 8 / 16
    assert coordinate_jaccard(a, b) == (2 + 2 + 2) / (6 + 2 + 2)
    assert coordinate_recall(a, b) == (2 + 2 + 2) / (4 + 2 + 2)


def test_a_tricluster_against_itself_is_one_and_against_a_disjoint_one_zero():
    a = Tricluster([0, 1, 2], [0, 1], [0, 1, 2])
    disjoint = Tricluster([5, 6], [3, 4], [5, 6])
    for similarity in (cell_jaccard, cell_recall, cell_precision, coordinate_jaccard, coordinate_recall):
        assert similarity(a, a) == 1.0 and similarity(a, disjoint) == 0.0


def test_sharing_genes_but_not_times_shares_no_cell():
    a = Tricluster([0, 1, 2], [0, 1], [0, 1])
    b = Tricluster([0, 1, 2], [0, 1], [2, 3])
    assert cell_jaccard(a, b) == 0.0 and coordinate_jaccard(a, b) == (3 + 2 + 0) / (3 + 2 + 4)


def test_the_jaccard_indices_are_symmetric_and_recall_is_precision_the_other_way():
    rng = np.random.default_rng(99)
    for _ in range(30):
        a, b = _random_tricluster(rng), _random_tricluster(rng)
        assert cell_jaccard(a, b) == cell_jaccard(b, a) and coordinate_jaccard(a, b) == coordinate_jaccard(b, a)
        assert cell_recall(a, b) == cell_precision(b, a)


def test_a_found_tricluster_inside_a_planted_one_is_precise_and_recalls_part_of_it():
    planted = Tricluster(range(10), range(4), range(6))
    found = Tricluster(range(5), range(4), range(6))
    assert cell_precision(found, planted) == 1.0 and cell_recall(found, planted) == 0.5


def test_recovery_and_relevance():
    planted = [Tricluster([0, 1, 2], [0, 1], [0, 1]), Tricluster([5, 6, 7, 8], [2, 3], [2, 3])]
    exact = Tricluster([0, 1, 2], [0, 1], [0, 1])
    elsewhere = Tricluster([10, 11], [0, 1], [0, 1])
    half = Tricluster([5, 6], [2, 3], [2, 3])              # half of the second planted one
    assert recovery([exact, elsewhere], planted) == 0.5 and relevance([exact, elsewhere], planted) == 0.5
    assert recovery([exact, half], planted) == 0.75 and relevance([exact, half], planted) == 0.75
    assert recovery(planted, planted) == 1.0 and relevance(planted, planted) == 1.0
    # The most similar one counts: a poor match beside the exact one changes nothing for recovery.
    assert recovery([elsewhere, exact, half], planted) == 0.75
    assert math.isclose(relevance([elsewhere, exact, half], planted), (0 + 1 + 0.5) / 3)


def test_recovery_and_relevance_take_another_similarity():
    planted = [Tricluster(range(10), range(4), range(6))]
    found = [Tricluster(range(5), range(4), range(6))]
    assert recovery(found, planted, cell_recall) == 0.5
    assert relevance(found, planted, cell_precision) == 1.0


def test_with_nothing_on_one_side():
    some = [Tricluster([0, 1], [0, 1], [0, 1])]
    assert recovery([], some) == 0.0 and relevance(some, []) == 0.0
    with pytest.raises(ValueError, match="planted"):
        recovery(some, [])
    with pytest.raises(ValueError, match="found"):
        relevance([], some)
