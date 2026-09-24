"""The history of a run: one record per iteration, in memory and, with ``history``, in a
JSON Lines file, continued across a pause and a resume."""
import json
import os

import pytest

from metagen.framework import Domain
from metagen.metaheuristics import GA, SA, HillClimbing, RandomSearch, TPE
from metagen.metaheuristics.genetic.genetic_tools import GAConnector

FIELDS = {"iteration", "evaluations", "seconds", "best", "iteration_best", "mean", "std", "worst",
          "population_size", "best_solution"}


def _domain(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 0, 20)
    return domain


def _objective(solution):
    return solution["x"] ** 2 + (solution["n"] - 7) ** 2


def _read(path):
    with open(path) as handle:
        return [json.loads(line) for line in handle]


def _without_seconds(records):
    return [{key: value for key, value in record.items() if key != "seconds"} for record in records]


@pytest.mark.parametrize("build", [
    lambda **kw: RandomSearch(_domain(), max_iterations=5, seed=0, **kw),
    lambda **kw: SA(_domain(), max_iterations=5, seed=0, **kw),
    lambda **kw: HillClimbing(_domain(), max_iterations=5, seed=0, **kw),
    lambda **kw: GA(_domain(GAConnector()), max_iterations=5, seed=0, **kw),
    lambda **kw: TPE(_domain(), max_iterations=5, seed=0, **kw),
], ids=["RandomSearch", "SA", "HillClimbing", "GA", "TPE"])
def test_one_record_per_iteration_in_memory_and_in_the_file(build, tmp_path):
    path = str(tmp_path / "history.jsonl")
    calls = {"n": 0}

    def counted(solution):
        calls["n"] += 1
        return _objective(solution)

    algorithm = build(fitness_function=counted, history=path)
    algorithm.run()
    records = algorithm.history
    assert [record["iteration"] for record in records] == list(range(5))
    assert all(set(record) == FIELDS for record in records)
    assert [record["best"] for record in records] == algorithm.best_solution_fitnesses
    assert records[-1]["evaluations"] == calls["n"]
    assert all(a["evaluations"] <= b["evaluations"] for a, b in zip(records, records[1:]))
    assert all(record["iteration_best"] <= record["mean"] <= record["worst"] for record in records)
    assert records[-1]["best_solution"] == {"x": algorithm.best_solution["x"], "n": algorithm.best_solution["n"]}
    assert _read(path) == records


def test_without_a_file_the_history_is_kept_in_memory_only(tmp_path):
    algorithm = RandomSearch(_domain(), _objective, max_iterations=3, seed=0)
    algorithm.run()
    assert len(algorithm.history) == 3
    assert os.listdir(tmp_path) == []


def test_a_new_run_starts_the_file_again(tmp_path):
    path = str(tmp_path / "history.jsonl")
    algorithm = RandomSearch(_domain(), _objective, max_iterations=3, seed=0, history=path)
    algorithm.run()
    algorithm.run()
    assert [record["iteration"] for record in _read(path)] == [0, 1, 2]


def test_a_resumed_run_continues_the_history(tmp_path):
    whole = GA(_domain(GAConnector()), _objective, max_iterations=8, seed=2,
               history=str(tmp_path / "whole.jsonl"))
    whole.run()

    path = str(tmp_path / "cut.jsonl")
    checkpoint = str(tmp_path / "run.ckpt")
    algorithm = GA(_domain(GAConnector()), _objective, max_iterations=8, seed=2,
                   history=path, checkpoint=checkpoint, checkpoint_every=2)

    def cut_after_the_checkpoint(solution):
        # Iteration 5 is written to the history but its checkpoint is not: the
        # last one is at the end of iteration 3, so the resumed run repeats 4 and 5.
        if algorithm.current_iteration == 6:
            raise KeyboardInterrupt
        return _objective(solution)

    algorithm.fitness_function = cut_after_the_checkpoint
    with pytest.raises(KeyboardInterrupt):
        algorithm.run()
    assert [record["iteration"] for record in _read(path)] == list(range(6))

    resumed = GA.resume(checkpoint, _objective)
    resumed.run()
    assert _without_seconds(_read(path)) == _without_seconds(whole.history)
    assert _without_seconds(resumed.history) == _without_seconds(whole.history)
    assert all(a["seconds"] <= b["seconds"] for a, b in zip(resumed.history, resumed.history[1:]))


def test_an_inactive_variable_is_recorded_as_none(tmp_path):
    domain = Domain()
    domain.define_real("momentum", 0.5, 0.99)
    domain.define_categorical("kind", ["a", "b"])
    domain.set_condition("momentum", "kind", ["b"])
    algorithm = RandomSearch(domain, lambda s: 0.0 if s["kind"] == "a" else 1.0, max_iterations=3, seed=0)
    algorithm.run()
    best_solution = algorithm.history[-1]["best_solution"]
    assert best_solution["kind"] == "a" and best_solution["momentum"] is None
