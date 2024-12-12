import sys
import os

# Agregar el directorio al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))


from metagen.metaheuristics import RandomSearch
from metagen.framework import Domain, Solution
from sklearn.datasets import make_classification, make_regression
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import cross_val_score

# Synthetic datasets
X_regression, y_regression = make_regression(n_samples=100, n_features=4,
                                             n_informative=2,
                                             random_state=0, shuffle=False)

# SGD regressor problem definition
sgd_regressor_definition = Domain()
sgd_regressor_definition.define_categorical(
    "loss", ["squared_error", "huber", "epsilon_insensitive"])
sgd_regressor_definition.define_categorical(
    "penalty", ['l2', 'l1', 'elasticnet'])
sgd_regressor_definition.define_real("alpha", .0001, 1., .01)
sgd_regressor_definition.define_integer("max_iter", 50, 2000, 5)
sgd_regressor_definition.define_real("tol", 1e-3, .1, 1e-3)
sgd_regressor_definition.define_categorical("learning_rate",
                                            ['constant', 'optimal', 'invscaling', 'adaptive'])


# SGD regressor fitness function
def sgd_regressor_fitness(individual):
    loss = individual["loss"]
    penalty = individual["penalty"]
    alpha = individual["alpha"]
    max_iter = individual["max_iter"]
    tol = individual["tol"]
    learning_rate = individual["learning_rate"]

    clf = SGDRegressor(loss=loss, penalty=penalty, alpha=alpha,
                       max_iter=max_iter, tol=tol, learning_rate=learning_rate)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()

if __name__ == "__main__":
    print('Running Random Search')
    random_search: RandomSearch = RandomSearch(sgd_regressor_definition, sgd_regressor_fitness, distributed=True)
    solution: Solution = random_search.run()
    print(solution)