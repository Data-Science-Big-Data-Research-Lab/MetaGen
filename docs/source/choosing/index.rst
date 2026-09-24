.. include:: ../aliases.rst

==========================
Choosing a metaheuristic
==========================

Every metaheuristic takes a |domain| and a fitness function, **minimizes**, and returns the best |solution| it found from ``run()``. They all accept ``seed`` (a reproducible run), ``log_dir`` (TensorBoard logs) and, except CVOA, which has its own launcher, ``distributed`` and ``distribution_model`` (see :doc:`../distributed_execution/distributed`).


Which one to use
----------------

.. list-table::
    :header-rows: 1
    :widths: 18 52 30

    * - Metaheuristic
      - What it is
      - Evaluations with its defaults
    * - |rs|
      - Keeps the best individual and mutates the rest over the whole domain.
      - ``population_size + (population_size − 1) × max_iterations``
    * - |hc|
      - Samples neighbors around the best solution and moves only when one improves.
      - at most ``population_size × (warmup_iterations + 1 + max_iterations)``
    * - |ts|
      - Tabu search: it moves to the best non-tabu neighbor even when it is worse, which lets it leave a local optimum.
      - as ``HillClimbing``
    * - |sa|
      - One walking point that accepts a worse neighbor with a probability that falls as the temperature cools; the cooling schedule is tied to ``max_iterations``.
      - ``warmup + 1 + neighbor_population_size × max_iterations``
    * - |ga|
      - A generational genetic algorithm: tournament selection, a blend (BLX-alpha) crossover on numeric variables, local mutation and two elites.
      - ``population_size × (max_iterations + 1)``
    * - |ssga|
      - The steady-state variant: two children per iteration replace the two worst.
      - ``population_size + 2 × max_iterations``
    * - |mm|
      - A genetic algorithm whose children are refined by a local search, which makes each iteration cost several times a genetic algorithm's.
      - grows with ``neighbor_population_size`` per child
    * - |tpe|
      - A Tree-structured Parzen Estimator that models each variable with one Gaussian per side and evaluates a pool of candidates per iteration.
      - ``population_size × (warmup_iterations + 1) + candidate_pool_size × max_iterations``
    * - |kernel_tpe|
      - A Tree-structured Parzen Estimator that models each variable with a mixture of kernels and makes **one evaluation per iteration**, the candidate that maximizes l(x)/g(x); for fitness functions that are expensive to evaluate.
      - ``population_size × (warmup_iterations + 1) + max_iterations``
    * - |cvoa| and |probabilistic_cvoa|
      - The Coronavirus Optimization Algorithm, with two strain classes that differ in how deaths, superspreaders and isolation are decided. Run through a launcher (see :ref:`the section below <choosing/index:Running CVOA>`).
      - set by the pandemic, not by a parameter


**The genetic algorithms need their connector.** |ga|, |ssga| and |mm| cross solutions over, so their domain is created with ``Domain(connector=GAConnector())``; with a plain ``Domain()`` their constructor raises an error that says so. Every other metaheuristic takes a plain ``Domain()``.

**The warmup is part of the budget.** Several metaheuristics sample the domain at random for a few rounds before the search starts, and those evaluations cost the same as any other: with its defaults ``HillClimbing`` spends ``population_size × (warmup_iterations + 1)`` evaluations before its first iteration, and ``TPE`` spends 220. When the fitness function takes seconds or minutes, check that figure first and lower ``warmup_iterations`` or ``population_size`` if needed.

Running CVOA
------------

CVOA is the one metaheuristic that is not run through a class but through a **launcher**, because a pandemic is several strains searching at once over a shared state.

CVOA is a metaheuristic inspired by the spreading of the coronavirus: a pandemic starts from a patient zero, each infected individual spreads the infection to new individuals (mutations of itself), and the pandemic state (recovered, dead and isolated individuals) is shared by every strain. A strain is configured with :py:class:`~metagen.metaheuristics.cvoa.common_tools.StrainProperties`, whose defaults are the values suggested in the paper, and a pandemic is run with a launcher:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.metaheuristics import StrainProperties, cvoa_launcher

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_real("y", -5.0, 5.0)

    def fitness(solution: Solution) -> float:
        return solution["x"] ** 2 + solution["y"] ** 2

    # Social distancing from the third iteration keeps a pandemic over a continuous
    # domain short: the suggested setup, from the seventh, suits binary encodings.
    strains = [StrainProperties("Strain#1", pandemic_duration=10, social_distancing=3),
               StrainProperties("Strain#2", pandemic_duration=10, social_distancing=3, p_travel=0.2)]

    best_solution = cvoa_launcher(strains, domain, fitness, seed=0)

Two strain classes
^^^^^^^^^^^^^^^^^^

In |cvoa| the worst carriers die and the best ones become superspreaders, and an isolated individual is counted but its point stays open to later infections. In |probabilistic_cvoa| death and superspreading are drawn per individual with their probabilities, the isolated join the recovered, and the isolation and re-infection draws are one per carrier. Both run with the same launchers, through ``strain_class``:

.. code-block:: python

    from metagen.metaheuristics import ProbabilisticCVOA

    best_solution = cvoa_launcher(strains, domain, fitness, strain_class=ProbabilisticCVOA)

How far an infection moves
^^^^^^^^^^^^^^^^^^^^^^^^^^

An infection copies its carrier and changes some of its variables: one, or more when the carrier travels. By default each changed variable is drawn again over its whole domain. ``infection_alteration_limit`` keeps it near the carrier's value instead, as the local searches do: a ``RelativeAlteration`` is a fraction of each variable's own range, and a plain number an absolute amount. A binary variable flips either way. A neighborhood needs iterations to travel from the patients zero, so it suits pandemics that run for a while:

.. code-block:: python

    from metagen.framework import RelativeAlteration

    strains = [StrainProperties("Strain#1", pandemic_duration=15, social_distancing=3,
                                infection_alteration_limit=RelativeAlteration(0.2))]

    best_solution = cvoa_launcher(strains, domain, fitness, seed=0)

``cvoa_launcher`` runs each strain in a thread; ``distributed_cvoa_launcher`` runs each strain as a Ray task (see :doc:`../distributed_execution/special`). The launchers, the strain properties and the strain classes are documented in :doc:`../metaheuristics/cvoa`.
