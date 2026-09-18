Tree-structured Parzen Estimator (TPE)
=======================================

.. autoclass:: metagen.metaheuristics.TPE
    :members:
    :show-inheritance:

.. autoclass:: metagen.metaheuristics.KernelTPE
    :members:
    :show-inheritance:

Gamma schedules
---------------

Both estimators split the solutions evaluated so far into the best fraction, ``gamma``, and the
rest, and model the two sides apart. ``gamma_config`` chooses how that fraction is set in each
iteration, by the name of one of four functions:

- ``"sampled_based"``, the default: a tenth of the solutions, capped at 25 of them.
- ``"sqrt"``: a quarter of the square root of the number of solutions, capped at 25 of them.
- ``"linear"``: from ``maximum`` down to ``minimum`` along the iterations.
- ``"exponential"``: from ``maximum`` down to ``minimum`` with a decay of rate ``alpha``.

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import TPE
    from metagen.metaheuristics.gamma_schedules import GammaConfig

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)

    def fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2

    schedule = GammaConfig("linear", minimum=0.1, maximum=0.3)
    best_solution = TPE(domain, fitness_function, gamma_config=schedule, seed=0).run()

.. autoclass:: metagen.metaheuristics.gamma_schedules.GammaConfig
