"""
The budget of a run: ``max_evaluations`` and ``timeout``, checked after the warmup and
the initialization and at the end of every iteration, so that a run goes past them by at
most one iteration, stops where an uninterrupted run would after a resume, and says what
stopped it.
"""
import time

import pytest

from metagen.framework import Domain
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch)

ALGORITHMS = [RandomSearch, GA, SSGA, SA, HillClimbing, TabuSearch, TPE, KernelTPE, Memetic]
GENETIC = (GA, SSGA, Memetic)


def _domain(algorithm) -> Domain:
    domain = Domain(connector=GAConnector()) if algorithm in GENETIC else Domain()
    domain.define_real("x", -5.12, 5.12)
    domain.define_real("y", -5.12, 5.12)
    return domain


def _sphere(solution) -> float:
    return solution["x"] ** 2 + solution["y"] ** 2


def _largest_iteration(algorithm) -> int:
    counts = [0] + [record["evaluations"] for record in algorithm.history]
    return max(later - earlier for earlier, later in zip(counts, counts[1:]))


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_a_run_stops_within_one_iteration_of_its_evaluations(algorithm):
    calls = []
    counted = lambda solution: calls.append(1) or _sphere(solution)
    budget = 400
    run = algorithm(_domain(algorithm), counted, max_iterations=10_000, max_evaluations=budget, seed=0)
    run.run()
    assert run.stop_reason == "max_evaluations"
    assert run.evaluations == len(calls) == run.history[-1]["evaluations"]
    assert budget <= run.evaluations < budget + _largest_iteration(run)


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_without_a_budget_a_run_stops_by_its_own_criterion_as_it_did(algorithm):
    reference = algorithm(_domain(algorithm), _sphere, max_iterations=5, seed=1)
    best = reference.run().get_fitness()
    run = algorithm(_domain(algorithm), _sphere, max_iterations=5, max_evaluations=10 ** 9, timeout=10 ** 6, seed=1)
    assert run.run().get_fitness() == best
    assert reference.best_solution_fitnesses == run.best_solution_fitnesses
    assert reference.stop_reason == run.stop_reason == "criterion"


def test_the_budget_cuts_the_run_an_unlimited_one_would_make():
    unlimited = HillClimbing(_domain(HillClimbing), _sphere, max_iterations=30, seed=2)
    unlimited.run()
    limited = HillClimbing(_domain(HillClimbing), _sphere, max_iterations=30, max_evaluations=100, seed=2)
    limited.run()
    without_time = lambda records: [{key: value for key, value in record.items() if key != "seconds"}
                                    for record in records]
    assert without_time(limited.history) == without_time(unlimited.history[:len(limited.history)])
    assert len(limited.history) < len(unlimited.history)


def test_a_budget_spent_by_the_start_runs_no_iteration():
    run = TPE(_domain(TPE), _sphere, population_size=10, warmup_iterations=2, max_evaluations=20, seed=0)
    best = run.run()
    assert run.stop_reason == "max_evaluations"
    assert run.history == [] and run.evaluations == 30
    assert best.get_fitness() == run.best_solution.get_fitness()


def test_a_run_stops_within_one_iteration_of_its_time():
    def slow(solution) -> float:
        time.sleep(0.005)
        return _sphere(solution)

    run = RandomSearch(_domain(RandomSearch), slow, population_size=5, max_iterations=10 ** 6, timeout=0.3, seed=0)
    run.run()
    assert run.stop_reason == "timeout"
    assert run.seconds >= 0.3
    assert run.history[-2]["seconds"] < 0.3


def test_the_first_limit_reached_is_the_one_that_stops_it():
    run = RandomSearch(_domain(RandomSearch), _sphere, max_iterations=10 ** 6, max_evaluations=50, timeout=3600, seed=0)
    run.run()
    assert run.stop_reason == "max_evaluations"


def test_a_resumed_run_stops_where_an_uninterrupted_one_would(tmp_path, monkeypatch):
    def build(**arguments):
        return GA(_domain(GA), _sphere, population_size=10, max_iterations=10_000, max_evaluations=200, seed=3,
                  **arguments)

    reference = build()
    reference.run()
    path = str(tmp_path / "run.pkl")
    original = GA.post_iteration

    def stop_after_two(self):
        original(self)
        if self.current_iteration >= 2:
            self.request_stop()

    monkeypatch.setattr(GA, "post_iteration", stop_after_two)
    cut = build(checkpoint=path)
    cut.run()
    assert cut.stop_reason == "request_stop"
    monkeypatch.undo()
    resumed = GA.resume(path, _sphere)
    assert resumed.run().get_fitness() == reference.best_solution.get_fitness()
    assert (resumed.evaluations, resumed.stop_reason) == (reference.evaluations, "max_evaluations")
    assert resumed.best_solution_fitnesses == reference.best_solution_fitnesses


def test_the_reason_is_none_before_a_run():
    assert RandomSearch(_domain(RandomSearch), _sphere).stop_reason is None


@pytest.mark.parametrize("arguments", [{"max_evaluations": 0}, {"max_evaluations": -5}, {"max_evaluations": 2.5},
                                       {"max_evaluations": True}, {"timeout": 0}, {"timeout": -1.0},
                                       {"timeout": float("inf")}, {"timeout": float("nan")}, {"timeout": "60"}])
def test_a_budget_that_is_not_one_is_refused(arguments):
    with pytest.raises(ValueError):
        RandomSearch(_domain(RandomSearch), _sphere, **arguments)
