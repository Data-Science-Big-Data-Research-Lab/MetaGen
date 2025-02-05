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
from locale import normalize

import numpy as np
import tensorflow as tf
from sklearn.datasets import make_regression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from metagen.framework import Domain, Solution, BaseConnector


def get_nn_domain(connector = BaseConnector()) -> Domain:
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




scaler_x = StandardScaler()
scaler_y = StandardScaler()

x, y = make_regression(n_samples=1000, n_features=24)

x, y = make_regression(n_samples=1000, n_features=24)
x = normalize(x)
xs_train, ys_train, xs_val, ys_val = train_test_split(x, y,
                            test_size=0.33, random_state=42)





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

def nn_fitness(solution: Solution) -> float:
    model = build_neural_network(solution)
    model.fit(x_train, y_train, epochs=10, batch_size=1024)
    mape = model.evaluate(x_val, y_val)[1]
    return mape
