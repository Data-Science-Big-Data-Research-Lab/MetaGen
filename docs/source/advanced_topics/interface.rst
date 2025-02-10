.. include:: ../aliases.rst

==================================
Extending the Metaheuristic Class
==================================

Developers can extend MetaGen by implementing new metaheuristics that **inherit from the abstract `Metaheuristic` class**.
This provides built-in support for:

- **Distributed execution** with Ray.
- **TensorBoard logging** for monitoring.

Implementing a Custom Metaheuristic
-----------------------------------

To create a new metaheuristic, extend `Metaheuristic` and implement:

1. **`initialize()`** – Defines how the population is initialized.
2. **`iterate()`** – Implements the logic for evolving solutions.

Example: Implementing a Genetic Algorithm

.. code-block:: python

    from metagen.metaheuristics.base import Metaheuristic
    from typing import List, Tuple

    class GA(Metaheuristic):
        def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
            """ Initialize the population """
            return solutions, best_solution

        def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
            """ Execute one generation """
            return new_solutions, best_solution

Extending `Metaheuristic` ensures that the algorithm:

- Supports **distributed execution** out of the box.
- Enables **TensorBoard integration** for logging performance.

Developers can leverage these features to implement **scalable** and **efficient** metaheuristic algorithms.