.. include:: ../aliases.rst

=============
Triclustering
=============

A **tricluster** is a block of a three-dimensional dataset, some genes under some conditions at some times, whose values behave alike. |metagen|'s ``metagen.triclustering`` package holds the data such a search works on and the measures that tell a good tricluster from a poor one. The measures are plain functions, so they evaluate a tricluster wherever it comes from.

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

MSL and LSL range from 0 to 2π, and ``normalized=True`` divides them by 2π. Their ``views`` option chooses the views they average: ``"distinct"``, the default, takes the three views, with the genes, the times and the conditions on the X axis in turn; ``"time"`` takes only the view with the times on the X axis, the time-series view; ``"trlab"`` counts the view with the genes on the X axis twice and the one with the times once.

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
    for name, tricluster in (("planted", planted), ("elsewhere", elsewhere)):
        print(name, round(msl(cube, tricluster, views="time"), 3), round(lsl(cube, tricluster, views="time"), 3),
              round(msr3d(cube, tricluster), 4))

A slope along the genes or the conditions depends on the order they have in the cube. It means something when that order does, such as doses, temperatures or positions on a map, and ``views="time"`` leaves those views out when it does not, as with genes listed in no particular order.

Reference
---------

See :doc:`reference`.
