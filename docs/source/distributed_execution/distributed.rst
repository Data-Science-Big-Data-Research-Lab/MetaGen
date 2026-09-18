.. include:: ../aliases.rst

=======================
Distributed Execution
=======================

|metagen| can run its metaheuristics on **Ray**, splitting the population into one slice per CPU and running each slice in its own worker, on a single machine or on a cluster. How the slices make up the next population is the **distribution model**, and there are two: read *How Distributed Execution Works* before enabling it.

Enabling Distributed Execution
------------------------------
To use distributed execution, the ``distributed`` parameter must be set to ``True`` when initializing a metaheuristic. Additionally, the **Ray** package must be installed. If Ray is not available, the metaheuristic will raise an error when attempting to execute in distributed mode.

To install Ray, run:

.. code-block:: bash

    pip install pymetagen-datalabupo[distributed]

Example usage:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import HillClimbing

    my_domain = Domain()
    my_domain.define_real("x", -5.0, 5.0)
    my_domain.define_real("y", -5.0, 5.0)

    def my_fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2

    metaheuristic = HillClimbing(my_domain, my_fitness_function,
                                 population_size=100,
                                 distributed=True)                      # the "global" model
    best_solution = metaheuristic.run()

    islands = HillClimbing(my_domain, my_fitness_function,
                           population_size=100,
                           distributed=True,
                           distribution_model="islands")
    best_solution = islands.run()

How Distributed Execution Works
-------------------------------
At every iteration the population is split into **one slice per CPU of the Ray cluster**,
each slice is handed to a worker that runs the whole ``iterate`` step **on that slice
alone**, and the driver keeps the best of what comes back. The initialization works the
same way: each worker builds its share of the initial population from scratch. What
happens to the slices afterwards is the ``distribution_model``.

**The global model** (``distribution_model="global"``, the default). Before the cut the
driver **shuffles** the population, so that every iteration the slices are made of
different individuals and they mix across workers. What each worker returns are the
**candidates** its slice produced: children in the genetic algorithms, mutants in
``RandomSearch``, neighbors in ``HillClimbing`` and ``TabuSearch``, a model's proposals
in TPE. Once every slice is back, the driver **selects the next population out of the
parents it sent and every candidate returned, all workers considered**: the
``population_size`` best by fitness, without duplicates, a (μ+λ) survivor selection.
An algorithm whose population is not a set of competing individuals overrides that
step (``Metaheuristic.select_survivors``): TPE merges the histories every slice
returned, and ``HillClimbing``, ``TabuSearch`` and ``SA`` keep the fresh candidates only.
Two things follow:

- **The budget of an iteration does not grow with the number of CPUs.** Each worker
  produces as many candidates as individuals it received, and TPE shares its candidate
  pool among the slices, so ``HillClimbing``, ``TabuSearch`` and TPE cost exactly what
  they cost sequentially. ``GA`` and ``Memetic`` breed pairs, so a slice with an odd
  number of individuals breeds one child fewer; ``RandomSearch`` keeps one elite copy
  per slice and mutates one individual fewer per slice; ``SSGA`` breeds its two
  children in every slice. For example, with a population of 10 over 15 iterations on
  two CPUs, a run of ``GA`` makes 160 evaluations sequentially and 130 distributed,
  ``RandomSearch`` 145 and 130, and ``SSGA`` 40 and 70.
- **The whole population competes.** Every individual can meet every other across
  iterations, which a population split into fixed islands cannot offer.
- **Runs are reproducible.** Two distributed runs with the same ``seed`` on the same
  number of CPUs reproduce each other, since the shuffle and every worker task are
  seeded from the driver's generator.

**The island model** (``distribution_model="islands"``). The slices come back with the
size they left with and are concatenated in order, so the next split hands **the same
individuals to the same worker every iteration: the islands never exchange
individuals**, and the only thing they share is the best solution the driver keeps,
which the algorithms that start from the best read from there. The algorithm each
worker runs is the algorithm on a smaller population: with two CPUs, a genetic algorithm
of 6 individuals is two independent genetic algorithms of 3 for the whole run, TPE
builds its model over its slice, and ``RandomSearch`` keeps one elite per slice. **The
number of evaluations changes with the number of CPUs**: for example, with a
population of 6 over 3 iterations on two CPUs, a run of ``GA`` makes 24 evaluations
sequentially and 18 on islands, and ``SSGA`` 12 and 18; ``TPE`` spends more on islands,
because every island evaluates a whole candidate pool.

``SA`` works on a population of one, so it gains nothing from either model.

Resource Allocation
-------------------
The workload is split into as many slices as **CPUs the cluster has**, read once per
iteration from ``ray.cluster_resources()``. Logging at each iteration shows the CPU
count and the split:

.. code-block:: text

    [ITERATION 10] Distributing with 8 CPUs -- [12, 12, 13, 13, 12, 12, 13, 13]
    [ITERATION 10] Best solution fitness: 0.0314

There is no fallback to sequential execution: with ``distributed=True`` and Ray not
installed, ``run()`` raises ``ImportError``.

Limitations and Considerations
------------------------------
- Distributed execution pays off **only for computationally expensive fitness functions**:
  Ray serializes a copy of the algorithm and the slice for every task, and with a fitness of
  a few milliseconds that overhead dominates.
- To compare runs, use the same ``seed`` and the same number of CPUs.
- Running Ray in a **multi-node cluster** requires additional setup beyond the default
  single-machine execution.

Shutting Down Ray
-----------------
At the end of execution, |metagen| ensures that **Ray is properly shut down** to release resources. If Ray was initialized at runtime, it is automatically terminated when the algorithm finishes.

If needed, users can manually shut down Ray by calling:

.. code-block:: python

    import ray
    ray.shutdown()

By leveraging distributed execution, |metagen| allows users to significantly speed up metaheuristic optimization, making it well-suited for large-scale and computationally intensive problems.
