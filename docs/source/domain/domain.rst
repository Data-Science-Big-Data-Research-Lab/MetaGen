Domain
=================

.. contents:: Table of Contents
    :depth: 3

=================
Definitions
=================
   
The ``Domain`` class describes the space of the solutions: which variables a solution has, of which type, and between which bounds. A variable is of one of three kinds:

* **Basic**: a single value.

    * ``INTEGER``: an integer between a minimum and a maximum, optionally on a grid of a given step that starts at the minimum.
    * ``REAL``: a floating point number between a minimum and a maximum, optionally on a grid of a given step.
    * ``CATEGORICAL``: one value out of a list of categories, which must all be of the same type (``int``, ``float``, ``str`` or ``bool``) and must not repeat. A single category is allowed, to fix a hyperparameter to one value.

* **Structure**: a list whose elements all share one definition, which may be basic, a group or another structure. A **static** structure has a fixed length; a **dynamic** one has a length between a minimum and a maximum, optionally on a grid of a given step, and the search changes it.
* **Group**: a set of named variables that travel together, such as the settings of one layer of a neural network. A structure of groups describes, for instance, an architecture with a variable number of layers.

.. code-block:: python

    from metagen.framework import Domain

    domain = Domain()
    domain.define_real("learning_rate", 0.0001, 0.1)
    domain.define_integer("batch_size", 16, 256, 16)            # 16, 32, 48 ... 256
    domain.define_categorical("solver", ["adam", "sgd"])

    domain.define_group("layer")
    domain.define_integer_in_group("layer", "neurons", 8, 128)
    domain.define_real_in_group("layer", "dropout", 0.0, 0.5)
    domain.define_dynamic_structure("architecture", 1, 4)       # one to four layers
    domain.set_structure_to_variable("architecture", "layer")

Internally every definition answers ``get_attributes()`` with a tuple whose first element names its type:

* ``("INTEGER", minimum, maximum, step)`` and ``("REAL", minimum, maximum, step)``, with ``None`` as the step when there is no grid.
* ``("CATEGORICAL", [categories])``.
* ``("DEFINITION", {"name": attributes, ...})`` for a group.
* ``("STATIC", length, attributes of the element)`` for a static structure.
* ``("DYNAMIC", minimum length, maximum length, length step, attributes of the element)`` for a dynamic one.

The details of the definition are described in the `Core`_.

=================
Domain class
=================

.. currentmodule:: metagen.framework

.. autosummary::
    ~Domain.__init__
    ~Domain.define_integer
    ~Domain.define_real
    ~Domain.define_categorical
    ~Domain.define_group
    ~Domain.define_integer_in_group
    ~Domain.define_real_in_group
    ~Domain.define_categorical_in_group
    ~Domain.link_variable_to_group
    ~Domain.define_dynamic_structure
    ~Domain.define_static_structure
    ~Domain.set_structure_to_integer
    ~Domain.set_structure_to_real
    ~Domain.set_structure_to_variable
    ~Domain.get_core

.. autoclass:: metagen.framework.Domain
    :members:
    :show-inheritance:

=================
Core
=================

.. inheritance-diagram:: metagen.framework.domain.core
    :top-classes: metagen.framework.domain.core.Base, metagen.framework.domain.core.BaseStructureDefinition
    :parts: 1

Base
----------
.. autoclass:: metagen.framework.domain.core.Base
    :members:
    :show-inheritance:

.. autoclass:: metagen.framework.domain.core.BaseDefinition
    :members:
    :show-inheritance:

.. autoclass:: metagen.framework.domain.core.BaseStructureDefinition
    :members:
    :show-inheritance:


IntegerDefinition
----------------------------
.. autoclass:: metagen.framework.domain.core.IntegerDefinition
    :members:
    :show-inheritance:

RealDefinition
----------------------------
.. autoclass:: metagen.framework.domain.core.RealDefinition
    :members:
    :show-inheritance:

CategoricalDefinition
----------------------------
.. autoclass:: metagen.framework.domain.core.CategoricalDefinition
    :members:
    :show-inheritance:

DynamicStructureDefinition
----------------------------
.. autoclass:: metagen.framework.domain.core.DynamicStructureDefinition
    :members:
    :show-inheritance:

StaticStructureDefinition
----------------------------
.. autoclass:: metagen.framework.domain.core.StaticStructureDefinition
    :members:
    :show-inheritance:

Definition
----------------------------
.. autoclass:: metagen.framework.domain.core.Definition
    :members:
    :show-inheritance:

