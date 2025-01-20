.. include:: ../../aliases.rst

=================================================================================
How to use to implement your own metaheuristic (**Development Use Case**)
=================================================================================

A *developer* uses the standard |solution| class to initialize, modify, and evaluate the potential solutions (trials) of the new metaheuristic.

In this way, the *developer* is isolated from the management of the potential solution's management, and the nature of the metaheuristic determines its programming skills.

The newly implemented metaheuristic works with any problem defined by the |domain| class and any fitness function implemented with the standard |solution| class.

.. toctree::
    :maxdepth: 1

    rs
    sa
