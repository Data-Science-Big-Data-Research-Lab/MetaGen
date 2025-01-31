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

=======================================
Special Cases in Distributed Execution
=======================================

While most metaheuristics in |metagen| follow a standard distributed execution model using Ray, some algorithms require additional considerations due to their specific computational structures. This section details two specialized cases:

1. **Memetic Algorithm**: Allows fine-grained control over distribution levels.
2. **Distributed CVOA**: Implements a complex epidemic-based optimization model with strain-level parallelism.

Memetic Algorithm and Distribution Levels
-----------------------------------------

The **Memetic Algorithm** extends standard evolutionary strategies by incorporating **local search** to refine solutions within each generation. In the distributed context, it introduces the concept of **distribution levels**, which control how computational tasks are assigned across available resources.

Enabling Distribution in Memetic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When initializing the `Memetic` algorithm, users can specify the ``distributed`` parameter and an additional **``distribution_level``**:

.. code-block:: python

    from metagen.metaheuristics.mm import Memetic

    memetic = Memetic(domain=my_domain,
                      fitness_function=my_fitness_function,
                      population_size=100,
                      mutation_rate=0.1,
                      neighbor_population_size=10,
                      alteration_limit=1.0,
                      distributed=True,
                      distribution_level=1)

    best_solution = memetic.run()

Understanding Distribution Levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``distribution_level`` parameter defines how computation is parallelized:

- **Level 0 (default)** – No distributed execution; all computations run sequentially.
- **Level 1** – Distributes **local search operations** (e.g., mutation and refinement of solutions) across available CPU cores.
- **Level 2+** – Extends distribution to additional genetic operations, further increasing parallelism.

This flexibility allows users to **balance overhead vs. performance gain**, ensuring that distribution is beneficial rather than introducing unnecessary communication costs.

When to Use Distribution in Memetic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Recommended for large populations where local search is computationally expensive.
- Not ideal for small-scale optimizations where overhead may outweigh speed improvements.

---

Distributed CVOA: Multi-Strain Parallelization
----------------------------------------------

The **Coronavirus Optimization Algorithm (CVOA)** in MetaGen follows a unique **epidemic-inspired** optimization model. Its distributed version extends this by allowing **multi-strain execution**, where different "viral strains" explore the search space in parallel.

How CVOA Executes in a Distributed Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Unlike traditional metaheuristics, **Distributed CVOA** manages a global state using **Ray actors**. Each strain operates independently while interacting with a shared environment.

Launching Distributed CVOA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Users must initialize **Ray** and execute multiple strains concurrently using the `distributed_cvoa_launcher` function:

.. code-block:: python

    from metagen.metaheuristics.cvoa import distributed_cvoa_launcher

    best_solution = distributed_cvoa_launcher(strains=my_strains,
                                              domain=my_domain,
                                              fitness_function=my_fitness_function,
                                              update_isolated=True,
                                              log_dir="logs/DCVOA")

Key Features of Distributed CVOA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Strain-Based Parallelism**
  Each strain represents an independent execution of CVOA, enabling **multiple parallel searches**.
- **Remote Pandemic State Management**
  A global state tracks recovered, dead, and infected individuals across all strains.
- **Ray-Based Worker Management**
  Tasks such as **infection spreading, mutation, and selection** are dynamically assigned to available computing resources.

Example Log Output
^^^^^^^^^^^^^^^^^^

During execution, logs provide real-time insight into the epidemic progression:

.. code-block:: text

    [Strain 1] Best individual fitness: 0.0291
    [Strain 2] Best individual fitness: 0.0312
    Pandemic Report: Recovered = 152, Deaths = 21, Best Individual = Solution(0.0291)
    Execution time: 00:02:14

When to Use Distributed CVOA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **For large-scale optimizations** requiring complex exploration strategies.
- **When multiple independent searches** need to run in parallel.

---

Comparison of Distributed Execution Approaches
----------------------------------------------

+----------------+------------------------------+---------------------------------+
| Metaheuristic  | Distribution Strategy        | Recommended Use Cases           |
+================+==============================+=================================+
| Memetic        | Selective distribution based | Large populations, local search |
|                | on ``distribution_level``    | is computationally expensive    |
+----------------+------------------------------+---------------------------------+
| CVOA           | Strain-based parallelization | Large-scale optimization with   |
|                | with a global pandemic state | epidemic-inspired search models |
+----------------+------------------------------+---------------------------------+

By leveraging these specialized distributed execution methods, |metagen| allows users to optimize metaheuristics efficiently, ensuring that distribution aligns with algorithmic needs.