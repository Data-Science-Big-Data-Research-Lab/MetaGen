.. include:: ../aliases.rst

CVOA - Coronavirus Optimization Algorithm
==========================================

The Coronavirus Optimization Algorithm: several strains run at once over a shared pandemic state, through a launcher. How to run it and how its two strain classes differ is in :ref:`choosing/index:Running CVOA`; this page is the reference.

Launchers
---------

.. autofunction:: metagen.metaheuristics.cvoa_launcher

.. autofunction:: metagen.metaheuristics.distributed_cvoa_launcher

Strain properties
-----------------

.. autoclass:: metagen.metaheuristics.StrainProperties
    :members:

The strain classes
------------------

.. autoclass:: metagen.metaheuristics.CVOA
    :members:
    :show-inheritance:

.. autoclass:: metagen.metaheuristics.ProbabilisticCVOA
    :members:
    :show-inheritance:

``DistributedCVOA`` is kept for backward compatibility: it is |cvoa| with ``distributed=True``.

.. autoclass:: metagen.metaheuristics.DistributedCVOA
    :show-inheritance:
