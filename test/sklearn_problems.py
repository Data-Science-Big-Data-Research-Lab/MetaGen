from cvoa import ProblemDefinition
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.svm import SVC, SVR
from sklearn.linear_model import SGDClassifier, SGDRegressor

X_regression, y_regression = make_regression(n_samples=1000, n_features=4,
                                             n_informative=2,
                                             random_state=0, shuffle=False)

X_classification, y_classification = make_classification(n_samples=1000, n_features=4,
                                                         n_informative=2, n_redundant=0,
                                                         random_state=0, shuffle=False)


"""
Random Forest classifier optimization
"""
random_forest_classifier_definition = ProblemDefinition()
random_forest_classifier_definition.register_integer_variable("max_depth", 2, 100, 1)
random_forest_classifier_definition.register_integer_variable("n_estimators", 10, 500, 1)
random_forest_classifier_definition.register_categorical_variable("criterion", ['gini', 'entropy'])
random_forest_classifier_definition.register_categorical_variable("max_features", ['auto', 'sqrt', 'log2'])


def random_forest_classifier_fitness(individual):
    max_depth = individual.get_variable_value("max_depth")
    n_estimators = individual.get_variable_value("n_estimators")
    criterion = individual.get_variable_value("criterion")
    max_features = individual.get_variable_value("max_features")

    clf = RandomForestClassifier(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                 max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_classification, y_classification,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


"""
Random Forest regressor optimization
"""
random_forest_regressor_definition = ProblemDefinition()
random_forest_regressor_definition.register_integer_variable("max_depth", 2, 100, 1)
random_forest_regressor_definition.register_integer_variable("n_estimators", 10, 500, 1)
random_forest_regressor_definition.register_categorical_variable("criterion", ['mse', 'mae'])
random_forest_regressor_definition.register_categorical_variable("max_features", ['auto', 'sqrt', 'log2'])


def random_forest_regressor_fitness(individual):
    max_depth = individual.get_variable_value("max_depth")
    n_estimators = individual.get_variable_value("n_estimators")
    criterion = individual.get_variable_value("criterion")
    max_features = individual.get_variable_value("max_features")

    clf = RandomForestRegressor(max_depth=max_depth, n_estimators=n_estimators, criterion=criterion,
                                 max_features=max_features, random_state=0, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()


"""
KNN classifier optimization
"""
knn_classifier_definition = ProblemDefinition()
knn_classifier_definition.register_integer_variable("n_neighbors", 2, 20, 1)
knn_classifier_definition.register_categorical_variable("weights", ['uniform', 'distance'])
knn_classifier_definition.register_integer_variable("p", 1, 10, 1)
knn_classifier_definition.register_categorical_variable("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


def knn_classifier_fitness(individual):
    n_neighbors = individual.get_variable_value("n_neighbors")
    weights = individual.get_variable_value("weights")
    p = individual.get_variable_value("p")
    algorithm = individual.get_variable_value("algorithm")

    clf = KNeighborsClassifier(n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

"""
KNN regressor optimization
"""
knn_regressor_definition = ProblemDefinition()
knn_regressor_definition.register_integer_variable("n_neighbors", 2, 20, 1)
knn_regressor_definition.register_categorical_variable("weights", ['uniform', 'distance'])
knn_regressor_definition.register_integer_variable("p", 1, 10, 1)
knn_regressor_definition.register_categorical_variable("algorithm", ['auto', 'ball_tree', 'kd_tree', 'brute'])


def knn_regressor_fitness(individual):
    n_neighbors = individual.get_variable_value("n_neighbors")
    weights = individual.get_variable_value("weights")
    p = individual.get_variable_value("p")
    algorithm = individual.get_variable_value("algorithm")

    clf = KNeighborsRegressor(n_neighbors=n_neighbors, weights=weights, p=p, algorithm=algorithm, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()



"""
Support vector classifier optimization
"""
support_vector_classifier_definition = ProblemDefinition()
support_vector_classifier_definition.register_real_variable("C", 0.5, 10, 0.5)
support_vector_classifier_definition.register_categorical_variable("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_classifier_definition.register_integer_variable("degree", 2, 5, 1)


def support_vector_classifier_fitness(individual):
    c = individual.get_variable_value("C")
    kernel = individual.get_variable_value("kernel")
    degree = individual.get_variable_value("degree")

    clf = SVC(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()

"""
Support vector regressor optimization
"""
support_vector_regressor_definition = ProblemDefinition()
support_vector_regressor_definition.register_real_variable("C", 0.5, 10, 0.5)
support_vector_regressor_definition.register_categorical_variable("kernel", ['linear', 'poly', 'rbf', 'sigmoid'])
support_vector_regressor_definition.register_integer_variable("degree", 2, 5, 1)


def support_vector_regressor_fitness(individual):
    c = individual.get_variable_value("C")
    kernel = individual.get_variable_value("kernel")
    degree = individual.get_variable_value("degree")

    clf = SVR(C=c, kernel=kernel, degree=degree)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()

"""
SGD classifier optimization
"""
sgd_classifier_definition = ProblemDefinition()
sgd_classifier_definition.register_categorical_variable("loss", ['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron'])
sgd_classifier_definition.register_categorical_variable("penalty", ['l2', 'l1', 'elasticnet'])
sgd_classifier_definition.register_real_variable("alpha", .0001, .0001, .01)
sgd_classifier_definition.register_integer_variable("max_iter", 50, 2000, 5)
sgd_classifier_definition.register_real_variable("tol", 1e-3, .1, 1e-3)
sgd_classifier_definition.register_categorical_variable("learning_rate", ['constant', 'optimal', 'invscaling', 'adaptive'])


def sgd_classifier_fitness(individual):
    loss = individual.get_variable_value("loss")
    penalty = individual.get_variable_value("penalty")
    alpha = individual.get_variable_value("alpha")
    max_iter = individual.get_variable_value("max_iter")
    tol = individual.get_variable_value("tol")
    learning_rate = individual.get_variable_value("learning_rate")

    clf = SGDClassifier(loss=loss, penalty=penalty, alpha=alpha, max_iter=max_iter, tol=tol, learning_rate=learning_rate, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="accuracy", cv=10, n_jobs=-1)

    return -scores.mean()


"""
SGD regressor optimization
"""
sgd_regressor_definition = ProblemDefinition()
sgd_regressor_definition.register_categorical_variable("loss", ['hinge', 'log', 'modified_huber', 'squared_hinge', 'perceptron'])
sgd_regressor_definition.register_categorical_variable("penalty", ['l2', 'l1', 'elasticnet'])
sgd_regressor_definition.register_real_variable("alpha", .0001, .0001, .01)
sgd_regressor_definition.register_integer_variable("max_iter", 50, 2000, 5)
sgd_regressor_definition.register_real_variable("tol", 1e-3, .1, 1e-3)
sgd_regressor_definition.register_categorical_variable("learning_rate", ['constant', 'optimal', 'invscaling', 'adaptive'])


def sgd_regressor_fitness(individual):
    loss = individual.get_variable_value("loss")
    penalty = individual.get_variable_value("penalty")
    alpha = individual.get_variable_value("alpha")
    max_iter = individual.get_variable_value("max_iter")
    tol = individual.get_variable_value("tol")
    learning_rate = individual.get_variable_value("learning_rate")

    clf = SGDRegressor(loss=loss, penalty=penalty, alpha=alpha, max_iter=max_iter, tol=tol, learning_rate=learning_rate, n_jobs=-1)
    scores = cross_val_score(clf, X_regression, y_regression,
                             scoring="neg_root_mean_squared_error", cv=10, n_jobs=-1)

    return -scores.mean()
