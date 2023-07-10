from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR

from metagen.framework import Domain

# Synthetic datasets
X_regression, y_regression = make_regression(n_samples=1000, n_features=4,
                                             n_informative=2,
                                             random_state=0, shuffle=False)

X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)

# Random Forest classifier problem definition
random_forest_classifier_definition = Domain()
random_forest_classifier_definition.define_integer("max_depth", 2, 8)
random_forest_classifier_definition.define_integer("n_estimators", 2, 16)
random_forest_classifier_definition.define_categorical(
    "criterion", ['gini', 'entropy'])
random_forest_classifier_definition.define_categorical(
    "max_features", ['sqrt', 'log2'])

# Random Forest classifier fitness function


def random_forest_classifier_fitness(individual):
    max_depth = individual["max_depth"]
    n_estimators = individual["n_estimators"]
    criterion = individual["criterion"]
    max_features = individual["max_features"]

    clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                 max_features=max_features, random_state=0, n_jobs=-1)

    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# Random Forest regressor problem definition
random_forest_regressor_definition = Domain()
random_forest_regressor_definition.define_integer("max_depth", 2, 8)
random_forest_regressor_definition.define_integer("n_estimators", 2, 16)
random_forest_regressor_definition.define_categorical("criterion", [
                                                      'absolute_error', 'squared_error', 'friedman_mse'])
random_forest_regressor_definition.define_categorical(
    "max_features", ['sqrt', 'log2'])


# Random Forest regressor fitness function
def random_forest_regressor_fitness(individual):
    max_depth = individual["max_depth"]
    n_estimators = individual["n_estimators"]
    criterion = individual["criterion"]
    max_features = individual["max_features"]

    clf = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# KNN classifier problem definition
knn_classifier_definition = Domain()
knn_classifier_definition.define_integer("n_neighbors", 2, 20)
knn_classifier_definition.define_categorical(
    "weights", ['uniform', 'distance'])
knn_classifier_definition.define_integer("p", 1, 10)
knn_classifier_definition.define_categorical(
    "algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


# KNN classifier fitness function
def knn_classifier_fitness(individual):
    n_neighbors = individual["n_neighbors"]
    weights = individual["weights"]
    p = individual["p"]
    algorithm = individual["algorithm"]

    clf = KNeighborsClassifier(
        n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# KNN regressor problem definition
knn_regressor_definition = Domain()
knn_regressor_definition.define_integer("n_neighbors", 2, 20)
knn_regressor_definition.define_categorical("weights", ['uniform', 'distance'])
knn_regressor_definition.define_integer("p", 1, 10)
knn_regressor_definition.define_categorical(
    "algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


# KNN regressor fitness function
def knn_regressor_fitness(individual):
    n_neighbors = individual["n_neighbors"]
    weights = individual["weights"]
    p = individual["p"]
    algorithm = individual["algorithm"]

    clf = KNeighborsRegressor(
        n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# SVM classifier problem definition
support_vector_classifier_definition = Domain()
support_vector_classifier_definition.define_real("C", 0.5, 10., 0.5)
support_vector_classifier_definition.define_categorical(
    "kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_classifier_definition.define_integer("degree", 2, 5, 1)


# SVM classifier fitness function
def support_vector_classifier_fitness(individual):
    c = individual["C"]
    kernel = individual["kernel"]
    degree = individual["degree"]

    clf = SVC(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# SVM regressor problem definition
support_vector_regressor_definition = Domain()
support_vector_regressor_definition.define_real("C", 0.5, 10., 0.5)
support_vector_regressor_definition.define_categorical(
    "kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_regressor_definition.define_integer("degree", 2, 5, 1)


# SVM regressor fitness function
def support_vector_regressor_fitness(individual):
    c = individual["C"]
    kernel = individual["kernel"]
    degree = individual["degree"]

    clf = SVR(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# SGD classifier problem definition
sgd_classifier_definition = Domain()
sgd_classifier_definition.define_categorical("loss", ['hinge', 'log', 'modified_huber', 'squared_hinge',
                                                      'perceptron'])
sgd_classifier_definition.define_categorical(
    "penalty", ['l2', 'l1', 'elasticnet'])
sgd_classifier_definition.define_real("alpha", .0001, 1., .01)
sgd_classifier_definition.define_integer("max_iter", 50, 2000, 5)
sgd_classifier_definition.define_real("tol", 1e-3, .1, 1e-3)
sgd_classifier_definition.define_categorical("learning_rate",
                                             ['constant', 'optimal', 'invscaling', 'adaptive'])


# SGD classifier fitness function
def sgd_classifier_fitness(individual):
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
