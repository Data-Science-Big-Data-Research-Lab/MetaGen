Domain
=================

.. contents:: Table of Contents
    :depth: 3

=================
Definitions
=================
   
This module describes the ``domain`` class which represents the space of the solution.

The variable definitions are internally stored in a member variable which support three different TYPES:

* ``BASIC``: Includes support for the basic types INTEGER, REAL and CATEGORICAL which are definitions of int, float and list respectively.
    
    * ``INTEGER``: Support integer possitive/negative numerical values.
    * ``REAL``: Support floating point possitive/negative numerical values.
    * ``CATEGORICAL``: Support list of int, float and str values. Every component in the category must have the same type.

* ``VECTOR``: Support an list of numerical values (``INTEGER`` or ``REAL``) with fixed range. The ``VECTOR`` also support for variable size definition.
* ``LAYER``: Support complex structures as a dictionary. The layer defines some variables (string) which value may be the previously described.

Every variable has a different definition depending of its ``TYPE`` using the tuple:
.. code-block:: python

    (``TYPE``, ``*args``)

where ``TYPE`` represents any type defined previously, while args are the specific configuration depending of its ``TYPE``.

**Structure for** ``BASIC`` **definition (** ``BASICDEF`` **)**

* ``INTEGERDEF``: (``INTEGER``, Maximum value [int], Minimum value [int], Step[int])
* ``REALDEF``: (``REAL``, Maximum value [float], Minimum value [float], Step[float])
* ``CATEGORICALDEF``: (``CATEGORICAL``, Categories[list(``BASIC``)*])

**Internal structure for** ``LAYER`` **definition (** ``LAYERDEF`` **)**

(``LAYER``, {``"ATTRIBUTE"``: ``BASICDEF``, ``"ATTRIBUTE"``: ``VECTORDEF``, ...})

**Internal structure for** ``VECTOR`` **definition (** ``VECTORDEF`` **)**

* (``VECTOR``, Maximum size [int], Minimum size [int], Step size [int], [``INTEGERDEF``, ...])
* (``VECTOR``, Maximum size [float], Minimum size [float], Step size [float], [``REALDEF``, ...])
* (``VECTOR``, Maximum size [float], Minimum size [float], Step size [float], [``CATEGORICALDEF``, ...])
* (``VECTOR``, Maximum size [float], Minimum size [float], Step size [float], [``LAYERDEF``, ...])

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

