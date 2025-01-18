import logging

import ray

from metagen.logging.metagen_logger import metagen_logger_setup, get_metagen_logger
from metagen.metaheuristics import TabuSearch
from metagen.framework import Domain, Solution
from sklearn.datasets import make_regression
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

p1_domain: Domain = Domain()
p1_domain.define_integer("x", -5, 10)

def p1_fitness(individual: Solution) -> float:
    x = individual["x"] # You could use the .get function alternatively.
    return x + 5

if __name__ == "__main__":
    logging.Logger("metagen_logger")
    metagen_logger_setup(logging.DEBUG)

    get_metagen_logger().info('Running Tabu Search')

    experiment: TabuSearch = TabuSearch(p1_domain, p1_fitness, population_size=5, tabu_size=40, max_iterations=40)


    # experiment: TabuSearch = TabuSearch(p1_domain, p1_fitness, population_size=5, tabu_size=10, max_iterations=30, alteration_limit=2, distributed=True)
    # experiment: TabuSearch = TabuSearch(sgd_regressor_definition, sgd_regressor_fitness, population_size=20, tabu_size=40, max_iterations=40)
    # ray.init(num_cpus=4)
    # experiment: TabuSearch = TabuSearch(sgd_regressor_definition, sgd_regressor_fitness, population_size=5, tabu_size=10, max_iterations=30, alteration_limit=2, distributed=True)

    solution: Solution = experiment.run()
    print(solution)