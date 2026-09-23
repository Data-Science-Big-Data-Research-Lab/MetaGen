"""
The mutation of the genetic algorithms' children.

A child is mutated with probability ``mutation_rate`` after the crossover. How far
that mutation may move it is ``mutation_alteration_limit``: GA and SSGA default to a
fifth of each variable's range, because a local mutation measured better on the
benchmark than redrawing the variable over its whole domain (GA went from 221 to
238 wins of 330 against random sampling on the same budget, thirty seeds); the
memetic algorithm keeps the whole domain, because its local search already works
the neighborhood and the wide mutation is its way out of it.
"""
import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import GA, SSGA, GAConnector, Memetic
from metagen.metaheuristics.genetic.genetic_tools import yield_two_children
from metagen.metaheuristics.tools import solution_class

WIDTH = 1000.0


def _problem():
    domain = Domain(connector=GAConnector())
    domain.define_real("x", 0.0, WIDTH)
    domain.define_real("y", 0.0, WIDTH)

    def fitness(solution: Solution) -> float:
        return solution["x"] + solution["y"]

    return domain, fitness


def _twins(domain):
    """Two parents with the same values: BLX-alpha over equal values returns them, so
    whatever separates a child from its parents afterwards is the mutation."""
    parents = []
    for _ in range(2):
        parent = solution_class(domain)(domain, connector=domain.get_connector())
        parent.set("x", 500.0)
        parent.set("y", 500.0)
        parents.append(parent)
    return tuple(parents)


def _largest_move(limit, draws: int = 200) -> float:
    domain, fitness = _problem()
    set_seed(0)
    largest = 0.0
    for _ in range(draws):
        for child in yield_two_children(_twins(domain), 1.0, fitness, limit):
            largest = max(largest, abs(child["x"] - 500.0), abs(child["y"] - 500.0))
    return largest


def test_a_limited_mutation_keeps_the_child_within_the_limit():
    """With RelativeAlteration(0.2) no mutated variable leaves a fifth of its range."""
    assert 0.0 < _largest_move(RelativeAlteration(0.2)) <= 0.2 * WIDTH


def test_without_a_limit_the_mutation_redraws_over_the_whole_domain():
    """None is what the function did before the parameter existed."""
    assert _largest_move(None) > 0.4 * WIDTH


def test_a_number_is_an_absolute_limit():
    assert 0.0 < _largest_move(5.0) <= 5.0


@pytest.mark.parametrize("algorithm,expected", [(GA, RelativeAlteration), (SSGA, RelativeAlteration),
                                                (Memetic, type(None))],
                         ids=["GA", "SSGA", "Memetic"])
def test_the_default_is_local_for_ga_and_ssga_and_the_whole_domain_for_memetic(algorithm, expected):
    domain, fitness = _problem()
    assert isinstance(algorithm(domain, fitness).mutation_alteration_limit, expected)


@pytest.mark.parametrize("algorithm", [GA, SSGA, Memetic], ids=lambda a: a.__name__)
def test_the_limit_given_to_the_algorithm_reaches_the_mutation(algorithm, monkeypatch):
    """The constructor's value is the one the children are mutated with."""
    import metagen.metaheuristics.genetic.genetic_algorithm as ga_module
    import metagen.metaheuristics.genetic.steady_state_genetic_algorithm as ssga_module
    import metagen.metaheuristics.memetic.memetic as memetic_module

    module = {GA: ga_module, SSGA: ssga_module, Memetic: memetic_module}[algorithm]
    original = module.yield_two_children
    seen = []

    def spy(parents, mutation_rate, fitness_function, mutation_alteration_limit=None):
        seen.append(mutation_alteration_limit)
        return original(parents, mutation_rate, fitness_function, mutation_alteration_limit)

    monkeypatch.setattr(module, "yield_two_children", spy)
    domain, fitness = _problem()
    algorithm(domain, fitness, population_size=6, max_iterations=2, seed=0,
              mutation_alteration_limit=7.5).run()
    assert seen and all(limit == 7.5 for limit in seen)
