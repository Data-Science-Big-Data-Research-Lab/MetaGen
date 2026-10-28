"""
Stopping by coverage: a run ends when its triclusters hold a share of the genes, or of the
pixels of a prism, when a search finds nothing new, when a noise rule says the last one is
no better than noise, or at the most triclusters; and it says why. By count, as before.
"""
import json

import pytest

from metagen.metaheuristics import TriGen, TriGenResult
from metagen.metaheuristics.trigen.fitness import NULL_SAMPLES, NULL_SIZES
from metagen.metaheuristics.trigen.shape import prism_parts
from metagen.triclustering import plant, plant_prisms

CUBE, PLANTED = plant((60, 6, 8), [(15, 3, 4), (15, 3, 4)], noise=0.05, seed=4)
SETTINGS = {"generations": 4, "population_size": 16, "min_sizes": (4, 2, 3), "max_sizes": (20, 5, 6), "seed": 0}


def _covered(triclusters, total=60):
    return len(set().union(*(set(t.genes) for t in triclusters))) / total


def test_by_count_a_run_says_it_ended_by_count():
    trigen = TriGen(CUBE, n_triclusters=2, **SETTINGS)
    found = trigen.run()
    assert trigen.stop_reason == "count" and len(found) == 2
    assert trigen.covered == pytest.approx(_covered(found))


def test_by_coverage_a_run_ends_at_the_first_tricluster_that_reaches_it():
    trigen = TriGen(CUBE, n_triclusters=20, stop="coverage", coverage=0.4, **SETTINGS)
    found = trigen.run()
    assert trigen.stop_reason == "coverage"
    assert _covered(found) >= 0.4 > _covered(found[:-1])
    assert [record["covered"] for record in trigen.history] == [_covered(found[:i + 1]) for i in range(len(found))]


def test_by_coverage_the_number_of_triclusters_is_the_most():
    trigen = TriGen(CUBE, n_triclusters=2, stop="coverage", coverage=1.0, **SETTINGS)
    assert len(trigen.run()) == 2 and trigen.stop_reason == "maximum" and trigen.covered < 1.0


def test_the_decline_rule_leaves_out_the_first_tricluster_well_below_the_best_so_far():
    trigen = TriGen(CUBE, n_triclusters=6, stop="coverage", scoring="significance", noise_rule="decline",
                    decline=0.95, **SETTINGS)
    found = trigen.run()
    assert trigen.stop_reason == "noise"
    significances = [-t.fitness for t in found]
    left_out = trigen.history[-1]
    assert left_out["tricluster"] is None and left_out["left_out"]["significance"] < 0.95 * max(significances)
    assert all(later >= 0.95 * max(significances[:i]) for i, later in enumerate(significances) if i)


def test_with_patience_a_run_ends_after_that_many_left_out_in_a_row_and_keeps_them_out(tmp_path):
    trigen = TriGen(CUBE, n_triclusters=8, stop="coverage", scoring="significance", noise_rule="decline",
                    decline=0.95, **SETTINGS)
    found = trigen.run()
    left = [record["tricluster"] is None and "left_out" in record for record in trigen.history]
    assert trigen.stop_reason == "noise" and left[-2:] == [True, True]
    assert not any(left[i] and left[i + 1] for i in range(len(left) - 2))
    assert any(left[i] and not left[i + 1] for i in range(len(left) - 1))
    assert len(found) == left.count(False)
    path = str(tmp_path / "run.json")
    trigen.save(path)
    result = TriGenResult.load(path)
    saved = [search["left_out"]["significance"] for search in result.searches if "left_out" in search]
    assert saved == [record["left_out"]["significance"] for record in trigen.history if "left_out" in record]
    again = result.trigen(CUBE)
    assert again.run() == found and again.patience == 2


def test_a_patience_of_one_ends_at_the_first_left_out():
    options = dict(n_triclusters=8, stop="coverage", scoring="significance", noise_rule="decline", decline=0.95,
                   **SETTINGS)
    trigen = TriGen(CUBE, patience=1, **options)
    found = trigen.run()
    assert trigen.history[-1]["tricluster"] is None and len(trigen.history) == len(found) + 1
    assert TriGen(CUBE, **options).run() != found


def test_the_null_rule_takes_its_threshold_from_a_run_in_the_null_cube_and_reproduces(tmp_path):
    trigen = TriGen(CUBE, n_triclusters=6, stop="coverage", scoring="significance", noise_rule="null", **SETTINGS)
    found = trigen.run()
    assert trigen.noise_threshold is not None and trigen.noise_threshold > 0
    assert all(-t.fitness > trigen.noise_threshold for t in found)
    path = str(tmp_path / "run.json")
    trigen.save(path)
    result = TriGenResult.load(path)
    assert result.provenance["stop_reason"] == trigen.stop_reason
    assert result.provenance["noise_threshold"] == trigen.noise_threshold and result.provenance["complete"]
    again = result.trigen(CUBE)
    assert again.run() == found and again.noise_threshold == trigen.noise_threshold


def test_a_prism_covers_pixels():
    cube, _ = plant_prisms((16, 16, 10), [(20, 5), (14, 4)], noise=0.05, seed=3)
    trigen = TriGen(cube, shape="prism", ordered=("genes", "conditions", "times"), views="time", n_triclusters=3,
                    generations=3, population_size=12, min_sizes=(2, 2, 3), max_sizes=(8, 8, 7), pixels=(4, 30),
                    stop="coverage", coverage=1.0, seed=1)
    found = trigen.run()
    pixels = set().union(*(set(prism_parts(t)[0]) for t in found))
    assert trigen.cover == "pixels" and trigen.covered == pytest.approx(len(pixels) / 256)


def test_a_file_saved_before_these_options_reads_as_a_run_by_count(tmp_path):
    trigen = TriGen(CUBE, n_triclusters=1, **SETTINGS)
    trigen.run()
    path = str(tmp_path / "old.json")
    trigen.save(path)
    document = json.load(open(path))
    for name in ("stop", "cover", "coverage", "noise_rule", "decline", "patience", "disjoint"):
        del document["configuration"][name]
    json.dump(document, open(path, "w"))
    assert TriGenResult.load(path).configuration["stop"] == "count"
    assert TriGenResult.load(path).configuration["patience"] == 1
    assert TriGenResult.load(path).configuration["disjoint"] is False


@pytest.mark.parametrize("shuffle_genes", [False, True])
def test_disjoint_no_two_triclusters_share_a_gene_and_each_search_works_on_the_genes_left(shuffle_genes, monkeypatch):
    searched = []
    original = TriGen._on_genes

    def spy(self, positions):
        searched.append(list(positions))
        return original(self, positions)

    monkeypatch.setattr(TriGen, "_on_genes", spy)
    trigen = TriGen(CUBE, n_triclusters=6, stop="coverage", scoring="significance", disjoint=True,
                    shuffle_genes=shuffle_genes, **SETTINGS)
    found = trigen.run()
    genes = [set(tricluster.genes) for tricluster in found]
    assert len(found) >= 3 and sum(len(one) for one in genes) == len(set().union(*genes))
    assert trigen.covered == pytest.approx(_covered(found))
    # Each search sees the genes no tricluster before it holds, and none of those
    assert [set(positions) for positions in searched] == [set(range(60)) - set().union(*genes[:i])
                                                          for i in range(len(found))]
    assert (trigen.stop_reason == "exhausted") == (len(found) < 6)
    if shuffle_genes:
        assert searched[0] != sorted(searched[0])
    assert trigen.started["chance_evaluations"] == len(found) * NULL_SIZES * NULL_SAMPLES


def test_disjoint_a_run_ends_when_fewer_genes_are_left_than_the_smallest_size():
    cube, _ = plant((12, 6, 8), [(5, 3, 4)], noise=0.05, seed=1)
    trigen = TriGen(cube, n_triclusters=10, disjoint=True, **{**SETTINGS, "max_sizes": (5, 5, 6)})
    found = trigen.run()
    assert trigen.stop_reason == "exhausted" and 12 - sum(len(t.genes) for t in found) < 4
    assert len(trigen.history) == len(found) < 10


def test_disjoint_the_genes_of_one_left_out_go_to_the_residue(monkeypatch):
    searched = []
    original = TriGen._on_genes

    def spy(self, positions):
        searched.append(set(positions))
        return original(self, positions)

    monkeypatch.setattr(TriGen, "_on_genes", spy)
    trigen = TriGen(CUBE, n_triclusters=8, stop="coverage", scoring="significance", noise_rule="decline",
                    decline=0.95, disjoint=True, **SETTINGS)
    found = trigen.run()
    held = set().union(*(set(t.genes) for t in found))
    left = [index for index, record in enumerate(trigen.history) if "left_out" in record]
    assert trigen.stop_reason == "noise" and left
    # After one left out, the genes the next search sees lose its genes as well
    for index in left[:-1]:
        lost = searched[index] - searched[index + 1]
        assert lost and not lost & held
    assert sum(len(t.genes) for t in found) == len(held)


def test_disjoint_reruns_from_its_result(tmp_path):
    trigen = TriGen(CUBE, n_triclusters=3, disjoint=True, scoring="significance", **SETTINGS)
    found = trigen.run()
    path = str(tmp_path / "run.json")
    trigen.save(path)
    again = TriGenResult.load(path).trigen(CUBE)
    assert again.disjoint and again.run() == found


@pytest.mark.parametrize("change, message", [
    ({"stop": "genes"}, "'count' or 'coverage'"),
    ({"stop": "coverage", "cover": "pixels"}, "shape='prism'"),
    ({"stop": "coverage", "coverage": 0.0}, "share in"),
    ({"stop": "coverage", "coverage": 1.5}, "share in"),
    ({"noise_rule": "null", "scoring": "significance"}, "stop='coverage'"),
    ({"stop": "coverage", "noise_rule": "null"}, "scoring='significance'"),
    ({"stop": "coverage", "scoring": "significance", "noise_rule": "z"}, "None, 'null' or 'decline'"),
    ({"decline": 1.0}, "share in"),
    ({"stop": "coverage", "scoring": "significance", "noise_rule": "null", "patience": 0}, "at least 1"),
    ({"disjoint": 1}, "True or False"),
    ({"disjoint": True, "shape": "prism", "ordered": ("genes", "conditions", "times"), "views": "time"},
     "shape='cube'"),
])
def test_what_a_stop_cannot_be_is_refused(change, message):
    with pytest.raises(ValueError, match=message):
        TriGen(CUBE, **{**SETTINGS, **change})
