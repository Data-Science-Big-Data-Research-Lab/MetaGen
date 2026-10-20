"""The result of a run of TriGen as a file: a JSON document that describes itself, holds
what was found and what it takes to run it again, and neither the data nor a path to them."""
import csv
import inspect
import json

import numpy as np
import pytest

from metagen.metaheuristics import TriGen, TriGenResult
from metagen.triclustering import Cube, Tricluster, plant

VALUES, _ = plant((40, 5, 6), [(10, 3, 4)], noise=0.05, seed=0)
GENES = [f"gene{index}" for index in range(40)]
CUBE = Cube(VALUES.values, genes=GENES, conditions=["a", "b", "c", "d", "e"], times=[0, 2, 4, 8, 16, 32])
SETTINGS = {"n_triclusters": 3, "generations": 6, "population_size": 12, "min_sizes": (3, 2, 2),
            "max_sizes": (12, 4, 5), "seed": 5}


def _run(**arguments):
    trigen = TriGen(CUBE, **{**SETTINGS, **arguments})
    trigen.run()
    return trigen


def _strict(path):
    """The file as strict JSON: no NaN and no infinities."""
    def refuse(constant):
        raise AssertionError(f"the file holds {constant}, which is not JSON")
    return json.loads(path.read_text(), parse_constant=refuse)


def test_a_result_comes_back_from_its_file_as_it_was_saved(tmp_path):
    trigen = _run()
    path = tmp_path / "run.json"
    trigen.save(str(path), label="planted")
    result = TriGenResult.load(str(path))
    assert result.triclusters == trigen.triclusters
    assert [t.fitness for t in result.triclusters] == [t.fitness for t in trigen.triclusters]
    assert result.configuration == _strict(path)["configuration"] == json.loads(json.dumps(trigen.configuration()))
    assert result.data == {"shape": [40, 5, 6], "sha256": CUBE.fingerprint, "label": "planted"}
    assert [search["search"] for search in result.searches] == [0, 1, 2]
    assert result.terms == [record["terms"] for record in trigen.history]
    assert list(tmp_path.iterdir()) == [path]


def test_the_file_says_what_it_is_and_names_what_was_found(tmp_path):
    trigen = _run()
    path = tmp_path / "run.json"
    trigen.save(str(path))
    document = _strict(path)
    assert document["format"] == "metagen-trigen" and document["version"] == 1
    assert set(document) == {"format", "version", "provenance", "configuration", "data", "triclusters", "searches"}
    assert document["provenance"]["seed"] == 5 and document["provenance"]["seconds"] > 0
    provenance = document["provenance"]
    assert provenance["evaluations"] == sum(record["evaluations"] for record in trigen.history)
    assert provenance["growth_evaluations"] == sum(record["growth_evaluations"] for record in trigen.history) > 0
    assert provenance["chance_evaluations"] == 0 and provenance["complete"] is True
    assert {"metagen", "python", "numpy", "platform", "date"} <= set(provenance)
    for entry, tricluster in zip(document["triclusters"], trigen.triclusters):
        assert entry["genes"] == list(tricluster.genes)
        assert entry["gene_names"] == [GENES[position] for position in tricluster.genes]
        assert entry["condition_names"] == [CUBE.conditions[position] for position in tricluster.conditions]
        assert entry["time_names"] == [CUBE.times[position] for position in tricluster.times]
        assert entry["fitness"] == tricluster.fitness and entry["terms"]["fitness"] == tricluster.fitness


@pytest.mark.parametrize("arguments", [{}, {"scoring": "significance"}, {"growth": None, "measure": "msr3d"},
                                       {"weights": {"quality": 1.0, "genes": 0.1, "conditions": 0.1, "times": 0.1,
                                                    "overlap_genes": 0.2, "overlap_conditions": 0.2,
                                                    "overlap_times": 0.2}, "size_reference": "max"}])
def test_a_result_runs_again_to_the_same_triclusters(tmp_path, arguments):
    trigen = _run(**arguments)
    trigen.save(str(tmp_path / "run.json"))
    result = TriGenResult.load(str(tmp_path / "run.json"))
    again = result.trigen(CUBE)
    assert again.configuration() == trigen.configuration()
    assert again.run() == result.triclusters
    assert [t.fitness for t in again.triclusters] == [t.fitness for t in result.triclusters]


def test_the_fingerprint_tells_the_data_apart_and_not_the_names():
    same = Cube(VALUES.values.copy())
    assert same.fingerprint == CUBE.fingerprint and len(CUBE.fingerprint) == 64
    assert Cube(np.asfortranarray(VALUES.values)).fingerprint == CUBE.fingerprint
    zeros = np.zeros((2, 2, 2))
    assert Cube(zeros).fingerprint == Cube(-zeros).fingerprint
    changed = VALUES.values.copy()
    changed[3, 2, 1] += 1e-9
    assert Cube(changed).fingerprint != CUBE.fingerprint
    assert Cube(VALUES.values.reshape(40, 6, 5)).fingerprint != CUBE.fingerprint
    result = _run().result()
    assert result.matches(same) and not result.matches(Cube(changed))
    with pytest.raises(ValueError, match="not the one"):
        result.trigen(Cube(changed))


def test_the_triclusters_go_to_a_long_table(tmp_path):
    trigen = _run()
    path = tmp_path / "triclusters.csv"
    trigen.result().to_csv(str(path))
    with open(path, newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == ["tricluster", "dimension", "position", "name"]
    expected = []
    for index, tricluster in enumerate(trigen.triclusters):
        for axis, positions, names in zip(("genes", "conditions", "times"),
                                          (tricluster.genes, tricluster.conditions, tricluster.times),
                                          (CUBE.genes, CUBE.conditions, CUBE.times)):
            expected += [[str(index), axis, str(position), str(names[position])] for position in positions]
    assert rows[1:] == expected


def test_a_search_that_finds_nothing_is_kept_as_such(tmp_path):
    cube = Cube([[[0.0, 1.0], [2.0, 3.0]], [[4.0, 5.0], [6.0, 7.0]]])
    trigen = TriGen(cube, n_triclusters=3, generations=2, population_size=4, seed=0)
    trigen.run()
    trigen.save(str(tmp_path / "run.json"))
    result = TriGenResult.load(str(tmp_path / "run.json"))
    assert result.triclusters == [Tricluster([0, 1], [0, 1], [0, 1])]
    assert [search["tricluster"] for search in result.searches] == [0, None, None]
    assert result.names == [{"genes": [0, 1], "conditions": [0, 1], "times": [0, 1]}]


def test_what_is_not_a_number_is_kept_as_null_and_numpy_values_as_plain_ones(tmp_path):
    result = _run().result()
    result.terms[0]["quality"] = float("nan")
    result.provenance["seed"] = np.int64(5)
    result.names[0]["times"] = [np.float32(0.5) for _ in result.names[0]["times"]]
    path = tmp_path / "run.json"
    result.save(str(path))
    document = _strict(path)
    assert document["triclusters"][0]["terms"]["quality"] is None and document["provenance"]["seed"] == 5
    assert document["triclusters"][0]["time_names"][0] == 0.5
    assert TriGenResult.load(str(path)).terms[0]["quality"] is None


def test_a_trigen_that_has_not_run_has_no_result_to_save(tmp_path):
    with pytest.raises(ValueError, match="has not run"):
        TriGen(CUBE, **SETTINGS).save(str(tmp_path / "run.json"))
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("content", ["", "not json", "[1, 2]", '{"format": "other", "version": 1}',
                                     '{"format": "metagen-trigen", "version": true}',
                                     '{"format": "metagen-trigen", "version": 0}',
                                     '{"format": "metagen-trigen", "version": 1, "triclusters": NaN}',
                                     '{"format": "metagen-trigen", "version": 1}',
                                     '{"format": "metagen-trigen", "version": "1"}'])
def test_a_file_that_is_not_a_result_is_rejected(tmp_path, content):
    path = tmp_path / "run.json"
    path.write_text(content)
    with pytest.raises(ValueError, match="not a TriGen result"):
        TriGenResult.load(str(path))


def test_a_later_version_of_the_format_asks_for_an_update(tmp_path):
    path = tmp_path / "run.json"
    path.write_text('{"format": "metagen-trigen", "version": 2}')
    with pytest.raises(ValueError, match="version 2.*update MetaGen"):
        TriGenResult.load(str(path))


def _document(tmp_path, change):
    """The saved document of a run with a change made to it, written back."""
    path = tmp_path / "run.json"
    _run().save(str(path))
    document = json.loads(path.read_text())
    change(document)
    path.write_text(json.dumps(document))
    return str(path)


def _set(*keys, value):
    def change(document):
        target = document
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = value
    return change


def _drop(*keys):
    def change(document):
        target = document
        for key in keys[:-1]:
            target = target[key]
        del target[keys[-1]]
    return change


@pytest.mark.parametrize("change", [
    _set("configuration", "history", value="somewhere.jsonl"), _set("configuration", "cube", value=1),
    _drop("configuration", "pruning"), _set("configuration", value=[1, 2]), _set("configuration", value=None),
    _set("data", value=None), _drop("data", "shape"), _set("data", "shape", value=[40, 5]),
    _set("data", "sha256", value=7), _drop("triclusters"), _drop("searches"), _drop("provenance"),
    _set("provenance", value=3), _set("triclusters", 0, "genes", value=[0]),
    _set("triclusters", 0, "genes", value=[0, 99]), _set("triclusters", 0, "gene_names", value=None),
    _set("triclusters", 0, "gene_names", value=["only one"]), _drop("triclusters", 0, "terms"),
    _set("triclusters", 0, "fitness", value="high"), _set("triclusters", value={"a": 1})])
def test_a_document_that_does_not_hold_a_result_is_rejected(tmp_path, change):
    with pytest.raises(ValueError, match="not a TriGen result"):
        TriGenResult.load(_document(tmp_path, change))


def test_the_configuration_is_every_argument_of_trigen_but_the_cube_and_the_history_file():
    from metagen.metaheuristics.trigen.results import CONFIGURATION
    arguments = set(inspect.signature(TriGen.__init__).parameters) - {"self", "cube", "history"}
    assert set(CONFIGURATION) == arguments == set(TriGen(CUBE, **SETTINGS).configuration())
    with_arrays = TriGen(CUBE, **{**SETTINGS, "min_sizes": np.array([3, 2, 2]), "selection_rate": np.float32(0.5)})
    assert json.loads(json.dumps(with_arrays.configuration()))["min_sizes"] == [3, 2, 2]


def test_a_run_with_no_default_left_runs_again_to_the_same_triclusters(tmp_path):
    trigen = _run(random_fraction=0.4, selection_rate=0.6, mutation_probability=0.5, views="time", measure="triq",
                  flat_profiles="zero", growth="quality", pruning=True)
    trigen.save(str(tmp_path / "run.json"))
    result = TriGenResult.load(str(tmp_path / "run.json"))
    for name, value in (("random_fraction", 0.4), ("selection_rate", 0.6), ("mutation_probability", 0.5),
                        ("views", "time"), ("measure", "triq"), ("flat_profiles", "zero"), ("growth", "quality"),
                        ("pruning", True)):
        assert result.configuration[name] == value
    assert result.trigen(CUBE).run() == result.triclusters


def test_the_result_is_what_the_run_recorded_whatever_is_done_to_the_trigen_afterwards(tmp_path):
    trigen = _run()
    found = list(trigen.triclusters)
    trigen.triclusters.reverse()
    trigen.generations = 99
    result = trigen.result()
    assert result.triclusters == found and result.configuration["generations"] == SETTINGS["generations"]
    assert [terms["fitness"] for terms in result.terms] == [tricluster.fitness for tricluster in result.triclusters]


def test_a_result_with_names_or_terms_that_are_not_those_of_its_triclusters_is_rejected():
    result = _run().result()
    with pytest.raises(ValueError):
        TriGenResult(result.configuration, result.provenance, result.data, result.triclusters)
    with pytest.raises(ValueError):
        TriGenResult(result.configuration, result.provenance, result.data, result.triclusters,
                     names=result.names[::-1], terms=result.terms)
    with pytest.raises(ValueError):
        TriGenResult({**result.configuration, "history": "x"}, result.provenance, result.data, [], [], [])


def test_a_run_cut_short_keeps_what_it_found_and_says_it_is_not_complete(monkeypatch):
    import metagen.metaheuristics.trigen.trigen as module
    trigen = _run()
    whole = trigen.result()
    assert whole.provenance["complete"] is True
    searches = []
    real = module.TriGenGA

    def failing(*arguments, **options):
        if len(searches) == 1:
            raise KeyboardInterrupt
        searches.append(1)
        return real(*arguments, **options)

    monkeypatch.setattr(module, "TriGenGA", failing)
    with pytest.raises(KeyboardInterrupt):
        trigen.run()
    cut = trigen.result()
    assert cut.provenance["complete"] is False and cut.triclusters == whole.triclusters[:1]
    assert 0 < cut.provenance["seconds"] < whole.provenance["seconds"] + 5
    assert cut.provenance["date"] >= whole.provenance["date"]


def test_the_significance_counts_the_evaluations_of_its_model_of_chance():
    assert _run(scoring="significance").result().provenance["chance_evaluations"] == 30 * 60


def test_saving_makes_the_folder_leaves_nothing_aside_and_keeps_the_file_on_failure(tmp_path, monkeypatch):
    result = _run().result()
    path = tmp_path / "new" / "folder" / "run.json"
    result.save(str(path))
    assert [entry.name for entry in path.parent.iterdir()] == ["run.json"]
    before = path.read_text()

    def full(*arguments, **options):
        raise OSError("no space left on device")

    monkeypatch.setattr("os.fsync", full)
    with pytest.raises(OSError):
        result.save(str(path))
    assert path.read_text() == before and [entry.name for entry in path.parent.iterdir()] == ["run.json"]


def test_names_that_are_not_text_or_numbers_are_kept_as_their_text(tmp_path):
    times = np.array(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04", "2020-01-05", "2020-01-06"],
                     dtype="datetime64[ns]")
    genes = [f"gene, the {index}th\n" if index % 2 else f"génē{index}" for index in range(40)]
    cube = Cube(VALUES.values, genes=genes, conditions=[("a", 1), b"b", 2.5, 3, None], times=list(times))
    trigen = TriGen(cube, **SETTINGS)
    trigen.run()
    trigen.save(str(tmp_path / "run.json"))
    result = TriGenResult.load(str(tmp_path / "run.json"))
    first = trigen.triclusters[0]
    assert result.names[0]["times"] == [str(times[position]) for position in first.times]
    assert result.names[0]["genes"] == [genes[position] for position in first.genes]
    plain = {0: ["a", 1], 1: "b", 2: 2.5, 3: 3, 4: None}
    assert result.names[0]["conditions"] == [plain[position] for position in first.conditions]
    result.to_csv(str(tmp_path / "table.csv"))
    with open(tmp_path / "table.csv", newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    assert [row[3] for row in rows[1:1 + len(first.genes)]] == [genes[position] for position in first.genes]


def test_a_result_saved_before_the_later_options_reads_with_the_values_it_ran_with(tmp_path):
    # A file of then ran with what the options came to default to, and with the hierarchy
    # by coordinates, its default until the hierarchy by cells took its place.
    trigen = TriGen(CUBE, **{**SETTINGS, "hierarchy": "coordinates"})
    trigen.run()
    path = tmp_path / "run.json"
    trigen.save(str(path))
    content = json.loads(path.read_text())
    for option in ("shuffle_genes", "overlap", "hierarchy"):
        del content["configuration"][option]
    path.write_text(json.dumps(content))
    result = TriGenResult.load(str(path))
    assert result.configuration["shuffle_genes"] is False
    assert result.configuration["overlap"] == result.configuration["hierarchy"] == "coordinates"
    assert result.trigen(CUBE).run() == result.triclusters


def test_a_run_by_cells_is_saved_and_run_again_as_it_was(tmp_path):
    trigen = TriGen(CUBE, **{**SETTINGS, "overlap": "cells", "hierarchy": "cells"})
    trigen.run()
    path = str(tmp_path / "run.json")
    trigen.save(path)
    result = TriGenResult.load(path)
    assert result.configuration["overlap"] == result.configuration["hierarchy"] == "cells"
    assert result.trigen(CUBE).run() == result.triclusters == trigen.triclusters


def test_a_shuffled_run_is_saved_and_run_again_as_it_was(tmp_path):
    trigen = TriGen(CUBE, **{**SETTINGS, "shuffle_genes": True})
    trigen.run()
    path = str(tmp_path / "run.json")
    trigen.save(path)
    result = TriGenResult.load(path)
    assert result.configuration["shuffle_genes"] is True
    assert result.matches(CUBE) and result.trigen(CUBE).run() == result.triclusters == trigen.triclusters
