.. include:: ../../aliases.rst

Optimizing the architecture of a tensorflow Deep Learning model
================================================================

Google Colab Notebook: `Deep Learning <https://colab.research.google.com/github/DataLabUPO/MetaGen/blob/master/notebooks/suc_p4.ipynb>`_

As preliminary step the following code can be used to generate a synthetic dataset.

.. code-block:: python

    from sklearn.datasets import make_regression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import numpy as np

    x, y = make_regression(n_samples=1000, n_features=24)
    x = normalize(x)
    x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.33, random_state=42)

    # Reshape for LSTM input
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))
    y_train = np.reshape(y_train, (y_train.shape[0], 1))
    x_val = np.reshape(x_val, (x_val.shape[0], x_val.shape[1], 1))
    y_val = np.reshape(y_val, (y_val.shape[0], 1))

Firstly, the required libraries must be imported. In this case, the |domain|, |solution| and the |rs| metaheuristic are imported from the metagen framework. The RandomForestClassifier is imported from the scikit-learn library.

.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     import tensorflow as tf

Next, the domain definition is created. The domain definition is used to define the search space of the hyperparameters. In this case, the hyperparameters are the `learning_rate`, `ema`, `arch` and `layer` of the neural network.

The |define_real| method is used to define the real hyperparameters, while the |define_categorical| method is used to define the categorical hyperparameters.

The |define_dynamic_structure| method is used to define the dynamic structure of the neural network.

The |define_group| method is used to define the group of hyperparameters, while the |define_integer_in_group|, |define_categorical_in_group| and |define_real_in_group| methods are used to define the hyperparameters inside the group.

Finally, the |set_structure_to_variable| method is used to link the `arch` variable to the definition of a `layer`. This will yield a architecture of from two to ten layers with a concrete set of `neurons`, `activation` function amd `dropout` for each potential |solution|.

.. code-block:: python

    nn_domain = Domain()
    nn_domain.define_real("learning_rate", 0.0, 0.000001)
    nn_domain.define_categorical("ema", [True, False])
    nn_domain.define_dynamic_structure("arch", 2, 10)
    nn_domain.define_group("layer")
    nn_domain.define_integer_in_group("layer", "neurons", 25, 300)
    nn_domain.define_categorical_in_group("layer", "activation", ["relu", "sigmoid", "softmax", "tanh"])
    nn_domain.define_real_in_group("layer", "dropout", 0.0, 0.45)
    nn_domain.set_structure_to_variable("arch", "layer")

Now, the fitness function is defined. It is used to evaluate every potential solution. In this case, the neural network is build considering the solution which encodes the hyperparameters. Secondly, the model is trained on the training set and evaluated on the validation set, returning the validation *MAPE*.

.. code-block:: python

    def build_neural_network(solution: Solution) -> tf.keras.Sequential:

            model = tf.keras.Sequential()

            for i, layer in enumerate(solution["arch"]):
                neurons = layer["neurons"]
                activation = layer["activation"]
                dropout = layer["dropout"]
                rs = True
                if i == len(solution["arch"]) - 1:
                    rs = False
                model.add(tf.keras.layers.LSTM(neurons, activation=activation, return_sequences=rs))
                model.add(tf.keras.layers.Dropout(dropout))

            model.add(tf.keras.layers.Dense(1, activation="tanh"))

            # Compile model
            learning_rate = solution["learning_rate"]
            ema = solution["ema"]
            model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate, use_ema=ema),
                  loss="mean_squared_error",
                  metrics=[tf.keras.metrics.MAPE])

            return model

    def nn_fitness(solution: Solution) -> float:
        model = build_neural_network(solution)
        batch_size = min(1024, x_train.shape[0])  # Avoid batch size error
        model.fit(x_train, y_train, epochs=10, batch_size=batch_size)
        mape = model.evaluate(x_val, y_val)[1]
        return mape

Finally, a metaheuristic is used to find the best hyperparameters. In this case, the |rs| metaheuristic is used to randomly sample the search space and evaluate the fitness function.

.. code-block:: python

    best_solution: Solution = RandomSearch(nn_domain, nn_fitness).run()

Every metaheuristic receives the |domain| definition and the **fitness function** at least. The instances contains the **run** function which executes the algorithm and always returns a the best |solution|.