"""
The logarithmic scale of integer and real variables: a positive minimum and no step; the value
the user reads and writes is the value itself, while drawing, mutating, crossing and modeling
happen on its logarithm, so that every order of magnitude weighs the same.
"""
import collections
import math

import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.rng import set_seed


def _domain(connector=None) -> Domain:
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_real("lr", 1e-4, 1e-1, log=True)
    domain.define_integer("n", 1, 1000, log=True)
    return domain


def _decades(values):
    return collections.Counter(int(math.floor(math.log10(value))) for value in values)


def test_a_log_variable_is_drawn_evenly_over_its_orders_of_magnitude():
    set_seed(0)
    domain = _domain()
    solutions = [Solution(domain) for _ in range(3000)]
    decades = _decades(solution["lr"] for solution in solutions)
    assert set(decades) == {-4, -3, -2} and min(decades.values()) > 900
    assert all(1e-4 <= solution["lr"] <= 1e-1 and isinstance(solution["lr"], float) for solution in solutions)
    integers = [solution["n"] for solution in solutions]
    assert all(isinstance(n, int) and 1 <= n <= 1000 for n in integers)
    # The integer [1, 1000] spans three decades on [0.5, 1000.5]: each about a third.
    assert 800 < _decades(integers)[1] < 1200


def test_a_log_mutation_stays_in_its_window_on_the_logarithm():
    set_seed(1)
    solution = Solution(_domain())
    solution.set("lr", 1e-3)
    reach = RelativeAlteration(0.2).of(math.log(1e-4), math.log(1e-1))
    for _ in range(500):
        solution.set("lr", 1e-3)
        solution.get("lr").mutate(RelativeAlteration(0.2))
        assert abs(math.log(solution["lr"]) - math.log(1e-3)) <= reach + 1e-12


def test_a_log_integer_always_changes_and_moves_at_least_one():
    set_seed(2)
    solution = Solution(_domain())
    for start in (1, 2, 500, 1000):
        for _ in range(300):
            solution.set("n", start)
            solution.get("n").mutate(RelativeAlteration(0.01))
            assert solution["n"] != start and 1 <= solution["n"] <= 1000


def test_a_log_scale_needs_a_positive_minimum_and_no_step():
    for arguments in (dict(min_value=0.0, max_value=1.0), dict(min_value=-1.0, max_value=1.0),
                      dict(min_value=1.0, max_value=10.0, step=1.0)):
        with pytest.raises(ValueError, match="logarithmic scale"):
            Domain().define_real("x", log=True, **arguments)
    with pytest.raises(ValueError, match="logarithmic scale"):
        Domain().define_integer("n", 0, 10, log=True)


def test_the_scale_is_part_of_the_definition_and_off_by_default():
    domain = _domain()
    domain.define_real("plain", 0.0, 1.0)
    core = domain.get_core()
    assert core.get("lr").log and core.get("n").log and not core.get("plain").log
    assert core.get("lr").get_attributes() == ("REAL", 1e-4, 1e-1, None)
    assert "Log" in str(core.get("lr")) and "Log" not in str(core.get("plain"))


def test_groups_and_structures_take_the_scale_too():
    set_seed(3)
    domain = Domain()
    domain.define_group("g")
    domain.define_real_in_group("g", "lr", 1e-5, 1.0, log=True)
    domain.define_integer_in_group("g", "n", 1, 10 ** 5, log=True)
    domain.define_static_structure("layers", 3)
    domain.set_structure_to_integer("layers", 1, 4096, log=True)
    domain.define_static_structure("rates", 2)
    domain.set_structure_to_real("rates", 1e-6, 1e-1, log=True)
    solutions = [Solution(domain) for _ in range(2000)]
    assert _decades(solution["g"]["lr"] for solution in solutions).keys() == {-5, -4, -3, -2, -1}
    assert min(_decades(width for solution in solutions for width in solution["layers"]).values()) > 400
    assert all(1e-6 <= rate <= 1e-1 for solution in solutions for rate in solution["rates"])


def test_the_genetic_crossover_blends_on_the_logarithm():
    from metagen.metaheuristics import GAConnector

    set_seed(4)
    domain = _domain(GAConnector())
    first, second = Solution(domain, connector=domain.get_connector()), Solution(domain, connector=domain.get_connector())
    for solution, (lr, n) in ((first, (1e-4, 10)), (second, (1e-2, 1000))):
        solution.set("lr", lr)
        solution.set("n", n)
    for _ in range(200):
        children = first.get("lr").crossover(second.get("lr"))
        for child in children:
            # BLX-0.5 on the logarithm of 1e-4 and 1e-2, clipped to the domain: [1e-4, 1e-1].
            assert 1e-4 <= child.get() <= 1e-1
        for child in first.get("n").crossover(second.get("n")):
            assert isinstance(child.get(), int) and 1 <= child.get() <= 1000


@pytest.mark.parametrize("name", ["TPE", "KernelTPE"])
def test_the_tpe_models_stay_in_the_domain_and_find_a_log_optimum(name):
    import metagen.metaheuristics as mh

    def fitness(solution):
        return (math.log10(solution["lr"]) + 3.3) ** 2 + (math.log10(solution["n"]) - 2) ** 2

    seen = []
    algorithm = getattr(mh, name)(_domain(), lambda s: seen.append((s["lr"], s["n"])) or fitness(s),
                                  warmup_iterations=0, max_evaluations=150, seed=0)
    best = algorithm.run()
    assert all(1e-4 <= lr <= 1e-1 and 1 <= n <= 1000 for lr, n in seen)
    assert best.get_fitness() < 0.5
