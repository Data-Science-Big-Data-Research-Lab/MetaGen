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
