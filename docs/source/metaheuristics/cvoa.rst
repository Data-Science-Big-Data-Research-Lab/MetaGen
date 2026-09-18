.. include:: ../aliases.rst

CVOA - Coronavirus Optimization Algorithm
==========================================

The Coronavirus Optimization Algorithm: several strains run at once over a shared pandemic state, through a launcher. How to run it and how its two strain classes differ is in :ref:`choosing/index:Running CVOA`; this page is the reference.

Launchers
---------

.. autofunction:: metagen.metaheuristics.cvoa.local_launcher.cvoa_launcher

.. autofunction:: metagen.metaheuristics.cvoa.distributed_launcher.distributed_cvoa_launcher

Strain properties
-----------------

.. autoclass:: metagen.metaheuristics.cvoa.common_tools.StrainProperties
    :members:

The strain classes
------------------

.. autoclass:: metagen.metaheuristics.cvoa.cvoa_local.CVOA
    :members:
    :show-inheritance:

.. autoclass:: metagen.metaheuristics.cvoa.cvoa_probabilistic.ProbabilisticCVOA
    :members:
    :show-inheritance:

``DistributedCVOA`` is kept for backward compatibility: it is |cvoa| with ``distributed=True``.

.. autoclass:: metagen.metaheuristics.cvoa.cvoa_distributed.DistributedCVOA
    :show-inheritance:
