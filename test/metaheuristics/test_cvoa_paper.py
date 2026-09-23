"""
The experiments of the CVOA paper, as far as they can be stated as tests.

The paper studies the algorithm on binary encodings with f(x) = (x - 15)^2 over
20 bits and reports three qualitative results: the pandemic curve rises, peaks
and decays once social distancing starts (Figure 2), R0 falls linearly with
P_ISOLATION and drops below 1 (Figure 5), and more strains explore more of the
space, with more recovered and more deaths (Figures 3 and 4). Each test here
states one of those results and runs it on both strain classes, CVOA and
ProbabilisticCVOA.

What is not asserted: the paper's numbers. Table 2 (five diseases, 10 to 50 bits)
is a benchmark, not a threshold, and belongs in a measurement, not in the suite.
Two implementation choices explain the margins the tests allow: a strain keeps its
best individual in the population, so the curve decays to a residual level rather
than to zero; and patients zero are drawn at random.
"""
from typing import Dict, List

import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from metagen.metaheuristics import ProbabilisticCVOA, StrainProperties
from metagen.metaheuristics.cvoa import CVOA
from metagen.metaheuristics.cvoa.local_state import LocalPandemicState

BITS = 20
VARIANTS = pytest.mark.parametrize("variant", [CVOA, ProbabilisticCVOA], ids=lambda c: c.__name__)


def _paper_problem():
    """The paper's toy problem: a 20-bit binary encoding of x, minimizing (x - 15)^2."""
    domain = Domain()
    for i in range(BITS):
        domain.define_integer(f"b{i}", 0, 1)

    def fitness(solution: Solution) -> float:
        x = sum(solution[f"b{i}"] << i for i in range(BITS))
        return float((x - 15) ** 2)

    return domain, fitness


def _traced(variant, curves: Dict[str, List[int]]):
    """A subclass that records the infected population of each strain after every iteration."""

    class Traced(variant):
        def iterate(self, solutions):
            result = super().iterate(solutions)
            curves.setdefault(self.strain_properties.strain_id, []).append(len(self.infected))
            return result

    return Traced


def _run(variant, seed: int, strains: int = 1, **properties):
    """Run a pandemic over a shared state and return the infected curve of every
    strain and the pandemic report. The strains run one after another, not in the
    launcher's threads: the accounting the paper plots is the same, and the run
    reproduces, which threads sharing one generator cannot promise."""
    set_seed(seed)
    domain, fitness = _paper_problem()
    state = LocalPandemicState(Solution(domain))
    curves: Dict[str, List[int]] = {}
    strain_class = _traced(variant, curves)
    for index in range(strains):
        strain_class(state, domain, fitness, StrainProperties(f"S{index}", **properties)).run()
    return curves, state.get_pandemic_report()


@VARIANTS
@pytest.mark.parametrize("seed", [0, 1, 2])
def test_the_pandemic_curve_rises_peaks_and_decays(variant, seed):
    """Figure 2: with the paper's parameters the number of new infected grows until
    social distancing starts, peaks there, and decays afterwards. The tail does not
    reach zero because the strain keeps its best individual; it stays below a tenth
    of the peak over the last ten iterations.

    A pandemic can also fail to take off: ProbabilisticCVOA makes patient zero a
    superspreader only with p_superspreader, and a strain that starts with a handful
    of carriers may never grow. That is a legitimate outcome of the paper's draws,
    not a curve to fit: such a run stays small throughout and is checked as such."""
    properties = StrainProperties("S0")
    curves, _ = _run(variant, seed)
    curve = curves["S0"]

    if max(curve) < 20:
        assert variant is ProbabilisticCVOA, f"CVOA's patient zero always superspreads; it should take off: {curve}"
        assert all(size <= 10 for size in curve), f"a pandemic that never took off should stay small: {curve}"
        return

    peak = curve.index(max(curve))
    assert peak <= properties.social_distancing, f"the peak came after distancing started: {curve}"
    assert all(a <= b for a, b in zip(curve, curve[1:peak + 1])), f"the curve is not rising to its peak: {curve}"
    tail = curve[-10:]
    assert sum(tail) / len(tail) < 0.1 * max(curve), f"the pandemic did not decay after distancing: {curve}"


@VARIANTS
def test_r0_falls_linearly_with_p_isolation(variant):
    """Figure 5: R0, measured as the growth of the infected population over the first
    two iterations with distancing, decreases with P_ISOLATION, is above 1 without
    isolation and below 1 with the paper's 0.7. The fall is at least a halving by
    0.9, which is what a linear drop toward zero implies."""
    distancing = 5
    grid = [0.0, 0.25, 0.5, 0.7, 0.9]
    r0 = {}
    for p_isolation in grid:
        ratios = []
        for seed in range(3):
            curves, _ = _run(variant, seed, pandemic_duration=distancing + 2, social_distancing=distancing,
                             p_isolation=p_isolation)
            curve = curves["S0"]
            ratios.append((curve[distancing] / curve[distancing - 1] + curve[distancing + 1] / curve[distancing]) / 2)
        r0[p_isolation] = sum(ratios) / len(ratios)

    values = [r0[p] for p in grid]
    assert all(a > b for a, b in zip(values, values[1:])), f"R0 does not fall with p_isolation: {r0}"
    assert r0[0.0] > 1.0, f"the pandemic should grow without isolation: {r0}"
    assert r0[0.7] < 1.0, f"the pandemic should decline with the paper's p_isolation: {r0}"
    assert r0[0.9] < 0.5 * r0[0.0], f"the fall is too shallow to be the paper's line: {r0}"


@VARIANTS
def test_more_strains_explore_more_and_leave_more_recovered_and_dead(variant):
    """Figures 3 and 4, first conclusion: the number of individuals explored, the
    accumulated recovered and the deaths all grow with the number of strains. Four
    strains against one on the same seed, over the same shared state."""
    one_curves, one_report = _run(variant, 0, strains=1)
    four_curves, four_report = _run(variant, 0, strains=4)

    explored_by_one = sum(sum(curve) for curve in one_curves.values())
    explored_by_four = sum(sum(curve) for curve in four_curves.values())
    assert len(four_curves) == 4
    assert explored_by_four > explored_by_one, (explored_by_one, explored_by_four)
    assert four_report["recovered"] > one_report["recovered"], (one_report, four_report)
    assert four_report["deaths"] > one_report["deaths"], (one_report, four_report)
