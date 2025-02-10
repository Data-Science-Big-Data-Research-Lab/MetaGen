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

Component Overview
------------------

- **Domain**: Define problem search spaces and variable constraints
- **Solution**: Represent and manipulate potential solutions
- **Metaheuristics**: Optimization algorithms and strategies
- **Connector**: Bridge between domain definitions and solution representations

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