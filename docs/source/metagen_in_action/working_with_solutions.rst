.. include:: ../aliases.rst

==========================
Working with a solution
==========================

A |solution| is an assignment of values to the variables of a |domain|. A fitness function reads it, a metaheuristic modifies it, and both do it through the same few operations. This page goes through them over one domain that has a variable of each kind.

.. code-block:: python

    from metagen.framework import Domain, RelativeAlteration, Solution

    domain = Domain()
    domain.define_real("learning_rate", 0.0001, 0.1)
    domain.define_integer("batch_size", 16, 256, 16)
    domain.define_categorical("solver", ["adam", "sgd"])

    domain.define_static_structure("class_weights", 3)          # exactly three reals
    domain.set_structure_to_real("class_weights", 0.0, 1.0)

    domain.define_group("layer")
    domain.define_integer_in_group("layer", "neurons", 8, 128)
    domain.define_real_in_group("layer", "dropout", 0.0, 0.5)
    domain.define_dynamic_structure("architecture", 1, 4)       # one to four layers
    domain.set_structure_to_variable("architecture", "layer")

    solution = Solution(domain)      # every variable is drawn at random from its definition

Reading
-------

``solution["name"]`` returns **plain Python values, at any depth**: a number or a string for a basic variable, a ``list`` for a structure and a ``dict`` for a group. It is what a fitness function uses.

.. code-block:: python

    solution["learning_rate"]             # a float
    solution["solver"]                    # 'adam' or 'sgd'
    solution["class_weights"]             # a list of three floats
    solution["architecture"]              # a list of dicts, one per layer

    first_layer = solution["architecture"][0]
    first_layer["neurons"], first_layer["dropout"]

A conditional variable (see :doc:`../domain/domain`) reads as ``None`` while it is inactive; ``solution.is_active("name")`` says whether it is.

.. code-block:: python

    conditional = Domain()
    conditional.define_categorical("solver", ["adam", "sgd"])
    conditional.define_real("momentum", 0.5, 0.99)
    conditional.set_condition("momentum", "solver", ["sgd"])

    tuned = Solution(conditional)
    tuned.set("solver", "adam")
    tuned["momentum"]                     # None
    tuned.is_active("momentum")           # False

``solution.get("name")`` returns the **object** that holds the value instead, which is what code that modifies a solution in place works with: a structure object has a length, and its ``get(i)`` returns the object at a position.

.. code-block:: python

    structure = solution.get("architecture")
    len(structure)                        # the number of layers
    structure.get(0)                      # the first layer, as an object

Writing
-------

``solution.set("name", value)`` takes the same plain values that ``[]`` returns, and checks them against the definition: a value out of range, a list of the wrong length or a missing group field raises a ``ValueError`` and leaves the solution as it was.

.. code-block:: python

    solution.set("learning_rate", 0.01)
    solution.set("solver", "sgd")
    solution.set("class_weights", [0.2, 0.3, 0.5])
    solution.set("architecture", [{"neurons": 64, "dropout": 0.1},
                                  {"neurons": 32, "dropout": 0.0}])

    solution.set("learning_rate", 3.0)            # ValueError: out of range
    solution.set("class_weights", [0.1, 0.2])     # ValueError: the structure holds three

Mutating
--------

``mutate`` changes the solution at random, and is how a metaheuristic produces a neighbor. ``alterations_number`` is how many variables change (by default, a random number of them), and ``alteration_limit`` is how far a numeric variable may move:

.. code-block:: python

    neighbor = Solution(domain)

    # One variable, moved by at most a tenth of its own range.
    neighbor.mutate(alterations_number=1, alteration_limit=RelativeAlteration(0.1))

    # A plain number is an absolute amount, the same for every variable.
    neighbor.mutate(alteration_limit=0.001)

    # No limit: each mutated variable is redrawn over its whole domain.
    neighbor.mutate()

A categorical variable always changes to another category, an integer on a grid stays on it, and a dynamic structure may also grow or shrink within its bounds.

Evaluating and comparing
------------------------

``evaluate`` calls the fitness function and stores the result, which ``get_fitness`` returns. Solutions compare by fitness, and **lower is better**: the package minimizes, so ``min`` picks the best of a population.

.. code-block:: python

    def fitness(candidate: Solution) -> float:
        return candidate["learning_rate"] + sum(layer["neurons"] for layer in candidate["architecture"]) / 1000

    solution.evaluate(fitness)
    neighbor.evaluate(fitness)

    best = min(solution, neighbor)
    best.get_fitness()

To maximize a score, return its negative from the fitness function.
