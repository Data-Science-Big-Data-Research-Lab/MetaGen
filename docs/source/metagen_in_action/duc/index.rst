.. include:: ../../aliases.rst

==================================================================================
How to implement your own metaheuristic (**Development Use Case**)
==================================================================================

A *developer* uses the standard |solution| class to initialize, modify, and evaluate the potential solutions (trials) of the new metaheuristic.

In this way, the *developer* does not have to manage the potential solutions, and can concentrate on the logic of the metaheuristic.

The newly implemented metaheuristic works with any problem defined by the |domain| class and any fitness function implemented with the standard |solution| class.

.. toctree::
    :maxdepth: 1

    rs
    sa
