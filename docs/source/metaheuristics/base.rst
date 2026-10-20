.. include:: ../aliases.rst

Base Metaheuristic
========================

.. autoclass:: metagen.metaheuristics.base.Metaheuristic
    :members:
    :show-inheritance:


Racing
========================

A fitness function that yields the value of each of its steps can be evaluated with racing,
which stops a candidate as soon as it is significantly worse than the population; see
:doc:`../choosing/index`.

.. autoclass:: metagen.metaheuristics.racing.Racing
    :members: eliminates




Reproducibility
========================

The package keeps its own random generators, apart from Python's global ``random`` and from
``numpy.random``. ``Metaheuristic(..., seed=N)`` seeds them at the start of ``run()``; code that
extends |metagen| must draw from them for the seed to control it.

.. autofunction:: metagen.framework.rng.set_seed

.. autofunction:: metagen.framework.rng.get_rng

.. autofunction:: metagen.framework.rng.get_numpy_rng
