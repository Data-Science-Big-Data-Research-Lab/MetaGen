.. include:: ../aliases.rst

=======================
Performance tracking
=======================

|metagen| integrates with **TensorBoard**: every metaheuristic takes a ``log_dir`` parameter, and when it is given the run writes its metrics there, so that the evolution of the algorithm can be followed graphically, while it runs or afterwards, and several runs or metaheuristics can be compared side by side.

Enabling it with ``log_dir``
----------------------------

Logging is **off by default**: ``log_dir=None`` writes nothing, whether or not TensorBoard is installed. Pass a directory to turn it on:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import RandomSearch

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)

    def fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2

    best_solution = RandomSearch(domain, fitness_function, log_dir="logs/random_search").run()

Each run writes to its own timestamped subdirectory of ``log_dir``, so several runs can share one directory and be compared in the dashboard. The CVOA launchers take the same parameter.

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

Console and file logs
---------------------

Apart from TensorBoard, the package reports its progress through Python's ``logging``. It is
silent by default; two functions of ``metagen.logging.metagen_logger`` turn it on:

.. code-block:: python

    import logging
    from metagen.logging.metagen_logger import (set_metagen_logger_level,
                                                set_metagen_logger_file_handler)

    set_metagen_logger_level(logging.INFO)             # print to the console from INFO up
    set_metagen_logger_file_handler("metagen_logs")    # and write a log file in that directory

Both can be called at any point before ``run()``, and calling them again does not duplicate the output.
