"""The framework end to end, on the domain with one of everything: a solution is
valid when born, stays valid however it is mutated, takes nested values and gives
them back, survives copying and pickling, and every algorithm can search it.

Validity is always judged by the domain itself, through check on the definition of
each variable, at every level of nesting."""
import copy
import math
import pickle

import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import GA, SSGA, TPE, GAConnector, HillClimbing, Memetic, RandomSearch, SA
from metagen.metaheuristics.tools import solution_class

from conftest import build_full_domain

SEEDS = range(10)


def _assert_valid(domain: Domain, solution: Solution) -> None:
    core = domain.get_core()
    for name in solution:
        assert core.check(name, solution[name]), (
            f"{name} = {solution[name]!r} is not valid for its definition")


def _fitness(solution: Solution) -> float:
    """Touches every kind of variable, so an algorithm that mishandles one shows."""
    values = {name: solution[name] for name in solution}
    return (
        values["I"] + 100 * values["R"] + len(values["C"])
        + values["L"]["EI"] + sum(values["SSI"]) + sum(values["SSR"])
        + len(values["DSI"]) + sum(values["DSR"])
        + sum(group["EI2"] for group in values["SSL"] + values["DSL"])
        + sum(sum(inner) for inner in values["SSS"])
    )


def test_a_fresh_solution_satisfies_its_domain(full_domain):
    for seed in SEEDS:
        set_seed(seed)
        _assert_valid(full_domain, Solution(full_domain))


@pytest.mark.parametrize("alteration_limit", [None, RelativeAlteration(0.2), 1])
def test_mutation_never_leaves_the_domain(full_domain, alteration_limit):
    for seed in SEEDS:
        set_seed(seed)
        solution = Solution(full_domain)
        for _ in range(20):
            solution.mutate(alterations_number=len(solution.get_variables()),
                            alteration_limit=alteration_limit)
            _assert_valid(full_domain, solution)


def test_values_set_from_builtins_read_back_as_given(solution):
    given = {
        "I": 7,
        "L": {"EI": 3, "ER": 0.5, "EC": "C2"},
        "SSI": [-5, 10, 0, 1, 2, 3, 4, 5, 6, 7],
        "SSL": [{"EI2": 1, "ER2": 0.25, "EC2": "C1"}, {"EI2": 2, "ER2": 0.75, "EC2": "C4"}],
        "DSI": [1] * 10 + [10] * 5,
        "DSL": [{"EI2": 9, "ER2": 0.0, "EC2": "C3"}] * 3,
        "SSS": [[0, 9], [5]],
    }
    for name, value in given.items():
        solution.set(name, value)
    for name, value in given.items():
        assert solution[name] == value, name
    assert len(solution.get("DSI")) == 15
    assert len(solution.get("SSS").get(0)) == 2


# Only values out of range: a list of the wrong length is accepted today, which is
# F-38 in the regression suite.
@pytest.mark.parametrize("name,value", [
    ("SSL", [{"EI2": 1, "ER2": 0.5, "EC2": "C1"}, {"EI2": 101, "ER2": 0.5, "EC2": "C1"}]),
    ("SSS", [[0, 9], [10]]),
    ("DSL", [{"EI2": 1, "ER2": 0.5, "EC2": "C1"}, {"EI2": 1, "ER2": 1.5, "EC2": "C1"}]),
    ("SSI", [-6, 10, 0, 1, 2, 3, 4, 5, 6, 7]),
])
def test_an_invalid_nested_value_is_rejected_at_its_level(solution, name, value):
    before = solution[name]
    with pytest.raises(ValueError):
        solution.set(name, value)
    assert solution[name] == before, "a rejected value must leave the variable as it was"


def test_copy_and_pickle_preserve_equality_and_independence(full_domain, solution):
    solution.evaluate(_fitness)
    twin = copy.deepcopy(solution)
    revived = pickle.loads(pickle.dumps(solution))
    for other in (twin, revived):
        assert other == solution
        assert hash(other) == hash(solution)
        assert other.get_fitness() == solution.get_fitness()
        _assert_valid(full_domain, other)

    frozen = {name: solution[name] for name in solution}
    set_seed(1)
    twin.mutate(alterations_number=len(solution.get_variables()))
    assert twin != solution
    assert {name: solution[name] for name in solution} == frozen, (
        "mutating a copy must not reach the original")


def test_genetic_crossover_stays_inside_the_domain():
    domain = build_full_domain(connector=GAConnector())
    cls = solution_class(domain)
    for seed in SEEDS:
        set_seed(seed)
        father, mother = cls(domain), cls(domain)
        for child in father.crossover(mother):
            _assert_valid(domain, child)
        _assert_valid(domain, father)
        _assert_valid(domain, mother)


def _algorithms(domain: Domain, ga_domain: Domain, seed: int):
    return {
        "RandomSearch": RandomSearch(domain, _fitness, population_size=4, max_iterations=3, seed=seed),
        "SA": SA(domain, _fitness, warmup_iterations=1, max_iterations=3, neighbor_population_size=2, seed=seed),
        "HillClimbing": HillClimbing(domain, _fitness, population_size=4, warmup_iterations=1, max_iterations=3, seed=seed),
        "TPE": TPE(domain, _fitness, warmup_iterations=2, max_iterations=3, seed=seed),
        "GA": GA(ga_domain, _fitness, population_size=4, max_iterations=3, seed=seed),
        "SSGA": SSGA(ga_domain, _fitness, population_size=4, max_iterations=3, seed=seed),
        "Memetic": Memetic(ga_domain, _fitness, population_size=4, max_iterations=3,
                           neighbor_population_size=2, seed=seed),
    }


@pytest.mark.parametrize("name", ["RandomSearch", "SA", "HillClimbing", "TPE", "GA", "SSGA", "Memetic"])
def test_every_algorithm_searches_the_full_domain(name):
    domain, ga_domain = build_full_domain(), build_full_domain(connector=GAConnector())
    for seed in (0, 1, 2):
        algorithm = _algorithms(domain, ga_domain, seed)[name]
        best = algorithm.run()
        _assert_valid(algorithm.domain, best)
        assert best.get_fitness() == _fitness(best)
        assert not math.isinf(best.get_fitness())
        history = algorithm.best_solution_fitnesses
        assert history == sorted(history, reverse=True), f"{name} reports a history that worsens"
        assert best.get_fitness() == history[-1]
