"""What needs an optional extra: every algorithm on Ray, and the TensorFlow problem
of the examples. Each test skips cleanly where its extra is missing, so this module
collects everywhere and runs wherever it can. The CI installs neither on purpose
(P-06); on a development machine with Ray, the Ray half runs."""
import math
import pathlib
import sys

import pytest

from metagen.framework import Domain
from metagen.metaheuristics import GA, SSGA, TPE, GAConnector, HillClimbing, Memetic, RandomSearch, SA

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _sphere_domain(connector=None) -> Domain:
    domain = Domain(connector=connector)
    domain.define_real("x", -5.12, 5.12)
    domain.define_real("y", -5.12, 5.12)
    return domain


def _sphere(solution) -> float:
    return solution["x"] ** 2 + solution["y"] ** 2


def _fitness_for_the_workers():
    """A Ray worker unpickles a module-level function by importing its module, and
    test_extras is not on the worker's path. A nested function is pickled by value,
    so this is what the algorithms get; the driver keeps checking with _sphere."""
    def sphere(solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2
    return sphere


@pytest.fixture(scope="module")
def ray_runtime():
    """One Ray runtime for the module. Started here, so that run() finds it running
    and neither starts nor stops one per test (F-21), and stopped at the end."""
    ray = pytest.importorskip("ray")
    started_here = not ray.is_initialized()
    if started_here:
        ray.init(num_cpus=2, include_dashboard=False, log_to_driver=False)
    yield ray
    if started_here:
        ray.shutdown()


def _distributed(name: str, seed: int):
    domain, ga_domain = _sphere_domain(), _sphere_domain(GAConnector())
    _sphere = _fitness_for_the_workers()
    return {
        "RandomSearch": lambda: RandomSearch(domain, _sphere, population_size=6, max_iterations=3,
                                             distributed=True, seed=seed),
        "SA": lambda: SA(domain, _sphere, warmup_iterations=1, max_iterations=3,
                         neighbor_population_size=2, distributed=True, seed=seed),
        "HillClimbing": lambda: HillClimbing(domain, _sphere, population_size=6, warmup_iterations=1,
                                             max_iterations=3, distributed=True, seed=seed),
        "TPE": lambda: TPE(domain, _sphere, warmup_iterations=2, max_iterations=3,
                           distributed=True, seed=seed),
        "GA": lambda: GA(ga_domain, _sphere, population_size=6, max_iterations=3,
                         distributed=True, seed=seed),
        "SSGA": lambda: SSGA(ga_domain, _sphere, population_size=6, max_iterations=3,
                             distributed=True, seed=seed),
        "Memetic": lambda: Memetic(ga_domain, _sphere, population_size=6, max_iterations=3,
                                   neighbor_population_size=2, distributed=True, seed=seed),
    }[name]()


@pytest.mark.parametrize("name", ["RandomSearch", "SA", "HillClimbing", "TPE", "GA", "SSGA", "Memetic"])
def test_every_algorithm_runs_distributed(ray_runtime, name):
    for seed in (0, 1):
        algorithm = _distributed(name, seed)
        best = algorithm.run()
        assert ray_runtime.is_initialized(), "run() shut down a Ray it did not start (F-21)"
        assert best.get_fitness() == _sphere(best)
        assert not math.isinf(best.get_fitness())
        history = algorithm.best_solution_fitnesses
        assert history == sorted(history, reverse=True), f"{name} reports a history that worsens"
        assert best.get_fitness() == history[-1]


def test_the_distributed_initialization_builds_the_whole_population(ray_runtime):
    """The load used to be split by len(current_solutions), which after the warmup is
    one entry per warmup round and not the population (F-03)."""
    algorithm = RandomSearch(_sphere_domain(), _fitness_for_the_workers(), population_size=7,
                             max_iterations=1, distributed=True, seed=0)
    algorithm.run()
    assert len(algorithm.current_solutions) == 7


def test_the_tensorflow_problem_of_the_examples_can_be_searched():
    """The dynamic neural network of examples/problems: a structure of two to ten
    layers, each a group of neurons, activation and dropout, evaluated by training an
    LSTM. Not verified on the development machine nor in the CI, where TensorFlow is
    not installed; it is here so that an installation with the extra runs it."""
    pytest.importorskip("tensorflow")
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from examples.problems.dispatcher import problem_dispatcher

    domain, fitness = problem_dispatcher("d-nn")
    best = RandomSearch(domain, fitness, population_size=2, max_iterations=1, seed=0).run()

    assert 2 <= len(best.get("arch")) <= 10
    assert math.isfinite(best.get_fitness())
    assert best.get_fitness() == best.get_fitness()   # not NaN
