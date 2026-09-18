.. include:: ../aliases.rst

=======================
Performance tracking
=======================

|metagen| integrates with **TensorBoard**: every metaheuristic takes a ``log_dir`` parameter, and when it is given the run writes its metrics there, so that the evolution of the algorithm can be followed graphically, while it runs or afterwards, and several runs or metaheuristics can be compared side by side.

Enabling it with ``log_dir``
----------------------------

Logging is **off by default**: ``log_dir=None`` writes nothing, whether or not TensorBoard is installed. Pass a directory to turn it on:

.. code-block:: python

    from metagen.metaheuristics import RandomSearch

    best_solution = RandomSearch(domain, fitness_function, log_dir="logs/random_search").run()

A different directory per run keeps the runs apart in the dashboard. The CVOA launchers take the same parameter.

Installing TensorBoard
----------------------

The feature needs the ``tensorboard`` package, which is an optional dependency:

.. code-block:: bash

    pip install pymetagen-datalabupo[tensorboard]

If ``log_dir`` is given and TensorBoard is not installed, nothing is written and the metaheuristic runs normally.

Visualizing the metrics
-----------------------

Point TensorBoard at the directory, during the run or once it has finished:

.. code-block:: bash

    tensorboard --logdir=logs

The dashboard shows, per iteration:

- **Fitness/Best** – the best fitness found so far.
- **Fitness/Average** – the average fitness of the population, the trend of the search as a whole.
- **Fitness/Distribution** – a histogram of the population's fitness values, which shows whether it is converging or still spread out.
- **Population Size** – the number of solutions the algorithm holds.
- **Average value of each numeric variable**, and the average length of each structure, which show where in the domain the population is settling.

and, at the end of the run, a **text summary** with the best solution found.
