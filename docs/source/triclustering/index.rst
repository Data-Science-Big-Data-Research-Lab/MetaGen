.. include:: ../aliases.rst

=============
Triclustering
=============

A **tricluster** is a block of a three-dimensional dataset, some genes under some conditions at some times, whose values behave alike. |metagen|'s ``metagen.triclustering`` package holds the data such a search works on, the measures and qualities that tell a good tricluster from a poor one, and synthetic data with planted triclusters to check a search against. The measures are plain functions, so they evaluate a tricluster wherever it comes from.

The data: a cube
----------------

A :py:class:`~metagen.triclustering.Cube` holds a value for every gene, condition and time, in an array whose first axis is the genes, the second the conditions and the third the times. The names are optional. Any data of that shape fits: the "genes" may be places, sensors or instances, and the "conditions", features.

.. code-block:: python

    import numpy as np
    from metagen.triclustering import Cube

    rng = np.random.default_rng(0)
    values = rng.normal(size=(40, 5, 8))
    cube = Cube(values, conditions=["c1", "c2", "c3", "c4", "c5"], times=[0, 1, 2, 4, 8, 12, 24, 48])
    print(cube)                                             # Cube(40 genes, 5 conditions, 8 times)

A cube holds no missing values: whatever stands for a gap, a zero for instance, would read as data, and a block of gaps would look like a perfect tricluster. Building a cube from values with gaps is an error that says where they are. ``Cube.without_missing`` drops, along one axis, every position that holds one, and tells which positions it keeps:

.. code-block:: python

    import numpy as np
    from metagen.triclustering import Cube

    values = np.random.default_rng(0).normal(size=(40, 5, 8))
    values[3, 1, 2] = np.nan
    cube, kept = Cube.without_missing(values)               # drops gene 3
    print(cube.shape, kept[:5])                             # (39, 5, 8) (0, 1, 2, 4, 5)

A tricluster
------------

A :py:class:`~metagen.triclustering.Tricluster` is given by the positions of its genes, conditions and times, kept sorted. It needs at least two of each.

.. code-block:: python

    import numpy as np
    from metagen.triclustering import Cube, Tricluster

    cube = Cube(np.random.default_rng(0).normal(size=(40, 5, 8)), conditions=["c1", "c2", "c3", "c4", "c5"])
    tricluster = Tricluster(genes=[12, 3, 7], conditions=[0, 2], times=[1, 2, 3, 4])
    print(tricluster.size)                                  # (3, 2, 4)
    print(cube.subcube(tricluster).shape)                   # (3, 2, 4)
    print(tricluster.labels(cube)["conditions"])            # ('c1', 'c3')

Measuring a tricluster
----------------------

The three measures are the lower the better, and zero for a perfectly coherent tricluster.

* :py:func:`~metagen.triclustering.msr3d`, the **mean squared residue**, measures how far the values are from the sum of the effects of their gene, condition and time. It is in the units of the data squared.
* :py:func:`~metagen.triclustering.msl`, the **multi-slope measure**, compares the shapes of the series in the graphical views of the tricluster: in each view one dimension goes on the X axis, another makes the series and the third the panels, and every segment of a series has an angle. Two series differ by the mean difference of the angles of their segments.
* :py:func:`~metagen.triclustering.lsl`, the **least-squares-lines measure**, does the same with the angle of the least squares line of each series.

The points of a series are taken one unit apart, whatever the names of the times. MSL and LSL range from 0 to 2π, and ``normalized=True`` divides them by 2π. Their ``views`` option chooses the views they average: ``"distinct"``, the default, takes the three views, with the genes, the times and the conditions on the X axis in turn; ``"time"`` takes only the view with the times on the X axis, the time-series view; ``"trlab"`` counts the view with the genes on the X axis twice and the one with the times once.

.. code-block:: python

    import numpy as np
    from metagen.triclustering import Cube, Tricluster, lsl, msl, msr3d

    rng = np.random.default_rng(0)
    values = rng.normal(size=(40, 5, 8))
    # Eight genes that rise alike over time under the first three conditions.
    values[:8, :3, :] = np.linspace(0, 3, 8) + rng.normal(scale=0.05, size=(8, 3, 8))
    cube = Cube(values)

    planted = Tricluster(range(8), range(3), range(8))
    elsewhere = Tricluster(range(20, 28), range(3), range(8))
    print(round(msl(cube, planted, views="time"), 3), round(msl(cube, elsewhere, views="time"), 3))  # 0.069 2.741
    print(round(lsl(cube, planted, views="time"), 3), round(lsl(cube, elsewhere, views="time"), 3))  # 0.01 3.003
    print(round(msr3d(cube, planted), 4), round(msr3d(cube, elsewhere), 4))                          # 0.0016 0.455
    print(round(msl(cube, planted), 3), round(msl(cube, elsewhere), 3))                              # 2.109 2.629

A slope along the genes or the conditions depends on the order they have in the cube. It means something when that order does, such as doses, temperatures or positions on a map, and ``views="time"`` leaves those views out when it does not, as with genes listed in no particular order. The last line of the example shows why it matters: the planted genes rise alike over time, so along the genes and the conditions their slopes are zero up to noise, and a slope a hair below zero turns into an angle of almost 2π, the largest difference there is. Those views then tell the planted block from the rest far less clearly than the time view does.

The quality of a tricluster
---------------------------

Four qualities describe a tricluster from 0 to 1, **the higher the better**, the other way round from the measures above:

* :py:func:`~metagen.triclustering.grq`, the **graphical quality**, is ``1 − MSL / 2π``, with the same ``views``.
* :py:func:`~metagen.triclustering.peq` and :py:func:`~metagen.triclustering.spq`, the **Pearson** and **Spearman qualities**, are the mean absolute correlation over every pair of profiles, a profile being the values of one gene under one condition over the times. A flat profile, the same value at every time, has no correlation with any other: its pairs are left out, and with fewer than two profiles that vary the quality is not defined (NaN). ``flat_profiles="zero"`` counts those pairs as 0 instead.
* :py:func:`~metagen.triclustering.triq`, **TRIQ**, is their weighted mean, 0.8, 0.1 and 0.1, or 0.4, 0.05, 0.05 and 0.5 when a biological quality is given as ``bioq``. A quality that is not defined is left out, with its weight.

The metaheuristics minimize: to search by TRIQ, give them ``1 − TRIQ``.

.. code-block:: python

    from metagen.triclustering import Tricluster, grq, peq, plant, spq, triq

    cube, planted = plant((100, 8, 10), [(20, 3, 5)], pattern="additive", noise=0.05, seed=0)
    target = planted[0]
    elsewhere = Tricluster([g for g in range(100) if g not in target.genes][:20], target.conditions, target.times)
    print(round(grq(cube, target, views="time"), 3), round(peq(cube, target), 3), round(spq(cube, target), 3))  # 0.991 0.995 1.0
    print(round(triq(cube, target, views="time"), 3), round(triq(cube, elsewhere, views="time"), 3))          # 0.992 0.556
    print(round(triq(cube, target, views="time", bioq=0.001), 3))                                         # 0.497

The biological quality
----------------------

For gene expression data, :py:func:`~metagen.triclustering.bioq`, the **biological quality** (BIOQ), scores how significant the functional terms of the genes of a tricluster are: an enrichment analysis tests every Gene Ontology term that annotates one of its genes against all the genes of the cube, and BIOQ scores the p-values by levels, the smaller the higher, from 0 to 1. Since most terms of an analysis are not significant, BIOQ is usually small, between :math:`10^{-5}` and :math:`10^{-3}`. Its ``bonus`` adds a fixed amount for the most significant term, and two options make it use more of its range: ``threshold``, the p-value below which every term falls in the last level, :math:`10^{-40}` by default, and ``alpha``, to score only the terms below that significance.

:py:func:`~metagen.triclustering.purity`, the **functional purity**, answers a different question: what share of the genes of the tricluster have a function in common. It is the largest share of them that a significant term annotates, beyond the share of the genes of the cube that the term annotates, from 0 to nearly 1. The p-value only decides which terms count, so the purity does not grow with the number of genes, as a score of p-values does, and it reads the same from one organism or dataset to another. Either quality can be given to TRIQ as its biological quality.

:py:func:`~metagen.triclustering.enrich` computes the analysis of a tricluster with an engine, and needs the cube to carry the names of its genes, as the organism's gene symbols:

* :py:class:`~metagen.triclustering.GProfiler`, the default choice, asks the g:Profiler web service, which keeps its annotations up to date and reports their version with every result. ``organism`` takes g:Profiler's names, such as ``"hsapiens"``, ``"mmusculus"`` or ``"scerevisiae"``, and ``cache_dir`` keeps each answer on disk so that the same analysis is not asked twice.
* :py:class:`~metagen.triclustering.LocalGO` computes the analysis without a connection, from an ontology file and an annotation file of the organism. Those files have to be kept up to date by hand: the current ones are at https://current.geneontology.org. It counts every gene of the cube as the population, where g:Profiler counts those it can annotate, so their p-values differ.
* :py:func:`~metagen.triclustering.ontologizer_table` reads a table already computed by Ontologizer.

.. code-block:: python

    from metagen.triclustering import Cube, GProfiler, bioq, enrich, plant, purity, triq

    MHC = ["HLA-DRA", "HLA-DRB1", "HLA-DRB5", "HLA-DQA1", "HLA-DQB1", "HLA-DPA1", "HLA-DPB1",
           "HLA-DMA", "HLA-DMB", "HLA-DOA", "HLA-DOB", "CD74"]
    OTHERS = ["ACTB", "GAPDH", "TP53", "EGFR", "MYC", "KRAS", "BRCA1", "BRCA2", "PTEN", "AKT1",
              "MTOR", "VEGFA", "TNF", "IL6", "INS", "ALB", "APOE", "CFTR", "HBB", "HBA1", "DMD",
              "SOD1", "APP", "MAPT", "LMNA", "FBN1", "COL1A1", "KIT"]

    # A tricluster planted on the genes of the MHC class II.
    data, (tricluster,) = plant((40, 4, 5), [(12, 3, 4)], pattern="additive", noise=0.05, seed=0)
    mhc, others = iter(MHC), iter(OTHERS)
    names = [next(mhc) if gene in tricluster.genes else next(others) for gene in range(40)]
    cube = Cube(data.values, genes=names)

    enrichment = enrich(cube, tricluster, GProfiler(organism="hsapiens"))
    print(enrichment.version)                                           # e114_eg62_p19_9dc92ac8
    best = enrichment.terms[0]
    print(best.name, f"{best.p_adjusted:.1e}")                          # MHC protein complex 1.7e-06
    print(len(enrichment.significant()))                                # 38
    quality = bioq(enrichment)
    print(round(quality, 4))                                            # 0.0008
    print(round(triq(cube, tricluster, views="time", bioq=quality), 3)) # 0.496
    # With fewer levels and only the significant terms.
    print(round(bioq(enrichment, threshold=1e-20, alpha=0.05), 4))      # 0.0338
    # The purity: 11 of its 12 genes share a term that 13 of the 40 genes of the cube have.
    print(round(purity(enrichment), 3))                                 # 0.592
    print(round(triq(cube, tricluster, views="time", bioq=purity(enrichment)), 3))   # 0.791

The figures of an analysis are those of the annotations it was run with, which g:Profiler updates: the version printed tells which. Any other engine works too: :py:func:`~metagen.triclustering.enrich` takes whatever has a method ``enrich(genes, population)`` that returns an :py:class:`~metagen.triclustering.Enrichment`.

Synthetic data with planted triclusters
---------------------------------------

To try a triclustering on data whose answer is known, :py:func:`~metagen.triclustering.plant` builds a cube of standard normal noise and plants triclusters in it: one per size ``(genes, conditions, times)``, at random positions, no two sharing a gene. Their values follow a pattern, ``"constant"``, ``"additive"`` (a mean plus an effect per gene, condition and time) or ``"multiplicative"`` (the same, multiplied), with optional noise. A ``seed`` makes the cube reproducible.

.. code-block:: python

    from metagen.triclustering import plant

    cube, planted = plant((100, 8, 10), [(20, 3, 5), (15, 4, 4)], pattern="multiplicative", noise=0.1, seed=0)
    print(cube.shape, [tricluster.size for tricluster in planted])   # (100, 8, 10) [(20, 3, 5), (15, 4, 4)]

Measuring what was recovered
----------------------------

Five similarities compare a tricluster found with one planted, from 0 to 1: :py:func:`~metagen.triclustering.cell_jaccard`, the cells they share over the cells of either; :py:func:`~metagen.triclustering.cell_recall` and :py:func:`~metagen.triclustering.cell_precision`, the share of the planted cells found and of the found cells planted; and :py:func:`~metagen.triclustering.coordinate_jaccard` and :py:func:`~metagen.triclustering.coordinate_recall`, the same over genes, conditions and times.

Over lists, :py:func:`~metagen.triclustering.recovery` takes, for each planted tricluster, its similarity to the most similar one found, and averages them: how much of what was planted has been found. :py:func:`~metagen.triclustering.relevance` does the same from the triclusters found: how much of what was found was planted. Both take the similarity to use, ``cell_jaccard`` by default.

.. code-block:: python

    from metagen.triclustering import Tricluster, cell_precision, cell_recall, plant, recovery, relevance

    cube, planted = plant((100, 8, 10), [(20, 3, 5), (15, 4, 4)], seed=0)
    first = planted[0]
    found = [Tricluster(first.genes[:10], first.conditions, first.times)]   # half of the first one
    print(recovery(found, planted), relevance(found, planted))                              # 0.25 0.5
    print(recovery(found, planted, cell_recall), relevance(found, planted, cell_precision))  # 0.25 1.0

Reference
---------

See :doc:`reference`.
