"""Permutation variables, defined with Domain.define_permutation: every value holds each
element exactly once, whatever initializes, mutates, crosses over or resamples it."""
from collections import Counter

import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, HillClimbing, KernelTPE, Memetic,
                                    ProbabilisticCVOA, RandomSearch, StrainProperties,
                                    TabuSearch, TPE, cvoa_launcher)
from metagen.metaheuristics.cvoa.cvoa import CVOA
from metagen.metaheuristics.genetic.genetic_tools import GAConnector
from metagen.metaheuristics.tools import solution_class

CITIES = [1, 2, 3, 4, 5, 6, 7, 8]


def _domain(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_permutation("route", CITIES)
    return domain


def _valid(route):
    return sorted(route) == CITIES


def _solution(domain):
    return solution_class(domain)(domain, connector=domain.get_connector())


def test_a_permutation_initializes_and_mutates_as_a_permutation():
    set_seed(0)
    domain = _domain()
    seen = set()
    for _ in range(200):
        solution = _solution(domain)
        assert isinstance(solution["route"], list) and _valid(solution["route"])
        seen.add(tuple(solution["route"]))
        for limit in (None, 1, 3, RelativeAlteration(0.2)):
            before = list(solution["route"])
            solution.get("route").mutate(limit)
            assert _valid(solution["route"]) and solution["route"] != before
    assert len(seen) > 150


def test_a_limit_counts_swaps():
    set_seed(1)
    solution = _solution(_domain())
    for _ in range(200):
        before = list(solution["route"])
        solution.get("route").mutate(1)
        moved = sum(a != b for a, b in zip(before, solution["route"]))
        assert moved == 2


@pytest.mark.parametrize("value", [[1, 2, 3], [1, 1, 2, 3, 4, 5, 6, 7], [1, 2, 3, 4, 5, 6, 7, 9], 12])
def test_set_rejects_what_is_not_an_ordering_of_the_elements(value):
    solution = _solution(_domain())
    before = list(solution["route"])
    with pytest.raises(ValueError):
        solution.set("route", value)
    assert solution["route"] == before


@pytest.mark.parametrize("elements", [[1], [1, 1, 2], [1, "a"], []])
def test_invalid_elements_are_rejected(elements):
    with pytest.raises(ValueError):
        Domain().define_permutation("route", elements)


def test_the_domain_checks_and_shows_it():
    domain = _domain()
    assert domain.get_core().check("route", [8, 7, 6, 5, 4, 3, 2, 1])
    assert not domain.get_core().check("route", [8, 7, 6, 5, 4, 3, 2, 2])
    assert "[PERMUTATION] {Elements = [1, 2, 3, 4, 5, 6, 7, 8]}" in str(domain)


def test_the_order_crossover_keeps_both_children_permutations():
    set_seed(2)
    domain = _domain(GAConnector())
    for _ in range(300):
        first, second = _solution(domain), _solution(domain)
        child1, child2 = first.crossover(second)
        assert _valid(child1["route"]) and _valid(child2["route"])


def _is_order_crossover(child, kept, donor):
    """Whether some segment of ``kept`` sits in place in ``child`` and the other
    elements follow, from the segment's end and wrapping round, the order they have in
    ``donor`` read from the same point."""
    size = len(child)
    for start in range(size):
        for end in range(start + 1, size + 1):
            segment = kept[start:end]
            if child[start:end] != segment:
                continue
            rest = [e for e in donor[end:] + donor[:end] if e not in segment]
            if child[end:] + child[:start] == rest:
                return True
    return False


def test_the_order_crossover_keeps_a_segment_and_the_other_parents_order():
    set_seed(3)
    domain = _domain(GAConnector())
    for _ in range(200):
        first, second = _solution(domain), _solution(domain)
        child1, child2 = first.crossover(second)
        assert _is_order_crossover(child1["route"], first["route"], second["route"])
        assert _is_order_crossover(child2["route"], second["route"], first["route"])


def test_a_structure_can_hold_permutations():
    domain = Domain()
    domain.define_static_structure("routes", 2)
    domain.define_permutation("route", ["a", "b", "c", "d"])
    domain.set_structure_to_variable("routes", "route")
    solution = Solution(domain)
    solution.set("routes", [["d", "c", "b", "a"], ["a", "b", "c", "d"]])
    assert solution["routes"] == [["d", "c", "b", "a"], ["a", "b", "c", "d"]]
    for _ in range(20):
        solution.mutate()
        assert all(sorted(route) == ["a", "b", "c", "d"] for route in solution["routes"])


ALGORITHMS = [RandomSearch, HillClimbing, TabuSearch, SA, GA, SSGA, Memetic, TPE, KernelTPE]


def _fitness_and_log():
    invalid = []

    def fitness(solution):
        route = solution["route"]
        if not _valid(route):
            invalid.append(route)
        # Displacement from the identity: 0 at [1, 2, ..., 8].
        return sum(abs(city - position - 1) for position, city in enumerate(route)) + solution["x"] ** 2

    return fitness, invalid


def _mixed_domain(connector=None):
    domain = _domain(connector)
    domain.define_real("x", -1.0, 1.0)
    return domain


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda a: a.__name__)
def test_every_algorithm_keeps_the_permutation_valid(algorithm):
    genetic = algorithm in (GA, SSGA, Memetic)
    domain = _mixed_domain(GAConnector() if genetic else None)
    fitness, invalid = _fitness_and_log()
    best = algorithm(domain, fitness, seed=4).run()
    assert invalid == []
    assert best.get_fitness() == fitness(best)


@pytest.mark.parametrize("strain_class", [CVOA, ProbabilisticCVOA], ids=lambda c: c.__name__)
def test_cvoa_keeps_the_permutation_valid(strain_class):
    fitness, invalid = _fitness_and_log()
    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2)]
    best = cvoa_launcher(strains, _mixed_domain(), fitness, seed=0, strain_class=strain_class)
    assert invalid == []
    assert best.get_fitness() == fitness(best)


def test_the_searches_improve_on_a_permutation_problem():
    """HillClimbing, with swaps, gets closer to the identity than where it starts."""
    fitness, _ = _fitness_and_log()
    wins = Counter()
    for seed in range(5):
        algorithm = HillClimbing(_mixed_domain(), fitness, seed=seed)
        best = algorithm.run()
        wins[best.get_fitness() < algorithm.best_solution_fitnesses[0]] += 1
    assert wins[True] == 5


def _one_swap_apart(first, second):
    return sum(a != b for a, b in zip(first, second)) == 2 and sorted(first) == sorted(second)


def test_tpe_resamples_a_permutation_from_one_of_the_best_orderings():
    from metagen.metaheuristics.tpe.tpe_tools import TPEConnector
    set_seed(6)
    domain = _domain(TPEConnector())
    best = [_solution(domain) for _ in range(3)]
    worst = [_solution(domain) for _ in range(3)]
    for _ in range(100):
        candidate = _solution(domain)
        candidate.resample(best, worst)
        assert any(_one_swap_apart(candidate["route"], reference["route"]) for reference in best)


def test_kernel_tpe_proposes_a_permutation_one_swap_from_a_good_ordering():
    set_seed(7)
    domain = _mixed_domain()
    algorithm = KernelTPE(domain, _fitness_and_log()[0], seed=7)
    good = [_solution(domain) for _ in range(4)]
    bad = [_solution(domain) for _ in range(4)]
    for solution in good + bad:
        solution.evaluate(algorithm.fitness_function)
    for _ in range(30):
        candidate = algorithm.propose(good, bad)
        assert any(_one_swap_apart(candidate["route"], reference["route"]) for reference in good)
