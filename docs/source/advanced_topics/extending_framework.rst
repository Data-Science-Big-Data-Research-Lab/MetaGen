.. include:: ../aliases.rst

===========================================================
Extending the Solution Framework for Custom Metaheuristics
===========================================================

|metagen| allows developers to extend the **Solution framework** to accommodate the needs of a custom metaheuristic. This section shows how, with a genetic algorithm as the example: its solutions need a **crossover operation**, which is not part of the default |solution| class. Four steps are involved:

1. **Defining a custom structure type** that extends |structure| with a crossover operation.
2. **Defining a custom solution type** that extends |solution| with the same operation.
3. **Creating a custom connector** that maps the domain definitions to the new types.
4. **Using the extended solution in a metaheuristic** that inherits from |metaheuristic|.

The example is complete: the code blocks below, put together in one file in the order they appear, run as they are. It is deliberately small. The genetic algorithms that ship with |metagen| follow the same four steps with richer operators (see :doc:`../metaheuristics/ga`): |ga_solution| and |ga_structure| blend numeric values with BLX-alpha instead of exchanging them, |ga_structure| recombines the lengths of a dynamic structure as well as its values, and |ga| selects parents by tournament and mutates children within a fraction of each variable's range.

.. code-block:: python

    from __future__ import annotations

    import heapq
    from copy import deepcopy
    from typing import Callable, List, Tuple

    from metagen.framework import BaseConnector, Domain, Solution
    from metagen.framework.domain.core import (BaseDefinition, CategoricalDefinition, IntegerDefinition,
                                               RealDefinition, StaticStructureDefinition)
    from metagen.framework.rng import get_rng
    from metagen.framework.solution import types
    from metagen.metaheuristics.base import Metaheuristic
    from metagen.metaheuristics.tools import random_exploration, solution_class

Custom Structure Type
---------------------

``SwapStructure`` extends |structure| with a crossover that exchanges positions between two parents. Two details matter. The elements are **deep-copied**: a structure may hold groups, and a shallow copy would leave parent and child sharing the same variables. And each child is built whole and handed over with a single ``set``, which is what checks the length against the definition.

.. code-block:: python

    class SwapStructure(types.Structure):
        """A structure whose positions are exchanged between two parents."""

        def crossover(self, other: SwapStructure) -> Tuple[SwapStructure, SwapStructure]:
            first, second = [], []
            for i in range(len(self)):
                mine, theirs = deepcopy(self.get(i)), deepcopy(other.get(i))
                if get_rng().random() < 0.5:
                    mine, theirs = theirs, mine
                first.append(mine)
                second.append(theirs)

            child1 = SwapStructure(self.get_definition(), connector=self.get_connector())
            child2 = SwapStructure(self.get_definition(), connector=self.get_connector())
            child1.set(first)
            child2.set(second)
            return child1, child2

Custom Solution Type
--------------------

``SwapSolution`` extends |solution|. For each variable it asks whether the value **knows how to cross over** and delegates to it if so; otherwise the two parents' values are exchanged with probability one half. Asking for the capability, rather than for a concrete class, is what lets another type with its own operator take part without touching this code.

.. code-block:: python

    class SwapSolution(Solution):
        """A solution that knows how to recombine with another one."""

        def crossover(self, other: SwapSolution) -> Tuple[SwapSolution, SwapSolution]:
            child1 = SwapSolution(self.get_definition(), connector=self.connector)
            child2 = SwapSolution(self.get_definition(), connector=self.connector)

            for name in self.get_variables():
                mine, theirs = self.get(name), other.get(name)
                if hasattr(mine, "crossover"):
                    # The variable brings its own operator: delegate to it.
                    value1, value2 = mine.crossover(theirs)
                elif get_rng().random() < 0.5:
                    value1, value2 = deepcopy(theirs), deepcopy(mine)
                else:
                    value1, value2 = deepcopy(mine), deepcopy(theirs)
                child1.set(name, value1)
                child2.set(name, value2)

            return child1, child2

Creating a Custom Connector
---------------------------

The connector maps each definition of the domain to the type that represents it in a solution and to its builtin type. Registering ``SwapSolution`` for the core definition and ``SwapStructure`` for the static structure is all it takes; a structure is registered with a discriminator because ``list`` maps to the static definition and to the dynamic one.

.. code-block:: python

    class SwapConnector(BaseConnector):
        def __init__(self) -> None:
            super().__init__()
            self.register(BaseDefinition, SwapSolution, dict)
            self.register(IntegerDefinition, types.Integer, int)
            self.register(RealDefinition, types.Real, float)
            self.register(CategoricalDefinition, types.Categorical, str)
            self.register(StaticStructureDefinition, (SwapStructure, "static"), list)

Extending the Metaheuristic class
---------------------------------

A metaheuristic inherits from |metaheuristic| and implements **three** methods:

1. ``initialize(num_solutions)`` returns the first population and its best solution.
2. ``iterate(solutions)`` returns the next population and the best solution of the iteration.
3. ``stopping_criterion()`` says when to stop. It is abstract: a subclass without it cannot be instantiated.

In exchange the base class provides the run loop, elitism (the best solution ever seen is kept even if an iteration returns something worse), and four constructor parameters that the subclass should pass through:

- ``seed``: the same seed reproduces the run. Draw every random number from :py:func:`metagen.framework.rng.get_rng` (or ``get_numpy_rng``), never from the global ``random`` module, or the seed will not control it.
- ``log_dir``: a directory to write TensorBoard logs to. ``None``, the default, writes nothing.
- ``distributed``: run ``initialize`` and ``iterate`` on slices of the population across the CPUs of a Ray cluster.
- ``distribution_model``: how a distributed run makes up the next population, ``"global"`` (the default) or ``"islands"``; see :doc:`../distributed_execution/distributed`.

One rule makes a metaheuristic work under ``distributed=True``: **``initialize`` and ``iterate`` must not keep state in ``self``**. Ray runs them on a serialized copy of the algorithm, and what they write there stays in the worker. State that must survive an iteration goes in what the method returns, or is rebuilt in ``post_iteration``, which runs in the driver.

.. code-block:: python

    class SwapGA(Metaheuristic):
        def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                     population_size: int = 20, max_iterations: int = 50, mutation_rate: float = 0.1,
                     **kwargs) -> None:
            super().__init__(domain, fitness_function, population_size=population_size, **kwargs)
            self.max_iterations = max_iterations
            self.mutation_rate = mutation_rate

        def initialize(self, num_solutions: int = 10) -> Tuple[List[Solution], Solution]:
            return random_exploration(self.domain, self.fitness_function, num_solutions)

        def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
            elite = heapq.nsmallest(2, solutions, key=Solution.get_fitness)
            offspring = [deepcopy(individual) for individual in elite]

            while len(offspring) < len(solutions):
                father = min(get_rng().sample(solutions, 2))      # a binary tournament
                mother = min(get_rng().sample(solutions, 2))
                for child in father.crossover(mother):
                    if get_rng().random() < self.mutation_rate:
                        child.mutate()
                    child.evaluate(self.fitness_function)
                    offspring.append(child)

            offspring = offspring[:len(solutions)]
            return offspring, min(offspring)

        def stopping_criterion(self) -> bool:
            return self.current_iteration >= self.max_iterations

Using it
--------

The domain is created with the custom connector, and from there everything is standard. ``solution_class`` returns the class the connector maps the domain to, which is how framework code builds solutions without naming a concrete type.

.. code-block:: python

    domain = Domain(connector=SwapConnector())
    domain.define_integer("max_depth", 2, 8)
    domain.define_real("learning_rate", 0.001, 0.1)
    domain.define_static_structure("weights", 3)
    domain.set_structure_to_real("weights", 0.0, 1.0)

    # The class the connector maps the domain to: SwapSolution here, Solution by default.
    assert solution_class(domain) is SwapSolution


    def fitness(solution: Solution) -> float:
        return solution["max_depth"] + solution["learning_rate"] + sum(solution["weights"])


    best = SwapGA(domain, fitness, max_iterations=20, seed=0).run()
    print(best)

By following these steps a metaheuristic stays **reproducible, distributable and extendable** within |metagen|.
