.. include:: aliases.rst

Welcome to |metagen|!
=====================

|metagen| is a Python scientific package designed to provide users with a comprehensive system for:

- Solution representation
- Methods to generate and modify solutions
- A standard interface between metaheuristics and potential users

These features simplify the development of metaheuristics and make hyperparameter tuning more accessible in machine learning model production.

.. figure:: images/overview.png
    :align: center
    :width: 400
    :alt: MetaGen's overview
    :class: vspace
    :name: fig-overview

    |metagen|'s architectural overview.

Key Design Principles
----------------------

1. **Abstraction**: Separate problem definition from solution exploration
2. **Flexibility**: Support for diverse optimization strategies
3. **Extensibility**: Easy integration of custom algorithms and problem domains
4. **Usability**: Intuitive interfaces for developers and researchers

Use Cases
----------
- Machine Learning Hyperparameter Tuning
- Deep Learning Architecture Optimization
- Scientific Computational Problems
- Engineering Design Optimization

User Profiles
-------------

|metagen| supports two primary user profiles:

Developer Profile
^^^^^^^^^^^^^^^^^

- Implements metaheuristics using the |solution| class
- Follows the **Development Use Case (DUC)**
- Simplifies algorithm development process
- Makes metaheuristic implementation accessible to a broader audience

Solver Profile
^^^^^^^^^^^^^^

- Defines problem using |domain| class tools
- Implements fitness function for optimization
- Uses |solution| class to explore potential solutions
- Follows the **Solving Use Case (SUC)**
- Can use built-in or third-party metaheuristics

Key Features
------------

- **Intuitive Development**: Lowers the barrier to creating new metaheuristics
- **Standardized Interface**: Isolates developer from end-user complexities
- **Dynamic Optimization**: Tools for adjusting deep learning architectures
- **Type Hints**: Leverages Python's typing for improved development experience
- **Flexible Problem Definition**: Easy-to-use domain configuration

For more details, explore the :doc:`understanding_metagen/index` section.

Installation
-------------

using pip:

.. code-block:: console

   (.venv) $ pip install pymetagen-datalabupo


Quick Example
--------------

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics import RandomSearch

    # Define problem domain
    domain = Domain()
    domain.defineInteger('x', -10, 10)
    domain.defineReal('y', -5, 5)

    # Define fitness function
    def fitness_function(solution):
        x, y = solution['x'], solution['y']
        return x**2 + y**2

    # Run optimization
    search = RandomSearch(domain, fitness_function)
    best_solution = search.run()

Index
-----

.. toctree::
    :maxdepth: 2

    understanding_metagen/index
    metagen_in_action/index
    performance_tracking/index
    distributed_execution/index
    advanced_topics/index
    api
