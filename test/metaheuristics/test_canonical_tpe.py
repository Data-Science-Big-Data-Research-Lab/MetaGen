"""
CanonicalTPE: Bergstra's TPE next to MetaGen's. Each test pins one of the pieces
that make it the published algorithm: the Parzen model with one kernel per
observation and a prior, the categorical counts with the prior, the choice of the
candidate that maximizes l(x)/g(x), and one evaluation per iteration.
"""
import math

import numpy as np
import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import CanonicalTPE
from metagen.metaheuristics.tpe.canonical_tpe import _draw, _kernels, _leaves, _log_density, _observations


def _domain():
    domain = Domain()
    domain.define_real("x", 0.0, 10.0)
    domain.define_integer("n", 0, 100)
    domain.define_categorical("c", ["a", "b", "c"])
    return domain


def _fitness(solution):
    return (solution["x"] - 2.0) ** 2 + abs(solution["n"] - 40) + (0.0 if solution["c"] == "b" else 5.0)


def test_the_model_has_one_kernel_per_observation_plus_the_prior():
    """Three observations give four kernels; the prior is as wide as the domain and
    centered on it, and every observation's kernel is narrower than the prior."""
    mus, sigmas, weights = _kernels([1.0, 2.0, 8.0], 0.0, 10.0, prior_weight=1.0)
    assert len(mus) == 4
    assert 5.0 in mus
    assert sigmas[list(mus).index(5.0)] == 10.0
    assert all(sigma < 10.0 for mu, sigma in zip(mus, sigmas) if mu != 5.0)
    assert weights.sum() == pytest.approx(1.0)


def test_a_kernel_is_as_wide_as_the_gap_to_its_nearest_neighbor():
    """The adaptive width: 8.0 is three from the prior's center at 5.0, so its
    kernel is three wide; 1.0 and 2.0 are one apart, but a kernel is never
    narrower than the prior's width over the number of kernels, 10 / 4 here, so
    both get 2.5. With more observations the floor drops and the gap rules."""
    mus, sigmas, _ = _kernels([1.0, 2.0, 8.0], 0.0, 10.0, prior_weight=1.0)
    widths = dict(zip(mus, sigmas))
    assert widths[8.0] == pytest.approx(3.0)
    assert widths[1.0] == pytest.approx(2.5) and widths[2.0] == pytest.approx(2.5)

    crowded = [1.0, 2.0, 8.0] + [3.0 + 0.1 * i for i in range(20)]
    mus, sigmas, _ = _kernels(crowded, 0.0, 10.0, prior_weight=1.0)
    assert dict(zip(mus, sigmas))[1.0] == pytest.approx(1.0)


def test_the_density_is_higher_where_the_observations_are():
    set_seed(0)
    solution = Solution(_domain())
    x = solution.get("x")
    near = _log_density(x, 2.0, [1.5, 2.0, 2.5], 1.0)
    far = _log_density(x, 9.0, [1.5, 2.0, 2.5], 1.0)
    assert near > far


def test_a_categorical_is_modeled_by_counts_with_the_prior():
    """Two observations of "b" and none of the others, prior weight one: the
    densities are (1, 3, 1) over 5 for a, b and c."""
    set_seed(0)
    c = Solution(_domain()).get("c")
    assert math.exp(_log_density(c, "b", ["b", "b"], 1.0)) == pytest.approx(3 / 5)
    assert math.exp(_log_density(c, "a", ["b", "b"], 1.0)) == pytest.approx(1 / 5)


def test_draws_stay_in_the_domain_and_on_the_grid():
    set_seed(1)
    domain = Domain()
    domain.define_integer("k", 10, 50, 5)
    domain.define_real("r", -1.0, 1.0)
    solution = Solution(domain)
    for _ in range(200):
        k = _draw(solution.get("k"), [12, 48], 1.0)
        assert 10 <= k <= 50 and (k - 10) % 5 == 0 and isinstance(k, int)
        r = _draw(solution.get("r"), [0.9, -0.9], 1.0)
        assert -1.0 <= r <= 1.0


def test_the_leaves_of_a_solution_reach_into_groups_and_structures():
    set_seed(0)
    domain = Domain()
    domain.define_real("y", 0.0, 1.0)
    domain.define_real("x", 0.0, 1.0)
    domain.define_group("g")
    domain.define_integer_in_group("g", "i", 0, 9)
    domain.define_static_structure("s", 3)
    domain.set_structure_to_variable("s", "x")  # x becomes the element of s
    solution = Solution(domain)
    paths = [path for path, _ in _leaves(solution)]
    assert ("y",) in paths and ("g", "i") in paths and ("s", 0) in paths and ("s", 2) in paths
    observed = _observations([solution, Solution(domain)])
    assert len(observed[("g", "i")]) == 2


def test_the_proposal_is_the_candidate_that_maximizes_the_ratio():
    """With the best solutions all around x = 2 and the rest all around x = 8, the
    proposal lands near 2: drawn from l and scored against g."""
    set_seed(2)
    domain = _domain()
    search = CanonicalTPE(domain, _fitness, seed=2)
    best, rest = [], []
    for value in (1.8, 2.0, 2.2, 1.9, 2.1):
        solution = Solution(domain)
        solution.set("x", value)
        best.append(solution)
    for value in (7.8, 8.0, 8.2, 7.9, 8.1):
        solution = Solution(domain)
        solution.set("x", value)
        rest.append(solution)
    proposals = [search.propose(best, rest)["x"] for _ in range(20)]
    assert all(abs(x - 2.0) < 2.0 for x in proposals), proposals


def test_one_evaluation_per_iteration_and_the_history_is_never_trimmed():
    """A run costs population_size * (warmup + 1) + max_iterations evaluations, and
    the history the search carries holds every one of the evaluated solutions."""
    calls = []

    def counting(solution):
        calls.append(1)
        return _fitness(solution)

    search = CanonicalTPE(_domain(), counting, population_size=6, warmup_iterations=1, max_iterations=9, seed=0)
    search.run()
    assert len(calls) == 6 * 2 + 9
    assert len(search.current_solutions) == 6 + 9


def test_it_finds_the_categorical_and_the_integer_that_matter():
    """The hyperparameter-shaped toy problem: the optimum has c = "b" and n = 40."""
    best = CanonicalTPE(_domain(), _fitness, max_iterations=150, seed=3).run()
    assert best["c"] == "b"
    assert abs(best["n"] - 40) <= 3


def test_a_seed_reproduces_a_run():
    runs = [CanonicalTPE(_domain(), _fitness, max_iterations=30, seed=5).run() for _ in range(2)]
    assert runs[0].get_fitness() == runs[1].get_fitness()
