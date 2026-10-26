"""
The prism: a surface of the plane of the genes and the conditions, one piece through its
neighbors, held along a window of the times. Every part of TriGen keeps it so: the
representation by a seed and steps, the initial population, the crossover and the
mutation, the growth and the model of chance; and it is measured by its pixels as series
along its window.
"""
import itertools
import math
import random

import numpy as np
import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriclusterFitness, TriGen, TriGenResult
from metagen.metaheuristics.trigen.population import DataHierarchy
from metagen.metaheuristics.trigen.shape import PrismShape, prism, prism_parts
from metagen.triclustering import Cube, Tricluster, plant_prisms
from metagen.triclustering.surface import connected, decode, encode, grow_by, removable

CUBE, PLANTED = plant_prisms((16, 16, 10), [(20, 5), (14, 4)], noise=0.05, seed=3)
ORDERED = ("genes", "conditions", "times")
SETTINGS = {"n_triclusters": 2, "generations": 5, "population_size": 16, "min_sizes": (2, 2, 3),
            "max_sizes": (8, 8, 7), "pixels": (4, 30), "seed": 1, "shape": "prism", "ordered": ORDERED,
            "views": "time"}


def _is_prism(tricluster, neighborhood, pixels=(4, 30), box=(8, 8), times=(3, 7)):
    surface, window = prism_parts(tricluster)
    rows, columns = [p[0] for p in surface], [p[1] for p in surface]
    return (connected(surface, neighborhood) and pixels[0] <= len(surface) <= pixels[1]
            and max(rows) - min(rows) < box[0] and max(columns) - min(columns) < box[1]
            and list(window) == list(range(window[0], window[-1] + 1)) and times[0] <= len(window) <= times[1])


@pytest.mark.parametrize("neighborhood", [4, 8])
def test_any_seed_and_steps_decode_to_a_connected_surface_of_their_size(neighborhood):
    rng = random.Random(0)
    for _ in range(200):
        extent = (rng.randint(2, 10), rng.randint(2, 10))
        steps = [rng.randrange(1000) for _ in range(rng.randint(0, 30))]
        seed = (rng.randrange(extent[0]), rng.randrange(extent[1]))
        surface = decode(extent, neighborhood, None, seed, steps)
        assert connected(surface, neighborhood)
        assert len(surface) == min(len(steps) + 1, extent[0] * extent[1])
        box = (rng.randint(1, extent[0]), rng.randint(1, extent[1]))
        boxed = decode(extent, neighborhood, box, seed, steps)
        assert connected(boxed, neighborhood)
        assert all(max(p[axis] for p in boxed) - min(p[axis] for p in boxed) < box[axis] for axis in (0, 1))


@pytest.mark.parametrize("neighborhood", [4, 8])
def test_every_connected_surface_of_a_small_plane_has_a_seed_and_steps(neighborhood):
    plane = [(x, y) for x in range(3) for y in range(3)]
    counted = 0
    for size in range(1, 6):
        for surface in itertools.combinations(plane, size):
            if not connected(surface, neighborhood):
                continue
            seed, steps = encode((3, 3), neighborhood, None, surface)
            assert decode((3, 3), neighborhood, None, seed, steps) == tuple(sorted(surface))
            assert all(0 <= step < neighborhood * size for step in steps)
            counted += 1
    assert counted > 30
    with pytest.raises(ValueError, match="one piece"):
        encode((3, 3), 4, None, [(0, 0), (2, 2)])


@pytest.mark.parametrize("neighborhood", [4, 8])
@pytest.mark.parametrize("scoring", ["weighted", "significance"])
def test_every_tricluster_a_search_evaluates_is_a_prism_within_its_bounds(neighborhood, scoring, monkeypatch):
    seen = []
    evaluate = TriclusterFitness.evaluate

    def recording(self, tricluster):
        seen.append(tricluster)
        return evaluate(self, tricluster)

    monkeypatch.setattr(TriclusterFitness, "evaluate", recording)
    found = TriGen(CUBE, scoring=scoring, neighborhood=neighborhood, **SETTINGS).run()
    assert seen and len(found) == 2
    for tricluster in seen + found:
        assert _is_prism(tricluster, neighborhood), tricluster


def test_a_prism_is_a_seed_steps_and_a_window_and_reads_back():
    form = PrismShape(neighborhood=4, pixels=(3, 12), box=(5, 5))
    domain = form.domain((10, 9, 8), ((2, 5), (2, 5), (2, 4)))
    for surface in ([(1, 1), (1, 2), (2, 2)], [(4, 4), (5, 4), (5, 5), (5, 6), (6, 6), (7, 6)]):
        tricluster = prism(surface, range(3, 6))
        solution = form.to_solution(tricluster, domain)
        assert sorted(solution) == ["seed_x", "seed_y", "steps", "times_length", "times_start"]
        assert len(solution["steps"]) == len(surface) - 1
        assert form.from_solution(solution) == tricluster


def test_a_rectangle_over_a_window_is_a_cube():
    tricluster = prism([(x, y) for x in (2, 3, 4) for y in (5, 6)], range(1, 4))
    assert tricluster.is_cube and tricluster == Tricluster([2, 3, 4], [5, 6], [1, 2, 3])
    assert prism_parts(tricluster) == ([(x, y) for x in (2, 3, 4) for y in (5, 6)], (1, 2, 3))
    with pytest.raises(ValueError, match="same times"):
        prism_parts(Tricluster.from_cells([0, 0, 1], [0, 0, 0], [0, 1, 0]))


def test_a_prism_is_the_tricluster_its_cells_make():
    draw = random.Random(5)
    windows = [range(2, 6), range(0, 1), [7, 3, 5]]
    for size, window in itertools.product((1, 2, 6, 25), windows):
        surface = grow_by((4, 4), size, (12, 12), 4, None, lambda pixel: draw.random())
        cells = [(x, y, t) for (x, y), t in itertools.product(surface, window)]
        draw.shuffle(cells)
        if len(cells) < 2:
            with pytest.raises(ValueError, match="at least two cells"):
                prism(surface, window)
            continue
        built, expected = prism(surface, window, fitness=-2), Tricluster.from_cells(*zip(*cells), fitness=-2)
        assert (built.genes, built.conditions, built.times, built.fitness, built.is_cube) == (
            expected.genes, expected.conditions, expected.times, expected.fitness, expected.is_cube)
        for mine, theirs in zip(built.cells(), expected.cells()):
            assert mine.dtype == theirs.dtype and np.array_equal(mine, theirs)
            assert mine.flags.writeable == theirs.flags.writeable
    with pytest.raises(ValueError, match="repeat"):
        prism([(1, 1), (1, 1)], range(2))


def test_the_crossover_and_the_mutation_give_prisms():
    set_seed(0)
    form = PrismShape(neighborhood=8, pixels=(4, 20), box=(6, 6))
    sizes = ((2, 6), (2, 6), (3, 6))
    domain = form.domain((12, 12, 9), sizes)
    parents = [form.to_solution(form.scattered((12, 12, 9), sizes), domain) for _ in range(6)]
    for first, second in itertools.combinations(parents, 2):
        for child in first.crossover(second):
            child.mutate(alterations_number=1, alteration_limit=1)
            assert _is_prism(form.from_solution(child), 8, pixels=(4, 20), box=(6, 6), times=(3, 6))


def test_the_initial_population_draws_scattered_surfaces_rectangles_and_the_least_held():
    set_seed(2)
    form = PrismShape(neighborhood=4, pixels=(4, 12), box=(6, 6))
    sizes = ((2, 6), (2, 6), (2, 4))
    rectangle = form.block((10, 10, 8), sizes)
    surface, _ = prism_parts(rectangle)
    rows, columns = {p[0] for p in surface}, {p[1] for p in surface}
    assert len(surface) == len(rows) * len(columns) and 4 <= len(surface) <= 12
    hierarchy = DataHierarchy((10, 10, 8), cells=True)
    hierarchy.update(prism([(x, y) for x in range(10) for y in range(9)], range(8)))
    for _ in range(10):
        drawn = form.hierarchical(hierarchy, sizes)
        assert _is_prism(drawn, 4, pixels=(4, 12), box=(6, 6), times=(2, 4))
        assert any(y == 9 for _, y in prism_parts(drawn)[0])      # it starts at the column nobody held


def test_growing_keeps_the_surface_one_piece_and_the_window_a_window():
    set_seed(0)
    form = PrismShape(neighborhood=4, pixels=(3, 25), box=(7, 7))
    scored = []
    rng = random.Random(1)

    def score(tricluster):
        scored.append(tricluster)
        return rng.random()

    start = prism([(4, 4), (4, 5), (5, 5)], range(3, 6))
    for pruning in (False, True):
        grown, evaluations = form.grow(start, score, ((2, 7), (2, 7), (2, 6)), (12, 12, 10), pruning=pruning)
        assert evaluations == len(scored) and _is_prism(grown, 4, pixels=(3, 25), box=(7, 7), times=(2, 6))
        assert all(_is_prism(one, 4, pixels=(3, 25), box=(7, 7), times=(2, 6)) for one in scored)
        scored.clear()


def test_removing_a_pixel_never_cuts_the_surface():
    surface = [(0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)]
    assert removable(surface, (5, 5), 4) == [(0, 0), (0, 2), (2, 2)]
    for pixel in removable(surface, (5, 5), 8):
        assert connected(set(surface) - {pixel}, 8)


def test_the_model_of_chance_draws_prisms_of_the_size_asked():
    set_seed(0)
    form = PrismShape(neighborhood=4, pixels=(2, 40))
    for count, length in ((2, 2), (17, 5), (60, 9)):
        drawn = form.chance((12, 12, 10), (count, length))
        assert connected(prism_parts(drawn)[0], 4)
        assert form.measured_size(drawn) == (count, length)
    assert form.chance_extents((12, 11, 10)) == (132, 10)


def test_a_prism_is_measured_by_its_pixels_as_series_along_its_window():
    values = np.random.default_rng(0).normal(size=(6, 6, 7))
    cube = Cube(values)
    surface, times = [(1, 1), (1, 2), (2, 2), (3, 2), (3, 3)], range(1, 6)
    fitness = TriclusterFitness(cube, views="time", form=PrismShape(pixels=(2, 10)))
    series = np.array([values[x, y, list(times)] for x, y in surface])
    angles = np.arctan(np.diff(series, axis=1))
    angles = np.where(angles < 0, angles + 2 * np.pi, angles)
    pairs = [np.abs(angles[i] - angles[j]).mean() for i, j in itertools.combinations(range(len(surface)), 2)]
    assert math.isclose(fitness.quality(prism(surface, times)), np.mean(pairs) / (2 * np.pi), rel_tol=1e-12)
    noiseless, alike = plant_prisms((10, 10, 8), [(12, 5)], seed=0)
    assert TriclusterFitness(noiseless, views="time", form=PrismShape(pixels=(2, 40))).quality(alike[0]) < 1e-12
    set_seed(0)
    assert TriclusterFitness(CUBE, views="time", form=PrismShape(pixels=(2, 40))).significance(PLANTED[0]) > 10


def test_what_two_prisms_share_is_their_common_pixels_over_their_common_times():
    form = PrismShape(pixels=(2, 20))
    first = prism([(0, 0), (0, 1), (1, 1), (2, 1)], range(2, 7))
    second = prism([(1, 1), (2, 1), (2, 2)], range(4, 9))
    assert form.shared(first, second) == prism([(1, 1), (2, 1)], range(4, 7))
    assert form.shared(first, prism([(2, 1), (3, 1)], range(0, 9))) is None


def test_a_prism_is_saved_with_its_cells_and_run_again_from_its_result(tmp_path):
    trigen = TriGen(CUBE, scoring="significance", **SETTINGS)
    found = trigen.run()
    path = str(tmp_path / "prism.json")
    trigen.save(path)
    result = TriGenResult.load(path)
    assert result.triclusters == found
    assert result.configuration["shape"] == "prism" and result.configuration["neighborhood"] == 4
    assert result.configuration["pixels"] == [4, 30]
    assert result.trigen(CUBE).run() == found


def test_a_cube_keeps_no_pixels_and_runs_as_it_did():
    trigen = TriGen(CUBE, n_triclusters=1, generations=3, population_size=8, seed=0)
    assert trigen.configuration()["pixels"] is None and trigen.configuration()["neighborhood"] == 4
    assert trigen.run() == TriGen(CUBE, n_triclusters=1, generations=3, population_size=8, seed=0,
                                  neighborhood=8).run()


@pytest.mark.parametrize("change, message", [
    ({"ordered": ("times",)}, "all three dimensions"),
    ({"views": "distinct"}, "views='time'"),
    ({"measure": "msr3d"}, "measure 'msl' or 'lsl'"),
    ({"shuffle_genes": True}, "shuffle_genes"),
    ({"pixels": (4, 65)}, "pixels of a box"),
    ({"pixels": (1, 10)}, "2 <= fewest"),
    ({"neighborhood": 6}, "4 or 8"),
])
def test_what_a_prism_cannot_be_is_refused(change, message):
    with pytest.raises(ValueError, match=message):
        TriGen(CUBE, **{**SETTINGS, **change})


def test_pixels_only_bound_a_prism():
    with pytest.raises(ValueError, match="shape='prism'"):
        TriGen(CUBE, pixels=(4, 10))


def test_the_pixels_default_to_the_rectangles_of_the_sizes():
    settings = {key: value for key, value in SETTINGS.items() if key != "pixels"}
    assert TriGen(CUBE, **settings).pixels == (4, 64)


def test_planted_prisms_are_surfaces_that_share_no_pixel():
    cube, planted = plant_prisms((12, 12, 8), [(30, 4), (25, 3), (20, 5)], seed=4, neighborhood=8)
    pixels = [set(prism_parts(one)[0]) for one in planted]
    assert [len(one) for one in pixels] == [30, 25, 20]
    assert all(connected(one, 8) for one in pixels)
    assert not (pixels[0] & pixels[1] or pixels[0] & pixels[2] or pixels[1] & pixels[2])
    with pytest.raises(ValueError, match="pixels"):
        plant_prisms((4, 4, 5), [(10, 3), (10, 3)])


def test_the_weighted_fitness_sizes_a_prism_by_the_side_of_its_area_not_by_the_rows_and_columns_it_spans():
    fitness = TriclusterFitness(CUBE, views="time", form=PrismShape(pixels=(2, 40)))
    line = prism([(x, 3) for x in range(8)], range(2, 6))                   # 8 pixels over 8 rows
    square = prism([(x, y) for x in range(4) for y in range(4)], range(2, 6))   # 16 pixels over 4 rows
    terms = fitness.terms(line)
    assert terms["genes"] == terms["conditions"] == math.sqrt(8 / 256) and terms["times"] == 4 / 10
    assert fitness.terms(square)["genes"] == math.sqrt(16 / 256) == 4 / 16    # a square: its side
    cube = TriclusterFitness(CUBE).terms(Tricluster(range(4), range(4), range(2, 6)))
    assert (cube["genes"], cube["conditions"]) == (4 / 16, 4 / 16)
