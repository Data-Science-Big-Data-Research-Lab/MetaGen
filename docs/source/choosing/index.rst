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


Setting a budget
----------------

Every metaheuristic but CVOA also takes ``max_evaluations``, the evaluations of the fitness function a run may make, warmup included, and ``timeout``, the seconds it may last. Without ``max_iterations``, a budget is what stops the run: the limit of iterations is lifted, and |sa|, |tpe|, |kernel_tpe| and a |hc| with a ``gamma_config``, which plan their search over ``max_iterations`` (the cooling schedule, the gamma schedule), take as ``max_iterations`` the iterations that ``max_evaluations`` buys; with ``timeout`` alone they keep their default. Given ``max_iterations`` and a limit, the run stops at whichever comes first. The limits are checked between the rounds of the warmup and between iterations, never in the middle of one, so a run goes past them by at most one round of the warmup and the initial population, which is always evaluated whole, or by one iteration, that is one evaluation for |kernel_tpe| and a whole population for a genetic algorithm or |rs|. With ``timeout``, a run goes past it by the time those evaluations take, which with a slow fitness function can be long. ``evaluations`` and ``seconds`` say what the run spent, and ``stop_reason`` what stopped it: ``"criterion"``, ``"max_evaluations"``, ``"timeout"`` or ``"request_stop"``.

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics import KernelTPE, RandomSearch

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 1, 100)

    def fitness(solution):
        return (solution["x"] - 1.0) ** 2 + abs(solution["n"] - 42) / 10

    search = KernelTPE(domain, fitness, population_size=10, warmup_iterations=0, max_evaluations=100, seed=0)
    search.run()
    print(search.evaluations, search.stop_reason)   # 100 max_evaluations
    print(search.max_iterations)                     # 90: the evaluations left after the 10 initial ones

    # A random search evaluates 29 individuals per iteration: it stops past the limit.
    search = RandomSearch(domain, fitness, population_size=30, max_evaluations=100, seed=0)
    search.run()
    print(search.evaluations, search.stop_reason)   # 117 max_evaluations

A run resumed from a checkpoint (see :doc:`../pausing_and_resuming/index`) carries on with what it had spent, so it stops where an uninterrupted run would. In a distributed run the evaluations of the workers count too.


Stopping bad evaluations early: racing
--------------------------------------

When evaluating a solution takes steps, such as the folds of a cross-validation, a fitness function can **yield** the value of each step instead of returning one number: its value is then the mean of its steps, all of them in the same order for every solution. With ``racing=Racing()`` a candidate stops as soon as it is significantly worse than the population its iteration started from, as F-race and irace do (Birattari et al., 2002; López-Ibáñez et al., 2016): after each step from ``first_steps`` on (3 by default), a Friedman test over the candidate and the population, followed by Conover's comparison against the best of them, decides at level ``alpha`` (0.05 by default) whether it gets more steps. The initial population is evaluated whole.

.. code-block:: python

    from sklearn.datasets import load_breast_cancer
    from sklearn.model_selection import StratifiedKFold
    from sklearn.tree import DecisionTreeClassifier

    from metagen.framework import Domain
    from metagen.metaheuristics import Racing, RandomSearch

    X, y = load_breast_cancer(return_X_y=True)
    folds = list(StratifiedKFold(10, shuffle=True, random_state=0).split(X, y))

    domain = Domain()
    domain.define_integer("max_depth", 1, 20)
    domain.define_integer("min_samples_leaf", 1, 60)

    def fitness(solution):
        for train, test in folds:                       # one error rate per fold
            model = DecisionTreeClassifier(max_depth=solution["max_depth"],
                                           min_samples_leaf=solution["min_samples_leaf"],
                                           random_state=0).fit(X[train], y[train])
            yield 1.0 - model.score(X[test], y[test])

    search = RandomSearch(domain, fitness, population_size=20, max_iterations=5, racing=Racing(), seed=0)
    best = search.run()
    print(search.evaluations, search.history[-1]["steps"])   # 115 817: 817 folds of the 1150 of evaluating every candidate whole
    print(round(best.get_fitness(), 4), best.raced_out)        # 0.0633 False

A candidate stopped early is marked with ``raced_out`` and is never the best solution of a run; its fitness is its mean over the steps it took, corrected by how the mean of the population changes from those steps to all of them. Every solution keeps its values per step in ``step_values``, and the history records the steps taken. With racing, ``max_evaluations`` counts the steps: a candidate stopped after 3 of 10 spends 0.3 of an evaluation.

Starting from known solutions
-----------------------------

``initial_solutions`` starts a run from solutions known beforehand, such as the configuration of an earlier study or the defaults of a library: each a mapping from variable names to values, with any variable left out drawn at random. They take the place of as many solutions of the initial population, so the cost of the run does not change, and they count as any other: the best of the run may be one of them. A metaheuristic takes at most ``population_size`` of them, and a value that does not fit the domain raises an error when the metaheuristic is built.

.. code-block:: python

    from metagen.framework import Domain
    from metagen.metaheuristics import KernelTPE

    domain = Domain()
    domain.define_real("x", -5.0, 5.0)
    domain.define_integer("n", 1, 100)

    def fitness(solution):
        return (solution["x"] - 1.0) ** 2 + abs(solution["n"] - 42) / 10

    known = [{"x": 1.0, "n": 40}, {"n": 45}]           # x of the second one is drawn
    search = KernelTPE(domain, fitness, population_size=10, max_evaluations=100,
                       initial_solutions=known, seed=0)
    search.run()
    print(search.best_solution_fitnesses[0])   # 0.2: the first known solution is the best to start from
    print(search.evaluations)                  # 100

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
