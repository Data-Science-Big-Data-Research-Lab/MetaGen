"""
Starting a run from known solutions: ``initial_solutions`` take the place of as many solutions of
the initial population, so the cost of a run does not change; the variables left out are drawn
from the seeded generators; and a value that does not fit the domain is refused when the
metaheuristic is built.
"""
import pytest

from metagen.framework import Domain
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch)

ALGORITHMS = [RandomSearch, GA, SSGA, SA, HillClimbing, TabuSearch, TPE, KernelTPE, Memetic]
GENETIC = (GA, SSGA, Memetic)
OPTIMUM = {"x": 1.25, "y": -0.5}


def _domain(algorithm) -> Domain:
    domain = Domain(connector=GAConnector()) if algorithm in GENETIC else Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_real("y", -5.0, 5.0)
    return domain


def _bowl(solution) -> float:
    return (solution["x"] - OPTIMUM["x"]) ** 2 + (solution["y"] - OPTIMUM["y"]) ** 2


def _counted():
    calls = []
    return calls, (lambda solution: calls.append(1) or _bowl(solution))


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_an_initial_solution_takes_a_place_of_the_population_and_the_cost_stays(algorithm):
    calls, fitness = _counted()
    algorithm(_domain(algorithm), fitness, max_iterations=3, seed=0).run()
    without = len(calls)
    calls.clear()
    run = algorithm(_domain(algorithm), fitness, max_iterations=3, seed=0, initial_solutions=[OPTIMUM])
    best = run.run()
    assert len(calls) == without
    assert best.get_fitness() == 0.0 and best["x"] == OPTIMUM["x"] and best["y"] == OPTIMUM["y"]
    assert run.best_solution_fitnesses[0] == 0.0


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_without_initial_solutions_a_run_is_as_it_was(algorithm):
    plain = algorithm(_domain(algorithm), _bowl, max_iterations=3, seed=2)
    empty = algorithm(_domain(algorithm), _bowl, max_iterations=3, seed=2, initial_solutions=[])
    assert plain.run().get_fitness() == empty.run().get_fitness()
    assert plain.best_solution_fitnesses == empty.best_solution_fitnesses


def test_the_variables_left_out_are_drawn_from_the_seed():
    def first_evaluated(seed):
        seen = []
        RandomSearch(_domain(RandomSearch), lambda s: seen.append((s["x"], s["y"])) or _bowl(s), population_size=4,
                     max_iterations=1, seed=seed, initial_solutions=[{"x": 2.0}]).run()
        return seen[0]

    first = first_evaluated(7)
    assert first[0] == 2.0 and -5.0 <= first[1] <= 5.0
    assert first_evaluated(7) == first
    assert first_evaluated(8)[1] != first[1]


def test_simulated_annealing_starts_from_the_initial_solution():
    seen = []
    SA(_domain(SA), lambda s: seen.append((s["x"], s["y"])) or _bowl(s), warmup_iterations=0, max_iterations=1,
       seed=0, initial_solutions=[{"x": 4.0, "y": 4.0}]).run()
    assert seen[0] == (4.0, 4.0)


def test_kernel_tpe_models_on_the_initial_solutions():
    run = KernelTPE(_domain(KernelTPE), _bowl, population_size=5, warmup_iterations=0, max_iterations=2, seed=0,
                    initial_solutions=[OPTIMUM, {"x": -4.0, "y": 4.0}])
    run.run()
    values = [(solution["x"], solution["y"]) for solution in run.current_solutions]
    assert (1.25, -0.5) in values and (-4.0, 4.0) in values


@pytest.mark.parametrize("initial, message", [
    ([{"z": 1.0}], "'z' is not a variable"),
    ([{"x": 9.0}], "not a valid value of 'x'"),
    ([{"x": "far"}], "not a valid value of 'x'"),
    ([OPTIMUM] * 11, "at most population_size=10"),
])
def test_an_initial_solution_that_does_not_fit_is_refused(initial, message):
    with pytest.raises(ValueError, match=message):
        RandomSearch(_domain(RandomSearch), _bowl, population_size=10, initial_solutions=initial)


def test_building_the_metaheuristic_draws_nothing():
    from metagen.framework.rng import get_rng, set_seed

    set_seed(3)
    expected = get_rng().random()
    set_seed(3)
    RandomSearch(_domain(RandomSearch), _bowl, initial_solutions=[{"x": 1.0}])
    assert get_rng().random() == expected
