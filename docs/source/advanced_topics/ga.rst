The Genetic Algorithm metaheuristic
=======================================


The provided code defines a Genetic Algorithm (GA) implementation by extending the functionality of some already defined classes and implementing custom classes specifically for the Genetic Algorithm.

**Extending the type classes**
Firsly the Structure and Solution classes are extended to include the crossover function.

* GAStructure is a custom class representing the structure of individuals in the genetic algorithm. It defines a crossover method for performing the crossover operation with another GAStructure instance.
* GASolution is a custom class representing a solution in the genetic algorithm. It inherits from the Solution class and also defines a crossover method for performing crossover with another GASolution instance. The crossover operation involves exchanging variables between two solutions.

.. code-block:: python

    from __future__ import annotations

    import random
    from copy import copy
    from typing import Tuple

    import metagen.framework.solution as types
    from metagen.framework import BaseConnector, Solution
    from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                        DynamicStructureDefinition,
                                        IntegerDefinition, RealDefinition,
                                        StaticStructureDefinition)


    class GAStructure(types.Structure):
        """
        Represents the custom Structure type for the Genetic Algorithm (GA).
        Methods:
            mutate(): Modify the Structure by performing an action selected randomly from three options. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            _resize(): Resizes the vector based on the definition provided at initialization. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            _alterate(): Randomly alters a certain number of elements in the vector by calling their `mutate` method. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            crossover(other: GAStructure) -> Tuple[GAStructure, GAStructure]: Performs crossover operation with another GAStructure instance.
        """

        def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
            """
            Performs crossover operation with another GAStructure instance by randomly modifying list positions. Note that this operation does not support an `DynamicStructureDefinition`.
            """

            child1 = GAStructure(self.get_definition(), connector=self.connector)
            child2 = GAStructure(self.get_definition(), connector=self.connector)

            current_size = min(len(self), len(other))
            number_of_changes = random.randint(1, current_size)
            indexes_to_change = random.sample(
                list(range(0, current_size)), number_of_changes)

            if isinstance(self.get_definition(), DynamicStructureDefinition):
                raise NotImplementedError()
            else:
                for i in range(current_size):
                    if i in indexes_to_change:
                        child1[i], child2[i] = copy(other.get(i)), copy(self.get(i))
                    else:
                        child1[i], child2[i] = copy(self.get(i)), copy(other.get(i))
            return child1, child2


    class GASolution(Solution):
        """
        Represents a Solution type for the Genetic Algorithm (GA).

        Methods:
            mutate(alterations_number: int = None): Modify a random subset of the solution's variables calling its mutate method. Inherited from :py:class:`~metagen.framework.solution.Structure`.
            crossover(other: GASolution) -> Tuple[GASolution, GASolution]: Performs crossover operation with another GASolution instance.
        """

        def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
            """
            Performs crossover operation with another GASolution instance by randomly exchanging variables.
            """
            assert self.get_variables().keys() == other.get_variables().keys()

            basic_variables = [variable_name for variable_name, variable_value in self.get_variables(
            ).items() if self.connector.get_builtin(variable_value) in [int, float, str]]

            if len(basic_variables) > 0:
                n_variables_to_exchange = random.randint(
                    1, len(basic_variables) - 1)

                variables_to_exchange = random.sample(
                    basic_variables, n_variables_to_exchange)
            else:
                variables_to_exchange = []

            child1 = GASolution(self.get_definition(), connector=self.connector)
            child2 = GASolution(self.get_definition(), connector=self.connector)

            for variable_name, variable_value in self.get_variables().items():  # Iterate over all variables

                if variable_name not in basic_variables:
                    variable_child1, variable_child2 = variable_value.crossover(
                        other.get(variable_name))
                    child1.set(variable_name, copy(variable_child1))
                    child2.set(variable_name, copy(variable_child2))
                elif variable_name in variables_to_exchange:
                    child1.set(variable_name, copy(other.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))
                else:
                    child1.set(variable_name, copy(self.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))

            return child1, child2


**Define the genetic algorithm**

The GA class represents the genetic algorithm for optimization problems is implemented using the metagen types.

It takes the following parameters in its constructor:

    * domain: The domain representing the problem space.
    * fitness_func: The fitness function used to evaluate solutions.
    * population_size: The size of the population (default is 10).
    * mutation_rate: The probability of mutation for each solution (default is 0.1).
    * n_generations: The number of generations to run the algorithm (default is 50).

The class initializes the genetic algorithm with the provided parameters and stores them as instance variables.

The initialize method is used to create and evaluate initial solutions to populate the population.

The select_parents method selects the top two parents from the population based on their fitness values.

The run method runs the genetic algorithm for the specified number of generations and returns the best solution found.

.. code-block:: python

    import random
    from collections.abc import Callable
    from typing import List

    from metagen.framework import Domain
    from metagen.framework.solution.devsolution import Solution


    class GA:
        """
        Genetic Algorithm (GA) class for optimization problems.
        :param domain: The domain representing the problem space.
        :type domain: Domain
        :param fitness_func: The fitness function used to evaluate solutions.
        :type fitness_func: Callable[[Solution], float]
        :param population_size: The size of the population (default is 10).
        :type population_size: int, optional
        :param mutation_rate: The probability of mutation for each solution (default is 0.1).
        :type mutation_rate: float, optional
        :param n_generations: The number of generations to run the algorithm (default is 50).
        :type n_generations: int, optional

        :ivar population_size: The size of the population.
        :vartype population_size: int
        :ivar mutation_rate: The probability of mutation for each solution.
        :vartype mutation_rate: float
        :ivar n_generations: The number of generations to run the algorithm.
        :vartype n_generations: int
        :ivar domain: The domain representing the problem space.
        :vartype domain: Domain
        :ivar fitness_func: The fitness function used to evaluate solutions.
        :vartype fitness_func: Callable[[Solution], float]"""

        def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float], population_size: int = 10, mutation_rate: float = 0.1, n_generations: int = 50) -> None:

            self.population_size: int = population_size
            self.mutation_rate: float = mutation_rate
            self.n_generations: int = n_generations
            self.domain: Domain = domain
            self.fitness_func: Callable[[Solution], float] = fitness_func
            self.population: List[Solution] = []

            self.initialize()

        def initialize(self):
            """
            Initialize the population of solutions by creating and evaluating initial solutions.
            """
            self.population = []

            for _ in range(self.population_size):
                solution = GASolution(
                    self.domain, connector=self.domain.get_connector())
                solution.evaluate(self.fitness_func)
                self.population.append(solution)

        def select_parents(self) -> List[Solution]:
            """
            Select the top two parents from the population based on their fitness values.

            :return: The selected parent solutions.
            :rtype: List[Solution]
            """

            parents = sorted(self.population, key=lambda sol: sol.fitness)[:2]
            return parents

        def run(self) -> Solution:
            """
            Run the genetic algorithm for the specified number of generations and return the best solution found.

            :return: The best solution found by the genetic algorithm.
            :rtype: Solution
            """

            for _ in range(self.n_generations):

                parent1, parent2 = self.select_parents()

                offspring = []
                for _ in range(self.population_size // 2):
                    child1, child2 = parent1.crossover(parent2)

                    if random.uniform(0, 1) <= self.mutation_rate:
                        child1.mutate()

                    if random.uniform(0, 1) <= self.mutation_rate:
                        child2.mutate()

                    child1.evaluate(self.fitness_func)
                    child2.evaluate(self.fitness_func)
                    offspring.extend([child1, child2])

                self.population = offspring

                best_individual = min(
                    self.population, key=lambda sol: sol.get_fitness())

            best_individual = min(
                self.population, key=lambda sol: sol.get_fitness())
            return best_individual

**Customize the BaseConnector**

GAConnector is a custom connector class specifically designed for the genetic algorithm. It maps the custom classes implemented to their corresponding definitions and built-in types.
Specifically, this class is used to define how the custom classes (GASolution and GAStructure) are connected to the definitions and built-in types used in the domain.

.. code-block:: python

    class GAConnector(BaseConnector):
        """
        Represents the custom Connector for the Genetic Algorithm (GA) which link the following classes:

        * `BaseDefinition` - `GASolution` - `dict`
        * `IntegerDefinition` - `types.Integer` - `int`
        * `RealDefinition` - `types.Real` - `float`
        * `CategoricalDefinition` - `types.Categorical` - `str`
        * `StaticStructureDefinition`- `GAStructure` - `list`

        Note that the `Solution` and `Structure` original classes has been replaced by the custom classes. Therefore, when instantiating an `StaticStructureDefinition`, the `GAStructure` will be employed.

        Methods:
            __init__(): Initializes the GAConnector instance.
        """

        def __init__(self) -> None:

            super().__init__()

            self.register(BaseDefinition, GASolution, dict)
            self.register(IntegerDefinition, types.Integer, int)
            self.register(RealDefinition, types.Real, float)
            self.register(CategoricalDefinition, types.Categorical, str)
            self.register(StaticStructureDefinition, GAStructure, list)
