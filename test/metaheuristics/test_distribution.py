"""
The two distribution models of a Ray run. The global model shuffles the population
before the cut and lets the driver select the next population out of the parents
and every candidate the workers returned; the island model concatenates the slices
in order. What the tests pin: the switch, the survivor selection, the budget under
the global model, and reproducibility. The Ray tests skip where Ray is missing.
"""
import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing, KernelTPE, Memetic,
                                    RandomSearch, TabuSearch)


def _sphere_domain(connector=None) -> Domain:
    domain = Domain(connector=connector)
    domain.define_real("x", -5.12, 5.12)
    domain.define_real("y", -5.12, 5.12)
    return domain


def _sphere(solution) -> float:
    return solution["x"] ** 2 + solution["y"] ** 2


def _sphere_for_the_workers():
    """A Ray worker unpickles a module-level function by importing its module, and
    this module is not on the worker's path; a nested function travels by value."""
    def sphere(solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2
    return sphere


def _counting_sphere(path):
    """A worker unpickles a nested function by value, and every call appends a line
    to a file the driver can count: a counter in the driver would not see the
    evaluations made in the workers."""
    def sphere(solution) -> float:
        with open(path, "a") as handle:
            handle.write("1\n")
        return solution["x"] ** 2 + solution["y"] ** 2
    return sphere


def _evaluations(path) -> int:
    with open(path) as handle:
        return sum(1 for _ in handle)


@pytest.fixture(scope="module")
def ray_runtime():
    ray = pytest.importorskip("ray")
    started_here = not ray.is_initialized()
    if started_here:
        ray.init(num_cpus=2, include_dashboard=False, log_to_driver=False)
    yield ray
    if started_here:
        ray.shutdown()


def test_an_unknown_distribution_model_is_refused():
    with pytest.raises(ValueError, match="distribution_model"):
        RandomSearch(_sphere_domain(), _sphere, distribution_model="archipelago")


def test_the_default_survivor_selection_keeps_the_best_without_duplicates():
    """The (μ+λ) step of the global model: population_size best of parents and
    offspring by fitness, and a candidate equal to a parent counts once."""
    set_seed(0)
    domain = _sphere_domain()
    search = RandomSearch(domain, _sphere, population_size=3)
    parents = [Solution(domain) for _ in range(3)]
    for parent, fitness in zip(parents, (5.0, 1.0, 9.0)):
        parent.set_fitness(fitness)
    offspring = [Solution(domain) for _ in range(3)]
    for child, fitness in zip(offspring, (0.5, 7.0, 3.0)):
        child.set_fitness(fitness)
    twin = Solution(domain)
    twin.set("x", parents[1]["x"])
    twin.set("y", parents[1]["y"])
    twin.set_fitness(1.0)

    survivors = search.select_survivors(parents, offspring + [twin])

    assert [survivor.get_fitness() for survivor in survivors] == [0.5, 1.0, 3.0]
    assert survivors[1] is parents[1]


def test_the_global_model_selects_on_the_driver_and_the_island_model_does_not(ray_runtime):
    """Under the global model the driver selects once per iteration, out of the parents
    it sent and everything that came back; under the island model it never does."""

    class Spied(RandomSearch):
        """Records what the driver's survivor selection is handed. Defined here so
        that it travels to the workers by value, like the fitness."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.selections = []

        def select_survivors(self, parents, offspring):
            self.selections.append((len(parents), len(offspring)))
            return super().select_survivors(parents, offspring)

    domain, sphere = _sphere_domain(), _sphere_for_the_workers()
    global_run = Spied(domain, sphere, population_size=6, max_iterations=3, distributed=True, seed=0)
    global_run.run()
    assert len(global_run.selections) == 3
    assert all(parents == 6 and offspring == 6 for parents, offspring in global_run.selections)
    assert len(global_run.current_solutions) == 6

    islands = Spied(domain, sphere, population_size=6, max_iterations=3, distributed=True, seed=0,
                    distribution_model="islands")
    islands.run()
    assert islands.selections == []


@pytest.mark.parametrize("name", ["GA", "HillClimbing", "TabuSearch", "TPE"])
def test_the_global_model_costs_what_the_sequential_run_costs(ray_runtime, tmp_path, name):
    """The promise of the global model: an iteration evaluates the fitness as many
    times on two CPUs as on one. GA needs slices of even size to breed the same
    number of children, so its population here is 8."""
    domain, ga_domain = _sphere_domain(), _sphere_domain(GAConnector())

    def build(distributed, path):
        fitness = _counting_sphere(path)
        return {
            "GA": lambda: GA(ga_domain, fitness, population_size=8, max_iterations=3, distributed=distributed, seed=0),
            "HillClimbing": lambda: HillClimbing(domain, fitness, population_size=6, warmup_iterations=1,
                                                 max_iterations=3, distributed=distributed, seed=0),
            "TabuSearch": lambda: TabuSearch(domain, fitness, population_size=6, warmup_iterations=1,
                                             max_iterations=3, distributed=distributed, seed=0),
            "TPE": lambda: TPE(domain, fitness, warmup_iterations=2, max_iterations=3, candidate_pool_size=8,
                               distributed=distributed, seed=0),
        }[name]()

    sequential, distributed = tmp_path / "sequential", tmp_path / "distributed"
    build(False, sequential).run()
    build(True, distributed).run()
    assert _evaluations(distributed) == _evaluations(sequential)


def test_random_search_mutates_one_individual_fewer_per_slice(ray_runtime, tmp_path):
    """RandomSearch keeps one elite copy per slice, so on two CPUs it mutates one
    individual fewer per iteration than the sequential run: the one exception the
    documentation names."""
    domain = _sphere_domain()
    sequential, distributed = tmp_path / "sequential", tmp_path / "distributed"
    RandomSearch(domain, _counting_sphere(sequential), population_size=6, max_iterations=3, seed=0).run()
    RandomSearch(domain, _counting_sphere(distributed), population_size=6, max_iterations=3, distributed=True,
                 seed=0).run()
    assert _evaluations(sequential) - _evaluations(distributed) == 3


@pytest.mark.parametrize("model", ["global", "islands"])
def test_the_same_seed_reproduces_a_run_under_either_model(ray_runtime, model):
    domain, sphere = _sphere_domain(GAConnector()), _sphere_for_the_workers()
    runs = [GA(domain, sphere, population_size=6, max_iterations=3, distributed=True, seed=4,
               distribution_model=model) for _ in range(2)]
    results = [run.run().get_fitness() for run in runs]
    assert results[0] == results[1]
    assert runs[0].best_solution_fitnesses == runs[1].best_solution_fitnesses


def _build(name: str, fitness, model: str, **extra):
    """One of the nine population-based or single-point algorithms, small, on Ray."""
    genetic = name in ("GA", "SSGA", "Memetic")
    domain = _sphere_domain(GAConnector() if genetic else None)
    common = dict(max_iterations=3, distributed=True, seed=2, distribution_model=model, **extra)
    if name == "SA":
        return SA(domain, fitness, warmup_iterations=1, **common)
    if name in ("TPE", "KernelTPE"):
        return {"TPE": TPE, "KernelTPE": KernelTPE}[name](domain, fitness, population_size=6,
                                                          warmup_iterations=1, **common)
    if name == "Memetic":
        return Memetic(domain, fitness, population_size=6, neighbor_population_size=2, **common)
    algorithm = {"RandomSearch": RandomSearch, "HillClimbing": HillClimbing, "TabuSearch": TabuSearch,
                 "GA": GA, "SSGA": SSGA}[name]
    return algorithm(domain, fitness, population_size=6, **common)


@pytest.mark.parametrize("model", ["global", "islands"])
@pytest.mark.parametrize("name", ["RandomSearch", "HillClimbing", "TabuSearch", "SA", "GA", "SSGA",
                                  "TPE", "KernelTPE", "Memetic"])
def test_every_algorithm_runs_under_both_models(ray_runtime, name, model):
    """The run ends, returns the best solution it saw, and its history never gets worse."""
    algorithm = _build(name, _sphere_for_the_workers(), model)
    best = algorithm.run()
    history = algorithm.best_solution_fitnesses
    assert best.get_fitness() == min(history)
    assert all(later <= earlier for earlier, later in zip(history, history[1:]))
    assert best.get_fitness() == pytest.approx(_sphere(best))


@pytest.mark.parametrize("model", ["global", "islands"])
@pytest.mark.parametrize("level", [1, 2])
def test_the_memetic_algorithm_runs_at_every_distribution_level(ray_runtime, level, model):
    algorithm = _build("Memetic", _sphere_for_the_workers(), model, distribution_level=level)
    best = algorithm.run()
    assert best.get_fitness() == min(algorithm.best_solution_fitnesses)
    assert best.get_fitness() == pytest.approx(_sphere(best))


def test_a_distributed_run_resumes_from_its_checkpoint(ray_runtime, tmp_path, monkeypatch):
    """The state of a distributed run lives on the driver, workers included through the
    seeds they are given, so a checkpoint continues it exactly."""
    path = str(tmp_path / "run.ckpt")
    sphere = _sphere_for_the_workers()
    build = lambda **kw: GA(_sphere_domain(GAConnector()), sphere, population_size=8, max_iterations=6,
                           distributed=True, seed=4, **kw)
    whole = build()
    reference = whole.run().get_fitness(), list(whole.best_solution_fitnesses)

    original = GA.post_iteration

    def stop_after_two(self):
        original(self)
        if self.current_iteration >= 2:
            self.request_stop()

    monkeypatch.setattr(GA, "post_iteration", stop_after_two)
    build(checkpoint=path).run()
    monkeypatch.undo()
    resumed = GA.resume(path, sphere)
    assert (resumed.run().get_fitness(), resumed.best_solution_fitnesses) == reference


def test_a_distributed_history_does_not_count_the_evaluations_of_the_workers(ray_runtime):
    algorithm = GA(_sphere_domain(GAConnector()), _sphere_for_the_workers(), population_size=8,
                   max_iterations=3, distributed=True, seed=4)
    algorithm.run()
    assert [record["iteration"] for record in algorithm.history] == [0, 1, 2]
    assert all(record["evaluations"] is None for record in algorithm.history)
