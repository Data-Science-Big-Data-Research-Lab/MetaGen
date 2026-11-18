"""Where TriGen's searches start: the data hierarchy of the coordinates already found,
and the scattered, block and hierarchical triclusters of the initial population."""
from collections import Counter

import pytest

from metagen.framework.rng import set_seed
from metagen.metaheuristics.trigen.population import (DataHierarchy, block, exact_floor, hierarchical,
                                                      initial_population, scattered)
from metagen.triclustering import Tricluster

SHAPE = (30, 6, 10)
SIZES = ((3, 8), (2, 4), (2, 6))


def _within(tricluster, shape=SHAPE, sizes=SIZES):
    for positions, length, (low, high) in zip((tricluster.genes, tricluster.conditions, tricluster.times),
                                              shape, sizes):
        assert low <= len(positions) <= high
        assert all(0 <= position < length for position in positions)


# --- the data hierarchy -----------------------------------------------------------

def test_a_tricluster_found_raises_the_level_of_each_of_its_coordinates():
    hierarchy = DataHierarchy((5, 3, 4))
    hierarchy.update(Tricluster([0, 2], [1, 2], [0, 3]))
    hierarchy.update(Tricluster([2, 4], [1, 2], [1, 3]))
    assert hierarchy.levels == [[1, 0, 2, 0, 1], [0, 2, 2], [1, 1, 0, 2]]


def test_the_lowest_levels_go_first_and_whole_when_they_fit():
    set_seed(0)
    hierarchy = DataHierarchy((6, 2, 2))
    hierarchy.levels[0] = [0, 2, 1, 0, 1, 3]       # level 0: 0, 3; level 1: 2, 4; level 2: 1; level 3: 5
    for _ in range(50):
        assert hierarchy.draw(0, 2) == [0, 3]
        three = hierarchy.draw(0, 3)
        assert three[:1] == [0] and 3 in three and len(set(three) & {2, 4}) == 1
        assert hierarchy.draw(0, 5) == [0, 1, 2, 3, 4]
        assert hierarchy.draw(0, 6) == [0, 1, 2, 3, 4, 5]


def test_within_a_level_the_positions_are_drawn_evenly():
    set_seed(1)
    hierarchy = DataHierarchy((10, 2, 2))
    counts = Counter()
    for _ in range(4000):
        counts.update(hierarchy.draw(0, 3))
    assert set(counts) == set(range(10))
    assert all(abs(count - 1200) < 120 for count in counts.values())


# --- the three kinds of tricluster ------------------------------------------------

@pytest.mark.parametrize("draw", [scattered, block])
def test_every_kind_keeps_to_the_sizes_and_the_cube(draw):
    set_seed(2)
    sizes_seen = [set(), set(), set()]
    for _ in range(500):
        tricluster = draw(SHAPE, SIZES)
        _within(tricluster)
        for seen, size in zip(sizes_seen, tricluster.size):
            seen.add(size)
    assert sizes_seen == [set(range(3, 9)), set(range(2, 5)), set(range(2, 7))]


def test_a_block_holds_consecutive_positions():
    set_seed(3)
    for _ in range(300):
        tricluster = block(SHAPE, SIZES)
        for positions in (tricluster.genes, tricluster.conditions, tricluster.times):
            assert list(positions) == list(range(positions[0], positions[0] + len(positions)))


def test_every_window_of_a_block_is_as_likely():
    """A window of 8 times among 14 can start at 0 to 6: each start a seventh of the time,
    so every time is held as often as the windows over it."""
    set_seed(4)
    starts = Counter()
    for _ in range(7000):
        starts[block((5, 2, 14), ((2, 2), (2, 2), (8, 8))).times[0]] += 1
    assert set(starts) == set(range(7))
    assert all(abs(count - 1000) < 120 for count in starts.values())


def test_a_hierarchical_tricluster_takes_the_least_explored_coordinates():
    set_seed(5)
    hierarchy = DataHierarchy(SHAPE)
    explored = Tricluster(range(20), range(4), range(7))
    hierarchy.update(explored)
    for _ in range(200):
        tricluster = hierarchical(hierarchy, ((3, 8), (2, 2), (2, 3)))
        _within(tricluster, sizes=((3, 8), (2, 2), (2, 3)))
        assert not set(tricluster.genes) & set(explored.genes)
        assert not set(tricluster.conditions) & set(explored.conditions)
        assert not set(tricluster.times) & set(explored.times)


def test_a_hierarchy_of_cells_counts_the_cells_of_each_tricluster_found():
    hierarchy = DataHierarchy(SHAPE, cells=True)
    hierarchy.update(Tricluster(range(5), range(2), range(3)))
    hierarchy.update(Tricluster(range(3, 8), [1, 2], [2, 3]))
    assert hierarchy.cells is not None and hierarchy.cells.sum() == 5 * 2 * 3 + 5 * 2 * 2
    assert hierarchy.cells[3, 1, 2] == 2 and hierarchy.cells[0, 0, 0] == 1 and hierarchy.cells[9, 0, 0] == 0
    assert hierarchy.levels[0][3] == 2
    assert DataHierarchy(SHAPE).cells is None


def test_the_genes_by_cells_are_those_least_held_in_the_conditions_and_times_drawn():
    set_seed(5)
    hierarchy = DataHierarchy(SHAPE, cells=True)
    explored = Tricluster(range(20), range(4), range(7))
    hierarchy.update(explored)
    # In other times the explored genes hold no cell, so they are as free as the rest.
    assert set(hierarchy.draw_genes([0, 1], [7, 8, 9], 30)) == set(range(30))
    # In its own conditions and times, the genes not explored go first.
    assert hierarchy.draw_genes([0, 1], [0, 1], 10) == list(range(20, 30))


def test_a_hierarchical_tricluster_by_cells_may_reuse_genes_in_other_times():
    set_seed(5)
    hierarchy = DataHierarchy(SHAPE, cells=True)
    explored = Tricluster(range(20), range(6), range(7))
    hierarchy.update(explored)
    reused = 0
    for _ in range(200):
        tricluster = hierarchical(hierarchy, ((3, 8), (2, 4), (2, 3)))
        _within(tricluster, sizes=((3, 8), (2, 4), (2, 3)))
        assert not set(tricluster.times) & set(explored.times)
        reused += bool(set(tricluster.genes) & set(explored.genes))
    assert reused > 100


# --- the initial population -------------------------------------------------------

def test_the_first_search_starts_half_scattered_and_half_from_blocks():
    set_seed(6)
    hierarchy = DataHierarchy(SHAPE)
    population = initial_population(SHAPE, SIZES, hierarchy, first=True, population_size=11, random_fraction=0.2)
    assert len(population) == 11
    for tricluster in population[5:]:                 # 11 // 2 = 5 scattered, then 6 blocks
        assert list(tricluster.genes) == list(range(tricluster.genes[0], tricluster.genes[-1] + 1))


@pytest.mark.parametrize("population_size, random_fraction, unguided", [(10, 0.2, 2), (11, 0.5, 5), (100, 0.29, 29),
                                                                          (10, 0.0, 0), (10, 1.0, 10)])
def test_later_searches_take_the_rest_from_the_hierarchy(population_size, random_fraction, unguided):
    set_seed(7)
    hierarchy = DataHierarchy(SHAPE)
    hierarchy.update(Tricluster(range(26), range(4), range(8)))   # unexplored: genes 26-29, conditions 4-5, times 8-9
    sizes = ((2, 4), (2, 2), (2, 2))
    population = initial_population(SHAPE, sizes, hierarchy, first=False, population_size=population_size,
                                    random_fraction=random_fraction)
    assert len(population) == population_size
    guided = population[unguided:]
    assert all(set(t.genes) <= {26, 27, 28, 29} and t.conditions == (4, 5) and t.times == (8, 9) for t in guided)
    if unguided:
        assert not all(set(t.genes) <= {26, 27, 28, 29} for t in population[:unguided])


@pytest.mark.parametrize("fraction, count, expected", [(0.42, 150, 63), (0.21, 300, 63), (0.13, 900, 117),
                                                      (0.29, 100, 29), (0.5, 10, 5), (0.2, 10, 2), (1 / 3, 9, 3),
                                                      (0.0, 10, 0), (1.0, 7, 7), (0.99, 10, 9)])
def test_the_share_of_a_count_is_floored_without_floating_point_slips(fraction, count, expected):
    assert exact_floor(fraction, count) == expected


def test_the_same_seed_gives_the_same_population():
    def draw():
        set_seed(8)
        hierarchy = DataHierarchy(SHAPE)
        hierarchy.update(Tricluster(range(10), range(2), range(3)))
        return initial_population(SHAPE, SIZES, hierarchy, first=False, population_size=20, random_fraction=0.4)
    assert draw() == draw()
