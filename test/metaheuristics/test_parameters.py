"""
Parameters and hooks every user can reach, each exercised end to end.

The benchmark runs the algorithms with their defaults; this module turns the other
knobs: the gamma schedules of the two Parzen estimators and of hill climbing, the
tournament size of the genetic algorithms, the tabu radius, the callbacks of the base
class, the console and file logs, and the constructor checks.
"""
import logging

import pytest

from metagen.framework import Domain, Solution
from metagen.logging import metagen_logger as logger_module
from metagen.metaheuristics import (GA, SSGA, GAConnector, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch, TPE)
from metagen.metaheuristics.gamma_schedules import GammaConfig, compute_gamma


def _sphere(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_real("y", -5.0, 5.0)

    def fitness(solution: Solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2

    return domain, fitness


def _is_sound(algorithm) -> None:
    """The run returns the best solution it saw and its history never gets worse."""
    best = algorithm.run()
    history = algorithm.best_solution_fitnesses
    assert best.get_fitness() == min(history)
    assert all(later <= earlier for earlier, later in zip(history, history[1:]))


SCHEDULES = [GammaConfig("sampled_based"), GammaConfig("sqrt"),
             GammaConfig("linear", minimum=0.1, maximum=0.4),
             GammaConfig("exponential", minimum=0.1, maximum=0.4, alpha=3.0)]


@pytest.mark.parametrize("schedule", SCHEDULES, ids=lambda s: s.gamma_function)
def test_every_gamma_schedule_gives_a_fraction(schedule):
    for iteration in range(0, 11):
        gamma = compute_gamma(schedule, iteration=iteration, max_iterations=10, num_solutions=40)
        assert 0.0 < gamma <= 1.0


def test_the_linear_and_exponential_schedules_fall_from_maximum_to_minimum():
    for schedule in SCHEDULES[2:]:
        first = compute_gamma(schedule, iteration=0, max_iterations=10, num_solutions=40)
        last = compute_gamma(schedule, iteration=10, max_iterations=10, num_solutions=40)
        assert first == pytest.approx(0.4) and last < first
        assert last >= 0.1 - 1e-9


def test_an_unknown_gamma_schedule_is_refused():
    with pytest.raises(ValueError):
        compute_gamma(GammaConfig("cubic"), iteration=1, max_iterations=10, num_solutions=40)


@pytest.mark.parametrize("schedule", SCHEDULES, ids=lambda s: s.gamma_function)
@pytest.mark.parametrize("estimator", [TPE, KernelTPE], ids=lambda c: c.__name__)
def test_the_parzen_estimators_run_under_every_gamma_schedule(estimator, schedule):
    domain, fitness = _sphere()
    _is_sound(estimator(domain, fitness, population_size=6, warmup_iterations=1, max_iterations=6,
                        gamma_config=schedule, seed=0))


def test_hill_climbing_samples_a_share_of_its_neighbors_under_a_gamma_schedule():
    domain, fitness = _sphere()
    calls = {"all": 0, "share": 0}

    def counting(key):
        def counted(solution):
            calls[key] += 1
            return fitness(solution)
        return counted

    HillClimbing(domain, counting("all"), population_size=10, warmup_iterations=0, max_iterations=5, seed=0).run()
    climber = HillClimbing(domain, counting("share"), population_size=10, warmup_iterations=0, max_iterations=5,
                           gamma_config=GammaConfig("linear", minimum=0.2, maximum=0.5), seed=0)
    _is_sound(climber)
    assert calls["share"] < calls["all"]


@pytest.mark.parametrize("tournament_size", [1, 3, 6])
@pytest.mark.parametrize("algorithm", [GA, SSGA, Memetic], ids=lambda c: c.__name__)
def test_the_genetic_algorithms_run_with_any_tournament_size(algorithm, tournament_size):
    domain, fitness = _sphere(GAConnector())
    _is_sound(algorithm(domain, fitness, population_size=6, max_iterations=3,
                        tournament_size=tournament_size, seed=0))


@pytest.mark.parametrize("tabu_radius", [None, 0.5])
def test_tabu_search_runs_with_no_radius_and_with_an_absolute_one(tabu_radius):
    domain, fitness = _sphere()
    _is_sound(TabuSearch(domain, fitness, population_size=6, warmup_iterations=1, max_iterations=6,
                         tabu_radius=tabu_radius, seed=0))


def test_the_callbacks_run_in_order_around_the_iterations():
    domain, fitness = _sphere()
    calls = []

    class Traced(RandomSearch):
        def pre_execution(self):
            calls.append("pre_execution")
            super().pre_execution()

        def pre_iteration(self):
            calls.append("pre_iteration")
            super().pre_iteration()

        def post_iteration(self):
            super().post_iteration()
            calls.append("post_iteration")

        def post_execution(self):
            super().post_execution()
            calls.append("post_execution")

    Traced(domain, fitness, population_size=4, max_iterations=3, seed=0).run()
    assert calls[0] == "pre_execution" and calls[-1] == "post_execution"
    assert calls[1:-1] == ["pre_iteration", "post_iteration"] * 3


@pytest.mark.parametrize("algorithm", [GA, SSGA, Memetic], ids=lambda c: c.__name__)
def test_a_population_too_small_to_cross_is_refused_at_construction(algorithm):
    domain, fitness = _sphere(GAConnector())
    with pytest.raises(ValueError, match="population of at least 2"):
        algorithm(domain, fitness, population_size=1)


def test_the_file_log_is_written_once_however_many_times_it_is_asked_for(tmp_path):
    logger = logger_module.metagen_logger
    before = list(logger.handlers)
    level = logger.level
    try:
        logger_module.set_metagen_logger_file_handler(str(tmp_path))
        logger_module.set_metagen_logger_file_handler(str(tmp_path))
        logger.setLevel(logging.INFO)
        logger.info("a line for the file")
        added = [handler for handler in logger.handlers if handler not in before]
        assert len(added) == 1
        added[0].flush()
        files = list(tmp_path.iterdir())
        assert len(files) == 1 and "a line for the file" in files[0].read_text()
    finally:
        for handler in [h for h in logger.handlers if h not in before]:
            logger.removeHandler(handler)
            handler.close()
        logger.setLevel(level)


# --------------------------------------------------------------------------------------------
# Every metaheuristic takes the options of the base class, with the same defaults, and hands
# them on to it: an option added to Metaheuristic and forgotten in one of the ten constructors
# would leave that algorithm without it, with no error.
# --------------------------------------------------------------------------------------------

import inspect

from metagen.metaheuristics import (SA, TPE, Metaheuristic, Racing, RandomSearch, TabuSearch)

#: The options of a run, which every metaheuristic takes as Metaheuristic does.
_COMMON = ("distributed", "log_dir", "seed", "distribution_model", "checkpoint", "checkpoint_every", "history",
           "max_evaluations", "timeout", "initial_solutions", "racing", "refit")

#: What an algorithm leaves out on purpose. Its own size of population, warmup and iterations
#: are its own choice; these are the base options it does not take at all.
_LEFT_OUT = {
    # A first population drawn at random: a warmup of random solutions adds nothing to it.
    RandomSearch: {"warmup_iterations"}, GA: {"warmup_iterations"}, SSGA: {"warmup_iterations"},
    Memetic: {"warmup_iterations"},
    # A single walker.
    SA: {"population_size"},
}

_ALGORITHMS = (RandomSearch, GA, SSGA, SA, HillClimbing, TabuSearch, TPE, KernelTPE, Memetic)


def _base_options():
    return [name for name in inspect.signature(Metaheuristic.__init__).parameters
            if name not in ("self", "domain", "fitness_function")]


@pytest.mark.parametrize("algorithm", _ALGORITHMS, ids=lambda c: c.__name__)
def test_a_metaheuristic_takes_every_option_of_the_base_class(algorithm):
    base = inspect.signature(Metaheuristic.__init__).parameters
    own = inspect.signature(algorithm.__init__).parameters
    missing = [name for name in _base_options() if name not in own and name not in _LEFT_OUT.get(algorithm, set())]
    assert not missing, f"{algorithm.__name__} does not take {missing}"
    for name in _COMMON:
        assert repr(own[name].default) == repr(base[name].default), (
            f"{algorithm.__name__}.{name} defaults to {own[name].default!r}, the base to {base[name].default!r}")


@pytest.mark.parametrize("algorithm", _ALGORITHMS, ids=lambda c: c.__name__)
def test_a_metaheuristic_hands_every_option_of_a_run_on_to_the_base_class(algorithm, tmp_path, monkeypatch):
    received = {}
    original = Metaheuristic.__init__

    def spy(self, *args, **kwargs):
        bound = inspect.signature(original).bind(self, *args, **kwargs)
        received.update(bound.arguments)
        # Built for real, but not distributed: the value is what is checked, Ray is not needed.
        bound.arguments["distributed"] = False
        original(*bound.args, **bound.kwargs)

    monkeypatch.setattr(Metaheuristic, "__init__", spy)
    given = {"distributed": True, "log_dir": str(tmp_path / "logs"), "seed": 1234, "distribution_model": "islands",
             "checkpoint": str(tmp_path / "run.ckpt"), "checkpoint_every": 3, "history": str(tmp_path / "run.jsonl"),
             "max_evaluations": 77, "timeout": 9.5, "initial_solutions": [], "racing": Racing(first_steps=4),
             "refit": len}
    connector = GAConnector() if algorithm in (GA, SSGA, Memetic) else None
    domain, fitness = _sphere(connector)
    algorithm(domain, fitness, **given)
    wrong = {name: received.get(name, "<not handed on>") for name in _COMMON if received.get(name) is not given[name]}
    assert not wrong, f"{algorithm.__name__} hands on {wrong}"


@pytest.mark.parametrize("algorithm", _ALGORITHMS, ids=lambda c: c.__name__)
def test_the_docstring_of_a_metaheuristic_documents_each_of_its_parameters_once(algorithm):
    import re

    documented = re.findall(r":param (\w+):", algorithm.__doc__)
    taken = [name for name in inspect.signature(algorithm.__init__).parameters if name != "self"]
    assert sorted(documented) == sorted(taken), (
        f"{algorithm.__name__}: documented and not taken {sorted(set(documented) - set(taken))}, "
        f"taken and not documented {sorted(set(taken) - set(documented))}, "
        f"documented twice {sorted({name for name in documented if documented.count(name) > 1})}")
    assert algorithm.__init__.__doc__ is None or ":param" not in algorithm.__init__.__doc__, (
        f"{algorithm.__name__}.__init__ documents parameters again: the reference shows both docstrings")
