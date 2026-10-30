"""
The report of a run of TriGen: the run, the triclusters, the searches and, with the cube,
the values of the triclusters, as an HTML page or a PDF, with the coordinates next to it.
"""
import os

import pytest

pytest.importorskip("matplotlib")

from metagen.metaheuristics import TriGen, TriGenResult  # noqa: E402
from metagen.triclustering import plant, plant_prisms  # noqa: E402

CUBE, _ = plant((60, 6, 8), [(12, 3, 5), (10, 3, 4)], noise=0.05, seed=4)


def _cubes(**options):
    trigen = TriGen(CUBE, n_triclusters=3, generations=4, population_size=16, min_sizes=(4, 2, 3),
                    max_sizes=(20, 5, 6), seed=0, **options)
    trigen.run()
    return trigen


def test_the_report_shows_the_run_the_triclusters_the_searches_and_three_views_of_each(tmp_path):
    trigen = _cubes()
    path = trigen.report(str(tmp_path / "run.html"), label="two planted")
    page = open(path, encoding="utf-8").read()
    assert "<title>two planted</title>" in page and "<h2>Run</h2>" in page and "<h2>Triclusters</h2>" in page
    assert page.count("<tr>") >= len(trigen.triclusters) and "run.csv" in page
    assert os.path.exists(tmp_path / "run.csv")
    # The fitness by generation, the share held, the overlap and three views per tricluster
    overlapping = 1 if "another one (column) also holds" in page else 0
    assert page.count("<svg") == 2 + overlapping + 3 * len(trigen.triclusters)
    for index in range(len(trigen.triclusters)):
        assert f"<h2>Tricluster {index}</h2>" in page


def test_only_the_first_triclusters_are_drawn_one_by_one(tmp_path):
    trigen = _cubes()
    page = open(trigen.report(str(tmp_path / "run.html"), detailed=1), encoding="utf-8").read()
    assert "<h2>Tricluster 0</h2>" in page and "<h2>Tricluster 1</h2>" not in page


def test_a_saved_result_is_reported_with_or_without_its_cube(tmp_path):
    trigen = _cubes()
    trigen.save(str(tmp_path / "run.json"))
    result = TriGenResult.load(str(tmp_path / "run.json"))
    without = open(result.report(str(tmp_path / "alone.html")), encoding="utf-8").read()
    assert "<h2>Tricluster 0</h2>" not in without and "<h2>Triclusters</h2>" in without
    with_cube = open(result.report(str(tmp_path / "cube.html"), CUBE), encoding="utf-8").read()
    assert "<h2>Tricluster 0</h2>" in with_cube
    other, _ = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=5)
    with pytest.raises(ValueError, match="not the one this run worked on"):
        result.report(str(tmp_path / "other.html"), other)
    with pytest.raises(ValueError, match=".html or a .pdf"):
        result.report(str(tmp_path / "run.txt"))


def test_the_report_can_be_a_pdf(tmp_path):
    path = _cubes().report(str(tmp_path / "run.pdf"))
    assert open(path, "rb").read().startswith(b"%PDF") and os.path.exists(tmp_path / "run.csv")


def test_a_segmentation_with_prisms_shows_the_plane_and_the_series_of_each_prism(tmp_path):
    plane, _ = plant_prisms((16, 16, 10), [(20, 5), (14, 4)], noise=0.05, seed=3)
    trigen = TriGen(plane, shape="prism", ordered=("genes", "conditions", "times"), views="time", n_triclusters=6,
                    generations=3, population_size=12, min_sizes=(2, 2, 3), max_sizes=(8, 8, 7), pixels=(6, 30),
                    scoring="significance", stop="coverage", disjoint=True, seed=1)
    trigen.run()
    page = open(trigen.report(str(tmp_path / "prisms.html")), encoding="utf-8").read()
    assert "<h2>Prisms</h2>" in page and "no two triclusters share a cell" in page
    assert "another one (column) also holds" not in page
    assert "pixels ×" in page
    assert page.count("<svg") == 2 + 1 + len(trigen.triclusters)
