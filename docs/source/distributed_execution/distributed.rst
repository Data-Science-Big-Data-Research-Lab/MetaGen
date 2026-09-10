.. include:: ../aliases.rst

=======================
Distributed Execution
=======================

|metagen| can run its metaheuristics on **Ray**, splitting the population into one slice per CPU and running each slice in its own worker, on a single machine or on a cluster. It is an island model, and it changes the search: read *How Distributed Execution Works* before enabling it.

Enabling Distributed Execution
------------------------------
To use distributed execution, the ``distributed`` parameter must be set to ``True`` when initializing a metaheuristic. Additionally, the **Ray** package must be installed. If Ray is not available, the metaheuristic will raise an error when attempting to execute in distributed mode.

To install Ray, run:

.. code-block:: bash

    pip install ray

Example usage:

.. code-block:: python

    from metagen.metaheuristics import SomeMetaheuristic

    metaheuristic = SomeMetaheuristic(domain=my_domain,
                                      fitness_function=my_fitness_function,
                                      population_size=100,
                                      distributed=True)
    best_solution = metaheuristic.run()

How Distributed Execution Works
-------------------------------
Distribution in |metagen| is an **island model**, not a parallel evaluation of the same
search. At every iteration the population is split into **one slice per CPU of the Ray
cluster**, each slice is handed to a worker that runs the whole ``iterate`` step **on that
slice alone**, and the slices that come back are concatenated for the next iteration. Since
every algorithm but TPE returns as many individuals as it received and the slices are cut in
order, **the same individuals go back to the same worker every iteration: the islands never
exchange individuals**. The only thing they share is the best solution the driver keeps,
which the algorithms that start from the best (``HillClimbing``, ``RandomSearch``'s elite)
read from there. The initialization works the same way: each worker builds its share of the
initial population from scratch.

This has consequences that the sequential mode does not have, and they are worth knowing
before switching it on:

- **The algorithm each worker runs is the algorithm on a smaller population.** With two
  CPUs, a genetic algorithm of 6 individuals is two independent genetic algorithms of 3
  for the whole run; TPE builds its model over the slice it receives, not over the
  whole history; ``RandomSearch`` keeps one elite copy **per slice**.
- **The number of evaluations changes with the number of CPUs.** Measured with the same
  configuration on two CPUs, per run: ``GA`` 24 evaluations sequential and 18
  distributed, ``SSGA`` 12 and 18, ``Memetic`` 60 and 42, ``TPE`` 132 and 204.
  ``HillClimbing`` and ``SA`` do not change.
- **The result depends on the machine.** A distributed run on 2 CPUs and one on 8 CPUs are
  different searches, and neither is comparable value by value with the sequential run.
  Two distributed runs with the same ``seed`` **on the same number of CPUs** do
  reproduce each other: every worker task is seeded from the driver's generator.
- ``SA`` works on a population of one, so it gains nothing from distribution.

If what you need is the **same search, only faster**, distribute the fitness function
yourself and keep ``distributed=False``: that keeps the algorithm, the budget and the
reproducibility of the sequential mode.

Resource Allocation
-------------------
The workload is split into as many slices as **CPUs the cluster has**, read once per
iteration from ``ray.cluster_resources()``. It is not the number of CPUs free at that
instant, which lags behind the tasks that just finished and used to send the whole
population to a single worker from the second iteration on. Logging at each iteration
shows the CPU count and the split:

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
- Since distributing changes the search, **compare distributed runs only with distributed
  runs on the same number of CPUs**.
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
