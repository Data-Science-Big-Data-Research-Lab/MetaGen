Tunning a scikit-learn Random Forest classification model
===========================================================

Solving use cases in google colab:

    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p1.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p2.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p3.ipynb
    * https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p4.ipynb

In this section, a hyperparameter optimization use case is detailed employing the Metagen library and scikit-learn in five steps.

Step 1: Import the required libraries. In most cases only the Domain and the meta-heuristic is required, the solution is included in this case just for type checking.

.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     from sklearn.ensemble import RandomForestClassifier


Step 2: Select your datasets. In this case, a syntetic classification dataset has been employed.

.. code-block:: python

    X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)



Step 3: Define the domain. The usual hyperparameters of a random forest classifier has been defined in our domain.

.. code-block:: python

    random_forest_classifier_definition = Domain()
    random_forest_classifier_definition.define_integer("max_depth", 2, 100, 1)
    random_forest_classifier_definition.define_integer("n_estimators", 10, 500, 1)
    random_forest_classifier_definition.define_categorical("criterion", ['gini', 'entropy'])
    random_forest_classifier_definition.define_categorical("max_features", ['auto', 'sqrt', 'log2'])


Step 4: Define fitness function. In this case, the the averaged accuracy over the folds on the cross validation has been selected. Note that the solution can be accessed like a dictionary to obtain the sampled hyparameters.

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

Step 5: Use an already defined meta-heuristic in the metagen framework.

.. code-block:: python

    random_search: RandomSearch = RandomSearch(random_forest_classifier_definition, random_forest_classifier_fitness)
    best_solution: Solution = random_search.run()

Every meta-heuristic receives the domain definition and the fitness function at least. The instances contains the `run` function which executes the algorithm and always returns a the best Solution.