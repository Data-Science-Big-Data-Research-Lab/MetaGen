.. include:: ../../aliases.rst

Tuning a scikit-learn Random Forest classification model
===========================================================

Google Colab Notebook: `Random Forest <https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p3.ipynb>`_

As preliminary step the following code can be used to generate a synthetic dataset.

.. code-block:: python

    from sklearn.datasets import make_classification
    X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)

Firstly, the required libraries must be imported. In this case, the |domain|, |solution| and the |rs| metaheuristic are imported from the metagen framework. The RandomForestClassifier is imported from the scikit-learn library.

.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     from sklearn.ensemble import RandomForestClassifier

Next, the domain definition is created. The domain definition is used to define the search space of the hyperparameters. In this case, the hyperparameters are the `max_depth`, `n_estimators`, `criterion` and `max_features` of the RandomForestClassifier. The |define_integer| method is used to define the integer hyperparameters, while the |define_categorical| method is used to define the categorical hyperparameters.

.. code-block:: python

    random_forest_classifier_definition = Domain()
    random_forest_classifier_definition.define_integer("max_depth", 2, 100, 1)
    random_forest_classifier_definition.define_integer("n_estimators", 10, 500, 1)
    random_forest_classifier_definition.define_categorical("criterion", ['gini', 'entropy'])
    random_forest_classifier_definition.define_categorical("max_features", ['auto', 'sqrt', 'log2'])

Now, the fitness function is defined. It is used to evaluate every potential solution. In this case, the fitness function is the averaged accuracy over the folds on the cross validation. The |solution| variables can be accessed like a dictionary to obtain the sampled hyperparameters.

.. code-block:: python

    def random_forest_classifier_fitness(solution):
        max_depth = solution["max_depth"]
        n_estimators = solution["n_estimators"]
        criterion = solution["criterion"]
        max_features = solution["max_features"]

        clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                     max_features=max_features, random_state=0, n_jobs=-1)
        scores = cross_val_score(clf, X_classification, y_classification,
                                 scoring="accuracy", cv=10, n_jobs=-1)

        return -scores.mean()

Finally, a metaheuristic is used to find the best hyperparameters. In this case, the |rs| metaheuristic is used to randomly sample the search space and evaluate the fitness function.

.. code-block:: python

    random_search: RandomSearch = RandomSearch(random_forest_classifier_definition, random_forest_classifier_fitness)
    best_solution: Solution = random_search.run()

Every metaheuristic receives the |domain| definition and the **fitness function** at least. The instances contains the **run** function which executes the algorithm and always returns a the best |solution|.