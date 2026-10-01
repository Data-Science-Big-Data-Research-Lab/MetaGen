"""What TriGen finds lies within planted triclusters: on cubes with two of them, far more
of the cells it finds belong to them than with random triclusters of the same sizes. How
much of each planted tricluster it recovers is not pinned here."""
import numpy as np

from metagen.framework.rng import set_seed
from metagen.metaheuristics import TriGen
from metagen.metaheuristics.trigen.population import scattered
from metagen.triclustering import cell_precision, plant, relevance

SIZES = ((5, 30), (2, 6), (3, 8))


def test_what_trigen_finds_lies_within_the_planted_triclusters():
    """Two additive triclusters planted in noise; a population of 100 over 50 generations,
    the sizes of the configurations used with TriGen. In each seed, the share of the cells
    found that belong to a planted tricluster: random triclusters of the same sizes reach
    about 0.05."""
    found_precision, random_precision = [], []
    for seed in range(10):
        cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=seed)
        found = TriGen(cube, n_triclusters=2, generations=50, population_size=100,
                       min_sizes=[low for low, _ in SIZES], max_sizes=[high for _, high in SIZES], seed=seed).run()
        found_precision.append(relevance(found, planted, cell_precision))
        set_seed(seed)
        random_precision.append(np.mean([relevance([scattered(cube.shape, SIZES)], planted, cell_precision)
                                         for _ in range(100)]))
    assert sum(precision >= 0.5 for precision in found_precision) >= 8
    assert np.mean(found_precision) > 10 * np.mean(random_precision)
