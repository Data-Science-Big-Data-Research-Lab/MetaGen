import numpy as np
import tensorflow as tf
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch

# MAC OSX note: the GPU optimization must be disabled since the tensorflow-metal plugin currently does not support
# exponential moving average (EMA)
tf.config.set_visible_devices([], "GPU")

# P4 legacy_domain
p4_domain = Domain()
p4_domain.define_real("learning_rate", 0.0, 0.000001)
p4_domain.define_categorical("ema", [True, False])
p4_domain.define_dynamic_structure("arch", 2, 10)
p4_domain.define_group("layer")
p4_domain.define_integer_in_group("layer", "neurons", 25, 300)
p4_domain.define_categorical_in_group(
    "layer", "activation", ["relu", "sigmoid", "softmax", "tanh"])
p4_domain.define_real_in_group("layer", "dropout", 0.0, 0.45)
p4_domain.set_structure_to_variable("arch", "layer")


# P4 fitness function
def build_neural_network(solution: Solution) -> tf.keras.Sequential():
    # Architecture building
    model = tf.keras.Sequential()

    for i, layer in enumerate(solution["arch"]):
        neurons = layer["neurons"].value
        activation = layer["activation"].value
        dropout = layer["dropout"].value
        rs = True
        if i == len(solution["arch"]):
            rs = False
        model.add(tf.keras.layers.LSTM(
            neurons, activation=activation, return_sequences=rs))
        model.add(tf.keras.layers.Dropout(dropout))
    model.add(tf.keras.layers.Dense(1, activation="tanh"))
    # Model compilation
    learning_rate = solution["learning_rate"].value
    ema = solution["ema"].value
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate, use_ema=ema),
                  loss="mean_squared_error", metrics=[tf.keras.metrics.MAPE])
    return model


x, y = make_regression(n_samples=1000, n_features=24)
scaler_x = StandardScaler()
scaler_y = StandardScaler()


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


def p4_fitness(solution: Solution) -> float:
    model = build_neural_network(solution)
    model.fit(x_train, y_train, epochs=10, batch_size=1024)
    mape = model.evaluate(x_val, y_val)[1]
    return mape


# P4 resolution
p4_solution: Solution = RandomSearch(
    p4_domain, p4_fitness, search_space_size=10, iterations=5).run()

# P4 result
print(p4_solution)
