.. include:: ../../aliases.rst

==================================================================================
How to define a problem and solve it using a metaheuristic (**Solving Use Case**)
==================================================================================

A *solver* have to make the following steps to solve a optimization problem (typically a hyperparameter optimization problem) using a |metagen|:

1. Define the problem space using the |domain| class.
2. Implement the fitness function using the |solution| class.
3. Choose a metaheuristic to solve the problem (can be a |metagen|'s implemented one or a custom one), instantiate it, and run it.

For example, to solve the following simple problem :math:`x + 5` where :math:`x \in \mathbb{I},\ -5 \leq x \leq 10`, you can use the Random Search algorithm by coding the following Python script:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.heuristics import RandomSearch

    # Step 1: Define the problem space
    domain = Domain()
    domain.define_integer("x", -5, 10)

    # Step 2: Implement the fitness function
    def fitness(solution: Solution) -> float:
        x = solution["x"]
        return x+5

    # Step 3: Choose a metaheuristic and run it
    best_solution: Solution = RandomSearch(domain, fitness).run()


Or, to solve another simple problem like :math:`x^2` where :math:`x \in \mathbb{R},\ 0 \leq x, y \leq 1`, you can use the Random Search algorithm by coding the following Python script:

.. code-block:: python

    from metagen.framework import Domain, Solution
    from metagen.heuristics import RandomSearch

    # Step 1: Define the problem space
    domain = Domain()
    domain.define_real("x", 0, 1)

    # Step 2: Implement the fitness function
    def fitness(solution: Solution) -> float:
        x = solution["x"]
        return x**2

    # Step 3: Choose a metaheuristic and run it
    best_solution: Solution = RandomSearch(domain, fitness).run()

Both simple examples can be executed by these Google Colab Notebooks:

* `x+5 <https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p1.ipynb>`_
* `x² <https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p2.ipynb>`_

Next, we will show how to use |metagen| to solve two hyperparameter optimization problems to tune a Random Forest Classifier using the scikit-learn library and a Deep Neural Network using the TensorFlow library.

.. toctree::
    :maxdepth: 1

    scikit-learn
    tensorflow