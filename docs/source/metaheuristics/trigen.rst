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

Each search returns the best tricluster of its last population that is not one already found, and that tricluster then **grows**: TriGen adds to it, one at a time, the gene, condition or time that leaves its fitness lowest, as long as the fitness does not rise and the dimension is below its largest size. With ``growth="quality"`` the steps follow the quality term alone, and with ``growth=None`` the tricluster is kept as the search returned it.

A search costs ``population_size`` evaluations to start and those of the children of each generation, ``population_size`` minus the selected, about half of it. Growing adds its own: each step scores every gene, condition and time not yet in the tricluster, in the dimensions below their largest size, so on a cube with thousands of genes growing can cost more than the search.

The fitness rewards size, so the largest sizes are what keeps the triclusters to the scale of the patterns sought: without ``max_sizes``, a tricluster may take in most of the cube, and growing it then costs many evaluations. Set them to the largest triclusters of interest.

The defaults are a quick start: 5 triclusters, 20 generations of 10 individuals. The configurations used with TriGen on real data range from populations of 100 to 200 over 50 to 400 generations.

Finding planted triclusters
---------------------------

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import cell_precision, plant, recovery, relevance, triq

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100,
                    min_sizes=(5, 2, 3), max_sizes=(30, 6, 8), seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])                    # [(16, 4, 5), (15, 2, 5)]
    print([round(tricluster.fitness, 3) for tricluster in found])       # [0.075, 0.151]
    print([round(triq(cube, tricluster), 3) for tricluster in found])   # [0.994, 0.915]
    # The share of the cells found that belong to a planted tricluster.
    print(round(relevance(found, planted, cell_precision), 3))          # 0.933
    # How much of each planted tricluster is found, on average.
    print(round(recovery(found, planted), 3))                           # 0.599

Each tricluster keeps the fitness it had when it was found, against the triclusters found before it. ``trigen.history`` holds, per search, the tricluster, every term of its fitness, the evaluations and seconds it took and the evaluations its growth took; with ``history="trigen.jsonl"`` it is also written to a file, a line per search. ``trigen.hierarchy`` counts how many triclusters found hold each gene, condition and time.

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
