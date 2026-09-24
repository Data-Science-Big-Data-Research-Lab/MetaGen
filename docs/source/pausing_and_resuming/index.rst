.. include:: ../aliases.rst

=========================
Pausing and resuming
=========================

A long run, such as a hyperparameter search whose fitness trains a model, can be stopped and continued later: after a power failure, when a job scheduler ends a job, or on purpose. Every metaheuristic but CVOA saves its state to a **checkpoint** file, and a run continued from it reaches exactly the result, and the history, it would have reached uninterrupted.

Saving as it goes
-----------------

Give a metaheuristic a ``checkpoint`` file and it saves its state there after every ``checkpoint_every`` iterations. If the file exists when ``run()`` starts, the run continues from it instead of starting over, so running the same script again after a cut is all it takes:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import GA, GAConnector

    domain = Domain(connector=GAConnector())
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 0, 20)

    def fitness_function(solution: Solution) -> float:
        return solution["x"] ** 2 + (solution["n"] - 7) ** 2

    algorithm = GA(domain, fitness_function, max_iterations=50, seed=0,
                   checkpoint="runs/ga.ckpt", checkpoint_every=5)
    best_solution = algorithm.run()

The file is written atomically, so a cut while writing it leaves the previous one whole, and a cut during an iteration loses that iteration only. It is removed when the run ends.

Continuing in another process
-----------------------------

``resume`` rebuilds the metaheuristic from its checkpoint, in the same process or in a new one. The fitness function is not stored in the file, since a lambda or a nested function cannot be, and is given again:

.. code-block:: python

    algorithm = GA.resume("runs/ga.ckpt", fitness_function)
    best_solution = algorithm.run()

Stopping on purpose
-------------------

``request_stop()`` makes ``run()`` finish the iteration in progress, save the checkpoint and return the best solution found so far. It only sets a flag, so it can be called from a callback, another thread or a signal handler. A job scheduler that sends a signal before ending a job, such as SLURM with ``--signal=B:USR1@120``, gives the run time to save:

.. code-block:: python

    import signal

    algorithm = GA(domain, fitness_function, max_iterations=50, seed=0,
                   checkpoint="runs/ga.ckpt")
    signal.signal(signal.SIGUSR1, lambda signum, frame: algorithm.request_stop())
    best_solution = algorithm.run()

Submitting the same job again continues the run.

What to keep in mind
--------------------

* The checkpoint stores the algorithm, its population and the state of MetaGen's random generators. With the same ``seed``, a run continued from a checkpoint gives the same result as one never stopped; a distributed run, on the same number of CPUs.
* A checkpoint is a Python pickle: load only files you wrote or trust. It is rejected by another version of the package, or by another metaheuristic class.
* Types of your own registered in a connector must be importable when the run continues.
* With ``log_dir``, a continued run keeps writing to the same TensorBoard run, so its curves stay in one piece.
* CVOA runs its strains through a launcher and has no checkpoint.
