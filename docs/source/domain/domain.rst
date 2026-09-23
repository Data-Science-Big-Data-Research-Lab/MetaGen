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

* **Structure**: a list whose elements share one definition, which may be basic, a group or another structure, or have one definition per position (see below). A **static** structure has a fixed length; a **dynamic** one has a length between a minimum and a maximum, optionally on a grid of a given step, and the search changes it.
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

By default the elements of a structure share one definition. With ``set_structure_to_variables`` every **position** gets a definition of its own instead, one already defined variable per position, in order: as many as the length of a static structure or the maximum length of a dynamic one. Element ``i`` is then always drawn, mutated and checked against the ``i``-th definition, and a dynamic structure grows and shrinks at its end, so that the elements keep their positions. The definitions may differ in range and in type, and may be groups.

.. code-block:: python

    from metagen.framework import Domain

    domain = Domain()
    domain.define_dynamic_structure("filters", 1, 3)       # one to three convolutional layers
    domain.define_integer("first", 8, 32)
    domain.define_integer("second", 16, 64)
    domain.define_integer("third", 32, 128)
    domain.set_structure_to_variables("filters", ["first", "second", "third"])

A solution of this domain holds ``[20]``, ``[12, 40]`` or ``[30, 50, 100]``, for instance: the first element is always between 8 and 32, the second between 16 and 64 and the third between 32 and 128. As with ``set_structure_to_variable``, the variables move into the structure unless ``remember=True`` is given.

Internally every definition answers ``get_attributes()`` with a tuple whose first element names its type:

* ``("INTEGER", minimum, maximum, step)`` and ``("REAL", minimum, maximum, step)``, with ``None`` as the step when there is no grid.
* ``("CATEGORICAL", [categories])``.
* ``("DEFINITION", {"name": attributes, ...})`` for a group.
* ``("STATIC", length, attributes of the element)`` for a static structure.
* ``("DYNAMIC", minimum length, maximum length, length step, attributes of the element)`` for a dynamic one.
* In a structure with a definition per position, the attributes of the element are a tuple with the attributes of each position.

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
    ~Domain.set_structure_to_variables
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

