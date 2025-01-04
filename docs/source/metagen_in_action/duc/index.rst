.. include:: ../../aliases.rst

=================================================================================
How to use to implement your own metaheuristic (Development Use Case)
=================================================================================

.. toctree::
    :maxdepth: 1

    rs
    sa
    ga
    ssga
    cvoa

A user (*developer*) can implement four types of metaheuristics depending on their programming skills.

|metagen| is conceived as a framework to develop Base/Universal Base metaheuristics. However, high-level programmers are enabled to modify the core of the package to extend its functionality.

These types are explained below.

Base metaheuristic
-------------------

A *developer* uses the standard |solution| class similarly to a *solver* who uses the |domain| class.

It instantiates the class and calls its methods to initialize, modify, and evaluate the potential solutions. In this case, the *developer* is isolated from the management of the potential solution's management, and the nature of the metaheuristic determines its programming skills.

The newly implemented metaheuristic works with any problem defined by the  |domain| class and any fitness function implemented with the standard |solution| class.

Universal Base metaheuristic
-----------------------------

This case is similar to the previous one. However, the |solution| class is instantiated using the |baseconnector| class, which can be obtained using the |get_connector| method of the |domain| class.

Once instantiated, the *developer* uses the standard |solution| class in the metaheuristic code, as in the previous case.

This action makes the metaheuristic work not only with the |domain| and the standard |solution| classes but also with custom |solution| classes.

A high-level programmer can implement a custom |solution| class by taking the following steps:

- Extend the type classes to customize and redefine their methods or create new ones.
- Extend the |solution| class, redefine its methods, or create new ones.
- Extend the |baseconnector| class to map the redefined type classes with the standard ones.

Extended metaheuristic
-------------------------
A high-level programmer implements a metaheuristic with their custom |solution| class following the previously mentioned method.

A *solver* must use that custom |solution| class to implement the fitness function.

Universal Extended metaheuristic
-----------------------------------
This case is the same as the previous one but becomes universal by using the |baseconnector| class, as described in the second point.

A *solver* can implement the fitness function in any |solution| class (standard or custom).
