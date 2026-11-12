.. include:: ../aliases.rst

Base Metaheuristic
========================

.. autoclass:: metagen.metaheuristics.Metaheuristic
    :members:
    :show-inheritance:


Racing
========================

A fitness function that yields the value of each of its steps can be evaluated with racing,
which stops a candidate as soon as it is significantly worse than the population; see
:doc:`../choosing/index`.

.. autoclass:: metagen.metaheuristics.Racing
    :members: eliminates




Reports
========================

A report of one or more runs, an HTML page or a PDF; see :doc:`../performance_tracking/index`.

.. autofunction:: metagen.reporting.report


Reproducibility
========================

The package keeps its own random generators, apart from Python's global ``random`` and from
``numpy.random``. ``Metaheuristic(..., seed=N)`` seeds them at the start of ``run()``; code that
extends |metagen| must draw from them for the seed to control it.

Runs with a seed may also run at once in several threads, as in a comparison spread over a
``ThreadPoolExecutor``: on any thread other than the main one, a run with a seed draws from
generators of its own, seeded alike, so each gives what it gives alone. TriGen does the same.

.. code-block:: python

    from concurrent.futures import ThreadPoolExecutor

    from metagen.framework import Domain
    from metagen.metaheuristics import RandomSearch

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)

    def fitness(solution):
        return (solution["x"] - 1.0) ** 2

    def best_of(seed):
        return RandomSearch(domain, fitness, max_iterations=10, seed=seed).run().get_fitness()

    with ThreadPoolExecutor(max_workers=4) as executor:
        in_threads = list(executor.map(best_of, range(4)))
    print(in_threads == [best_of(seed) for seed in range(4)])   # True

.. autofunction:: metagen.framework.set_seed

.. autofunction:: metagen.framework.get_rng

.. autofunction:: metagen.framework.get_numpy_rng
