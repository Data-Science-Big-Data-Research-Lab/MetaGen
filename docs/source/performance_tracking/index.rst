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

The run history
---------------

Every metaheuristic also keeps a record of each iteration in its ``history`` attribute, with no extra package: the iteration, the evaluations and seconds spent since the start, the best fitness so far, the best, mean, standard deviation and worst fitness of the population, its size, and the values of the best solution so far. The ``history`` parameter writes the same records to a file, one JSON line per iteration, which pandas reads as a table:

.. code-block:: python

    import pandas as pd

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import RandomSearch

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)

    def fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2

    algorithm = RandomSearch(domain, fitness_function, history="runs/random_search.jsonl")
    best_solution = algorithm.run()

    table = pd.read_json("runs/random_search.jsonl", lines=True)
    table[["iteration", "evaluations", "best", "mean"]]

The file is written as the run goes, so it can be read while the run is in progress. A new run starts it again, and a run continued from a checkpoint (see :doc:`../pausing_and_resuming/index`) continues it. In a distributed run the evaluations happen in the workers and are recorded as ``None``.

Reports
-------

``report(path)`` writes a report of the last run: an HTML page that holds everything in it and opens in any browser, or, when ``path`` ends in ``.pdf``, a PDF. It shows the algorithm and its parameters, the domain, what the run spent and what stopped it, and the best solution, and draws, against the evaluations, the best fitness, the best of each iteration and the population, the value of each variable of the best solution so far, and the evaluations and seconds of each iteration. :py:func:`metagen.reporting.report` also puts several runs in one report, with their convergence side by side. The figures need matplotlib, which ``pip install pymetagen-datalabupo[report]`` installs; the HTML page can also be printed to PDF from the browser.

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics import GA, GAConnector, RandomSearch
    from metagen.reporting import report

    def domain(connector=None):
        domain = Domain(connector) if connector is not None else Domain()
        domain.define_real("learning_rate", 1e-3, 1.0, log=True)
        domain.define_integer("layers", 1, 8)
        domain.define_categorical("activation", ["relu", "tanh"])
        return domain

    def fitness(solution):
        penalty = 0.0 if solution["activation"] == "relu" else 0.2
        return (solution["learning_rate"] - 0.05) ** 2 + abs(solution["layers"] - 3) / 10 + penalty

    genetic = GA(domain(GAConnector()), fitness, max_iterations=10, seed=0)
    genetic.run()
    print(genetic.report("ga.html"))                                     # ga.html

    random = RandomSearch(domain(), fitness, max_iterations=10, seed=0)
    random.run()
    print(report([genetic, random], "comparison.pdf", title="GA and random search"))   # comparison.pdf

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
