.. include:: ../aliases.rst

Base Metaheuristic
========================

.. autoclass:: metagen.metaheuristics.base.Metaheuristic
    :members:
    :show-inheritance:




Reproducibility
========================

The package keeps its own random generators, apart from Python's global ``random`` and from
``numpy.random``. ``Metaheuristic(..., seed=N)`` seeds them at the start of ``run()``; code that
extends |metagen| must draw from them for the seed to control it.

.. autofunction:: metagen.framework.rng.set_seed

.. autofunction:: metagen.framework.rng.get_rng

.. autofunction:: metagen.framework.rng.get_numpy_rng
