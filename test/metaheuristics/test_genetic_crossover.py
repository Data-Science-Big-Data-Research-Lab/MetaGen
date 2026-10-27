"""
The crossover of a dynamic structure, cut and splice: each parent is cut at a point of
its own, drawn among the pairs of cuts that give both children a valid length. The
pairs are counted rather than listed, and the pair drawn has to be the one listing
them all and drawing one gives.
"""
import pytest

from metagen.framework import Domain
from metagen.framework.rng import get_rng, set_seed
from metagen.metaheuristics import GAConnector
from metagen.metaheuristics.genetic.genetic_tools import _draw_cuts, _valid_length


def _definition(low, high, step=None):
    domain = Domain(connector=GAConnector())
    if step is None:
        domain.define_dynamic_structure("v", low, high)
    else:
        domain.define_dynamic_structure("v", low, high, step)
    domain.set_structure_to_integer("v", 0, 9)
    return domain.get_core().get("v")


def _listed(definition, length1, length2):
    pairs = [(cut1, cut2)
             for cut1 in range(length1 + 1) for cut2 in range(length2 + 1)
             if _valid_length(definition, cut1 + length2 - cut2)
             and _valid_length(definition, cut2 + length1 - cut1)]
    return pairs[get_rng().randrange(len(pairs))] if pairs else None


@pytest.mark.parametrize("low, high, step", [(1, 8, None), (2, 40, 2), (3, 30, 3), (5, 6, None), (10, 900, None)])
@pytest.mark.parametrize("length1, length2", [(1, 8), (6, 6), (2, 7), (40, 4), (5, 5)])
def test_the_cuts_drawn_are_those_of_listing_every_pair(low, high, step, length1, length2):
    definition = _definition(low, high, step)
    for seed in range(20):
        set_seed(seed)
        listed, after_listing = _listed(definition, length1, length2), get_rng().random()
        set_seed(seed)
        drawn, after_drawing = _draw_cuts(definition, length1, length2), get_rng().random()
        assert drawn == listed and after_drawing == after_listing


def test_without_a_pair_of_valid_lengths_nothing_is_drawn():
    definition = _definition(4, 4)
    assert _draw_cuts(definition, 4, 3) is None
