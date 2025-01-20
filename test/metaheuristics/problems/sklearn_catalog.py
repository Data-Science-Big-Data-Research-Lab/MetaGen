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
from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR

from metagen.framework import Domain, Solution
from metagen.framework.connector import BaseConnector
# Synthetic datasets
X_regression, y_regression = make_regression(n_samples=100, n_features=4,
                                             n_informative=2,
                                             random_state=0, shuffle=False)

X_classification, y_classification = make_classification(n_samples=100, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)

def get_random_forest_classifier_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)
    domain.define_categorical("criterion", ['gini', 'entropy'])
    domain.define_categorical("max_features", ['sqrt', 'log2'])
    return domain

def get_random_forest_regressor_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("max_depth", 2, 8)
    domain.define_integer("n_estimators", 2, 16)
    domain.define_categorical("criterion", ['absolute_error', 'squared_error', 'friedman_mse'])
    domain.define_categorical("max_features", ['sqrt', 'log2'])
    return domain

def get_knn_classifier_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("n_neighbors", 2, 20)
    domain.define_categorical("weights", ['uniform', 'distance'])
    domain.define_integer("p", 1, 10)
    domain.define_categorical("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])
    return domain

def get_knn_regressor_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("n_neighbors", 2, 20)
    domain.define_categorical("weights", ['uniform', 'distance'])
    domain.define_integer("p", 1, 10)
    domain.define_categorical("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])
    return domain

def get_support_vector_classifier_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_real("C", 0.5, 10., 0.5)
    domain.define_categorical("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
    domain.define_integer("degree", 2, 5, 1)
    return domain

def get_support_vector_regressor_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_real("C", 0.5, 10., 0.5)
    domain.define_categorical("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
    domain.define_integer("degree", 2, 5, 1)
    return domain

def get_sgd_classifier_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_categorical("loss", ['hinge', 'log_loss', 'modified_huber', 'squared_hinge', 'perceptron'])
    domain.define_categorical("penalty", ['l2', 'l1', 'elasticnet'])
    domain.define_real("alpha", .0001, 1., .01)
    domain.define_integer("max_iter", 50, 2000, 5)
    domain.define_real("tol", 1e-3, .1, 1e-3)
    domain.define_categorical("learning_rate", ['constant', 'optimal', 'invscaling', 'adaptive'])
    return domain

def get_sgd_regressor_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_categorical("loss", ["squared_error", "huber", "epsilon_insensitive"])
    domain.define_categorical("penalty", ['l2', 'l1', 'elasticnet'])
    domain.define_real("alpha", .0001, 1., .01)
    domain.define_integer("max_iter", 50, 2000, 5)
    domain.define_real("tol", 1e-3, .1, 1e-3)
    domain.define_categorical("learning_rate", ['constant', 'optimal', 'invscaling', 'adaptive'])
    return domain


def random_forest_classifier_fitness(individual:Solution) -> float:
    max_depth = individual["max_depth"]
    n_estimators = individual["n_estimators"]
    criterion = individual["criterion"]
    max_features = individual["max_features"]

    clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                 max_features=max_features, random_state=0, n_jobs=-1)

    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

# Random Forest regressor fitness function
def random_forest_regressor_fitness(individual:Solution) -> float:
    max_depth = individual["max_depth"]
    n_estimators = individual["n_estimators"]
    criterion = individual["criterion"]
    max_features = individual["max_features"]

    clf = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# KNN classifier fitness function
def knn_classifier_fitness(individual:Solution) -> float:
    n_neighbors = individual["n_neighbors"]
    weights = individual["weights"]
    p = individual["p"]
    algorithm = individual["algorithm"]

    clf = KNeighborsClassifier(
        n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

# KNN regressor fitness function
def knn_regressor_fitness(individual:Solution) -> float:
    n_neighbors = individual["n_neighbors"]
    weights = individual["weights"]
    p = individual["p"]
    algorithm = individual["algorithm"]

    clf = KNeighborsRegressor(
        n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()

# SVM classifier fitness function
def support_vector_classifier_fitness(individual:Solution) -> float:
    c = individual["C"]
    kernel = individual["kernel"]
    degree = individual["degree"]

    clf = SVC(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

# SVM regressor fitness function
def support_vector_regressor_fitness(individual:Solution) -> float:
    c = individual["C"]
    kernel = individual["kernel"]
    degree = individual["degree"]

    clf = SVR(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# SGD classifier fitness function
def sgd_classifier_fitness(individual:Solution) -> float:
    loss = individual["loss"]
    penalty = individual["penalty"]
    alpha = individual["alpha"]
    max_iter = individual["max_iter"]
    tol = individual["tol"]
    learning_rate = individual["learning_rate"]

    clf = SGDClassifier(loss=loss, penalty=penalty, alpha=alpha, max_iter=max_iter, tol=tol,
                        learning_rate=learning_rate, eta0=0.01, n_jobs=-1)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

# SGD regressor fitness function
def sgd_regressor_fitness(individual:Solution) -> float:
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
