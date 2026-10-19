"""
Racing: a fitness function that yields its steps is evaluated step by step, and with a Racing a
candidate significantly worse than the population it started from gets no more steps. The best
of a run is always a solution evaluated whole, the budget counts the steps, and a run without
racing evaluates every step.
"""
import numpy as np
import pytest

from metagen.framework import Domain
from metagen.metaheuristics import GA, TPE, GAConnector, HillClimbing, KernelTPE, Racing, RandomSearch
from metagen.metaheuristics.racing import corrected_mean, worse_than_the_best

NOISE = np.random.default_rng(0).normal(0, 0.3, size=10)


def _domain(connector=None) -> Domain:
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_real("y", -5.0, 5.0)
    return domain


def _folds(solution):
    base = solution["x"] ** 2 + solution["y"] ** 2
    for fold in range(10):
        yield base + NOISE[fold] + 0.5 * fold      # the later folds are harder for everyone


def _mean_of_folds(solution):
    return float(np.mean(list(_folds(solution))))


@pytest.mark.parametrize("arguments", [{"first_steps": 1}, {"first_steps": 2.5}, {"alpha": 0.0}, {"alpha": 1.0}])
def test_a_racing_that_is_not_one_is_refused(arguments):
    with pytest.raises(ValueError):
        Racing(**arguments)


def test_only_racing_or_none_is_taken():
    with pytest.raises(ValueError, match="racing"):
        RandomSearch(_domain(), _folds, racing="yes")


def test_the_test_stops_a_clearly_worse_candidate_and_not_an_equal_one():
    population = [[1.0 + 0.1 * j + 0.01 * i for j in range(5)] for i in range(6)]
    racing = Racing(first_steps=3)
    assert racing.eliminates([5.0, 5.1, 5.2], population)
    assert not racing.eliminates(population[0][:3], population[1:])
    assert not racing.eliminates([5.0, 5.1], population), "not before first_steps"
    matrix = np.array([[1.0, 1.0, 1.0]] * 5)
    assert not worse_than_the_best(matrix, 0, 0.05), "all tied"


def test_a_stopped_candidate_is_corrected_by_the_steps_it_did_not_see():
    population = [[1.0, 2.0, 3.0, 4.0], [1.2, 2.2, 3.2, 4.2]]
    # Its partial mean is 6.0; the population's mean moves by +1.0 from two steps to four.
    assert corrected_mean([5.5, 6.5], population) == pytest.approx(7.0)


def test_without_racing_a_yielding_fitness_is_the_mean_of_its_steps():
    run = RandomSearch(_domain(), _folds, population_size=5, max_iterations=2, seed=0)
    best = run.run()
    assert best.get_fitness() == pytest.approx(_mean_of_folds(best))
    assert len(best.step_values) == 10 and best.raced_out is False
    assert run.history[-1]["steps"] == 10 * run.evaluations


def test_every_solution_must_yield_as_many_steps():
    def uneven(solution):
        yield from range(3 if solution["x"] < 0 else 4)

    with pytest.raises(ValueError, match="as many"):
        RandomSearch(_domain(), uneven, population_size=20, max_iterations=2, seed=0).run()


@pytest.mark.parametrize("algorithm", [RandomSearch, GA, TPE, KernelTPE, HillClimbing],
                         ids=lambda algorithm: algorithm.__name__)
def test_racing_saves_steps_and_the_best_is_always_evaluated_whole(algorithm):
    domain = _domain(GAConnector()) if algorithm is GA else _domain()
    extra = {"max_iterations": 40} if algorithm is KernelTPE else {"max_iterations": 8}
    plain = algorithm(domain, _folds, seed=0, **extra)
    plain.run()
    raced = algorithm(domain, _folds, seed=0, racing=Racing(), **extra)
    best = raced.run()
    assert best.raced_out is False and best.get_fitness() == pytest.approx(_mean_of_folds(best))
    assert raced.history[-1]["steps"] < plain.history[-1]["steps"]
    assert raced.history[-1]["evaluations"] == plain.history[-1]["evaluations"]


def test_the_initial_population_is_evaluated_whole():
    run = RandomSearch(_domain(), _folds, population_size=10, max_iterations=0, seed=0, racing=Racing())
    run.run()
    assert all(len(solution.step_values) == 10 and not solution.raced_out for solution in run.current_solutions)


def test_with_racing_the_budget_counts_the_steps():
    run = GA(_domain(GAConnector()), _folds, max_evaluations=200, seed=0, racing=Racing())
    run.run()
    spent = run.history[-1]["steps"] / 10
    assert run.stop_reason == "max_evaluations" and spent >= 200
    assert run.evaluations > spent, "candidates stopped early spend less than a whole evaluation"


def test_a_raced_run_is_reproducible():
    first = GA(_domain(GAConnector()), _folds, max_iterations=6, seed=3, racing=Racing())
    second = GA(_domain(GAConnector()), _folds, max_iterations=6, seed=3, racing=Racing())
    assert first.run().get_fitness() == second.run().get_fitness()
    without_time = lambda run: [{key: value for key, value in record.items() if key != "seconds"}
                                for record in run.history]
    assert without_time(first) == without_time(second)
