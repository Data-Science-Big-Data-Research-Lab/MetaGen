.. include:: ../aliases.rst

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