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
verdicts below are ratios over ten seeds instead of single runs.

The problems are the six classics of continuous optimization, each on its own
canonical domain. Keeping the canonical domains rather than normalizing them is
deliberate, and it is what turned up F-32: the default alteration_limit of 1.0
means something quite different on [-2.048, 2.048] than on [-600, 600], and the
two algorithms built around local search fall below random sampling on the wide
domains for exactly that reason.

Properties 1 and 2 are structural, and are asked of every algorithm on every
function: an optimizer that reports an improving history and then hands back
something else is broken whatever the problem. Properties 3 and 4 are
statistical, and the pairs that fail them carry an xfail naming what is
responsible.

Property 4 is not asked of RandomSearch: it *is* random sampling, so tying with
the baseline is the correct outcome and not a defect.
"""

import math

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, TPE, GAConnector, HillClimbing,
                                    Memetic, RandomSearch)

SEEDS = tuple(range(10))

# Out of len(SEEDS). Not unanimity: these are stochastic algorithms and an
# occasional bad seed is legitimate. A healthy algorithm sits at 8-10 and a
# broken one at 0-4, so anything in between is a signal rather than noise.
REQUIRED_WINS = 7

ALGORITHMS = ("RandomSearch", "SA", "HillClimbing", "GA", "SSGA", "TPE", "Memetic")


def _sphere(x: float, y: float) -> float:
    return x ** 2 + y ** 2


def _rastrigin(x: float, y: float) -> float:
    return 20 + sum(v ** 2 - 10 * math.cos(2 * math.pi * v) for v in (x, y))


def _rosenbrock(x: float, y: float) -> float:
    return 100 * (y - x ** 2) ** 2 + (1 - x) ** 2


def _ackley(x: float, y: float) -> float:
    return (-20 * math.exp(-0.2 * math.sqrt(0.5 * (x ** 2 + y ** 2)))
            - math.exp(0.5 * (math.cos(2 * math.pi * x) + math.cos(2 * math.pi * y)))
            + math.e + 20)


def _griewank(x: float, y: float) -> float:
    return 1 + (x ** 2 + y ** 2) / 4000 - math.cos(x) * math.cos(y / math.sqrt(2))


def _schwefel(x: float, y: float) -> float:
    return 418.9829 * 2 - sum(v * math.sin(math.sqrt(abs(v))) for v in (x, y))


# name -> (lower bound, upper bound, objective). Canonical domains, and all six
# have their global minimum at 0.
FUNCTIONS = {
    "Sphere": (-5.12, 5.12, _sphere),
    "Rastrigin": (-5.12, 5.12, _rastrigin),
    "Rosenbrock": (-2.048, 2.048, _rosenbrock),
    "Ackley": (-32.768, 32.768, _ackley),
    "Griewank": (-600.0, 600.0, _griewank),
    "Schwefel": (-500.0, 500.0, _schwefel),
}


def _domain(bounds, connector=None) -> Domain:
    low, high, _ = bounds
    domain = Domain(connector=connector) if connector is not None else Domain()
    domain.define_real("x", low, high)
    domain.define_real("y", low, high)
    return domain


class _CountingFitness:
    """The objective, counting calls so every algorithm can be charged its own budget."""

    def __init__(self, objective) -> None:
        self.objective = objective
        self.evaluations = 0

    def __call__(self, solution) -> float:
        self.evaluations += 1
        return self.objective(solution["x"], solution["y"])


def _build(name: str, bounds, fitness, seed: int, log_dir: str):
    if name == "RandomSearch":
        return RandomSearch(_domain(bounds), fitness, population_size=10,
                            max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SA":
        return SA(_domain(bounds), fitness, max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "HillClimbing":
        return HillClimbing(_domain(bounds), fitness, population_size=10,
                            max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "GA":
        return GA(_domain(bounds, GAConnector()), fitness, population_size=10,
                  max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "SSGA":
        return SSGA(_domain(bounds, GAConnector()), fitness, population_size=10,
                    max_iterations=15, seed=seed, log_dir=log_dir)
    if name == "TPE":
        return TPE(_domain(bounds), fitness, max_iterations=15,
                   warmup_iterations=5, seed=seed, log_dir=log_dir)
    if name == "Memetic":
        return Memetic(_domain(bounds, GAConnector()), fitness, population_size=10,
                       max_iterations=15, neighbor_population_size=3, seed=seed,
                       log_dir=log_dir)
    raise ValueError(f"unknown algorithm: {name}")


def _best_of_random_sampling(bounds, evaluations: int, seed: int) -> float:
    """Best of `evaluations` solutions drawn at random: the baseline to beat."""
    set_seed(100_000 + seed)
    domain = _domain(bounds)
    objective = bounds[2]
    return min(objective(Solution(domain)["x"], Solution(domain)["y"])
               for _ in range(evaluations))


@pytest.fixture(scope="module")
def runs(tmp_path_factory):
    """Run every algorithm on every function once per seed, and reuse that."""
    log_dir = str(tmp_path_factory.mktemp("behavior"))
    measured = {}
    for function_name, bounds in FUNCTIONS.items():
        for name in ALGORITHMS:
            rows = []
            for seed in SEEDS:
                fitness = _CountingFitness(bounds[2])
                algorithm = _build(name, bounds, fitness, seed, log_dir)
                solution = algorithm.run()
                rows.append({
                    "final": solution.get_fitness(),
                    "history": list(algorithm.best_solution_fitnesses),
                    "evaluations": fitness.evaluations,
                    "random_baseline": _best_of_random_sampling(
                        bounds, fitness.evaluations, seed),
                })
            measured[(function_name, name)] = rows
    return measured


# --------------------------------------------------------------------------
# The (function, algorithm) pairs expected to fail a statistical property.
# --------------------------------------------------------------------------

_SA = ("F-30: SA accepts almost anything. With initial_temp 50 and cooling_rate 0.99 "
       "the temperature is still 40.9 after 20 iterations, so the Metropolis criterion "
       "takes a worsening of 5.0 with probability 0.89: a random walk, not annealing")

_GA = ("A-01: best_parents is computed outside the loop, so every crossover of a "
       "generation uses the very same pair and the population collapses to variations "
       "of two individuals")

_SSGA = ("Steady state with no selection pressure: it always crosses the top two and "
         "replaces the bottom two, 40 evaluations of a population that converges on "
         "its first pair. A-05, which used to be blamed here, was refuted")

_WIDE = ("F-32: alteration_limit defaults to an absolute 1.0, about a thousandth of "
         "this domain's range, so the local search cannot go anywhere")

_TPE = ("TPE models each variable on its own, which suits a separable bowl. Rosenbrock "
        "couples x and y along a curved valley, Rastrigin oscillates faster than the "
        "model resolves, and Schwefel is deceptive: 15 iterations of an independent "
        "model do not beat dice on any of the three")

# Measured, not guessed, and kept per property: a pair can fail one and pass the
# other, so a single shared table would turn the passes into XPASS(strict).
_IMPROVES_ON_ITS_START = {
    **{("Sphere", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA))},
    **{("Rastrigin", n): r for n, r in (("SSGA", _SSGA),)},
    **{("Rosenbrock", n): r for n, r in (("SSGA", _SSGA), ("TPE", _TPE))},
    **{("Ackley", n): r for n, r in (("SA", _SA), ("SSGA", _SSGA))},
    **{("Griewank", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA))},
    **{("Schwefel", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                       ("TPE", _TPE))},
}

_BEATS_RANDOM = {
    **{("Sphere", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA))},
    **{("Rastrigin", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                        ("TPE", _TPE))},
    **{("Rosenbrock", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                         ("TPE", _TPE))},
    **{("Ackley", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA))},
    **{("Griewank", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                       ("HillClimbing", _WIDE), ("Memetic", _WIDE))},
    **{("Schwefel", n): r for n, r in (("SA", _SA), ("GA", _GA), ("SSGA", _SSGA),
                                       ("TPE", _TPE), ("HillClimbing", _WIDE),
                                       ("Memetic", _WIDE))},
}


def _pairs(expected=None, exclude=()):
    """Build the (function, algorithm) parameter list, marking the known failures."""
    expected = expected or {}
    parameters = []
    for function_name in FUNCTIONS:
        for name in ALGORITHMS:
            if name in exclude:
                continue
            reason = expected.get((function_name, name))
            marks = [pytest.mark.xfail(reason=reason, strict=True)] if reason else []
            parameters.append(pytest.param(function_name, name, marks=marks,
                                           id=f"{function_name}-{name}"))
    return parameters


@pytest.mark.parametrize("function_name,name", _pairs())
def test_the_best_fitness_history_never_gets_worse(runs, function_name, name):
    """The record of the best solution so far can only improve or stay put."""
    for seed, row in zip(SEEDS, runs[(function_name, name)]):
        history = row["history"]
        worsening = [(i, history[i], history[i + 1])
                     for i in range(len(history) - 1)
                     if history[i + 1] > history[i]]
        assert not worsening, (
            f"{name} on {function_name}, seed {seed}: the best fitness got worse "
            f"at {worsening}"
        )


@pytest.mark.parametrize("function_name,name", _pairs())
def test_the_returned_solution_is_the_best_one_seen(runs, function_name, name):
    """Whatever run() hands back must be the best point of the whole history."""
    for seed, row in zip(SEEDS, runs[(function_name, name)]):
        assert row["final"] == pytest.approx(min(row["history"])), (
            f"{name} on {function_name}, seed {seed}: returned {row['final']} while "
            f"the history reached {min(row['history'])}"
        )


@pytest.mark.parametrize("function_name,name", _pairs(_IMPROVES_ON_ITS_START))
def test_the_run_ends_better_than_it_started(runs, function_name, name):
    """Searching has to pay off: the end of the history beats its beginning."""
    rows = runs[(function_name, name)]
    improved = sum(1 for row in rows
                   if len(row["history"]) > 1 and row["history"][-1] < row["history"][0])
    assert improved >= REQUIRED_WINS, (
        f"{name} on {function_name} improved on its own starting point in only "
        f"{improved} of {len(SEEDS)} seeds"
    )


@pytest.mark.parametrize("function_name,name",
                         _pairs(_BEATS_RANDOM, exclude=("RandomSearch",)))
def test_it_beats_random_sampling_on_the_same_budget(runs, function_name, name):
    """An optimizer must do better than spending its evaluations on dice rolls."""
    rows = runs[(function_name, name)]
    wins = sum(1 for row in rows if row["final"] <= row["random_baseline"])
    mean = sum(row["final"] for row in rows) / len(SEEDS)
    mean_baseline = sum(row["random_baseline"] for row in rows) / len(SEEDS)
    assert wins >= REQUIRED_WINS, (
        f"{name} on {function_name} beat random sampling in only {wins} of "
        f"{len(SEEDS)} seeds (mean fitness {mean:.4f} against {mean_baseline:.4f} for "
        f"random sampling, on {rows[0]['evaluations']} evaluations)"
    )
