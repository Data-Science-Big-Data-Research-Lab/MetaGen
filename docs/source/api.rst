.. include:: aliases.rst

API Reference
=============

This section provides comprehensive documentation for |metagen|'s core components and APIs.

Core Components
---------------

.. toctree::
    :maxdepth: 2
    :caption: API Documentation

    domain/domain
    solution/solution
    metaheuristics/index
    connector/connector
    triclustering/reference

Public API
----------

What a program imports comes from these packages, and the names each of them lists in its
``__all__`` are the public API:

- ``metagen.framework``, with ``metagen.framework.domain`` (the definitions) and
  ``metagen.framework.solution`` (the solution types), for extending the framework
- ``metagen.metaheuristics``, the algorithms and what writing one of your own takes
- ``metagen.triclustering``, with ``metagen.triclustering.data`` for loading data
- ``metagen.reporting`` and ``metagen.logging``

The modules inside them are where each name is implemented, and they may be reorganized
between releases. The version of the installed package is ``metagen.__version__``:

.. code-block:: python

    import metagen
    from metagen.metaheuristics import CVOA, Metaheuristic, random_exploration

    print(metagen.__version__)

Component Overview
------------------

- **Domain**: Define problem search spaces and variable constraints
- **Solution**: Represent and manipulate potential solutions
- **Metaheuristics**: Optimization algorithms and strategies
- **Connector**: Bridge between domain definitions and solution representations
- **Triclustering**: Data, triclusters and the measures of their quality

Usage Guidelines
----------------

- Refer to each component's documentation for detailed usage instructions
- Use type hints and docstrings for context-aware development
- Explore example implementations in the :doc:`metagen_in_action/index` section

Extensibility
-------------

|metagen| is designed to be easily extensible. Developers can:

- Create custom domain types
- Implement new solution manipulation strategies
- Develop novel metaheuristic algorithms

For advanced usage and customization, consult the :doc:`advanced_topics/index` section.