"""Pausing and resuming a run: a run cut short and continued from its checkpoint reaches
exactly the result, and the history, of the same run left alone."""
import os
import pickle
import subprocess
import sys
import textwrap

import pytest

from metagen.framework import Domain
from metagen.metaheuristics import (GA, SA, SSGA, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch, TPE)
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.genetic.genetic_tools import GAConnector


def _domain(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 0, 20)
    domain.define_categorical("c", ["a", "b", "c"])
    return domain


def _objective(solution):
    return solution["x"] ** 2 + (solution["n"] - 7) ** 2 + (0 if solution["c"] == "b" else 1)


ALGORITHMS = {
    "RandomSearch": lambda **kw: RandomSearch(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
    "HillClimbing": lambda **kw: HillClimbing(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
    "TabuSearch": lambda **kw: TabuSearch(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
    "SA": lambda **kw: SA(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
    "GA": lambda **kw: GA(_domain(GAConnector()), kw.pop("fitness"), max_iterations=8, **kw),
    "SSGA": lambda **kw: SSGA(_domain(GAConnector()), kw.pop("fitness"), max_iterations=8, **kw),
    "Memetic": lambda **kw: Memetic(_domain(GAConnector()), kw.pop("fitness"), max_iterations=8, **kw),
    "TPE": lambda **kw: TPE(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
    "KernelTPE": lambda **kw: KernelTPE(_domain(), kw.pop("fitness"), max_iterations=8, **kw),
}


class _Cut(Exception):
    pass


def _reference(name):
    algorithm = ALGORITHMS[name](fitness=_objective, seed=3)
    best = algorithm.run()
    return best.get_fitness(), list(algorithm.best_solution_fitnesses)


@pytest.mark.parametrize("name", ALGORITHMS)
def test_stopping_and_resuming_gives_the_uninterrupted_result(name, tmp_path):
    path = str(tmp_path / "run.ckpt")
    algorithm = ALGORITHMS[name](fitness=_objective, seed=3, checkpoint=path)

    def stops_after_three_iterations(solution):
        if algorithm.current_iteration >= 3:
            algorithm.request_stop()
        return _objective(solution)

    algorithm.fitness_function = stops_after_three_iterations
    algorithm.run()
    assert os.path.exists(path)
    assert algorithm.current_iteration < 8

    resumed = type(algorithm).resume(path, _objective)
    best = resumed.run()
    assert (best.get_fitness(), resumed.best_solution_fitnesses) == _reference(name)
    assert not os.path.exists(path)


@pytest.mark.parametrize("name", ALGORITHMS)
def test_a_run_cut_short_continues_from_its_checkpoint(name, tmp_path):
    path = str(tmp_path / "run.ckpt")
    algorithm = ALGORITHMS[name](fitness=_objective, seed=3, checkpoint=path)

    def cut_during_the_fourth_iteration(solution):
        if algorithm.current_iteration >= 3 and os.path.exists(path):
            raise _Cut()
        return _objective(solution)

    algorithm.fitness_function = cut_during_the_fourth_iteration
    with pytest.raises(_Cut):
        algorithm.run()
    assert os.path.exists(path)

    # A new object built as the first: run() finds the file and continues.
    again = ALGORITHMS[name](fitness=_objective, seed=3, checkpoint=path)
    best = again.run()
    assert (best.get_fitness(), again.best_solution_fitnesses) == _reference(name)


class _SavesSpy(RandomSearch):
    saved = []

    def _write_checkpoint(self):
        _SavesSpy.saved.append(self.current_iteration)
        super()._write_checkpoint()


def test_checkpoint_every_saves_every_so_many_iterations(tmp_path):
    path = str(tmp_path / "run.ckpt")
    _SavesSpy.saved = []
    _SavesSpy(_domain(), _objective, max_iterations=8, seed=0, checkpoint=path, checkpoint_every=3).run()
    assert _SavesSpy.saved == [3, 6]


def test_checkpoint_every_must_be_positive():
    with pytest.raises(ValueError, match="checkpoint_every"):
        RandomSearch(_domain(), _objective, checkpoint="x.ckpt", checkpoint_every=0)


def test_a_cut_while_writing_leaves_the_previous_checkpoint_whole(tmp_path, monkeypatch):
    path = str(tmp_path / "run.ckpt")
    algorithm = RandomSearch(_domain(), _objective, max_iterations=8, seed=0, checkpoint=path)

    def cut_on_the_third_save(solution):
        if algorithm.current_iteration >= 3:
            algorithm.request_stop()
        return _objective(solution)

    algorithm.fitness_function = cut_on_the_third_save
    algorithm.run()
    with open(path, "rb") as handle:
        before = handle.read()

    real_dump = pickle.dump

    def dump_half_then_fail(obj, handle, *args, **kwargs):
        handle.write(b"half a checkpoint")
        raise OSError("power failure")

    resumed = RandomSearch.resume(path, _objective)
    monkeypatch.setattr(pickle, "dump", dump_half_then_fail)
    with pytest.raises(OSError):
        resumed.run()
    monkeypatch.setattr(pickle, "dump", real_dump)
    with open(path, "rb") as handle:
        assert handle.read() == before
    RandomSearch.resume(path, _objective)


def test_a_checkpoint_of_another_class_or_version_is_rejected(tmp_path):
    path = str(tmp_path / "run.ckpt")
    algorithm = RandomSearch(_domain(), _objective, max_iterations=8, seed=0, checkpoint=path)

    def stop(solution):
        algorithm.request_stop()
        return _objective(solution)

    algorithm.fitness_function = stop
    algorithm.run()
    with pytest.raises(ValueError, match="RandomSearch"):
        GA.resume(path, _objective)
    with pytest.raises(ValueError, match="RandomSearch"):
        SA(_domain(), _objective, checkpoint=path).run()
    assert isinstance(Metaheuristic.resume(path, _objective), RandomSearch)

    with open(path, "rb") as handle:
        state = pickle.load(handle)
    state["version"] = "0.0.1"
    with open(path, "wb") as handle:
        pickle.dump(state, handle)
    with pytest.raises(ValueError, match="version"):
        RandomSearch.resume(path, _objective)


def test_a_run_resumes_in_another_process(tmp_path):
    """The case the feature is for: the process that started the run is gone."""
    path = str(tmp_path / "run.ckpt")
    script = textwrap.dedent(f"""
        import sys
        from metagen.framework import Domain
        from metagen.metaheuristics import GA
        from metagen.metaheuristics.genetic.genetic_tools import GAConnector

        def objective(solution):
            return solution["x"] ** 2

        domain = Domain(GAConnector())
        domain.define_real("x", -5.0, 5.0)
        if sys.argv[1] == "start":
            algorithm = GA(domain, objective, max_iterations=10, seed=5, checkpoint={path!r})
            def stop(solution):
                if algorithm.current_iteration >= 4:
                    algorithm.request_stop()
                return objective(solution)
            algorithm.fitness_function = stop
            algorithm.run()
        elif sys.argv[1] == "resume":
            algorithm = GA.resume({path!r}, objective)
            print(repr(algorithm.run().get_fitness()), algorithm.best_solution_fitnesses)
        else:
            algorithm = GA(domain, objective, max_iterations=10, seed=5)
            print(repr(algorithm.run().get_fitness()), algorithm.best_solution_fitnesses)
    """)
    run = lambda mode: subprocess.run([sys.executable, "-c", script, mode], capture_output=True,
                                      text=True, check=True).stdout
    run("start")
    assert os.path.exists(path)
    assert run("resume") == run("whole")
