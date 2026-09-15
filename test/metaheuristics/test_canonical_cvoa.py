"""
CanonicalCVOA: the paper's CVOA next to MetaGen's. Each test pins one of the
places where the two differ, and the last ones run it end to end, in threads and
on Ray, and check that a seed reproduces it.
"""
import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import CanonicalCVOA, StrainProperties, cvoa_launcher
from metagen.metaheuristics.cvoa.common_tools import SolutionSet
from metagen.metaheuristics.cvoa.local_tools import LocalPandemicState


def _domain():
    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 0, 100)
    return domain


def _fitness(solution):
    return (solution["x"] - 1.234) ** 2 + abs(solution["n"] - 42)


def _strain(update_isolated=False, **properties):
    set_seed(0)
    domain = _domain()
    state = LocalPandemicState(Solution(domain))
    strain = CanonicalCVOA(state, domain, _fitness, StrainProperties("S1", **properties), update_isolated)
    return strain, state


def _carriers(domain, how_many):
    carriers = SolutionSet()
    for _ in range(how_many):
        carrier = Solution(domain)
        carrier.evaluate(_fitness)
        carriers.add(carrier)
    return carriers


def test_an_isolated_individual_joins_the_recovered():
    """Algorithm 3, line 12. With p_isolation 1 and distancing on, a superspreader's
    offspring, six at least, all end up recovered and counted, none in the population."""
    strain, state = _strain(pandemic_duration=3, social_distancing=1, p_isolation=1.0)
    strain.time = 1
    carrier = next(iter(_carriers(strain.domain, 1)))
    strain.superspreaders.add(carrier)

    new = strain.infect_from_carrier(state, strain.domain, _fitness, strain.strain_properties, carrier,
                                     strain.superspreaders, strain.time)

    assert len(new) == 0
    assert state.get_recovered_len() >= 6
    assert state.get_pandemic_report()["isolated"] == state.get_recovered_len()


@pytest.mark.parametrize("p_isolation", [0.3, 0.5, 0.7])
def test_isolation_is_drawn_once_per_carrier(p_isolation):
    """Algorithm 3 draws R4 once and every offspring of the carrier shares it: the
    admitted population is all of them or none, never a fraction."""
    strain, state = _strain(pandemic_duration=3, social_distancing=1, p_isolation=p_isolation)
    strain.time = 1
    outcomes = set()
    for seed in range(20):
        set_seed(seed)
        carrier = next(iter(_carriers(strain.domain, 1)))
        new = strain.infect_individuals_from(state, _fitness, strain.strain_properties, carrier, 1, 8, strain.time)
        outcomes.add(len(new))
    assert outcomes <= {0, 8}, f"a carrier's offspring split between isolated and admitted: {outcomes}"
    assert outcomes == {0, 8}, "twenty carriers should see both draws"


@pytest.mark.parametrize("p_die, p_superspreader, dead, superspreaders", [
    (1.0, 1.0, 5, 5), (0.0, 0.0, 0, 0)])
def test_death_and_superspreading_are_drawn_per_individual(p_die, p_superspreader, dead, superspreaders):
    """Algorithms 2 and 4: with the probabilities at 1 every carrier dies and
    superspreads; at 0, none. CVOA's bounded sets would take a fixed share instead."""
    strain, state = _strain(pandemic_duration=3, p_die=p_die, p_superspreader=p_superspreader)
    strain.initialize()
    strain.infected = _carriers(strain.domain, 5)
    strain.best_strain_solution = next(iter(strain.infected))

    strain.update_pandemic_global_state()

    assert len(strain.dead) == dead
    assert len(strain.superspreaders) == superspreaders
    assert state.get_recovered_len() == 0, "nobody recovers before spreading"


def test_the_carriers_recover_after_spreading():
    """Algorithm 1, line 22: once they have spread, the carriers are recovered, so the
    next iteration cannot infect them again except by reinfection."""
    strain, state = _strain(pandemic_duration=3, p_die=0.0)
    population, _ = strain.initialize()
    patient_zero = population[0]

    strain.iterate(population)

    assert state.get_individual_state(patient_zero).recovered


def test_it_runs_through_the_launcher_and_a_seed_reproduces_it():
    strains = [StrainProperties("S1", pandemic_duration=4, social_distancing=2)]
    first = cvoa_launcher(strains, _domain(), _fitness, seed=3, strain_class=CanonicalCVOA)
    second = cvoa_launcher(strains, _domain(), _fitness, seed=3, strain_class=CanonicalCVOA)
    assert first.get_fitness() == _fitness(first)
    assert first.get_fitness() == second.get_fitness()


def test_it_runs_on_ray():
    ray = pytest.importorskip("ray")
    from metagen.metaheuristics.cvoa import distributed_cvoa_launcher

    started_here = not ray.is_initialized()
    if started_here:
        ray.init(num_cpus=2, include_dashboard=False, ignore_reinit_error=True)
    # Defined here so that Ray pickles it by value: a worker cannot import this module.
    def fitness(solution):
        return (solution["x"] - 1.234) ** 2 + abs(solution["n"] - 42)

    try:
        strains = [StrainProperties("S1", pandemic_duration=3, social_distancing=1)]
        best = distributed_cvoa_launcher(strains, _domain(), fitness, seed=0, strain_class=CanonicalCVOA)
        assert best.get_fitness() == fitness(best)
    finally:
        if started_here and ray.is_initialized():
            ray.shutdown()
