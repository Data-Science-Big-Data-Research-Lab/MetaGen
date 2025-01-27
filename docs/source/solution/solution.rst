Solution
================
.. contents:: Table of Contents
    :depth: 4

=================
Solution class
=================

.. currentmodule:: metagen.framework

.. autosummary::
    ~Solution.__init__
    ~Solution.get_variables
    ~Solution.get_definition
    ~Solution.set
    ~Solution.get
    ~Solution.get_connector
    ~Solution.evaluate
    ~Solution.set_fitness
    ~Solution.get_fitness
    ~Solution.keys
    ~Solution.values
    ~Solution.is_available
    ~Solution.initialize
    ~Solution.mutate

.. autoclass:: metagen.framework.Solution
    :members:
    :private-members:

=================
Types
=================

.. inheritance-diagram:: metagen.framework.solution.types.base metagen.framework.solution.types.integer metagen.framework.solution.types.real metagen.framework.solution.types.categorical metagen.framework.solution.types.structure
    :top-classes: metagen.framework.solution.types.base.BaseType
    :parts: 1

BaseType
-------------
.. autoclass:: metagen.framework.solution.types.BaseType
    :members:
    :show-inheritance:

Integer
------------
.. autoclass:: metagen.framework.solution.types.Integer
    :members:
    :show-inheritance:

Real
------------
.. autoclass:: metagen.framework.solution.types.Real
    :members:
    :show-inheritance:

Categorical
------------
.. autoclass:: metagen.framework.solution.types.Categorical
    :members:
    :show-inheritance:

Structure
------------
.. autoclass:: metagen.framework.solution.types.Structure
    :members:
    :private-members:
    :show-inheritance: