"""
The budget of a run: ``max_evaluations`` and ``timeout``, checked after each round of the
warmup, after the initialization and at the end of every iteration, so that a run goes past
them by at most one of those, stops where an uninterrupted run would after a resume, and
says what stopped it.
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


@pytest.mark.parametrize("algorithm", [TPE, KernelTPE], ids=lambda algorithm: algorithm.__name__)
def test_a_budget_smaller_than_the_warmup_ends_it_early(algorithm):
    # Ten rounds of 20 for TPE and five for KernelTPE by default: three rounds reach 60, and
    # the initial population of 20 is evaluated whole.
    calls = []
    run = algorithm(_domain(algorithm), lambda solution: calls.append(1) or _sphere(solution), max_evaluations=60, seed=0)
    best = run.run()
    assert run.stop_reason == "max_evaluations" and run.evaluations == len(calls) == 80
    assert best.get_fitness() == min(run.best_solution_fitnesses or [best.get_fitness()])


@pytest.mark.parametrize("algorithm", [TPE, KernelTPE], ids=lambda algorithm: algorithm.__name__)
def test_a_budget_reached_inside_a_round_of_the_warmup_goes_past_by_that_round_and_the_initial_population(algorithm):
    # 30 is reached in the second round of 20 (40), and the initial population of 20 follows:
    # 30 past the limit, more than either step alone and no more than both, as documented
    run = algorithm(_domain(algorithm), _sphere, max_evaluations=30, seed=0)
    run.run()
    assert run.stop_reason == "max_evaluations" and run.evaluations == 60
    assert run.evaluations - 30 > 20 and run.evaluations <= 30 + 20 + 20


def test_a_budget_larger_than_the_warmup_runs_all_of_it():
    calls = []
    TPE(_domain(TPE), lambda solution: calls.append(1) or _sphere(solution), max_evaluations=230,
        max_iterations=1, seed=0).run()
    assert len(calls) == 200 + 20 + 24


def test_a_timeout_ends_the_warmup_early():
    def slow(solution) -> float:
        time.sleep(0.01)
        return _sphere(solution)

    run = TPE(_domain(TPE), slow, timeout=0.3, seed=0)
    run.run()
    assert run.stop_reason == "timeout" and run.history == []
    assert run.evaluations < 200, "the warmup alone is 200 evaluations of 10 ms"


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


# --- max_iterations under a budget ------------------------------------------------

NO_HORIZON = [RandomSearch, GA, SSGA, HillClimbing, TabuSearch, Memetic]
DEFAULTS = {RandomSearch: 20, GA: 50, SSGA: 50, SA: 20, HillClimbing: 20, TabuSearch: 20, TPE: 50,
            KernelTPE: 100, Memetic: 20}


def _iterations_of(run) -> object:
    return run.max_generations if isinstance(run, Memetic) else run.max_iterations


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_without_a_budget_the_default_iterations_are_those_of_always(algorithm):
    run = algorithm(_domain(algorithm), _sphere, seed=5)
    assert _iterations_of(run) == DEFAULTS[algorithm]
    explicit = algorithm(_domain(algorithm), _sphere, max_iterations=DEFAULTS[algorithm], seed=5)
    assert run.run().get_fitness() == explicit.run().get_fitness()
    assert run.best_solution_fitnesses == explicit.best_solution_fitnesses


@pytest.mark.parametrize("algorithm", NO_HORIZON, ids=lambda algorithm: algorithm.__name__)
def test_a_budget_without_max_iterations_lifts_the_limit_of_iterations(algorithm):
    run = algorithm(_domain(algorithm), _sphere, max_evaluations=1500, seed=0)
    assert _iterations_of(run) is None
    run.run()
    assert run.stop_reason == "max_evaluations" and run.evaluations >= 1500
    assert len(run.history) > DEFAULTS[algorithm] or algorithm in (GA, Memetic)


def test_a_timeout_without_max_iterations_lifts_the_limit_too():
    run = SSGA(_domain(SSGA), _sphere, timeout=0.5, seed=0)
    run.run()
    assert run.stop_reason == "timeout" and len(run.history) > DEFAULTS[SSGA]


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_with_both_the_first_reached_stops_the_run(algorithm):
    run = algorithm(_domain(algorithm), _sphere, max_iterations=2, max_evaluations=10 ** 9, seed=0)
    run.run()
    assert (run.stop_reason, len(run.history)) == ("criterion", 2)


def test_the_cooling_of_sa_spans_the_iterations_its_budget_buys():
    run = SA(_domain(SA), _sphere, warmup_iterations=5, neighbor_population_size=5, max_evaluations=306, seed=0)
    assert run.max_iterations == 60          # (306 - 5 warmup - 1 start) / 5 neighbors
    assert run.cooling_rate == pytest.approx((run.T_min / run.initial_temp) ** (1 / 60))
    run.run()
    assert (run.stop_reason, len(run.history), run.evaluations) == ("max_evaluations", 60, 306)
    assert run.current_temp == pytest.approx(run.T_min)


@pytest.mark.parametrize("algorithm, start, per_iteration", [(TPE, 10 * 3, 4), (KernelTPE, 10 * 3, 1)],
                         ids=["TPE", "KernelTPE"])
def test_a_tpe_plans_over_the_iterations_its_budget_buys(algorithm, start, per_iteration):
    extra = {"candidate_pool_size": 4} if algorithm is TPE else {}
    run = algorithm(_domain(algorithm), _sphere, population_size=10, warmup_iterations=2, max_evaluations=110,
                    seed=0, **extra)
    assert run.max_iterations == (110 - start) // per_iteration
    run.run()
    assert (run.stop_reason, len(run.history), run.evaluations) == ("max_evaluations", run.max_iterations, 110)


@pytest.mark.parametrize("algorithm", [SA, TPE, KernelTPE], ids=lambda algorithm: algorithm.__name__)
def test_with_a_timeout_alone_an_algorithm_that_plans_keeps_its_default(algorithm):
    run = algorithm(_domain(algorithm), _sphere, timeout=3600, seed=0)
    assert run.max_iterations == DEFAULTS[algorithm]
    run.run()
    assert (run.stop_reason, len(run.history)) == ("criterion", DEFAULTS[algorithm])


@pytest.mark.parametrize("schedule", ["linear", "exponential", "sampled_based"])
def test_the_gamma_schedule_of_hill_climbing_spans_its_budget(schedule):
    from metagen.metaheuristics.gamma_schedules import GammaConfig

    run = HillClimbing(_domain(HillClimbing), _sphere, max_evaluations=600, seed=0,
                       gamma_config=GammaConfig(gamma_function=schedule))
    run.run()
    assert run.stop_reason == "max_evaluations"
    assert abs(len(run.history) - run.max_iterations) <= 2


def test_a_gamma_schedule_past_its_horizon_stays_at_its_end():
    from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma

    for schedule in ("linear", "exponential"):
        config = GammaConfig(gamma_function=schedule)
        end = compute_gamma(config, iteration=10, max_iterations=10, num_solutions=20)
        assert compute_gamma(config, iteration=25, max_iterations=10, num_solutions=20) == end
