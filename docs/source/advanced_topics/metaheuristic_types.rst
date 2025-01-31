.. include:: ../aliases.rst

========================
Implementing Metaheuristics
========================

MetaGen provides a flexible framework for developing and integrating new metaheuristic algorithms. Developers can implement metaheuristics in different ways depending on their needs and the level of integration required with the framework.

Developer Profiles
-------------------

There are three main approaches to developing a metaheuristic in MetaGen, each with different levels of integration with the framework:

1. **Standard Metaheuristic**: The simplest approach, where the developer implements a metaheuristic using the standard `Solution` class without extending it. This case is illustrated in the **MetaGen in Action** section.

2. **Flexible Metaheuristic**: The developer ensures that the metaheuristic is compatible with possible future extensions of the `Solution` class by using a `BaseConnector`.

3. **Extended Metaheuristic**: The developer requires a custom `Solution` class for domain-specific operations and ensures that the metaheuristic remains compatible with standard and extended solutions.

Standard Metaheuristic
-----------------------

A **Standard Metaheuristic** is implemented using the built-in `Solution` class. This approach is ideal when the developer does not need custom data structures or variable types. The metaheuristic can be applied to any optimization problem without requiring modifications to the framework.

This case is covered in the **MetaGen in Action** section.

Flexible Metaheuristic
------------------------

A **Flexible Metaheuristic** ensures compatibility with future extensions of the `Solution` class by obtaining the `BaseConnector` from the `Domain` and using it to instantiate solutions. This allows the metaheuristic to work seamlessly with both standard and extended `Solution` representations.

Example:

.. code-block:: python

    from metagen.framework import Domain

    # Define a domain using a specific connector
    connector = AnyConnector()
    domain = Domain(connector)
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)

    # Dynamically determine the correct solution type
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    potential: Solution = solution_type(domain, connector=domain.get_connector())

Key characteristics:

- Uses `BaseConnector` from the `Domain` to instantiate solutions.
- Ensures compatibility with both standard and extended `Solution` classes.
- Future extensions of `Solution` can be used without modifying the metaheuristic.

Extended Metaheuristic
-----------------------

An **Extended Metaheuristic** is implemented when a developer needs a custom extension of the `Solution` class. This is necessary when the metaheuristic requires domain-specific data structures or specialized operations beyond what the standard `Solution` class offers.

Example (GA with a custom `Solution` class):

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics.ga import GA
    from metagen.metaheuristics.ga_tools import GAConnector, GASolution

    # Define a domain using the GA-specific connector
    connector = GAConnector()
    domain = Domain(connector)
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)

    # Dynamically determine the correct solution type
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    potential: Solution = solution_type(domain, connector=domain.get_connector())

Key characteristics:

- Requires defining a custom `Solution` class (e.g., `GASolution`).
- The metaheuristic must work with both standard and extended `Solution` classes.
- Uses a custom `BaseConnector` (e.g., `GAConnector`) to map the new `Solution` class to the framework.

Choosing the Right Approach
----------------------------

+----------------------------+------------------------------------------------+---------------------------------------------------+
| Approach                   | Key Features                                   | Best Suited For                                   |
+============================+================================================+===================================================+
| Standard Metaheuristic     | Uses standard `Solution` class                 | General-purpose optimization without extensions   |
|                            | Works with any `Domain`                        |                                                   |
+----------------------------+------------------------------------------------+---------------------------------------------------+
| Flexible Metaheuristic     | Uses `BaseConnector` for compatibility         | Ensuring compatibility with extended solutions    |
|                            | Can work with standard and extended `Solution` |                                                   |
+----------------------------+------------------------------------------------+---------------------------------------------------+
| Extended Metaheuristic     | Requires a custom `Solution` class             | Specialized metaheuristics with custom structures |
|                            | Uses a custom `BaseConnector`                  |                                                   |
+----------------------------+------------------------------------------------+---------------------------------------------------+

MetaGen is designed primarily for developing **Standard** and **Flexible** metaheuristics. However, advanced users can extend the framework to create **Extended** metaheuristics when needed.

By selecting the appropriate approach, developers can ensure their metaheuristics are both efficient and compatible with future enhancements in MetaGen.