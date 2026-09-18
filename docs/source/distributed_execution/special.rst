.. include:: ../aliases.rst

=======================================
Special Cases in Distributed Execution
=======================================

While most metaheuristics in |metagen| follow a standard distributed execution model using Ray, some algorithms require additional considerations due to their specific computational structures. This section details two specialized cases:

1. **Memetic Algorithm**: Allows fine-grained control over distribution levels.
2. **CVOA**: An epidemic-based optimization model with strain-level parallelism.

Memetic Algorithm and Distribution Levels
-----------------------------------------

The **Memetic Algorithm** extends standard evolutionary strategies by incorporating **local search** to refine solutions within each generation. In the distributed context, it introduces the concept of **distribution levels**, which control how computational tasks are assigned across available resources.

Enabling Distribution in Memetic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When initializing the `Memetic` algorithm, users can specify the ``distributed`` parameter and an additional **``distribution_level``**:

.. code-block:: python

    from metagen.framework import Domain, RelativeAlteration
    from metagen.metaheuristics import GAConnector, Memetic

    # The memetic algorithm crosses solutions over: its domain needs the GA connector.
    my_domain = Domain(connector=GAConnector())
    my_domain.define_real("x", -5.0, 5.0)
    my_domain.define_real("y", -5.0, 5.0)

    def my_fitness_function(solution):
        return solution["x"] ** 2 + solution["y"] ** 2

    memetic = Memetic(domain=my_domain,
                      fitness_function=my_fitness_function,
                      population_size=100,
                      mutation_rate=0.1,
                      neighbor_population_size=10,
                      alteration_limit=RelativeAlteration(0.2),   # a fifth of each variable's range
                      distributed=True,
                      distribution_level=1)

    best_solution = memetic.run()

Understanding Distribution Levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``distribution_level`` parameter defines how computation is parallelized:

- **Level 0 (default)** – The local search runs sequentially inside each slice of the population. The population itself is still split across CPUs, as in every metaheuristic under ``distributed=True``.
- **Level 1** – The local search of the **two children of each crossover** is dispatched as Ray tasks, one per child.
- **Level 2** – In addition, the **neighbors of each individual** under local search are generated and evaluated in Ray tasks split across the CPUs.

``distribution_level`` is ignored, and set to 0, when ``distributed`` is ``False``.

This flexibility allows users to **balance overhead vs. performance gain**, ensuring that distribution is beneficial rather than introducing unnecessary communication costs.

When to Use Distribution in Memetic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Recommended when the fitness function is expensive, so that a task's work outweighs the cost of sending it; level 2 pays only with a large ``neighbor_population_size``.
- Not ideal for small-scale optimizations where overhead may outweigh speed improvements.

---

CVOA: Multi-Strain Parallelization
----------------------------------

The **Coronavirus Optimization Algorithm (CVOA)** in |metagen| follows an **epidemic-inspired** optimization model in which several "viral strains" explore the search space at once over a shared pandemic state. There is one strain class, |cvoa|, and two launchers: ``cvoa_launcher`` runs each strain in a thread, and ``distributed_cvoa_launcher`` runs each strain as a Ray task.

How CVOA Executes in a Distributed Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Under ``distributed_cvoa_launcher`` the global pandemic state lives in a **Ray actor**, each strain runs as a Ray task, and within a strain the spreading of the infection is dispatched as **one task per carrier**. Each strain operates independently while interacting with the shared state.

Launching Distributed CVOA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The launcher starts Ray if it is not running, and shuts it down afterwards only if it started it; a Ray runtime the user initialized, for instance to connect to a cluster, is left as it was.

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import StrainProperties
    from metagen.metaheuristics.cvoa import distributed_cvoa_launcher

    my_domain = Domain()
    my_domain.define_real("x", -5.0, 5.0)
    my_domain.define_real("y", -5.0, 5.0)

    def my_fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2

    my_strains = [StrainProperties("Strain#1", pandemic_duration=10),
                  StrainProperties("Strain#2", pandemic_duration=10, p_travel=0.2)]

    best_solution = distributed_cvoa_launcher(strains=my_strains,
                                              domain=my_domain,
                                              fitness_function=my_fitness_function,
                                              log_dir="logs/DCVOA",   # optional: TensorBoard logs
                                              seed=0)

Both launchers take ``strain_class``, which defaults to |cvoa|. Passing ``strain_class=ProbabilisticCVOA`` runs strains whose deaths, superspreaders and isolation are drawn per individual (see :ref:`choosing/index:Running CVOA`).

Key Features of Distributed CVOA
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Strain-Based Parallelism**
  Each strain represents an independent execution of CVOA, enabling **multiple parallel searches**.
- **Remote Pandemic State Management**
  A global state tracks recovered, dead, and infected individuals across all strains.
- **Ray-Based Worker Management**
  Each strain is a Ray task, and the infection spread by each carrier is another.

Example Log Output
^^^^^^^^^^^^^^^^^^

Nothing is printed unless the logger is enabled with ``set_metagen_logger_level``. With it at ``logging.INFO`` the launcher reports when the pandemic ends:

.. code-block:: python

    import logging
    from metagen.logging.metagen_logger import set_metagen_logger_level

    set_metagen_logger_level(logging.INFO)

.. code-block:: text

    ********** Results by strain **********
    [Strain#1] Best individual: F = 0.0291	{x = 0.12 , y = -0.12}
    [Strain#2] Best individual: F = 0.0312	{x = -0.10 , y = 0.15}

    ********** Best result **********
    Best individual: F = 0.0291	{x = 0.12 , y = -0.12}

    ********** Pandemic report **********
    Pandemic report: {'recovered': 152, 'deaths': 21, 'isolated': 64, 'best_individual': ...}

    ********** Performance **********
    Execution time: 0:02:14

When to Use the Distributed Launcher
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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