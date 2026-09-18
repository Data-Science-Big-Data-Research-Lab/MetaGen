"""
What a run writes to TensorBoard when it is given a ``log_dir``.

The tests read the event files back, so they hold the names of the series the
documentation lists. They skip where TensorBoard is not installed.
"""
import pytest

pytest.importorskip("tensorboard")

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator  # noqa: E402

from metagen.framework import Domain, Solution  # noqa: E402
from metagen.metaheuristics import GA, TPE, GAConnector, RandomSearch  # noqa: E402


def _rich_domain(connector=None) -> Domain:
    """A real, an integer, a categorical, a static structure and a dynamic structure of groups."""
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("rate", 0.0, 1.0)
    domain.define_integer("size", 1, 10)
    domain.define_categorical("kind", ["a", "b", "c"])
    domain.define_static_structure("weights", 3)
    domain.set_structure_to_real("weights", 0.0, 1.0)
    domain.define_group("layer")
    domain.define_integer_in_group("layer", "neurons", 1, 8)
    domain.define_dynamic_structure("layers", 1, 3)
    domain.set_structure_to_variable("layers", "layer")
    return domain


def _fitness(solution: Solution) -> float:
    return solution["rate"] + solution["size"] + sum(solution["weights"]) + len(solution["layers"])


def _read(log_dir):
    runs = [path for path in log_dir.iterdir() if path.is_dir()] or [log_dir]
    accumulator = EventAccumulator(str(runs[0]), size_guidance={"scalars": 0, "histograms": 0, "tensors": 0})
    accumulator.Reload()
    return accumulator


@pytest.mark.parametrize("name", ["RandomSearch", "GA", "TPE"])
def test_a_run_writes_the_fitness_series_and_the_population_size(tmp_path, name):
    if name == "RandomSearch":
        algorithm = RandomSearch(_rich_domain(), _fitness, population_size=5, max_iterations=4, seed=0,
                                 log_dir=str(tmp_path))
    elif name == "GA":
        algorithm = GA(_rich_domain(GAConnector()), _fitness, population_size=6, max_iterations=4, seed=0,
                       log_dir=str(tmp_path))
    else:
        algorithm = TPE(_rich_domain(), _fitness, population_size=5, warmup_iterations=1, max_iterations=4,
                        candidate_pool_size=4, seed=0, log_dir=str(tmp_path))
    algorithm.run()

    scalars = set(_read(tmp_path).Tags()["scalars"])
    assert {"Fitness/Best", "Fitness/Average"} <= scalars
    assert any("Population" in tag for tag in scalars)

    best = [event.value for event in _read(tmp_path).Scalars("Fitness/Best")]
    assert len(best) == 4
    assert all(later <= earlier for earlier, later in zip(best, best[1:]))
    assert best[-1] == pytest.approx(algorithm.best_solution.get_fitness(), rel=1e-5)


def test_a_run_writes_the_average_of_every_numeric_variable(tmp_path):
    RandomSearch(_rich_domain(), _fitness, population_size=5, max_iterations=3, seed=0,
                 log_dir=str(tmp_path)).run()
    scalars = " ".join(_read(tmp_path).Tags()["scalars"])
    for variable in ("rate", "size", "weights", "layers"):
        assert variable in scalars, f"no series mentions {variable}: {scalars}"


def test_two_runs_share_a_directory_without_mixing(tmp_path):
    for seed in (0, 1):
        RandomSearch(_rich_domain(), _fitness, population_size=4, max_iterations=2, seed=seed,
                     log_dir=str(tmp_path)).run()
    assert len([path for path in tmp_path.iterdir() if path.is_dir()]) == 2
