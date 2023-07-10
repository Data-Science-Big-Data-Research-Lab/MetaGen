import numpy as np
import tensorflow as tf
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize

from metagen.framework import Domain, Solution

lstm_domain = Domain()
lstm_domain.define_real("learning_rate", 0.0, 0.000001)
lstm_domain.define_categorical("ema", [True, False])
lstm_domain.define_vector("arch", 2, 10)
lstm_domain.define_components_as_layer("arch")
lstm_domain.define_layer_vector_integer_element("arch", "neurons", 25, 300)
lstm_domain.define_layer_vector_categorical_element("arch", "activation", ["relu", "sigmoid", "softmax", "tanh"])
lstm_domain.define_layer_vector_real_element("arch", "dropout", 0.0, 0.45)

x, y = make_regression(n_samples=100, n_features=24)
x = normalize(x)
xs_tr, xs_ts, ys_tr, ys_ts = train_test_split(x, y, test_size=0.33, random_state=42)
x_tr = np.reshape(xs_tr, (xs_tr.shape[0], xs_tr.shape[1], 1))
y_tr = np.reshape(ys_tr, (ys_tr.shape[0], 1))
x_ts = np.reshape(xs_ts, (xs_ts.shape[0], xs_ts.shape[1], 1))
y_ts = np.reshape(ys_ts, (ys_ts.shape[0], 1))


def lstm_fitness(solution: Solution) -> float:

    model = build_neural_network(solution)

    model.fit(x_tr, y_tr, epochs=10, batch_size=1024)

    mape = model.evaluate(x_ts, y_ts)[1]

    return mape



def build_neural_network(solution:Solution) -> tf.keras.Sequential():
    model = tf.keras.Sequential()
    arch_size = solution.get_vector_size("arch")
    for i in range(0, arch_size):
        neurons = solution.get_layer_component_element("arch", i, "neurons")
        activation = solution.get_layer_component_element("arch", i, "activation")
        dropout = solution.get_layer_component_element("arch", i, "dropout")
        rs = True
        if i == arch_size - 1:
            rs = False
        model.add(tf.keras.layers.LSTM(neurons, activation=activation, return_sequences=rs))
        model.add(tf.keras.layers.Dropout(dropout))
    model.add(tf.keras.layers.Dense(1, activation="tanh"))
    learning_rate = solution.get_basic_value("learning_rate")
    ema = solution.get_basic_value("ema")
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate, use_ema=ema),
                  loss="mean_squared_error", metrics=[tf.keras.metrics.MAPE])
    return model
