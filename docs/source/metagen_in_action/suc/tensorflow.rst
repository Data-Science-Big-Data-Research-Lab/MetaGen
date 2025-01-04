Optimizing the architecture of a tensorflow Deep Learning model
================================================================

In this section, a hyperparameter optimization usecase is detailed employing the Metagen library and tensorflow in five steps.

Step 1: Import the required libraries. In most cases only the Domain and the meta-heuristic is required, the solution is included in this case just for type checking.

.. code-block:: python

     from metagen.framework import Domain, Solution
     from metagen.heuristics import RandomSearch
     import tensorflow as tf


Step 2: Select your datasets. In this case, a syntetic regression dataset has been employed.

.. code-block:: python

    from sklearn.datasets import make_regression
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    import numpy as np

    scaler_x = StandardScaler()
    scaler_y = StandardScaler()

    x, y = make_regression(n_samples=1000, n_features=24)

    xs_train, xs_val, ys_train, ys_val = train_test_split(
        x, y, test_size=0.33, random_state=42)

    xs_train = scaler_x.fit_transform(xs_train)
    ys_train = scaler_y.fit_transform(ys_train)
    xs_val = scaler_x.transform(xs_val)
    ys_val = scaler_y.transform(ys_val)

    x_train = np.reshape(xs_train, (xs_train.shape[0], xs_train.shape[1], 1))
    y_train = np.reshape(ys_train, (ys_train.shape[0], 1))
    x_val = np.reshape(xs_val, (xs_val.shape[0], xs_val.shape[1], 1))
    y_val = np.reshape(ys_val, (ys_val.shape[0], 1))

Step 3: Define the domain. The usual hyperparameters of a neural network has been defined in our domain.

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

Step 4: Define fitness function. First, the neural network is build considering the solution which encodes the hyperparameters. Secondly, the model is trained on the training set and evaluated on the validation set, returning the validation MSE.

.. code-block:: python

    def build_neural_network(solution: Solution) -> tf.keras.Sequential():
        model = tf.keras.Sequential()

        for i, layer in enumerate(solution["arch"]):
            neurons = layer["neurons"]
            activation = layer["activation"]
            dropout = layer["dropout"]
            rs = True
            if i == len(solution["arch"]):
                rs = False
            model.add(tf.keras.layers.LSTM(neurons, activation=activation, return_sequences=rs))
            model.add(tf.keras.layers.Dropout(dropout))
        model.add(tf.keras.layers.Dense(1))
        # Model compilation
        learning_rate = solution["learning_rate"]
        ema = solution["ema"].value
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate, use_ema=ema),
                    loss="mean_squared_error", metrics=[tf.keras.metrics.MAPE])
        return model

    def fitness(solution: Solution, x_train, y_train, x_val, y_val) -> float:
        model = build_neural_network(solution)
        model.fit(x_train, y_train, epochs=10, batch_size=1024)
        mape = model.evaluate(x_val, y_val)[1]
        return mape


Step 5: Execute the optimization algorithm. Note than the fitness function must be Callabe[[Solution], float], so cannot set a function with more than one parameters. For that reason, a lambda function is employed.

.. code-block:: python

    best_solution: Solution = RandomSearch(nn_domain, lambda solution: fitness(solution, x_train, y_train, x_val, y_val), search_space_size=5, iterations=2).run()

Every meta-heuristic receives the domain definition and the fitness function at least. The instances contains the `run` function which executes the algorithm and always returns a the best Solution.