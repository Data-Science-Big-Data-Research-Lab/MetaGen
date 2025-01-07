Implementing the Simulated Annealing metaheuristic with MetaGen
================================================================

In this example a simple SimulatedAnnealing algorithm has been developed using the metagen framework.

**Initialization**

The SA class is defined, and its constructor (__init__) is provided with the following parameters:

    * domain: Domain: The domain of possible solutions.
    * fitness: Callable[[Solution], float]: A function that calculates the fitness of a solution.
    * search_space_size: int = 30: The number of potential solutions to generate.
    * n_iterations: int = 20: The number of search iterations to perform.
    * alteration_limit: float = 0.1: The alteration applied to every `Solution` to generate the neighbors.
    * initial_temp: float = 50.0: The initial temperature for the simulated annealing.
    * cooling_rate: float = 0.99: Meassures the speed of the cooling procedure.
    * The constructor stores these parameters as instance variables.

**Generating initial Solution**

Initially, a random solution is gennerated from the defined `Domain`.


**Best Solution search**
The simulated annealing process attempts to find a global optimum by allowing occasional acceptance of worse solutions.

The algorithm, iterates for the specified number of iterations (`n_iterations`).

In each iteration:
    * Creates a neighboring solution by copying and mutating the current solution.
    * Evaluates the neighbor's fitness.
    * Computes an exploration rate based on the fitness difference and current temperature.
    * Accepts the neighbor as the new solution if it is better or based on a probability influenced by the exploration rate.
    * Lowers the temperature according to the cooling rate.

Finally, the run method returns the best solution found after all iterations.

.. code-block:: python

    from metagen.framework import Domain, Solution
    from collections.abc import Callable
    from copy import deepcopy
    import random
    import math

    class SA:

        def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], n_iterations: int = 50, alteration_limit: float=0.1, initial_temp: float = 50.0, cooling_rate: float=0.99) -> None:

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
            Initialize the population of solutions by creating and evaluating initial solutions.
            """
            self.solution = Solution()
            self.solution.evaluate(self.fitness_func)


        def run(self) -> Solution:
            """
            Run the simulated annealing for the specified number of generations and return the best solution found.

            :return: The best solution found by the simulated annealing.
            :rtype: Solution
            """

            current_iteration = 0
            temperature = self.initial_temp


            while current_iteration <= self.n_iterations:

                neighbour = deepcopy(self.solution)

                neighbour.mutate(alteration_limit=self.alteration_limit)

                neighbour.evaluate(self.fitness_func)

                exploration_rate = math.exp((self.solution.fitness - neighbour.fitness) / temperature)

                if neighbour.fitness < self.solution.fitness or exploration_rate > random.random():
                    self.solution = neighbour

                temperature *= self.cooling_rate

                current_iteration += 1

            return self.solution
