"""Structures whose positions each have a definition of their own, set with
Domain.set_structure_to_variables: position i is always initialized, checked, mutated
and recombined against the i-th definition, a dynamic structure grows and shrinks at
its end, and every algorithm keeps the positions valid."""
import pytest

from metagen.framework import Domain
from metagen.framework.rng import set_seed
from metagen.metaheuristics.cvoa.cvoa import CVOA
from metagen.metaheuristics import (GA, SA, SSGA, HillClimbing, KernelTPE,
                                    Memetic, ProbabilisticCVOA, RandomSearch,
                                    StrainProperties, TabuSearch, TPE,
                                    cvoa_launcher)
from metagen.metaheuristics.genetic.genetic_tools import GAConnector
from metagen.metaheuristics.tools import solution_class

LOW = [1, 6, 11]
HIGH = [5, 10, 20]


def _domain(connector=None, dynamic=True):
    domain = Domain(connector) if connector is not None else Domain()
    if dynamic:
        domain.define_dynamic_structure("v", 1, 3)
    else:
        domain.define_static_structure("v", 3)
    for i, (low, high) in enumerate(zip(LOW, HIGH)):
        domain.define_integer(f"p{i}", low, high)
    domain.set_structure_to_variables("v", ["p0", "p1", "p2"])
    return domain


def _valid(values):
    return 1 <= len(values) <= 3 and all(LOW[i] <= x <= HIGH[i] for i, x in enumerate(values))


def _solution(domain):
    return solution_class(domain)(domain, connector=domain.get_connector())


def _variables(domain):
    return domain.get_core().get_attributes()[1]


@pytest.mark.parametrize("dynamic", [True, False])
def test_every_position_is_initialized_and_mutated_within_its_own_range(dynamic):
    set_seed(0)
    domain = _domain(dynamic=dynamic)
    lengths = set()
    for _ in range(200):
        solution = _solution(domain)
        assert _valid(solution["v"])
        for _ in range(5):
            solution.mutate()
            assert _valid(solution["v"])
            lengths.add(len(solution["v"]))
    assert lengths == ({1, 2, 3} if dynamic else {3})


def test_the_moved_variables_leave_the_top_level_unless_remembered():
    assert list(_variables(_domain())) == ["v"]

    domain = Domain()
    domain.define_static_structure("v", 2)
    domain.define_integer("a", 0, 1)
    domain.define_real("b", 5.0, 6.0)
    domain.set_structure_to_variables("v", ["a", "b"], remember=True)
    assert sorted(_variables(domain)) == ["a", "b", "v"]


def test_the_number_of_variables_must_be_the_number_of_positions():
    domain = Domain()
    domain.define_dynamic_structure("v", 1, 3)
    domain.define_integer("a", 0, 1)
    domain.define_integer("b", 0, 1)
    with pytest.raises(ValueError, match="3 positions"):
        domain.set_structure_to_variables("v", ["a", "b"])
    # Nothing moved: the failed call left both variables where they were.
    domain.set_structure_to_integer("v", 0, 1)
    assert sorted(_variables(domain)) == ["a", "b", "v"]


def test_set_checks_each_value_against_its_position():
    domain = _domain()
    solution = _solution(domain)
    solution.set("v", [5, 10, 20])
    assert solution["v"] == [5, 10, 20]
    assert domain.get_core().check("v", [1, 6])
    assert not domain.get_core().check("v", [6, 1])
    with pytest.raises(ValueError):
        solution.set("v", [6, 10])  # 6 is outside the first position's range
    with pytest.raises(ValueError):
        solution.set("v", [1, 2])   # 2 is outside the second position's range
    assert solution["v"] == [5, 10, 20]


def test_each_position_keeps_its_own_type():
    domain = Domain()
    domain.define_static_structure("v", 3)
    domain.define_integer("n", 0, 10)
    domain.define_real("x", 0.0, 1.0)
    domain.define_categorical("c", ["a", "b"])
    domain.set_structure_to_variables("v", ["n", "x", "c"])
    set_seed(3)
    solution = _solution(domain)
    for _ in range(50):
        solution.mutate()
        n, x, c = solution["v"]
        assert isinstance(n, int) and 0 <= n <= 10
        assert isinstance(x, float) and 0.0 <= x <= 1.0
        assert c in ("a", "b")
    # An integer given for the real position becomes a real.
    solution.set("v", [3, 1, "b"])
    assert solution["v"] == [3, 1.0, "b"] and isinstance(solution["v"][1], float)


def test_a_position_can_be_a_group():
    domain = Domain()
    domain.define_dynamic_structure("layers", 1, 2)
    domain.define_group("dense")
    domain.define_integer_in_group("dense", "units", 1, 8)
    domain.define_group("output")
    domain.define_categorical_in_group("output", "activation", ["softmax", "sigmoid"])
    domain.set_structure_to_variables("layers", ["dense", "output"])
    set_seed(5)
    solution = _solution(domain)
    for _ in range(30):
        solution.mutate()
        layers = solution["layers"]
        assert 1 <= layers[0]["units"] <= 8
        if len(layers) == 2:
            assert layers[1]["activation"] in ("softmax", "sigmoid")


def test_a_dynamic_structure_grows_and_shrinks_at_its_end():
    domain = _domain()
    solution = _solution(domain)
    solution.set("v", [2, 7, 12])
    structure = solution.get("v")
    del structure[-1]
    assert solution["v"] == [2, 7]
    structure.append(15)
    assert solution["v"] == [2, 7, 15]
    # Deleting the first element would move 7 to a position whose range is 1 to 5.
    with pytest.raises(ValueError):
        del structure[0]
    assert solution["v"] == [2, 7, 15]
    with pytest.raises(ValueError):
        structure.append(1)  # no fourth position
    with pytest.raises(ValueError):
        structure[1] = 3     # 3 is outside the second position's range


def test_the_crossover_recombines_position_by_position():
    set_seed(1)
    domain = _domain(GAConnector())
    for _ in range(200):
        first, second = _solution(domain), _solution(domain)
        child1, child2 = first.crossover(second)
        assert _valid(child1["v"]) and _valid(child2["v"])
        assert sorted([len(child1["v"]), len(child2["v"])]) == \
            sorted([len(first["v"]), len(second["v"])])


ALGORITHMS = [RandomSearch, HillClimbing, TabuSearch, SA, GA, SSGA, Memetic, TPE, KernelTPE]


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda a: a.__name__)
def test_every_algorithm_keeps_every_position_valid(algorithm):
    genetic = algorithm in (GA, SSGA, Memetic)
    domain = _domain(GAConnector() if genetic else None)
    invalid = []

    def fitness(solution):
        values = solution["v"]
        if not _valid(values):
            invalid.append(values)
        return sum((x - LOW[i]) ** 2 for i, x in enumerate(values)) + 10 * (3 - len(values))

    best = algorithm(domain, fitness, seed=1).run()
    assert invalid == []
    assert _valid(best["v"])
    assert best.get_fitness() == fitness(best)


@pytest.mark.parametrize("strain_class", [CVOA, ProbabilisticCVOA], ids=lambda a: a.__name__)
def test_cvoa_keeps_every_position_valid(strain_class):
    domain = _domain()
    invalid = []

    def fitness(solution):
        values = solution["v"]
        if not _valid(values):
            invalid.append(values)
        return sum((x - LOW[i]) ** 2 for i, x in enumerate(values)) + 10 * (3 - len(values))

    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2)]
    best = cvoa_launcher(strains, domain, fitness, seed=0, strain_class=strain_class)
    assert invalid == []
    assert _valid(best["v"])
