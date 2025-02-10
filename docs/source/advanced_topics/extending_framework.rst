.. include:: ../aliases.rst

===========================================================
Extending the Solution Framework for Custom Metaheuristics
===========================================================

|metagen| allows developers to extend the **Solution framework** to accommodate domain-specific requirements in custom metaheuristics. This section illustrates how to extend the |solution| framework using the **Genetic Algorithm (GA)** as an example.

In |ga|, solutions require **crossover operations**, which are not part of the default |solution| class. To implement this functionality, the following steps are necessary:

1. **Defining a Custom Structure Type**: The |ga_structure| class extends the standard |structure| class to include a crossover operation.
2. **Defining a Custom Solution Type**: The |ga_solution| class extends |solution|, implementing specific operations required by |ga|.
3. **Creating a Custom Connector**: The |ga_connector| class maps |ga_solution| and |ga_structure| to the framework.
4. **Using the Extended Solution in a Metaheuristic**: The |ga| class uses the extended solution representation to perform evolutionary optimization.

Custom Structure Type
---------------------

The |ga_structure| class extends the default |structure| class, adding a crossover operation that allows solutions to recombine genetic information.

.. code-block:: python

    class GAStructure(types.Structure):
        def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
            child1 = GAStructure(self.get_definition(), connector=self.connector)
            child2 = GAStructure(self.get_definition(), connector=self.connector)

            current_size = min(len(self), len(other))
            indexes_to_change = random.sample(range(current_size), random.randint(1, current_size))

            for i in range(current_size):
                if i in indexes_to_change:
                    child1[i], child2[i] = copy(other.get(i)), copy(self.get(i))
                else:
                    child1[i], child2[i] = copy(self.get(i)), copy(other.get(i))

            return child1, child2

This structure allows |ga| solutions to maintain genetic information in a structured manner.

Custom Solution Type
--------------------

The |ga_solution| class extends |solution|, implementing the `crossover` method for solution-level recombination.

.. code-block:: python

    class GASolution(Solution):
        def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
            assert self.get_variables().keys() == other.get_variables().keys()

            basic_variables = [var for var, val in self.get_variables().items()
                               if self.connector.get_builtin(val) in [int, float, str]]

            if len(basic_variables) > 1:
                variables_to_exchange = random.sample(basic_variables, random.randint(1, len(basic_variables) - 1))
            else:
                variables_to_exchange = []

            child1 = GASolution(self.get_definition(), connector=self.connector)
            child2 = GASolution(self.get_definition(), connector=self.connector)

            for variable_name, variable_value in self.get_variables().items():
                if variable_name in variables_to_exchange:
                    child1.set(variable_name, copy(other.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))
                else:
                    child1.set(variable_name, copy(self.get(variable_name)))
                    child2.set(variable_name, copy(variable_value))

            return child1, child2

This extension enables **genetic operators** to be applied directly to solution objects.

Creating a Custom Connector
---------------------------

The |ga_connector| class defines mappings between base definitions and the new |ga_solution| and |ga_structure| types.

.. code-block:: python

    class GAConnector(BaseConnector):
        def __init__(self) -> None:
            super().__init__()

            self.register(BaseDefinition, GASolution, dict)
            self.register(IntegerDefinition, types.Integer, int)
            self.register(RealDefinition, types.Real, float)
            self.register(CategoricalDefinition, types.Categorical, str)
            self.register(StaticStructureDefinition, (GAStructure, "static"), list)

This connector ensures that |metagen| correctly recognizes and processes the extended solution types.

Using the Extended Solution in a Metaheuristic
----------------------------------------------

To integrate the extended solution with a metaheuristic, the developer must:

- Instantiate the |domain| using the custom |ga_connector|.
- Obtain the correct |solution| type dynamically.

Example:

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics.ga_tools import GAConnector

    # Define a domain using the GA-specific connector
    connector = GAConnector()
    domain = Domain(connector)
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)

    # Dynamically determine the correct solution type
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    potential: Solution = solution_type(domain, connector=domain.get_connector())

This guarantees compatibility with both **standard** and **custom** solutions.

Extending and Customizing the Metaheuristic class
--------------------------------------------------

Developers can implement new metaheuristics by **inheriting from `Metaheuristic`**, which provides built-in support for:

- **Distributed execution** with Ray.
- **TensorBoard logging** for monitoring.

Implementing a Genetic Algorithm
--------------------------------

The |ga| class extends |metaheuristic| and implements:

1. **`initialize()`** – Defines how the population is initialized.
2. **`iterate()`** – Implements the logic for evolving solutions.

.. code-block:: python

    from metagen.metaheuristics.base import Metaheuristic
    from typing import List, Tuple
    from metagen.metaheuristics.ga_tools import GASolution, yield_two_children
    from copy import deepcopy

    class GA(Metaheuristic):
        def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                     population_size: int = 20, max_iterations: int = 50, mutation_rate: float = 0.1):
            super().__init__(domain, fitness_function, population_size)
            self.mutation_rate = mutation_rate
            self.max_iterations = max_iterations

        def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
            current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
            return current_solutions, best_solution

        def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
            best_parents = heapq.nsmallest(2, solutions, key=lambda sol: sol.get_fitness())
            best_solution = deepcopy(self.best_solution)
            current_solutions = [deepcopy(best_parents[0]), deepcopy(best_parents[1])]

            for _ in range(len(solutions) // 2):
                father = cast(GASolution, best_parents[0])
                mother = cast(GASolution, best_parents[1])
                child1, child2 = yield_two_children((father, mother), self.mutation_rate, self.fitness_function)
                current_solutions.extend([child1, child2])

                best_solution = min(best_solution, child1, child2, key=lambda sol: sol.get_fitness())

            return current_solutions[:len(solutions)], best_solution

        def stopping_criterion(self) -> bool:
            return self.current_iteration >= self.max_iterations


By following this methodology, developers can ensure their metaheuristics are **scalable, reusable, and extendable** within |metagen|.