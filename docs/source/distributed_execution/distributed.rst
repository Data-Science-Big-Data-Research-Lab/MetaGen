.. include:: ../aliases.rst

=======================
Distributed Execution
=======================

|metagen| provides support for distributed execution using **Ray**, enabling the parallel evaluation of solutions in metaheuristic algorithms. This functionality allows users to scale optimization processes efficiently across multiple CPU cores or even multiple machines in a cluster.

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
When distribution is enabled, |metagen| leverages **Ray** to parallelize key operations such as:

- **Solution Initialization:**
  The initial population of solutions is distributed across available computing resources.
- **Evaluation of Solutions:**
  The fitness function is executed in parallel for multiple individuals, reducing computation time.
- **Metaheuristic Iterations:**
  Selection, crossover, mutation, and other algorithmic operations are processed concurrently across different CPU cores.

The execution flow remains the same as in the sequential case, but internally, computation-heavy tasks are dispatched to worker processes managed by Ray.

Resource Allocation and Load Balancing
--------------------------------------
|metagen| automatically distributes the computational load using **Ray's dynamic task scheduling**. The number of available CPUs is detected at runtime, and tasks are divided among them to maximize efficiency.

- The distribution strategy ensures that workload is **balanced** across all available cores.
- Logging information is provided at each iteration to indicate the number of active CPUs and the assigned workload.
- If no distributed resources are available, execution falls back to sequential processing.

Example log output during distributed execution:

.. code-block:: text

    [ITERATION 10] Distributing with 8 CPUs -- [12, 12, 13, 13, 12, 12, 13, 13]
    [ITERATION 10] Best solution fitness: 0.0314

Limitations and Considerations
------------------------------
- Distributed execution is beneficial **only for computationally expensive problems** where evaluating solutions is the primary bottleneck.
- The overhead of launching distributed tasks may **not be efficient for very small populations** or extremely fast fitness evaluations.
- Running Ray in a **multi-node cluster** requires additional setup beyond the default single-machine execution.

Shutting Down Ray
-----------------
At the end of execution, |metagen| ensures that **Ray is properly shut down** to release resources. If Ray was initialized at runtime, it is automatically terminated when the algorithm finishes.

If needed, users can manually shut down Ray by calling:

.. code-block:: python

    import ray
    ray.shutdown()

By leveraging distributed execution, |metagen| allows users to significantly speed up metaheuristic optimization, making it well-suited for large-scale and computationally intensive problems.
