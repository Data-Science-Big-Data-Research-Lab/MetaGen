The Steady-State Genetic Algorithm metaheuristic
==================================================

Using an existing metaheuristic and adapting it to a variation is simple. Lets try a variation of simple GA called Steady-State Genetic Algorithm (SSGA). First lets analyze the pseudocode and their differences with the previously implemented algorithm:

    1. Generate the initial population of size N -> No changes in this step as this is implemented in the initialize method inside the GA class.
    2. Evaluate each solution's fitness/goodness -> No changes in this step as this is implemented in the initialize method inside the GA class.
    3. Select two solutions as parents without repetition -> No changes in this step as this is implemented in the select_parents method inside the GA class.
    4. Do Crossover, Mutation, and Inversion and create two offsprings -> No changes in this step as this is implemented in the ga_types modules with our defined GAStructure and GASolution.
    5. If offspring is duplicated, go to step 3 -> This is not implemented. Still, it is supported by our library as the equality method (__eq__) is implemented and inherited for every type.
    6. If not, then evaluate the fitness of offspring -> No changes in this step as this is implemented in the main workflow (run method) inside the class.
    7. If offspring are better than the worst solutions, then replace the worst individuals with the offspring such that population size remains constant -> This step is not implemented as this is the main difference with the standard implementation of the Genetic Algorithm. However, it could be implemented by determining the worst individual using the max or min Python functions, depending on whether the problem maximizes or minimizes some functions. Python supports even the sorted function or a more efficient alternative.
    8. Check for convergence criteria -> This step is also different as the concept of generations does not exist. These criteria would replace the main loop in the run function in the GA class. More changes are not required.
    9. If convergence criteria are met, then terminate the program, else continue with step 3 -> The changes from the previous step would include this one.

Using this pseudocode, the complete implementation of SSGA can be implemented in the following way employing the previously defined types and connector:

.. code-block:: python

    import random
    from collections.abc import Callable
    from typing import List

    from metagen.framework import Domain
    from .ga_types import GASolution

    class SSGA:
        """
        Steady State Genetic Algorithm (SSGA) class for optimization problems which is a variant of the Genetic Algorithm (GA) with population replacement.

        :param domain: The domain representing the problem space.
        :type domain: Domain
        :param fitness_func: The fitness function used to evaluate solutions.
        :type fitness_func: Callable[[Solution], float]
        :param population_size: The size of the population (default is 10).
        :type population_size: int, optional
        :param mutation_rate: The probability of mutation for each solution (default is 0.1).
        :type mutation_rate: float, optional
        :param n_iterations: The number of generations to run the algorithm (default is 50).
        :type n_iterations: int, optional

        :ivar population_size: The size of the population.
        :vartype population_size: int
        :ivar mutation_rate: The probability of mutation for each solution.
        :vartype mutation_rate: float
        :ivar n_iterations: The number of generations to run the algorithm.
        :vartype n_iterations: int
        :ivar domain: The domain representing the problem space.
        :vartype domain: Domain
        :ivar fitness_func: The fitness function used to evaluate solutions.
        :vartype fitness_func: Callable[[Solution], float]"""

        def __init__(self, domain: Domain, fitness_func: Callable[[GASolution], float], population_size: int = 10, mutation_rate: float = 0.1, n_iterations: int = 50) -> None:

            self.population_size: int = population_size
            self.mutation_rate: float = mutation_rate
            self.n_iterations: int = n_iterations
            self.domain: Domain = domain
            self.fitness_func: Callable[[GASolution], float] = fitness_func
            self.population: List[GASolution] = []

            self.initialize()

        def initialize(self):
            """
            Initialize the population of solutions by creating and evaluating initial solutions.
            """
            self.population = []
            solution_type: type[GASolution] = self.domain.get_connector().get_type(
                self.domain.get_core())

            for _ in range(self.population_size):
                solution = solution_type(
                    self.domain, connector=self.domain.get_connector())
                solution.evaluate(self.fitness_func)
                self.population.append(solution)

            self.population = sorted(self.population, key=lambda sol: sol.fitness)


        def select_parents(self) -> List[GASolution]:
            """
            Select the top two parents from the population based on their fitness values.

            :return: The selected parent solutions.
            :rtype: List[Solution]
            """

            parents = self.population[:2]
            return parents

        def replace_wost(self, child) -> None:
            """
            Replace the solution in the population with worst fitness.

            :return: The selected parent solutions.
            :rtype: List[Solution]
            """

            worst_solution = self.population[-1]

            if worst_solution.fitness > child.fitness:
                self.population[-1] = child

            self.population = sorted(self.population, key=lambda sol: sol.fitness)

        def run(self) -> GASolution:
            """
            Run the steady-satate genetic algorithm for the specified number of generations and return the best solution found.

            :return: The best solution found by the genetic algorithm.
            :rtype: Solution
            """

            current_iteration = 0


            while current_iteration <= self.n_iterations:

                parent1, parent2 = self.select_parents()

                child1, child2 = parent1.crossover(parent2)

                if random.uniform(0, 1) <= self.mutation_rate:
                    child1.mutate()

                if random.uniform(0, 1) <= self.mutation_rate:
                    child2.mutate()

                if child1 == child2:
                    continue

                child1.evaluate(self.fitness_func)
                child2.evaluate(self.fitness_func)

                self.replace_wost(child1)
                self.replace_wost(child2)

                current_iteration += 1

            best_individual = min(
                self.population, key=lambda sol: sol.get_fitness())

            return best_individual