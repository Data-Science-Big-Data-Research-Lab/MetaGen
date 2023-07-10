import tensorflow as tf
from sklearn.datasets import make_regression
from sklearn.preprocessing import normalize
from sklearn.model_selection import train_test_split
import numpy as np

tf.config.set_visible_devices([], "GPU")

ARCH_SIZE = 2
NEURONS = 25
ACTIVATION = "relu"
DROPOUT = 0.45
LR = 0.00001
AMSGRAD = True

x, y = make_regression(n_samples=1000, n_features=24)
x = normalize(x)
xs_train, xs_val, ys_train, ys_val = train_test_split(x, y, test_size=0.33, random_state=42)

x_train = np.reshape(xs_train, (xs_train.shape[0], xs_train.shape[1], 1))
y_train = np.reshape(ys_train, (ys_train.shape[0], 1))
x_val = np.reshape(xs_val, (xs_val.shape[0], xs_val.shape[1], 1))
y_val = np.reshape(ys_val, (ys_val.shape[0], 1))

model = tf.keras.Sequential()
model.add(tf.keras.layers.LSTM(NEURONS, activation=ACTIVATION, return_sequences=True))
model.add(tf.keras.layers.LSTM(NEURONS, activation=ACTIVATION, return_sequences=False))
model.add(tf.keras.layers.Dropout(DROPOUT))

model.add(tf.keras.layers.Dense(1, activation="tanh"))
model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=LR, use_ema=True),
              loss="mean_squared_error", metrics=[tf.keras.metrics.MAPE])

model.fit(x_train, y_train, epochs=10, batch_size=1024)
mape = model.evaluate(x_val, y_val)[1]

print("MAPE = "+str(mape))