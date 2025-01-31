.. include:: ../aliases.rst

=============================================
Extending MetaGen with Custom Variable Types
=============================================

|metagen| provides a **flexible framework** for representing and managing solutions in optimization problems.
While it includes a variety of predefined types—such as integers, real numbers, categorical values, and structures—developers can **extend these types** or create entirely new ones to suit specific needs.

This section explains how to:
- Define a **new variable type**.
- Implement a **custom Solution class**.
- Integrate the new type using a **BaseConnector**.
- Use the new type correctly by specifying the **appropriate connector** when defining a domain.

A concrete example of this extension is the **Genetic Algorithm (GA) implementation in** |metagen|, which introduces **GAStructure** and **GASolution** as custom types.


Why Extend Variable Definitions?
--------------------------------

Extending variable definitions allows:
- Custom **data representations** for optimization problems.
- Domain-specific **constraints** while maintaining compatibility with |metagen|’s framework.
- Seamless integration with **existing metaheuristics**.

1. Extending the Structure Type in GA
The **Genetic Algorithm (GA)** in |metagen| introduces a custom `GAStructure`, which extends the standard `Structure` class and supports crossover operations:

.. code-block:: python

    class GAStructure(Structure):
        def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
            """ Performs crossover between two GAStructure instances. """
            # Implementation details...

2. Creating a Custom Solution Type
The custom `GASolution` integrates `GAStructure`, modifying how solutions interact within the metaheuristic:

.. code-block:: python

    class GASolution(Solution):
        def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
            """ Performs crossover between two GASolution instances. """
            # Implementation details...

3. Integrating the New Types with a Custom Connector
To ensure compatibility, GA defines `GAConnector`, which **links the new solution and structure types** with the |metagen| framework:

.. code-block:: python

    class GAConnector(BaseConnector):
        def __init__(self):
            super().__init__()
            self.register(BaseDefinition, GASolution, dict)
            self.register(StaticStructureDefinition, (GAStructure, "static"), list)

---

Using the New Type in a Metaheuristic
-------------------------------------
When using a custom **Solution type**, the domain must be instantiated **with the corresponding connector** to ensure correct type mapping.

For example, when defining a **Random Forest Regressor optimization domain**, the **GAConnector** must be explicitly passed:

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics.ga.ga_tools import GAConnector

    domain = Domain(GAConnector())
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)
    domain.define_categorical("criterion", ['absolute_error', 'squared_error', 'friedman_mse'])
    domain.define_categorical("max_features", ['sqrt', 'log2'])

If the connector is not explicitly provided, the default **BaseConnector** will be used, which may not include custom solution types like `GASolution` or `GAStructure`.

By following this approach, developers can **extend** |metagen| **with new types**, while ensuring full compatibility with **existing metaheuristics** and the overall framework.