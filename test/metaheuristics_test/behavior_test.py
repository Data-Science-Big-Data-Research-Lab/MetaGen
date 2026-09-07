"""Behavioral tests: every metaheuristic must actually optimize.

The rest of the metaheuristic suite only checks that a run returns something. An
algorithm can be thoroughly broken and still satisfy that, which is what P-05
objects to. These tests check the properties that make an optimizer an optimizer:

1. the best-fitness history never gets worse;
2. the returned solution is the best one the run ever saw;
3. the run ends better than it started;
4. it beats spending the very same number of fitness evaluations on random
   sampling.

Every run is seeded, so the outcome is fixed rather than a coin toss, and the
verdicts below are ratios over ten seeds instead of single runs. The problem is
the 2D sphere, f(x, y) = x^2 + y^2, one of the benchmark functions used in the
MetaGen paper: a plain bowl with its minimum at the origin and no local traps. An
algorithm that cannot beat random sampling on a bowl is broken, with no excuses
about problem difficulty.

Property 4 is not asked of RandomSearch: it *is* random sampling, so tying with
the baseline is the correct outcome and not a defect. Memetic joined the module
once F-24 stopped it from requiring Ray, and passes every property.

The algorithms marked xfail below do not merely lose, they lose measurably: with
the same budget SA scores 2.00 where random sampling scores 0.17.
"""

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, Memetic,
                                    RandomSearch, TabuSearch)

SEEDS = tuple(range(10))

# Out of len(SEEDS). Not unanimity: these are stochastic algorithms and an
# occasional bad seed is legitimate. A healthy algorithm sits at 8-10 and a
# broken one at 0-4, so anything in between is a signal rather than noise.
REQUIRED_WINS = 7

ALGORITHMS = ("RandomSearch", "SA", "TabuSearch", "GA", "SSGA", "TPE", "Memetic")

_SA_REASON = ("F-20 and F-03: SA inherits a population of 20, keeps solutions[0] "
              "instead of the best one, and throws the warmup evaluations away")
_GA_REASON = ("A-01: best_parents is computed outside the loop, so every crossover "
              "of a generation uses the very same pair and the population collapses "
              "to variations of two individuals")
_SSGA_REASON = ("A-05: solutions.index(worst) replaces by value equality rather than "
                "identity, so with duplicates both replacements land on the same slot")


def _broken(name: str, reason: str):
    """Mark an algorithm as expected to fail a property until its finding is fixed."""
    return pytest.param(name, marks=pytest.mark.xfail(reason=reason, strict=True))


def _sphere_domain(connector=None) -> Domain:
    domain = Domain(connector=connector) if connector is not None else Domain()
    domain.define_real("x", -5.12, 5.12)
    domain.define_real("y", -5.12, 5.12)
    return domain


def _sphere(solution) -> float:
    return solution["x"] ** 2 + solution["y"] ** 2


class _CountingFitness:
    """The objective, counting calls so every algorithm can be charged its own budget."""

    def __init__(self) -> None:
        self.evaluations = 0

    def __call__(self, solution) -> float:
        self.evaluations += 1
        return _sphere(solution)


def _build(name: str, fitness, seed: int, log_dir: str):
    if name == "RandomSearch":
        return RandomSearch(_sphere_domain(), fitness, population_size=10,
                            max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SA":
        return SA(_sphere_domain(), fitness, max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "TabuSearch":
        return TabuSearch(_sphere_domain(), fitness, population_size=10,
                          max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "GA":
        return GA(_sphere_domain(GAConnector()), fitness, population_size=10,
                  max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SSGA":
        return SSGA(_sphere_domain(GAConnector()), fitness, population_size=10,
                    max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "TPE":
        return TPE(_sphere_domain(), fitness, max_iterations=15,
                   warmup_iterations=5, seed=seed, log_dir=log_dir)
    if name == "Memetic":
        return Memetic(_sphere_domain(GAConnector()), fitness, population_size=10,
                       max_iterations=15, neighbor_population_size=3, seed=seed,
                       log_dir=log_dir)
    raise ValueError(f"unknown algorithm: {name}")


def _best_of_random_sampling(evaluations: int, seed: int) -> float:
    """Best of `evaluations` solutions drawn at random: the baseline to beat."""
    set_seed(100_000 + seed)
    domain = _sphere_domain()
    return min(_sphere(Solution(domain)) for _ in range(evaluations))


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Run every algorithm once per seed, and reuse that across the four properties."""
    log_dir = str(tmp_path_factory.mktemp("behavior"))
    measured = {}
    for name in ALGORITHMS:
        rows = []
        for seed in SEEDS:
            fitness = _CountingFitness()
            algorithm = _build(name, fitness, seed, log_dir)
            solution = algorithm.run()
            rows.append({
                "final": solution.get_fitness(),
                "history": list(algorithm.best_solution_fitnesses),
                "evaluations": fitness.evaluations,
                "random_baseline": _best_of_random_sampling(fitness.evaluations, seed),
            })
        measured[name] = rows
    return measured


@pytest.mark.parametrize("name", ALGORITHMS)
def test_the_best_fitness_history_never_gets_worse(runs, name):
    """The record of the best solution so far can only improve or stay put."""
    for seed, row in zip(SEEDS, runs[name]):
        history = row["history"]
        worsening = [(i, history[i], history[i + 1])
                     for i in range(len(history) - 1)
                     if history[i + 1] > history[i]]
        assert not worsening, (
            f"{name} seed {seed}: the best fitness got worse at {worsening}"
        )


@pytest.mark.parametrize("name", ALGORITHMS)
def test_the_returned_solution_is_the_best_one_seen(runs, name):
    """Whatever run() hands back must be the best point of the whole history."""
    for seed, row in zip(SEEDS, runs[name]):
        assert row["final"] == pytest.approx(min(row["history"])), (
            f"{name} seed {seed}: returned {row['final']} while the history "
            f"reached {min(row['history'])}"
        )


@pytest.mark.parametrize("name", [
    "RandomSearch",
    "TabuSearch",
    "TPE",
    "Memetic",
    _broken("SA", _SA_REASON),
    _broken("GA", _GA_REASON),
    _broken("SSGA", _SSGA_REASON),
])
def test_the_run_ends_better_than_it_started(runs, name):
    """Searching has to pay off: the end of the history beats its beginning."""
    improved = sum(1 for row in runs[name]
                   if len(row["history"]) > 1 and row["history"][-1] < row["history"][0])
    assert improved >= REQUIRED_WINS, (
        f"{name} improved on its own starting point in only {improved} of "
        f"{len(SEEDS)} seeds"
    )


@pytest.mark.parametrize("name", [
    "TabuSearch",
    "TPE",
    "Memetic",
    _broken("SA", _SA_REASON),
    _broken("GA", _GA_REASON),
    _broken("SSGA", _SSGA_REASON),
])
def test_it_beats_random_sampling_on_the_same_budget(runs, name):
    """An optimizer must do better than spending its evaluations on dice rolls."""
    wins = sum(1 for row in runs[name] if row["final"] <= row["random_baseline"])
    mean = sum(row["final"] for row in runs[name]) / len(SEEDS)
    mean_baseline = sum(row["random_baseline"] for row in runs[name]) / len(SEEDS)
    assert wins >= REQUIRED_WINS, (
        f"{name} beat random sampling in only {wins} of {len(SEEDS)} seeds "
        f"(mean fitness {mean:.4f} against {mean_baseline:.4f} for random sampling, "
        f"on {runs[name][0]['evaluations']} evaluations)"
    )
