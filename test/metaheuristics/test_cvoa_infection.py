"""How far a CVOA infection moves each variable it changes: StrainProperties'
infection_alteration_limit, handed to Solution.mutate by infect()."""
import pytest

from metagen.framework import Domain, RelativeAlteration, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import ProbabilisticCVOA, StrainProperties, cvoa_launcher
from metagen.metaheuristics.cvoa.common_tools import infect
from metagen.metaheuristics.cvoa.cvoa import CVOA


def _domain():
    domain = Domain()
    domain.define_real("x", -10.0, 10.0)
    domain.define_integer("n", 0, 100)
    domain.define_integer("bit", 0, 1)
    return domain


def _fitness(solution):
    return solution["x"] ** 2 + solution["n"] + solution["bit"]


def test_with_a_limit_every_changed_variable_stays_near_the_carrier():
    set_seed(0)
    domain = _domain()
    carrier = Solution(domain)
    carrier.set("x", 0.0)
    carrier.set("n", 50)
    for _ in range(300):
        infected = infect(carrier, _fitness, 3, RelativeAlteration(0.1))
        assert abs(infected["x"]) <= 2.0
        assert abs(infected["n"] - 50) <= 10
        assert infected.get_fitness() == _fitness(infected)


def test_without_a_limit_a_changed_variable_is_drawn_over_its_whole_domain():
    set_seed(0)
    domain = _domain()
    carrier = Solution(domain)
    carrier.set("x", 0.0)
    far = sum(abs(infect(carrier, _fitness, 3)["x"]) > 2.0 for _ in range(300))
    assert far > 100


def test_a_bit_flips_with_or_without_a_limit():
    domain = Domain()
    domain.define_integer("bit", 0, 1)
    for limit in (None, RelativeAlteration(0.2)):
        set_seed(1)
        carrier = Solution(domain)
        for _ in range(50):
            assert infect(carrier, _fitness_bit, 1, limit)["bit"] == 1 - carrier["bit"]


def _fitness_bit(solution):
    return solution["bit"]


def test_the_default_is_the_whole_domain():
    assert StrainProperties().infection_alteration_limit is None
    domain = _domain()
    set_seed(2)
    carrier = Solution(domain)
    set_seed(3)
    default = infect(carrier, _fitness, 2)
    set_seed(3)
    explicit = infect(carrier, _fitness, 2, None)
    assert default == explicit


@pytest.mark.parametrize("strain_class", [CVOA, ProbabilisticCVOA], ids=lambda c: c.__name__)
def test_a_pandemic_runs_with_a_neighborhood(strain_class):
    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2,
                                infection_alteration_limit=RelativeAlteration(0.2))]
    best = cvoa_launcher(strains, _domain(), _fitness, seed=0, strain_class=strain_class)
    assert best.get_fitness() == _fitness(best)
