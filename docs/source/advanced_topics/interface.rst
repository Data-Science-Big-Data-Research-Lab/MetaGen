.. include:: ../aliases.rst

==================================
Extending the Metaheuristic Class
==================================

A metaheuristic can be any class that takes a |domain| and a fitness function and returns a |solution| (see :doc:`../metagen_in_action/duc/index`). It can also **inherit from the abstract** |metaheuristic| **class**, which provides:

- The **run loop**: warmup, initialization, iterations and the callbacks around them.
- **Elitism**: the best solution ever seen is kept even if an iteration returns a worse one.
- **Reproducibility**: a ``seed`` parameter that controls every random draw of the run.
- **Distributed execution** with Ray, under ``distributed=True``.
- **TensorBoard logging**, when a ``log_dir`` is given.

Implementing a Custom Metaheuristic
-----------------------------------

A metaheuristic that extends |metaheuristic| implements three methods:

1. ``initialize(num_solutions)`` – returns the first population and its best solution.
2. ``iterate(solutions)`` – returns the next population and the best solution of the iteration.
3. ``stopping_criterion()`` – returns ``True`` when the run must stop. It is abstract: a subclass that does not define it cannot be instantiated.

Example: a search that mutates every solution in each iteration and stops after a number of them.

.. code-block:: python

    from copy import deepcopy
    from typing import Callable, List, Tuple

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics.base import Metaheuristic
    from metagen.metaheuristics.tools import random_exploration


    class MutateAll(Metaheuristic):
        def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                     population_size: int = 10, max_iterations: int = 20, **kwargs) -> None:
            super().__init__(domain, fitness_function, population_size=population_size, **kwargs)
            self.max_iterations = max_iterations

        def initialize(self, num_solutions: int = 10) -> Tuple[List[Solution], Solution]:
            """Draw the first population at random."""
            return random_exploration(self.domain, self.fitness_function, num_solutions)

        def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
            """Mutate and evaluate every solution."""
            population = [deepcopy(solution) for solution in solutions]
            for solution in population:
                solution.mutate()
                solution.evaluate(self.fitness_function)
            return population, min(population)

        def stopping_criterion(self) -> bool:
            return self.current_iteration >= self.max_iterations


    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    best = MutateAll(domain, lambda solution: solution["x"] ** 2, seed=0).run()

Passing ``**kwargs`` through to the base class is what gives the new algorithm ``seed``, ``log_dir``, ``distributed`` and ``distribution_model`` for free.

Callbacks
---------

Four methods do nothing in the base class and may be overridden to hook into the run. They run
in the driver, also under ``distributed=True``, so they are where state that must survive an
iteration is kept:

- ``pre_execution()`` – once, before the warmup and the initialization.
- ``pre_iteration()`` – before every iteration.
- ``post_iteration()`` – after every iteration, with ``self.current_solutions`` and
  ``self.best_solution`` already updated. Call ``super().post_iteration()`` to keep the
  TensorBoard logging.
- ``post_execution()`` – once, when the stopping criterion is met.

.. code-block:: python

    class MutateAllWithTrace(MutateAll):
        def pre_execution(self) -> None:
            super().pre_execution()
            self.trace = []

        def post_iteration(self) -> None:
            super().post_iteration()
            self.trace.append(self.best_solution.get_fitness())

Two rules to keep
-----------------

- **Draw random numbers from the package's generators**, :py:func:`metagen.framework.rng.get_rng` and ``get_numpy_rng``, never from the global ``random`` or ``numpy.random``. The ``seed`` parameter seeds those generators and nothing else, so a draw made elsewhere makes the run irreproducible.
- **Do not keep state in** ``self`` **inside** ``initialize`` **or** ``iterate``. Under ``distributed=True`` Ray runs them on a serialized copy of the algorithm, and whatever they write to ``self`` stays in the worker. What the algorithm needs later must be in what the method returns, or be rebuilt in ``post_iteration``, which runs in the driver.

See :doc:`extending_framework` for a complete example that also extends the solution types, and :doc:`../distributed_execution/distributed` for what distributing a run means.
