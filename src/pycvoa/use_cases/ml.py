from sklearn.datasets import make_classification, make_regression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import SGDClassifier, SGDRegressor
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR

from pycvoa.problem.domain import Domain

# Synthetic datasets
X_regression, y_regression = make_regression(n_samples=1000, n_features=4,
                                             n_informative=2,
                                             random_state=0, shuffle=False)

X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)

# Random Forest classifier problem definition
random_forest_classifier_definition = Domain()
random_forest_classifier_definition.define_integer("max_depth", 2, 100, 1)
random_forest_classifier_definition.define_integer("n_estimators", 10, 500, 1)
random_forest_classifier_definition.define_categorical("criterion", ['gini', 'entropy'])
random_forest_classifier_definition.define_categorical("max_features", ['auto', 'sqrt', 'log2'])


# Random Forest classifier fitness function
def random_forest_classifier_fitness(individual):
    max_depth = individual.get_basic_value("max_depth")
    n_estimators = individual.get_basic_value("n_estimators")
    criterion = individual.get_basic_value("criterion")
    max_features = individual.get_basic_value("max_features")

    clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                 max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# Random Forest regressor problem definition
random_forest_regressor_definition = Domain()
random_forest_regressor_definition.define_integer("max_depth", 2, 100, 1)
random_forest_regressor_definition.define_integer("n_estimators", 10, 500, 1)
random_forest_regressor_definition.define_categorical("criterion", ['mse', 'mae'])
random_forest_regressor_definition.define_categorical("max_features", ['auto', 'sqrt', 'log2'])


# Random Forest regressor fitness function
def random_forest_regressor_fitness(individual):
    max_depth = individual.get_basic_value("max_depth")
    n_estimators = individual.get_basic_value("n_estimators")
    criterion = individual.get_basic_value("criterion")
    max_features = individual.get_basic_value("max_features")

    clf = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# KNN classifier problem definition
knn_classifier_definition = Domain()
knn_classifier_definition.define_integer("n_neighbors", 2, 20, 1)
knn_classifier_definition.define_categorical("weights", ['uniform', 'distance'])
knn_classifier_definition.define_integer("p", 1, 10, 1)
knn_classifier_definition.define_categorical("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


# KNN classifier fitness function
def knn_classifier_fitness(individual):
    n_neighbors = individual.get_basic_value("n_neighbors")
    weights = individual.get_basic_value("weights")
    p = individual.get_basic_value("p")
    algorithm = individual.get_basic_value("algorithm")

    clf = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# KNN regressor problem definition
knn_regressor_definition = Domain()
knn_regressor_definition.define_integer("n_neighbors", 2, 20, 1)
knn_regressor_definition.define_categorical("weights", ['uniform', 'distance'])
knn_regressor_definition.define_integer("p", 1, 10, 1)
knn_regressor_definition.define_categorical("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


# KNN regressor fitness function
def knn_regressor_fitness(individual):
    n_neighbors = individual.get_basic_value("n_neighbors")
    weights = individual.get_basic_value("weights")
    p = individual.get_basic_value("p")
    algorithm = individual.get_basic_value("algorithm")

    clf = KNeighborsRegressor(n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# SVM classifier problem definition
support_vector_classifier_definition = Domain()
support_vector_classifier_definition.define_real("C", 0.5, 10, 0.5)
support_vector_classifier_definition.define_categorical("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_classifier_definition.define_integer("degree", 2, 5, 1)


# SVM classifier fitness function
def support_vector_classifier_fitness(individual):
    c = individual.get_basic_value("C")
    kernel = individual.get_basic_value("kernel")
    degree = individual.get_basic_value("degree")

    clf = SVC(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# SVM regressor problem definition
support_vector_regressor_definition = Domain()
support_vector_regressor_definition.define_real("C", 0.5, 10, 0.5)
support_vector_regressor_definition.define_categorical("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_regressor_definition.define_integer("degree", 2, 5, 1)


# SVM regressor fitness function
def support_vector_regressor_fitness(individual):
    c = individual.get_basic_value("C")
    kernel = individual.get_basic_value("kernel")
    degree = individual.get_basic_value("degree")

    clf = SVR(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


# SGD classifier problem definition
sgd_classifier_definition = Domain()
sgd_classifier_definition.define_categorical("loss", ['hinge', 'log', 'modified_huber', 'squared_hinge',
                                                                 'perceptron'])
sgd_classifier_definition.define_categorical("penalty", ['l2', 'l1', 'elasticnet'])
sgd_classifier_definition.define_real("alpha", .0001, .0001, .01)
sgd_classifier_definition.define_integer("max_iter", 50, 2000, 5)
sgd_classifier_definition.define_real("tol", 1e-3, .1, 1e-3)
sgd_classifier_definition.define_categorical("learning_rate",
                                             ['constant', 'optimal', 'invscaling', 'adaptive'])


# SGD classifier fitness function
def sgd_classifier_fitness(individual):
    loss = individual.get_basic_value("loss")
    penalty = individual.get_basic_value("penalty")
    alpha = individual.get_basic_value("alpha")
    max_iter = individual.get_basic_value("max_iter")
    tol = individual.get_basic_value("tol")
    learning_rate = individual.get_basic_value("learning_rate")

    clf = SGDClassifier(loss=loss, penalty=penalty, alpha=alpha, max_iter=max_iter, tol=tol,
                        learning_rate=learning_rate, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


# SGD regressor problem definition
sgd_regressor_definition = Domain()
sgd_regressor_definition.define_categorical("loss", ['hinge', 'log', 'modified_huber', 'squared_hinge',
                                                                'perceptron'])
sgd_regressor_definition.define_categorical("penalty", ['l2', 'l1', 'elasticnet'])
sgd_regressor_definition.define_real("alpha", .0001, .0001, .01)
sgd_regressor_definition.define_integer("max_iter", 50, 2000, 5)
sgd_regressor_definition.define_real("tol", 1e-3, .1, 1e-3)
sgd_regressor_definition.define_categorical("learning_rate",
                                            ['constant', 'optimal', 'invscaling', 'adaptive'])


# SGD regressor fitness function
def sgd_regressor_fitness(individual):
    loss = individual.get_basic_value("loss")
    penalty = individual.get_basic_value("penalty")
    alpha = individual.get_basic_value("alpha")
    max_iter = individual.get_basic_value("max_iter")
    tol = individual.get_basic_value("tol")
    learning_rate = individual.get_basic_value("learning_rate")

    clf = SGDRegressor(loss=loss, penalty=penalty, alpha=alpha, max_iter=max_iter, tol=tol, learning_rate=learning_rate,
                       n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()