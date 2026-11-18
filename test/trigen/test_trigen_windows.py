"""
Dimensions with order: a tricluster holds a window there, consecutive positions, and every
part of TriGen keeps it so: the initial population, the crossover and the mutation, the
growth and the model of chance. Without them TriGen is as it was.
"""
import numpy as np
import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriclusterFitness, TriGen, TriGenResult
from metagen.metaheuristics.trigen.population import DataHierarchy
from metagen.metaheuristics.trigen.shape import CubeShape, grow, tricluster_domain
from metagen.triclustering import Tricluster, plant

CUBE, _ = plant((60, 6, 10), [(12, 3, 4), (10, 3, 3)], noise=0.05, seed=1)
SETTINGS = {"n_triclusters": 2, "generations": 6, "population_size": 16, "min_sizes": (3, 2, 2),
            "max_sizes": (20, 5, 6), "seed": 2}


def _window(positions):
    return list(positions) == list(range(positions[0], positions[-1] + 1))


@pytest.mark.parametrize("ordered", [("times",), ("conditions", "times"), ("genes",)])
@pytest.mark.parametrize("scoring", ["weighted", "significance"])
def test_every_tricluster_a_search_evaluates_holds_windows_in_the_dimensions_with_order(ordered, scoring,
                                                                                       monkeypatch):
    seen = []
    evaluate = TriclusterFitness.evaluate

    def recording(self, tricluster):
        seen.append(tricluster)
        return evaluate(self, tricluster)

    monkeypatch.setattr(TriclusterFitness, "evaluate", recording)
    found = TriGen(CUBE, ordered=ordered, scoring=scoring, **SETTINGS).run()
    assert seen and found
    for tricluster in seen + found:
        for axis in ordered:
            assert _window(getattr(tricluster, axis)), (axis, getattr(tricluster, axis))
        for (low, high), size in zip(((3, 20), (2, 5), (2, 6)), tricluster.size):
            assert low <= size <= high


def test_without_order_the_runs_are_as_they_were():
    assert TriGen(CUBE, **SETTINGS).run() == TriGen(CUBE, ordered=(), **SETTINGS).run()


def test_a_window_is_its_start_and_its_length_and_every_window_can_be_read():
    shape, sizes = (8, 5, 9), ((2, 4), (2, 3), (3, 5))
    form = CubeShape(ordered=[2])
    domain = tricluster_domain(shape, sizes, form.ordered)
    seen = set()
    for length in range(3, 6):
        for start in range(0, 9 - 3 + 1):
            tricluster = Tricluster([0, 1], [0, 1], range(min(start, 9 - length), min(start, 9 - length) + length))
            solution = form.to_solution(tricluster, domain)
            solution.set("times_start", start)        # a start past the end is cut so the window fits
            read = form.from_solution(solution)
            assert _window(read.times) and len(read.times) == length and read.times[-1] < 9
            seen.add(read.times)
    assert seen == {tuple(range(start, start + length)) for length in range(3, 6) for start in range(9 - length + 1)}


def test_a_start_or_a_length_that_can_take_one_value_is_fixed():
    form = CubeShape(ordered=[1, 2])
    domain = tricluster_domain((8, 3, 5), ((2, 4), (3, 3), (2, 5)), form.ordered)
    solution = form.to_solution(Tricluster([0, 1], [0, 1, 2], [1, 2]), domain)
    assert form.from_solution(solution) == Tricluster([0, 1], [0, 1, 2], [1, 2])


@pytest.mark.parametrize("cells", [False, True])
def test_the_hierarchy_draws_the_window_least_explored(cells):
    set_seed(0)
    hierarchy = DataHierarchy((20, 6, 10), cells=cells)
    for found in (Tricluster(range(5), range(3), range(0, 4)), Tricluster(range(5, 9), range(3, 6), range(3, 7))):
        hierarchy.update(found)
    levels = hierarchy.levels[2]
    lowest = min(sum(levels[start:start + 3]) for start in range(8))
    for _ in range(20):
        window = hierarchy.draw(2, 3, window=True)
        assert _window(window) and sum(levels[position] for position in window) == lowest
    if cells:
        genes = hierarchy.draw_genes([0, 1], [0, 1], 4, window=True)
        held = hierarchy.cells[:, [0, 1]][:, :, [0, 1]].sum(axis=(1, 2))
        assert _window(genes) and held[genes].sum() == min(held[s:s + 4].sum() for s in range(17))


def test_growing_a_window_only_tries_its_two_ends():
    tried = []

    def score(tricluster):
        tried.append(tricluster.times)
        return 0.0

    start = Tricluster([0, 1, 2], [0, 1], [3, 4, 5])
    grow(start, score, ((3, 3), (2, 2), (2, 8)), (10, 4, 10), pruning=True, ordered=[2])
    assert all(_window(times) for times in tried)
    assert {(2, 3, 4, 5), (3, 4, 5, 6), (4, 5), (3, 4)} <= set(tried)


def test_the_model_of_chance_draws_windows():
    set_seed(3)
    form = CubeShape(ordered=[2])
    drawn = [form.chance((30, 6, 10), (5, 3, 4)) for _ in range(50)]
    assert all(_window(tricluster.times) and tricluster.size == (5, 3, 4) for tricluster in drawn)
    assert {tricluster.times[0] for tricluster in drawn} == set(range(7)), "every start of a window is drawn"
    assert not all(_window(tricluster.genes) for tricluster in drawn), "the genes, without order, are any"


def test_the_order_is_kept_with_the_result_and_an_older_file_reads_without_it(tmp_path):
    import json
    trigen = TriGen(CUBE, ordered=("times",), **SETTINGS)
    trigen.run()
    path = tmp_path / "run.json"
    trigen.save(str(path))
    result = TriGenResult.load(str(path))
    assert result.configuration["ordered"] == ["times"]
    assert result.trigen(CUBE).run() == trigen.triclusters
    content = json.loads(path.read_text())
    del content["configuration"]["ordered"]
    path.write_text(json.dumps(content))
    assert TriGenResult.load(str(path)).configuration["ordered"] == []


@pytest.mark.parametrize("ordered", ["times", ("days",), ("times", "times")])
def test_an_order_that_is_not_of_the_dimensions_is_refused(ordered):
    with pytest.raises(ValueError, match="ordered names dimensions"):
        TriGen(CUBE, ordered=ordered, **SETTINGS)


def test_the_dimensions_with_order_come_in_the_order_of_the_cube():
    assert TriGen(CUBE, ordered=("times", "genes"), **SETTINGS).ordered == ("genes", "times")
    assert np.array_equal(TriGen(CUBE, ordered=("times",), **SETTINGS).form.ordered, (2,))
