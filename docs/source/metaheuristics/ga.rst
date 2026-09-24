Basic genetic algorithm
===========================

.. autoclass:: metagen.metaheuristics.GA
    :members:
    :show-inheritance:

Steady-state genetic algorithm
================================

.. autoclass:: metagen.metaheuristics.SSGA
    :members:
    :show-inheritance:


The genetic connector and its types
=====================================

The genetic algorithms cross solutions over, so their domain is built with
``Domain(connector=GAConnector())``. The connector maps the definitions to the types below,
which add a ``crossover`` method to the standard ones.

.. autoclass:: metagen.metaheuristics.genetic.genetic_tools.GAConnector
    :show-inheritance:

.. autoclass:: metagen.metaheuristics.genetic.genetic_tools.GASolution
    :members: crossover
    :show-inheritance:

.. autoclass:: metagen.metaheuristics.genetic.genetic_tools.GAStructure
    :members: crossover
    :show-inheritance:
