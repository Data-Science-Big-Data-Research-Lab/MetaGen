"""
The best model of a run: a fitness function may return its value and the model it
trained, and the run keeps the model of its best evaluation in ``best_model``; ``refit``
trains one for the best solution when the run ends; ``save_best_model`` writes it in the
format of its library.
"""
import pickle
import sys
import types

import pytest

from metagen.framework import Domain
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch)

ALGORITHMS = [RandomSearch, GA, SSGA, SA, HillClimbing, TabuSearch, TPE, KernelTPE, Memetic]
GENETIC = (GA, SSGA, Memetic)
OPTIONS = {RandomSearch: {}, GA: {}, SSGA: {}, SA: {}, HillClimbing: {}, TabuSearch: {},
           TPE: dict(warmup_iterations=1, candidate_pool_size=4), KernelTPE: dict(warmup_iterations=1), Memetic: {}}


def _domain(algorithm) -> Domain:
    domain = Domain(connector=GAConnector()) if algorithm in GENETIC else Domain()
    domain.define_real("x", -5.12, 5.12)
    domain.define_real("y", -5.12, 5.12)
    return domain


def _sphere(solution) -> float:
    return solution["x"] ** 2 + solution["y"] ** 2


def _trained(solution):
    """A fitness function that returns the model it trained: here, what it was trained on."""
    return _sphere(solution), ("model", solution["x"], solution["y"])


def _build(algorithm, fitness, **options):
    return algorithm(_domain(algorithm), fitness, max_iterations=4, seed=3, **{**OPTIONS[algorithm], **options})


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda algorithm: algorithm.__name__)
def test_the_model_of_the_best_evaluation_is_kept_and_the_search_does_not_change(algorithm):
    plain = _build(algorithm, _sphere)
    best_plain = plain.run()
    run = _build(algorithm, _trained)
    best = run.run()
    assert run.best_model == ("model", best["x"], best["y"])
    timeless = [[{key: value for key, value in record.items() if key != "seconds"} for record in history]
                for history in (run.history, plain.history)]
    assert best.get_fitness() == best_plain.get_fitness() and timeless[0] == timeless[1]
    assert plain.best_model is None


def test_refit_trains_the_model_of_the_best_solution_once():
    calls = []

    def refit(solution):
        calls.append((solution["x"], solution["y"]))
        return ("refitted", solution["x"])

    run = _build(GA, _trained, refit=refit)
    best = run.run()
    assert calls == [(best["x"], best["y"])] and run.best_model == ("refitted", best["x"])
    with pytest.raises(ValueError, match="refit"):
        _build(GA, _sphere, refit="no")


def test_a_run_ends_with_no_model_when_none_was_given(tmp_path):
    run = _build(GA, _sphere)
    run.run()
    with pytest.raises(ValueError, match="no model"):
        run.save_best_model(str(tmp_path / "model.joblib"))


def test_a_solution_evaluated_alone_takes_the_value_of_the_pair():
    domain = _domain(GA)
    from metagen.metaheuristics.tools import solution_class
    solution = solution_class(domain)(domain, connector=domain.get_connector())
    solution.evaluate(_trained)
    assert solution.get_fitness() == _sphere(solution)


class _Unpicklable:
    def __reduce__(self):
        raise TypeError("cannot pickle this model")


def test_a_resumed_run_keeps_the_best_model_and_one_the_checkpoint_cannot_hold_is_left_out(tmp_path):
    whole = _build(GA, _trained, max_evaluations=None)
    whole.run()
    path = str(tmp_path / "ga.ckpt")
    seen = []

    def stopping(solution):
        seen.append(1)
        if len(seen) == 25:
            cut.request_stop()
        return _trained(solution)

    cut = _build(GA, stopping, checkpoint=path)
    cut.run()
    resumed = GA.resume(path, _trained)
    resumed.run()
    assert resumed.best_model == whole.best_model

    def unpicklable(solution):
        return _sphere(solution), _Unpicklable()

    run = _build(GA, unpicklable, checkpoint=str(tmp_path / "other.ckpt"), checkpoint_every=1)
    with pytest.warns(RuntimeWarning, match="cannot be saved in the checkpoint"):
        run.run()
    assert isinstance(run.best_model, _Unpicklable)


def test_a_model_is_saved_in_the_format_of_its_library(tmp_path, monkeypatch):
    pytest.importorskip("joblib")
    import joblib
    run = _build(GA, _trained)
    run.run()
    path = run.save_best_model(str(tmp_path / "plain.joblib"))
    assert joblib.load(path) == run.best_model

    saved = {}

    def writes(library):
        def save(*arguments):
            target = arguments[-1]
            saved[library] = target
            with open(target, "w") as handle:
                handle.write(library)
        return save

    keras_like = type("Sequential", (), {"__module__": "keras.src.models.sequential",
                                         "save": lambda self, path: writes("keras")(path)})
    run.best_model = keras_like()
    written = run.save_best_model(str(tmp_path / "net"))
    assert written == str(tmp_path / "net.keras") and open(written).read() == "keras"

    fake_torch = types.ModuleType("torch")
    fake_torch.save = lambda model, path: writes("torch")(path)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    torch_like = type("Linear", (), {"__module__": "torch.nn.modules.linear"})
    run.best_model = torch_like()
    written = run.save_best_model(str(tmp_path / "net.pt"))
    assert written == str(tmp_path / "net.pt") and open(written).read() == "torch"
    # A network is most often a class of the user's own, built on the library's
    own_network = type("Network", (torch_like,), {"__module__": "my_project.models"})
    run.best_model = own_network()
    assert open(run.save_best_model(str(tmp_path / "own.pt"))).read() == "torch"
    own_keras = type("MyModel", (keras_like,), {"__module__": "my_project.models"})
    run.best_model = own_keras()
    written = run.save_best_model(str(tmp_path / "mine"))
    assert written == str(tmp_path / "mine.keras") and open(written).read() == "keras"
    # Written aside and renamed over: nothing partial is left
    assert not [child for child in tmp_path.iterdir() if ".partial" in child.name]


def test_without_joblib_a_model_is_pickled(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "joblib", None)
    run = _build(GA, _trained)
    run.run()
    path = run.save_best_model(str(tmp_path / "plain.pkl"))
    with open(path, "rb") as handle:
        assert pickle.load(handle) == run.best_model


@pytest.fixture(scope="module")
def ray_runtime():
    ray = pytest.importorskip("ray")
    started_here = not ray.is_initialized()
    if started_here:
        ray.init(num_cpus=2, include_dashboard=False, log_to_driver=False)
    yield ray
    if started_here:
        ray.shutdown()


@pytest.mark.parametrize("model", ["global", "islands"])
def test_on_ray_the_best_model_comes_back_from_the_worker_that_trained_it(ray_runtime, model):
    def trained(solution):
        return solution["x"] ** 2 + solution["y"] ** 2, ("model", solution["x"], solution["y"])

    run = GA(_domain(GA), trained, population_size=6, max_iterations=3, distributed=True, seed=4,
             distribution_model=model)
    best = run.run()
    assert run.best_model == ("model", best["x"], best["y"])


def test_a_model_no_format_can_hold_is_not_saved_and_is_not_lost(tmp_path):
    run = _build(GA, _trained)
    run.run()
    path = tmp_path / "model.joblib"
    path.write_bytes(b"what was there")
    model = _Unpicklable()
    run.best_model = model
    with pytest.raises(ValueError, match="cannot be saved with .*save it with the method of its library"):
        run.save_best_model(str(path))
    assert run.best_model is model and path.read_bytes() == b"what was there"
    assert sorted(child.name for child in tmp_path.iterdir()) == ["model.joblib"]
    # And a library's own save that fails, likewise
    failing = type("Sequential", (), {"__module__": "keras.src.models.sequential",
                                      "save": lambda self, path: (open(path, "w").write("half"), 1 / 0)})
    run.best_model = failing()
    with pytest.raises(ValueError, match="cannot be saved with its own save"):
        run.save_best_model(str(tmp_path / "net"))
    assert sorted(child.name for child in tmp_path.iterdir()) == ["model.joblib"]
