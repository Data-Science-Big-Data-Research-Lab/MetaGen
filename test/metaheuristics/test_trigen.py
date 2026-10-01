"""TriGen as a whole: N searches, each adding a tricluster that does not repeat one
found, with the fitness it had when it was found, reproducible from a seed."""
import json
import logging
import subprocess
import sys
import textwrap

import pytest

from metagen.metaheuristics import TriclusterFitness, TriGen
from metagen.triclustering import Cube, Tricluster, plant

CUBE, PLANTED = plant((60, 6, 8), [(12, 3, 5), (10, 2, 4)], noise=0.05, seed=0)
SETTINGS = {"generations": 8, "population_size": 20, "min_sizes": (4, 2, 3), "max_sizes": (15, 4, 6)}


def _trigen(**arguments):
    return TriGen(CUBE, **{**SETTINGS, "n_triclusters": 3, "seed": 1, **arguments})


def test_it_finds_as_many_different_triclusters_as_asked_within_the_sizes():
    triclusters = _trigen(n_triclusters=4).run()
    assert len(triclusters) == 4 and len(set(triclusters)) == 4
    for tricluster in triclusters:
        tricluster.check(CUBE)
        for size, low, high in zip(tricluster.size, SETTINGS["min_sizes"], SETTINGS["max_sizes"]):
            assert low <= size <= high


def test_each_tricluster_has_the_fitness_it_had_against_those_found_before_it():
    trigen = _trigen(n_triclusters=4)
    triclusters = trigen.run()
    for index, tricluster in enumerate(triclusters):
        fitness = TriclusterFitness(CUBE, found=triclusters[:index])
        assert tricluster.fitness == fitness.evaluate(tricluster)
    assert trigen.fitness.found == triclusters


def test_the_same_seed_gives_the_same_triclusters_and_running_again_starts_over():
    trigen = _trigen()
    first = trigen.run()
    again = trigen.run()
    other = _trigen().run()
    assert first == again == other
    assert [t.fitness for t in first] == [t.fitness for t in again]
    assert _trigen(seed=2).run() != first


def test_the_same_seed_gives_the_same_triclusters_in_other_processes():
    script = textwrap.dedent("""
        from metagen.metaheuristics import TriGen
        from metagen.triclustering import plant
        cube, _ = plant((40, 5, 6), [(10, 3, 4)], noise=0.05, seed=0)
        found = TriGen(cube, n_triclusters=2, generations=5, population_size=12, min_sizes=(3, 2, 2),
                       max_sizes=(12, 4, 5), seed=4).run()
        print([(t.genes, t.conditions, t.times, t.fitness) for t in found])
    """)
    outputs = {subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True,
                              env={"PYTHONHASHSEED": seed, "PATH": ""}).stdout
               for seed in ("0", "1", "2")}
    assert len(outputs) == 1


def test_a_search_that_finds_nothing_new_adds_nothing_and_says_so(caplog):
    """A cube of 2 × 2 × 2 holds one tricluster of at least two of each: the first search
    finds it and the others have nothing new to find."""
    cube = Cube([[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]])
    trigen = TriGen(cube, n_triclusters=3, generations=2, population_size=4, seed=0)
    with caplog.at_level(logging.WARNING, logger="metagen_logger"):
        triclusters = trigen.run()
    assert triclusters == [Tricluster([0, 1], [0, 1], [0, 1])]
    assert [record["tricluster"] is None for record in trigen.history] == [False, True, True]


def test_in_a_small_space_it_takes_new_triclusters_from_everything_the_search_evaluated():
    """Three genes, two conditions, two times: four possible triclusters. With a
    population that soon holds only repeats, each search still finds a new one among the
    triclusters it evaluated, until there are none left."""
    cube = Cube([[[float(g + c + t) for t in range(2)] for c in range(2)] for g in range(3)])
    triclusters = TriGen(cube, n_triclusters=6, generations=5, population_size=6, seed=3).run()
    assert len(triclusters) == len(set(triclusters)) == 4


def test_the_history_has_a_line_per_search(tmp_path):
    path = tmp_path / "trigen.jsonl"
    trigen = _trigen(history=str(path))
    triclusters = trigen.run()
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    assert lines == json.loads(json.dumps(trigen.history))
    assert [line["search"] for line in lines] == [0, 1, 2]
    for line, tricluster in zip(lines, triclusters):
        assert line["tricluster"] == {"genes": list(tricluster.genes), "conditions": list(tricluster.conditions),
                                      "times": list(tricluster.times)}
        assert line["fitness"] == tricluster.fitness and line["evaluations"] > 0
    trigen.run()
    assert len(path.read_text().splitlines()) == 3


@pytest.mark.parametrize("arguments", [
    {"n_triclusters": 0},
    {"population_size": 3},
    {"selection_rate": 0.0},
    {"min_sizes": (1, 2, 3)},
    {"min_sizes": (4, 2, 3), "max_sizes": (3, 4, 6)},
    {"max_sizes": (61, 4, 6)},
    {"max_sizes": (15, 4)},
    {"measure": "mse"},
    {"size_reference": "cube"},
])
def test_parameters_out_of_range_are_rejected(arguments):
    with pytest.raises(ValueError):
        _trigen(**arguments)


def test_the_hierarchy_counts_how_many_triclusters_found_hold_each_coordinate():
    trigen = _trigen(n_triclusters=4)
    triclusters = trigen.run()
    for dimension, levels in enumerate(trigen.hierarchy.levels):
        for position, level in enumerate(levels):
            holding = sum(position in (t.genes, t.conditions, t.times)[dimension] for t in triclusters)
            assert level == holding
