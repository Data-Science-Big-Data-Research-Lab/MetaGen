"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from sklearn.datasets import make_regression
from sklearn.preprocessing import normalize, StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
import tensorflow as tf

from metagen.framework import Domain, Solution, BaseConnector


def get_static_nn_domain(connector = BaseConnector()) -> Domain:
    nn_domain = Domain(connector)
    nn_domain.define_real("learning_rate", 0.0, 0.000001)
    nn_domain.define_categorical("ema", [True, False])
    nn_domain.define_static_structure("arch", 5)
    nn_domain.define_group("layer")
    nn_domain.define_integer_in_group("layer", "neurons", 25, 300)
    nn_domain.define_categorical_in_group("layer", "activation", ["relu", "sigmoid", "softmax", "tanh"])
    nn_domain.define_real_in_group("layer", "dropout", 0.0, 0.45)
    nn_domain.set_structure_to_variable("arch", "layer")
    return nn_domain



def get_dynamic_nn_domain(connector = BaseConnector()) -> Domain:
    nn_domain = Domain(connector)
    nn_domain.define_real("learning_rate", 0.0, 0.000001)
    nn_domain.define_categorical("ema", [True, False])
    nn_domain.define_dynamic_structure("arch", 2, 10)
    nn_domain.define_group("layer")
    nn_domain.define_integer_in_group("layer", "neurons", 25, 300)
    nn_domain.define_categorical_in_group("layer", "activation", ["relu", "sigmoid", "softmax", "tanh"])
    nn_domain.define_real_in_group("layer", "dropout", 0.0, 0.45)
    nn_domain.set_structure_to_variable("arch", "layer")
    return nn_domain


# Generación de datos
x, y = make_regression(n_samples=1000, n_features=24)
scaler_x = StandardScaler()
scaler_y = StandardScaler()

x = scaler_x.fit_transform(x)
y = scaler_y.fit_transform(y.reshape(-1, 1)).astype(np.float32)

xs_train, xs_val, ys_train, ys_val = train_test_split(x, y, test_size=0.33, random_state=42)

x_train = np.reshape(xs_train, (xs_train.shape[0], xs_train.shape[1], 1))
y_train = np.reshape(ys_train, (ys_train.shape[0], 1))
x_val = np.reshape(xs_val, (xs_val.shape[0], xs_val.shape[1], 1))
y_val = np.reshape(ys_val, (ys_val.shape[0], 1))


# Definición del modelo
def build_neural_network(solution: dict) -> tf.keras.Sequential:
    model = tf.keras.Sequential()
    for i, layer in enumerate(solution["arch"]):
        neurons = layer["neurons"]
        activation = layer["activation"]
        dropout = layer["dropout"]

        return_sequences = i < len(solution["arch"]) - 1  # Última capa LSTM sin return_sequences

        model.add(tf.keras.layers.LSTM(neurons,
                                       activation=activation,
                                       return_sequences=return_sequences))
        model.add(tf.keras.layers.Dropout(dropout))

    model.add(tf.keras.layers.Dense(1, activation="tanh"))

    # Compilación
    learning_rate = solution["learning_rate"]
    ema = solution["ema"]
    model.compile(optimizer=tf.keras.optimizers.Adam(
        learning_rate=learning_rate,
        use_ema=ema),
        loss="mean_squared_error",
        metrics=[tf.keras.metrics.MAE])  # Cambiado MAPE → MAE para evitar problemas
    return model


def nn_fitness(solution: dict) -> float:
    model = build_neural_network(solution)

    batch_size = min(1024, x_train.shape[0])  # Evita batch_size mayor que el dataset
    model.fit(x_train, y_train, epochs=10, batch_size=batch_size, verbose=0)

    mae = model.evaluate(x_val, y_val, verbose=0)[1]  # Obtiene MAE
    return mae