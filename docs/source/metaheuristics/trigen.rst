.. include:: ../aliases.rst

TriGen
======

TriGen finds triclusters: blocks of a three-dimensional dataset, some genes under some conditions at some times, whose values behave alike. It is a genetic algorithm that finds them one after another, each with a search of its own, and what it has found shapes the searches that follow: the fitness penalizes repeating the coordinates of the triclusters found, and every search after the first starts mostly from the least explored genes, conditions and times. The data, the measures and the qualities it works with are in :doc:`../triclustering/index`.

How it searches
---------------

A tricluster is three subsets, of the genes, the conditions and the times of the cube, each between a smallest and a largest size. Each search runs a genetic algorithm over them:

* **The initial population** mixes triclusters drawn at random, blocks of consecutive positions and, after the first search, triclusters drawn from the least explored coordinates.
* **Each generation** selects a share of the population (``selection_rate``) by groups: the population is split at random into three groups, the best of each is selected, and then the best left in a group drawn at random. The selected pass on untouched and are the only parents. The rest of the population is bred from pairs of them, crossing the genes, the conditions and the times each at one point, and each child mutates, with probability ``mutation_probability``, by adding, removing or changing one coordinate.
* **The fitness**, :py:class:`~metagen.metaheuristics.TriclusterFitness`, is minimized: a weighted mean of a quality term (MSL by default), of the size of each dimension, larger being better, and of how much each dimension repeats the triclusters already found.

Each search returns the best tricluster of its last population that is not one already found. A search costs ``population_size`` evaluations to start and those of the children of each generation, ``population_size`` minus the selected, about half of it.

The defaults are a quick start: 5 triclusters, 20 generations of 10 individuals. The configurations used with TriGen on real data range from populations of 100 to 200 over 50 to 400 generations.

Finding planted triclusters
---------------------------

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import cell_precision, plant, relevance, triq

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100,
                    min_sizes=(5, 2, 3), max_sizes=(30, 6, 8), seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])                    # [(5, 2, 4), (10, 3, 3)]
    print([round(tricluster.fitness, 3) for tricluster in found])       # [0.088, 0.096]
    print([round(triq(cube, tricluster), 3) for tricluster in found])   # [0.994, 0.993]
    # The share of the cells found that belong to a planted tricluster: all of them.
    print(relevance(found, planted, cell_precision))                    # 1.0

Each tricluster keeps the fitness it had when it was found, against the triclusters found before it. ``trigen.history`` holds, per search, the tricluster, every term of its fitness and the evaluations and seconds it took; with ``history="trigen.jsonl"`` it is also written to a file, a line per search. ``trigen.hierarchy`` counts how many triclusters found hold each gene, condition and time.

When a search evaluates nothing that has not been found already, which only happens in a small search space, it adds no tricluster and says so in the log: TriGen then returns fewer triclusters than asked for.

Reference
---------

.. autoclass:: metagen.metaheuristics.TriGen
    :members: run

.. autoclass:: metagen.metaheuristics.TriclusterFitness
    :members: evaluate, terms, quality

.. autoclass:: metagen.metaheuristics.trigen.trigen_ga.TriGenGA
    :members: initialize, iterate
    :show-inheritance:
