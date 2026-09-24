"""Variables active only for some values of another one, set with Domain.set_condition:
an inactive variable reads as None, is not mutated, does not tell two solutions apart,
and does not feed the models of TPE and KernelTPE."""
from collections import Counter

import pytest

from metagen.framework import Domain
from metagen.framework.rng import set_seed
from metagen.metaheuristics import (GA, SA, SSGA, HillClimbing, KernelTPE, Memetic,
                                    ProbabilisticCVOA, RandomSearch, StrainProperties,
                                    TabuSearch, TPE, cvoa_launcher)
from metagen.metaheuristics.cvoa.cvoa import CVOA
from metagen.metaheuristics.genetic.genetic_tools import GAConnector
from metagen.metaheuristics.tools import solution_class


def _domain(connector=None):
    domain = Domain(connector) if connector is not None else Domain()
    domain.define_categorical("solver", ["adam", "sgd"])
    domain.define_real("momentum", 0.5, 0.99)
    domain.define_real("learning_rate", 0.0, 1.0)
    domain.set_condition("momentum", "solver", ["sgd"])
    return domain


def _solution(domain):
    return solution_class(domain)(domain, connector=domain.get_connector())


def test_an_inactive_variable_reads_as_none_and_keeps_its_value():
    domain = _domain()
    solution = _solution(domain)
    solution.set("solver", "adam")
    solution.set("momentum", 0.9)
    assert not solution.is_active("momentum")
    assert solution["momentum"] is None
    assert solution.get("momentum").get() == 0.9
    solution.set("solver", "sgd")
    assert solution.is_active("momentum") and solution["momentum"] == 0.9
    assert solution.is_active("solver") and solution.is_active("learning_rate")


def test_the_mutation_leaves_inactive_variables_alone():
    set_seed(0)
    domain = _domain()
    solution = _solution(domain)
    solution.set("solver", "adam")
    for _ in range(200):
        before = solution.get("momentum").get()
        solution.mutate(alterations_number=1)
        if solution["solver"] == "adam":
            assert solution.get("momentum").get() == before
        else:
            solution.set("solver", "adam")


def test_two_solutions_that_differ_only_in_an_inactive_variable_are_the_same():
    domain = _domain()
    first, second = _solution(domain), _solution(domain)
    for solution, momentum in ((first, 0.6), (second, 0.9)):
        solution.set("solver", "adam")
        solution.set("learning_rate", 0.1)
        solution.set("momentum", momentum)
    assert first == second and hash(first) == hash(second)
    first.set("solver", "sgd")
    second.set("solver", "sgd")
    assert first != second


@pytest.mark.parametrize("name, variable, values, message", [
    ("momentum", "nothing", ["sgd"], "not"),
    ("momentum", "learning_rate", [0.5], "integer or a categorical"),
    ("momentum", "solver", ["lbfgs"], "not valid"),
    ("momentum", "solver", [], "non-empty"),
    ("momentum", "momentum", ["sgd"], "itself"),
])
def test_an_invalid_condition_is_rejected(name, variable, values, message):
    domain = Domain()
    domain.define_categorical("solver", ["adam", "sgd"])
    domain.define_real("momentum", 0.5, 0.99)
    domain.define_real("learning_rate", 0.0, 1.0)
    with pytest.raises(ValueError, match=message):
        domain.set_condition(name, variable, values)


def test_conditions_do_not_chain_and_are_one_per_variable():
    domain = _domain()
    domain.define_integer("layers", 1, 3)
    domain.define_categorical("nesterov", ["yes", "no"])
    with pytest.raises(ValueError, match="already"):
        domain.set_condition("momentum", "layers", [1])
    # solver controls momentum, so solver cannot become conditional itself.
    with pytest.raises(ValueError, match="chain"):
        domain.set_condition("solver", "layers", [1])
    # nesterov is conditional, so nothing can depend on it.
    domain.set_condition("nesterov", "solver", ["sgd"])
    with pytest.raises(ValueError, match="chain"):
        domain.set_condition("layers", "nesterov", ["yes"])


def test_a_variable_in_a_condition_cannot_be_moved_into_a_structure():
    domain = _domain()
    domain.define_static_structure("v", 2)
    with pytest.raises(ValueError, match="condition"):
        domain.set_structure_to_variable("v", "momentum")


def test_the_domain_shows_the_condition():
    assert "Active if solver in ['sgd']" in str(_domain())


def test_kernel_tpe_models_a_variable_only_where_it_was_active():
    from metagen.metaheuristics.tpe.kernel_tpe import _observations
    domain = _domain()
    solutions = []
    for solver, momentum in (("adam", 0.51), ("sgd", 0.7), ("adam", 0.52), ("sgd", 0.8)):
        solution = _solution(domain)
        solution.set("solver", solver)
        solution.set("momentum", momentum)
        solutions.append(solution)
    observed = _observations(solutions)
    assert observed[("momentum",)] == [0.7, 0.8]
    assert len(observed[("solver",)]) == 4


ALGORITHMS = [RandomSearch, HillClimbing, TabuSearch, SA, GA, SSGA, Memetic, TPE, KernelTPE]


def _fitness_and_log():
    seen = Counter()

    def fitness(solution):
        momentum = solution["momentum"]
        if solution["solver"] == "adam":
            assert momentum is None
            seen["adam"] += 1
            return (solution["learning_rate"] - 0.3) ** 2 + 0.05
        assert momentum is not None
        seen["sgd"] += 1
        return (solution["learning_rate"] - 0.3) ** 2 + (momentum - 0.9) ** 2

    return fitness, seen


@pytest.mark.parametrize("algorithm", ALGORITHMS, ids=lambda a: a.__name__)
def test_every_algorithm_runs_with_a_conditional_variable(algorithm):
    genetic = algorithm in (GA, SSGA, Memetic)
    domain = _domain(GAConnector() if genetic else None)
    fitness, seen = _fitness_and_log()
    best = algorithm(domain, fitness, seed=2).run()
    assert best.get_fitness() == fitness(best)
    assert seen["adam"] > 0 and seen["sgd"] > 0


@pytest.mark.parametrize("strain_class", [CVOA, ProbabilisticCVOA], ids=lambda c: c.__name__)
def test_cvoa_runs_with_a_conditional_variable(strain_class):
    fitness, seen = _fitness_and_log()
    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2)]
    best = cvoa_launcher(strains, _domain(), fitness, seed=0, strain_class=strain_class)
    assert best.get_fitness() == fitness(best)


def _tpe_solutions(pairs):
    from metagen.metaheuristics.tpe.tpe_tools import TPEConnector
    domain = _domain(TPEConnector())
    solutions = []
    for solver, momentum in pairs:
        solution = _solution(domain)
        solution.set("solver", solver)
        solution.set("momentum", momentum)
        solutions.append(solution)
    return domain, solutions


def test_tpe_models_a_variable_only_from_the_references_where_it_is_active(monkeypatch):
    from metagen.metaheuristics.tpe.tpe_tools import TPEReal
    seen = {}
    original = TPEReal.resample

    def spy(self, best_values, worst_values):
        if self.get_definition().get_attributes()[1] == 0.5:      # momentum's minimum
            seen["best"] = sorted(value.get() for value in best_values)
            seen["worst"] = sorted(value.get() for value in worst_values)
        return original(self, best_values, worst_values)

    monkeypatch.setattr(TPEReal, "resample", spy)
    domain, solutions = _tpe_solutions([("sgd", 0.9), ("adam", 0.51), ("sgd", 0.8),
                                        ("adam", 0.52), ("sgd", 0.6), ("adam", 0.53)])
    candidate = _solution(domain)
    candidate.resample(solutions[:4], solutions[4:])
    assert seen == {"best": [0.8, 0.9], "worst": [0.6]}


def test_tpe_leaves_a_variable_alone_when_no_reference_has_it_active():
    domain, solutions = _tpe_solutions([("adam", 0.51), ("adam", 0.52), ("adam", 0.53)])
    set_seed(0)
    candidate = _solution(domain)
    before = candidate.get("momentum").get()
    candidate.resample(solutions[:2], solutions[2:])
    assert candidate.get("momentum").get() == before


def test_an_inactive_variable_prints_as_inactive():
    domain = _domain()
    solution = _solution(domain)
    solution.set("solver", "adam")
    assert "momentum = None (inactive)" in str(solution)
    solution.set("solver", "sgd")
    assert "momentum = None" not in str(solution)
