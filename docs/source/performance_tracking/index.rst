.. include:: ../aliases.rst

=======================
Performance tracking
=======================

In |metagen|, every available metaheuristic includes a ``log_dir`` parameter that allows users to enable TensorBoard logging for real-time monitoring of key optimization metrics. This feature helps track the optimization process and compare different metaheuristics effectively.

Optional Logging with ``log_dir``
---------------------------------
- Users can specify a directory for logging by setting the ``log_dir`` parameter when initializing a metaheuristic. If logging is not needed, this parameter can be left as default.
- The logs include information about fitness progression, population size, and the distribution of solutions over iterations.

Required Installation of TensorBoard
------------------------------------
To use this feature, the **``tensorboard`` package must be installed**. If TensorBoard is not available, logging will be automatically disabled, but the metaheuristic will still function normally.

To install TensorBoard, run:

.. code-block:: bash

    pip install tensorboard

Visualization of Optimization Metrics
-------------------------------------
Once the execution of a metaheuristic is complete, users can analyze the results using TensorBoard:

.. code-block:: bash

    tensorboard --logdir=logs

This will open an interactive dashboard displaying the following metrics:

- **Best fitness per iteration** – Tracks the highest-performing solution at each step.
- **Average fitness per iteration** – Shows the trend of overall population performance.
- **Fitness distribution per iteration** – Provides a histogram of fitness values to analyze variability.
- **Population size per iteration** – Monitors how the number of evaluated individuals evolves.
- **Solution component tracking** – Logs numerical values of solution variables to detect structural changes.
- **Final best solution summary** – Displays key statistics of the best solution found.

By ensuring TensorBoard is installed, users can take advantage of powerful visualizations that provide deeper insights into the optimization process within **MetaGen**.