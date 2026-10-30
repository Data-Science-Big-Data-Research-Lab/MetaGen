.. include:: ../aliases.rst

TriGen
======

TriGen finds triclusters: blocks of a three-dimensional dataset, some genes under some conditions at some times, whose values behave alike. It is a genetic algorithm that finds them one after another, each with a search of its own, and what it has found shapes the searches that follow: the fitness penalizes repeating the coordinates of the triclusters found, and every search after the first starts mostly from what they have explored least: the conditions and times they hold least and, in them, the genes with the fewest of their cells. The data, the measures and the qualities it works with are in :doc:`../triclustering/index`.

How it searches
---------------

A tricluster is three subsets, of the genes, the conditions and the times of the cube, each between a smallest and a largest size. Each search runs a genetic algorithm over them:

* **The initial population** mixes triclusters drawn at random, blocks of consecutive positions and, after the first search, triclusters drawn from what the triclusters found have explored least (see `Counting what was found by cells`_).
* **Each generation** selects a share of the population (``selection_rate``) by groups: the population is split at random into three groups, the best of each is selected, and then the best left in a group drawn at random. The selected pass on untouched and are the only parents. The rest of the population is bred from pairs of them, crossing the genes, the conditions and the times each at one point, and each child mutates, with probability ``mutation_probability``, by adding, removing or changing one coordinate.
* **The fitness**, :py:class:`~metagen.metaheuristics.TriclusterFitness`, is minimized. By default it is a weighted mean of a quality term (MSL by default), of the size of each dimension, larger being better, and of how much each dimension repeats the triclusters already found; with ``scoring="significance"`` it is the significance of the tricluster instead (see `Scoring by significance`_).

Each search returns the best tricluster of its last population that is not one already found, and that tricluster then **grows**: TriGen adds to it, one at a time, the gene, condition or time that leaves its fitness lowest, as long as the fitness does not rise and the dimension is below its largest size. With ``growth="quality"`` the steps follow the quality term alone, and with ``growth=None`` the tricluster is kept as the search returned it.

A search costs ``population_size`` evaluations to start and those of the children of each generation, ``population_size`` minus the selected, about half of it. Growing adds its own: each step scores every gene, condition and time not yet in the tricluster, in the dimensions below their largest size, and, with ``pruning``, every one it holds, so on a cube with thousands of genes growing can cost more than the search.

The fitness rewards size, so the largest sizes are what keeps the triclusters to the scale of the patterns sought: without ``max_sizes``, a tricluster may take in most of the cube, and growing it then costs many evaluations. Set them to the largest triclusters of interest.

The defaults are 5 triclusters, each searched by a population of 200 over 50 generations, with a selection rate of 0.5 and a mutation probability of 0.1. They are a starting point: the values that suit a dataset depend on it, and a smaller population or fewer generations give a quicker first look.

Finding planted triclusters
---------------------------

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import cell_precision, plant, recovery, relevance, triq

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100,
                    min_sizes=(5, 2, 3), max_sizes=(30, 6, 8), seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])                    # [(16, 4, 5), (18, 2, 3)]
    print([round(tricluster.fitness, 3) for tricluster in found])       # [0.075, 0.211]
    print([round(triq(cube, tricluster), 3) for tricluster in found])   # [0.994, 0.846]
    # The share of the cells found that belong to a planted tricluster.
    print(round(relevance(found, planted, cell_precision), 3))          # 0.833
    # How much of each planted tricluster is found, on average.
    print(round(recovery(found, planted), 3))                           # 0.471

Each tricluster keeps the fitness it had when it was found, against the triclusters found before it. ``trigen.history`` holds, per search, the tricluster, every term of its fitness, the evaluations and seconds it took and the evaluations its growth took; with ``history="trigen.jsonl"`` it is also written to a file, a line per search. ``trigen.hierarchy`` counts how many triclusters found hold each gene, condition and time.

When a search evaluates nothing that has not been found already, which only happens in a small search space, it adds no tricluster and says so in the log: TriGen then returns fewer triclusters than asked for.

The order of the genes
----------------------

The search is not blind to the order of the genes in the cube: the initial population draws blocks of consecutive positions, and MSL, with the default views, reads the slopes along the genes in the order they have. When that order means something, such as positions along a chromosome, that is what is wanted. When it does not, as in most expression data, where the genes are often listed by name, ``shuffle_genes=True`` makes each run search the genes in an order of its own, drawn from the seeded generator, and gives back the triclusters with the positions of the cube:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import plant, recovery

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100,
                    min_sizes=(5, 2, 3), max_sizes=(30, 6, 8), shuffle_genes=True, seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])     # [(18, 4, 5), (15, 2, 3)]
    print(found[0].genes[:5])                            # (2, 10, 20, 28, 30)
    print(round(recovery(found, planted), 3))            # 0.557

The fitness and the terms of each tricluster are those of the order its run saw; with ``views="time"`` they do not depend on the order. A seed reproduces the order, and a saved run keeps the option, so ``TriGenResult.trigen(cube)`` runs it again in the same order.

Dimensions with order
---------------------

For TriGen, by default, no dimension has an order: a tricluster holds any genes, any conditions and any times. When the positions of a dimension do have one, as the times of a time series do, ``ordered`` says so, and a tricluster then holds a **window** there, consecutive positions: the searches draw, cross, mutate and grow windows in that dimension, the hierarchy starts the later searches from the window least explored, and the model of chance of the significance draws windows. ``plant`` takes the same argument, to plant triclusters on windows:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import plant, recovery

    cube, planted = plant((100, 6, 12), [(20, 3, 5), (15, 3, 4)], noise=0.05, seed=0, ordered=("times",))
    print([tricluster.times for tricluster in planted])        # [(2, 3, 4, 5, 6), (4, 5, 6, 7)]

    trigen = TriGen(cube, n_triclusters=2, generations=30, population_size=80, min_sizes=(5, 2, 3),
                    max_sizes=(30, 6, 8), scoring="significance", ordered=("times",), seed=0)
    found = trigen.run()
    print([tricluster.times for tricluster in found])          # [(2, 3, 4, 5, 6), (2, 3, 4, 5, 6)]
    print(round(recovery(found, planted), 3))                  # 0.5

A window holds consecutive positions only: when the same genes and conditions follow a pattern in two stretches of time apart, a tricluster that holds both also holds the times between them. Without an order, the two stretches can be one tricluster on their times alone. A saved run keeps the dimensions with order.

Prisms
------

In a series of images, the first two dimensions are the rows and the columns of a plane and the third is the time, and a pattern is often a region of irregular outline through a stretch of time, such as a field through a season. A cube, even with the three dimensions in order, can only hold a rectangle of it. With ``shape="prism"`` a tricluster is a **prism**: a surface of the plane, pixels that are one piece through their neighbors, the 4 that share a side with each or, with ``neighborhood=8``, the 8 that share a side or a corner, held along a window of the times. The prism needs the three dimensions in ``ordered``, and it is measured by its pixels as series along its window, with ``views="time"`` and the quality ``"msl"`` or ``"lsl"``. ``max_sizes`` bound the extent of its surface in the rows and the columns, and ``pixels`` its number of pixels. :py:func:`~metagen.triclustering.plant_prisms` plants prisms of random outline:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import plant_prisms, recovery

    cube, planted = plant_prisms((30, 30, 12), [(40, 6), (25, 5)], noise=0.05, seed=0)
    print([tricluster.n_cells for tricluster in planted])      # [240, 125]

    trigen = TriGen(cube, shape="prism", ordered=("genes", "conditions", "times"), views="time",
                    n_triclusters=2, generations=20, population_size=60, min_sizes=(2, 2, 3),
                    max_sizes=(15, 15, 8), pixels=(4, 80), scoring="significance", seed=0)
    found = trigen.run()
    print(round(recovery(found, planted), 3))                  # 0.63

Prisms are searched with ``scoring="significance"``, as in the example: its model of chance draws random prisms of the same pixels and times, so a surface scores by how unlikely its coherence is whatever its outline. The weighted fitness also takes a prism, and sizes it in the genes and the conditions by the side of a square of the area of its surface.

A search represents a prism by a seed pixel, steps of growth and a window: the surface starts at the seed, and each step adds one of the free neighbors around it, so every individual of a search is a prism and the crossover and the mutation of the genetic algorithm apply as they are. Growing adds a pixel of the frontier or a time at either end of the window, and, with ``pruning``, removes a pixel of the border that leaves the surface one piece, or a time at an end. Each pixel is a step of what a search represents, so ``pixels`` well below the size of the plane keep the searches light. A saved run keeps its prisms by their cells, and the shape, the neighborhood and the pixels with its configuration.

Counting what was found by cells
--------------------------------

What the triclusters found have taken can be counted by coordinates, dimension by dimension, or by cells. The searches after the first start, by default, from the conditions and times the triclusters found hold least and, in them, from the genes with the fewest cells held, ``hierarchy="cells"``; with ``hierarchy="coordinates"`` they start from the genes, conditions and times held least in the whole cube. The overlap of the weighted fitness is, by default, the share of the genes, of the conditions and of the times of a tricluster that the triclusters found hold, so that a tricluster with the genes of one found, in other times, counts as a repeat although it shares none of its cells; ``overlap="cells"`` makes it the share of the cells of a tricluster that a tricluster found holds, weighted by the three overlap weights together:

.. code-block:: python

    from metagen.metaheuristics import TriclusterFitness, TriGen
    from metagen.triclustering import Tricluster, plant

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    found = Tricluster(range(20), range(4), range(6))
    later = Tricluster(range(20), range(4), range(6, 12))   # the same genes and conditions, other times
    print(TriclusterFitness(cube, found=[found]).terms(later)["overlap_genes"])               # 1.0
    print(TriclusterFitness(cube, found=[found], overlap="cells").cell_overlap(later))        # 0.0

    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100, min_sizes=(5, 2, 3),
                    max_sizes=(30, 6, 8), overlap="cells", hierarchy="cells", seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])        # [(16, 4, 5), (23, 3, 3)]
    # How many triclusters found hold each cell.
    print(int(trigen.hierarchy.cells.sum()))                 # 527

The significance already compares the cells two triclusters share, so ``overlap`` leaves it as it is; ``hierarchy`` applies to both scorings. A saved run keeps both options.

Scoring by significance
-----------------------

The weighted fitness rewards size with a weight of its own, and the largest sizes keep the triclusters to the scale of the patterns sought. With ``scoring="significance"``, the fitness instead asks how unlikely the coherence of a tricluster is among random triclusters of its same size in the cube: its significance, :math:`z`, the number of deviations its quality is better than theirs. There is no size term. The whole of a pattern scores higher than any part of it, because the same coherence over less data is likelier by chance, and coordinates that do not follow the pattern bring its quality back towards that of chance, so the best score lies at the edge of the pattern. Noise and the whole cube score about 0. Only the significance not already found counts: the tricluster scores its significance less the largest significance of the coordinates it shares with a tricluster found, so repeating one found, even with other coordinates added, scores no better than 0, while a new pattern that only shares some conditions or times with one found keeps its whole score.

With the significance, growing by the fitness also prunes by default (``pruning``): each step may remove a gene, condition or time as well as add one, so a tricluster that a search returns across two patterns can shed what does not belong. The smallest and largest sizes still bound every tricluster, whichever the scoring, and here the largest can be left at the size of the cube:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import cell_precision, plant, recovery, relevance

    cube, planted = plant((100, 10, 12), [(20, 4, 6), (15, 3, 5)], pattern="additive", noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=50, population_size=100, min_sizes=(5, 2, 3),
                    scoring="significance", seed=0)
    found = trigen.run()
    print([tricluster.size for tricluster in found])                # [(20, 4, 6), (15, 3, 5)]
    print([round(record["terms"]["z"], 1) for record in trigen.history])   # [40.2, 29.5]
    print(round(relevance(found, planted, cell_precision), 3))      # 1.0
    print(round(recovery(found, planted), 3))                       # 1.0

The significance measures how unlikely a coherence is, not how strong: on data where many genes follow a broad, weak common trend, it can favor large triclusters of moderate coherence over small, tightly coherent ones. The model of chance is fitted at the start of each run from random triclusters, drawn with MetaGen's generator, so a seed reproduces it; it takes about two thousand evaluations of the quality measure. It follows MSL, the default quality, closely; with MSR3D it can be off by a few deviations at some sizes, so MSL is the measure to use with the significance.

Stopping by coverage
--------------------

By default a run makes ``n_triclusters`` searches. With ``stop="coverage"`` it goes on until its triclusters hold the ``coverage`` share of the genes, held by a tricluster in any conditions and times, or, with a prism, of the pixels of the plane, with ``cover="pixels"``, the default for a prism. ``n_triclusters`` is then the most it makes, and a search that finds nothing new also ends it. What no tricluster holds is the residue: the data no pattern found takes in. With the significance, ``noise_rule`` leaves out a tricluster found that is no better than noise: ``"null"`` when its significance not already found is no higher than the highest a short run of three searches finds in :py:func:`~metagen.triclustering.null_cube` of the data, made at the start, and ``"decline"`` when it is below ``decline`` times that of the most significant found so far. The run ends when ``patience`` triclusters in a row are left out, 2 by default; one left out still counts as found, so the next search looks elsewhere. ``"null"`` is the rule that tells data with no pattern apart, and it relies on the patterns of the data standing out from its null cube: where they do not, the coverage or ``n_triclusters`` end the run. ``"decline"`` only compares the triclusters with one another, so it suits data known to hold patterns. ``trigen.stop_reason`` says why the run ended, ``"coverage"``, ``"maximum"``, ``"exhausted"`` or ``"noise"``, and ``trigen.covered`` the share it holds:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import plant

    cube, planted = plant((100, 8, 10), [(20, 3, 5), (20, 4, 4), (20, 3, 6)], noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=10, generations=30, population_size=60, min_sizes=(5, 2, 3),
                    scoring="significance", stop="coverage", coverage=0.6, noise_rule="null", seed=0)
    found = trigen.run()
    print(len(found), trigen.stop_reason, round(trigen.covered, 2))      # 3 coverage 0.6

The triclusters still share genes as the scoring allows. With ``disjoint=True`` no two share a gene: each search works on the genes no tricluster holds yet, with a model of chance of its own, the genes of a tricluster left out go to the residue, and a run also ends, ``"exhausted"``, when fewer genes are left than the smallest size. It applies to either way of stopping. With ``disjoint=True`` the noise rule is what keeps noise out: without one, the run hands every gene it can to a tricluster.

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import plant

    cube, planted = plant((100, 8, 10), [(20, 3, 5), (20, 4, 4), (20, 3, 6)], noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=10, generations=30, population_size=60, min_sizes=(5, 2, 3),
                    scoring="significance", stop="coverage", noise_rule="null", disjoint=True, seed=0)
    found = trigen.run()
    genes = [set(tricluster.genes) for tricluster in found]
    print(len(found), trigen.stop_reason, sum(map(len, genes)) == len(set().union(*genes)))   # 3 noise True

With a prism, ``disjoint=True`` keeps the pixels apart instead, at any time: the prisms segment the plane. A prism then grows only over the pixels no prism holds yet and starts in a free piece of the plane that holds its fewest pixels, and the run ends, ``"exhausted"``, when no piece does. The model of chance is fitted again over the free pixels once they have fallen a tenth since it last was:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.metaheuristics.trigen.shape import prism_parts
    from metagen.triclustering import plant_prisms

    cube, planted = plant_prisms((24, 24, 10), [(60, 5), (45, 4), (50, 6)], noise=0.05, seed=3)
    trigen = TriGen(cube, shape="prism", ordered=("genes", "conditions", "times"), views="time", n_triclusters=30,
                    generations=10, population_size=30, min_sizes=(2, 2, 3), max_sizes=(12, 12, 8), pixels=(6, 80),
                    scoring="significance", stop="coverage", disjoint=True, seed=0)
    found = trigen.run()
    surfaces = [set(prism_parts(prism)[0]) for prism in found]
    print(trigen.stop_reason, sum(map(len, surfaces)) == len(set().union(*surfaces)))   # exhausted True

A saved run keeps the options, why it ended, the share it held, the significance of each tricluster left out and, with ``noise_rule="null"``, the threshold it found in the null cube.

Saving a run
------------

``trigen.save(path)`` writes the result of a run to a JSON file: the triclusters, with the positions and the names of their genes, conditions and times and the terms of their fitness; the configuration and the seed; the versions, the platform and the date; the progress, the evaluations and the seconds of each search; whether the run reached its end; and a fingerprint of the data. Names that are neither text nor numbers, such as dates, are kept as their text. The file says the name and the version of its format, and holds neither the data nor a path to them, so it can be moved and read on its own, from any language.

:py:class:`~metagen.metaheuristics.TriGenResult` reads it back. ``matches(cube)`` tells whether a cube holds the data the run worked on, by its fingerprint, and ``trigen(cube)`` builds a TriGen with the configuration of the run, to run it again. ``to_csv(path)`` writes the triclusters as a long table, a row per coordinate with its tricluster, its dimension, its position and its name.

.. code-block:: python

    from metagen.metaheuristics import TriGen, TriGenResult
    from metagen.triclustering import Cube, plant

    data, planted = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
    cube = Cube(data.values, genes=[f"gene{index}" for index in range(60)])
    trigen = TriGen(cube, n_triclusters=2, generations=10, population_size=20,
                    min_sizes=(4, 2, 3), max_sizes=(15, 4, 6), seed=0)
    trigen.run()
    trigen.save("run.json", label="planted example")

    result = TriGenResult.load("run.json")
    print(result.triclusters == trigen.triclusters)            # True
    print(result.data["label"], result.matches(cube))          # planted example True
    print(result.configuration["generations"], result.configuration["seed"])   # 10 0
    print(result.names[0]["genes"][:3])                        # ['gene0', 'gene1', 'gene6']
    print(result.trigen(cube).run() == result.triclusters)     # True
    result.to_csv("triclusters.csv")

Quality and enrichment measures are computed from a result, not kept in it: the file of a run stays the same however it is evaluated afterwards. The ``history`` file, a line per search as it ends, remains the record to look at while a long run is under way.

``trigen.report(path)`` writes a report of the run, an HTML page that holds everything in it or, when ``path`` ends in ``.pdf``, a PDF, and next to it the triclusters as a table of coordinates, as ``to_csv`` writes it. It shows the data and the options of the run, what it spent and why it ended, a table of the triclusters with their sizes, fitness, terms and cost, the best fitness of each search by generation, the share of the genes or pixels held as the triclusters were found, the share of the cells of each tricluster another one also holds, and the values of the first ``detailed`` triclusters, 10 by default: for a cube, three views, a panel per time with a line per condition along the genes, a panel per condition with a line per time along the genes, and a panel per condition with a line per gene along the times; for prisms, a map of the plane with every surface and the series of the pixels of each prism along its window. Given the cube, the table also holds the TRIQ of each tricluster of a cube and its graphical, Pearson and Spearman qualities, computed with the ``views`` and ``flat_profiles`` of the run (see :doc:`../triclustering/index`). ``result.report(path, cube)`` does the same from a saved result, and without the cube leaves the values out. The figures need matplotlib, which ``pip install pymetagen-datalabupo[report]`` installs.

.. code-block:: python

    from metagen.metaheuristics import TriGen, TriGenResult
    from metagen.triclustering import plant

    cube, planted = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
    trigen = TriGen(cube, n_triclusters=2, generations=10, population_size=20,
                    min_sizes=(4, 2, 3), max_sizes=(15, 4, 6), seed=0)
    trigen.run()
    print(trigen.report("run.html", label="planted example"))         # run.html
    trigen.save("run.json")
    print(TriGenResult.load("run.json").report("run.pdf", cube))      # run.pdf

With ``enrichment``, an engine such as :py:class:`~metagen.triclustering.GProfiler` or :py:class:`~metagen.triclustering.LocalGO` (see :doc:`../triclustering/index`), or the enrichment of each tricluster already computed, the report also shows the biological enrichment of the genes of each tricluster of cubes: its purity, its BIOQ, its significant terms and, with the cube, its TRIQ with BIOQ in the table; the most significant terms of every tricluster side by side, a dot where a term is significant, its size the share of the genes it annotates and its color how significant it is; and, for each tricluster drawn, its terms by the share of its genes they annotate. With an engine that gives the genes of each term, as LocalGO does, it also shows which of its genes each term annotates and, with networkx installed, a map of its terms joined by the genes they share. Next to the report go the significant terms of every tricluster, with their genes, as a CSV table.

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import Cube, LocalGO, plant

    data, (planted,) = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
    cube = Cube(data.values, genes=[f"gene{g}" for g in range(60)])

    # A small ontology and annotation file, in the formats of geneontology.org: the planted
    # genes share a function, and half of all the genes another one.
    with open("ontology.obo", "w") as handle:
        handle.write("format-version: 1.2\ndata-version: example\n\n")
        for identifier, name in (("GO:0000001", "planted function"), ("GO:0000002", "common function")):
            handle.write(f"[Term]\nid: {identifier}\nname: {name}\n\n")
    with open("genes.gaf", "w") as handle:
        handle.write("!gaf-version: 2.2\n")
        for gene in range(60):
            for term in ["GO:0000001"] * (gene in planted.genes) + ["GO:0000002"] * (gene % 2 == 0):
                handle.write("\t".join(["DB", f"ID{gene}", f"gene{gene}", "involved_in", term, "REF", "IEA",
                                        "", "P", "", "", "protein", "taxon:1", "20260101", "DB"]) + "\n")

    trigen = TriGen(cube, n_triclusters=2, generations=10, population_size=20,
                    min_sizes=(4, 2, 3), max_sizes=(15, 4, 6), seed=0)
    trigen.run()
    print(trigen.report("run.html", enrichment=LocalGO("ontology.obo", "genes.gaf")))   # run.html
    print(open("run_enrichment.csv").readlines()[1].split(",")[2])                       # planted function

Triclusters that recur
----------------------

Runs with different seeds may find different triclusters. :py:func:`~metagen.triclustering.stability` tells, for each tricluster of a set of runs on the same data, how much it recurs in the others: the share of the pairs of its genes that share a tricluster in each of the other runs, on average, what that share would be by chance, and its **core**, the genes that turn up together with it in at least half of the other runs. :py:func:`~metagen.triclustering.null_cube` shuffles the rows of a cube apart in each condition, so that no group of genes moves together across conditions but by chance; runs on such cubes show how much triclusters recur where there is nothing to find, which gives a threshold:

.. code-block:: python

    from metagen.metaheuristics import TriGen
    from metagen.triclustering import null_cube, plant, stability

    cube, planted = plant((80, 6, 8), [(20, 4, 6)], noise=0.1, seed=0)
    settings = dict(n_triclusters=3, generations=15, population_size=30, min_sizes=(5, 2, 3),
                    max_sizes=(30, 6, 8), shuffle_genes=True)
    runs = [TriGen(cube, seed=seed, **settings) for seed in range(4)]
    nulls = [TriGen(null_cube(cube, seed=seed), seed=seed, **settings) for seed in range(4)]
    for trigen in runs + nulls:
        trigen.run()

    real = stability([trigen.result() for trigen in runs])
    threshold = max(found.stability for run in stability([trigen.result() for trigen in nulls]) for found in run)
    print([found.stability > threshold for found in real[0]])          # [True, True, False]
    core = real[0][0].core
    print(len(core), len(set(core) & set(planted[0].genes)))           # 21 19

The runs are compared by the names of the genes, so they may search the genes in orders of their own, as ``shuffle_genes`` does. ``stability`` also takes the runs as lists of the gene names of their triclusters, with the number of genes of the data as ``population``.

Reference
---------

.. autoclass:: metagen.metaheuristics.TriGen
    :members: run, save, result, report, configuration

.. autoclass:: metagen.metaheuristics.TriGenResult
    :members: load, save, matches, trigen, to_csv, report, from_run

.. autofunction:: metagen.metaheuristics.trigen.report.trigen_report

.. autoclass:: metagen.metaheuristics.TriclusterFitness
    :members: evaluate, terms, quality, significance, fit_chance

.. autoclass:: metagen.metaheuristics.trigen.trigen_ga.TriGenGA
    :members: initialize, iterate
    :show-inheritance:
