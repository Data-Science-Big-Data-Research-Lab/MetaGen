.. include:: ../../aliases.rst

Implementing the Simulated Annealing metaheuristic with MetaGen
================================================================

In this example a simple SimulatedAnnealing algorithm has been developed using the metagen framework.

**Initialization**

The SA class is defined, and its constructor (__init__) is provided with the following parameters:

    * domain: Domain: The domain of possible solutions.
    * fitness: Callable[[Solution], float]: A function that calculates the fitness of a solution.
    * n_iterations: int = 50: The number of search iterations to perform.
    * alteration_limit: How far a neighbor may move from the current solution. ``RelativeAlteration(0.1)`` is a tenth of each variable's own range, which suits domains whose variables have different widths; a plain number is an absolute amount, the same for every variable.
    * initial_temp: float = 50.0: The initial temperature for the simulated annealing.
    * cooling_rate: float = 0.99: Measures the speed of the cooling procedure.
    * The constructor stores these parameters as instance variables.

**Generating initial Solution**

Initially, a random solution is generated from the defined `Domain`.


**Best Solution search**
The simulated annealing process attempts to find a global optimum by allowing occasional acceptance of worse solutions.

The algorithm iterates for the specified number of iterations (`n_iterations`).

In each iteration:
    * Creates a neighboring solution by copying and mutating the current solution.
    * Evaluates the neighbor's fitness.
    * Computes an exploration rate based on the fitness difference and current temperature.
    * Accepts the neighbor as the new solution if it is better, or else with a probability that falls as the neighbor gets worse and as the temperature drops.
    * Remembers the best solution seen, because the current one may get worse.
    * Lowers the temperature according to the cooling rate.

Finally, the run method returns the best solution found after all iterations.

.. code-block:: python

    import math
    import random
    from collections.abc import Callable
    from copy import deepcopy
    from typing import Any

    from metagen.framework import Domain, RelativeAlteration, Solution

    class SA:

        def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], n_iterations: int = 50,
                     alteration_limit: Any = RelativeAlteration(0.1), initial_temp: float = 50.0,
                     cooling_rate: float = 0.99) -> None:

            self.domain: Domain = domain
            self.n_iterations: int = n_iterations
            self.initial_temp: float = initial_temp
            self.alteration_limit: Any = alteration_limit
            self.cooling_rate: float = cooling_rate
            self.solution = None
            self.fitness_func: Callable[[Solution], float] = fitness_func

            self.initialize()

        def initialize(self):
            """
            Create and evaluate the initial solution.
            """
            self.solution = Solution(self.domain, connector=self.domain.get_connector())
            self.solution.evaluate(self.fitness_func)


        def run(self) -> Solution:
            """
            Run the simulated annealing for the specified number of generations and return the best solution found.

            :return: The best solution found by the simulated annealing.
            :rtype: Solution
            """

            best = deepcopy(self.solution)
            temperature = self.initial_temp

            for _ in range(self.n_iterations):

                neighbour = deepcopy(self.solution)
                neighbour.mutate(alteration_limit=self.alteration_limit)
                neighbour.evaluate(self.fitness_func)

                worsening = neighbour.get_fitness() - self.solution.get_fitness()

                # A better neighbour is always taken; a worse one, with the Metropolis probability.
                if worsening < 0 or random.random() < math.exp(-worsening / temperature):
                    self.solution = neighbour

                if self.solution < best:
                    best = deepcopy(self.solution)

                temperature *= self.cooling_rate

            return best

The class above is a teaching example. It draws from Python's global ``random`` module, so it is not
controlled by |metagen|'s ``seed``; the simulated annealing that ships with the package,
:py:class:`~metagen.metaheuristics.SA`, inherits from ``Metaheuristic``, is seedable, and ties its
cooling schedule to the number of iterations.
