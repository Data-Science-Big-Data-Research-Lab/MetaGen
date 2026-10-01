"""TriGen's fitness: against the terms the original implementation computes, on cases
worked out by hand, and on the properties its terms promise."""
import json
import math
from pathlib import Path

import numpy as np
import pytest

from metagen.framework import Domain, Solution
from metagen.metaheuristics import TriclusterFitness
from metagen.triclustering import Cube, Tricluster, msl, plant, triq

REFERENCE = json.loads((Path(__file__).parents[1] / "triclustering" / "data" / "reference.json").read_text())
SYNTHETIC = Cube(np.array(REFERENCE["synthetic"]["values"]))
CONFIG = REFERENCE["synthetic"]["config"]
STORED = CONFIG["weights_as_stored"]
# The weights as the reference stored them, by this module's names.
REFERENCE_WEIGHTS = {"quality": STORED["Wf"], "genes": STORED["Wg"], "conditions": STORED["Wc"],
                     "times": STORED["Wt"], "overlap_genes": STORED["WOg"], "overlap_conditions": STORED["WOc"],
                     "overlap_times": STORED["WOt"]}
MAX_SIZES = (CONFIG["maxG"], CONFIG["maxC"], CONFIG["maxT"])


def _tricluster(positions):
    return Tricluster(positions["genes"], positions["conditions"], positions["times"])


@pytest.mark.parametrize("case", REFERENCE["synthetic"]["cases"], ids=lambda case: case["id"])
@pytest.mark.parametrize("measure", ["msl", "lsl", "msr3d"])
def test_the_quality_and_size_terms_match_the_reference(case, measure):
    """Measured against the largest sizes allowed and with the reference's views. The
    overlap term differs on purpose: the reference counts the coordinates of the
    triclusters found that the candidate does not hold, and adds them to a fitness that
    is minimized, which favors overlap; this one counts those it repeats."""
    fitness = TriclusterFitness(SYNTHETIC, measure=measure, views="trlab", weights=REFERENCE_WEIGHTS,
                                size_reference="max", max_sizes=MAX_SIZES,
                                found=[_tricluster(previous) for previous in case["previous"]])
    terms = fitness.terms(_tricluster(case["effective"]))
    expected = case["fitness"][measure]
    # abs_tol: the quality of a planted block is zero up to rounding on both sides.
    assert math.isclose(terms["quality"], expected["quality"], rel_tol=1e-12, abs_tol=1e-15)
    size_term = sum(REFERENCE_WEIGHTS[axis] * (1 - terms[axis]) for axis in ("genes", "conditions", "times"))
    assert math.isclose(size_term, expected["size_term"], rel_tol=1e-12)
    if not case["previous"]:
        assert math.isclose(terms["fitness"], expected["FF"], rel_tol=1e-12, abs_tol=1e-15)


def test_the_overlap_worked_out_by_hand():
    """Two triclusters found. The candidate holds genes 0-3: 2 of them in the first and 4
    in the second, 6 of 4 × 2; conditions 0-1: 2 and 0, 2 of 2 × 2; times 0-1: 1 and 1,
    2 of 2 × 2."""
    found = [Tricluster([0, 1, 9], [0, 1], [1, 5]), Tricluster([0, 1, 2, 3], [4, 5], [0, 6])]
    fitness = TriclusterFitness(SYNTHETIC, found=found)
    terms = fitness.terms(Tricluster([0, 1, 2, 3], [0, 1], [0, 1]))
    assert terms["overlap_genes"] == 6 / 8
    assert terms["overlap_conditions"] == 2 / 4
    assert terms["overlap_times"] == 2 / 4


def test_overlap_is_zero_before_anything_is_found_and_one_for_a_repeat():
    candidate = Tricluster([2, 5, 7], [1, 3], [0, 2, 4])
    fitness = TriclusterFitness(SYNTHETIC)
    assert all(fitness.terms(candidate)[f"overlap_{axis}"] == 0.0 for axis in ("genes", "conditions", "times"))
    fitness.found.append(candidate)
    assert all(fitness.terms(candidate)[f"overlap_{axis}"] == 1.0 for axis in ("genes", "conditions", "times"))


def test_repeating_what_was_found_makes_the_fitness_worse():
    cube, planted = plant((60, 6, 8), [(15, 3, 5)], noise=0.05, seed=0)
    target = planted[0]
    fitness = TriclusterFitness(cube)
    alone = fitness.evaluate(target)
    fitness.found.append(Tricluster(target.genes[:8], target.conditions, target.times))
    partly = fitness.evaluate(target)
    fitness.found.append(target)
    assert alone < partly < fitness.evaluate(target)
    elsewhere = Tricluster([g for g in range(60) if g not in target.genes][:15], target.conditions[:2],
                           target.times[:3])
    assert fitness.terms(elsewhere)["overlap_genes"] == 0.0


def test_the_size_is_measured_against_the_dataset_or_the_largest_size_allowed():
    tricluster = Tricluster(range(6), range(3), range(4))
    on_dataset = TriclusterFitness(SYNTHETIC).terms(tricluster)
    assert (on_dataset["genes"], on_dataset["conditions"], on_dataset["times"]) == (6 / 30, 3 / 8, 4 / 6)
    on_max = TriclusterFitness(SYNTHETIC, size_reference="max", max_sizes=(12, 4, 6)).terms(tricluster)
    assert (on_max["genes"], on_max["conditions"], on_max["times"]) == (6 / 12, 3 / 4, 4 / 6)


def test_the_fitness_is_the_weighted_mean_and_the_weights_need_not_add_up_to_one():
    tricluster = Tricluster(range(6), range(3), range(4))
    found = [Tricluster(range(3, 9), range(2), range(2))]
    fitness = TriclusterFitness(SYNTHETIC, found=found)
    terms = fitness.terms(tricluster)
    expected = (0.8 * terms["quality"] + 0.04 * (1 - terms["genes"]) + 0.03 * (1 - terms["conditions"])
                + 0.03 * (1 - terms["times"]) + 0.04 * terms["overlap_genes"]
                + 0.03 * terms["overlap_conditions"] + 0.03 * terms["overlap_times"])
    assert math.isclose(terms["fitness"], expected, rel_tol=1e-12)
    doubled = {name: 2 * weight for name, weight in fitness.weights.items()}
    assert math.isclose(TriclusterFitness(SYNTHETIC, weights=doubled, found=found).evaluate(tricluster),
                        terms["fitness"], rel_tol=1e-12)
    only_quality = {name: 0.0 for name in fitness.weights} | {"quality": 1.0}
    assert TriclusterFitness(SYNTHETIC, weights=only_quality).evaluate(tricluster) == terms["quality"]


@pytest.mark.parametrize("measure", ["msl", "lsl", "msr3d", "triq"])
def test_each_measure_is_its_quality_term(measure):
    tricluster = Tricluster(range(5), range(3), range(4))
    quality = TriclusterFitness(SYNTHETIC, measure=measure, views="time").quality(tricluster)
    if measure == "msl":
        assert quality == msl(SYNTHETIC, tricluster, views="time") / (2 * math.pi)
    if measure == "triq":
        assert quality == 1.0 - triq(SYNTHETIC, tricluster, views="time")
    assert quality >= 0.0


def test_a_solution_of_three_subsets_has_the_fitness_of_its_tricluster():
    domain = Domain()
    for name, size in zip(("genes", "conditions", "times"), SYNTHETIC.shape):
        domain.define_subset(name, list(range(size)), 2, size)
    solution = Solution(domain)
    fitness = TriclusterFitness(SYNTHETIC)
    tricluster = Tricluster(solution["genes"], solution["conditions"], solution["times"])
    assert fitness(solution) == fitness.evaluate(tricluster)


@pytest.mark.parametrize("arguments", [
    {"measure": "mse"},
    {"views": "all"},
    {"flat_profiles": "drop", "measure": "triq"},
    {"weights": {"quality": 1.0}},
    {"weights": dict(TriclusterFitness(SYNTHETIC).weights, genes=-0.1)},
    {"weights": dict(TriclusterFitness(SYNTHETIC).weights, genes=math.inf)},
    {"weights": {name: 0.0 for name in TriclusterFitness(SYNTHETIC).weights}},
    {"size_reference": "max"},
    {"size_reference": "max", "max_sizes": (31, 4, 4)},
    {"size_reference": "max", "max_sizes": (10, 4)},
    {"size_reference": "cube"},
])
def test_options_that_do_not_fit_are_rejected(arguments):
    with pytest.raises(ValueError):
        TriclusterFitness(SYNTHETIC, **arguments)
