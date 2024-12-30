import warnings
from sklearn.exceptions import ConvergenceWarning

import metagen
from metagen.metaheuristics.cvoa.distributed_cvoa import DistributedCVOA, StrainProperties, cvoa_launcher

# Suppress all ConvergenceWarning warnings
warnings.filterwarnings("ignore", category=ConvergenceWarning)

from sklearn.datasets import make_regression
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import cross_val_score

from metagen.framework import Domain, Solution
from metagen.metaheuristics.sa.sa import DistributedSA, SA




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
def sgd_regressor_fitness(individual: Solution) -> float:
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
p1_domain.define_integer("x", -5, 20)

def p1_fitness(individual: Solution) -> float:
    x = individual["x"] # You could use the .get function alternatively.
    return x + 5

if __name__ == "__main__":

    strain1:StrainProperties = StrainProperties(strain_id="STR-1")
    strain2:StrainProperties = StrainProperties(strain_id="STR-2")
    strain3: StrainProperties = StrainProperties(strain_id="STR-3",pandemic_duration=20)

    print('CVOA')
    # solution: Solution = metagen.metaheuristics.cvoa.cvoa_launcher([strain1, strain2, strain3], p1_domain, p1_fitness)
    solution: Solution = metagen.metaheuristics.cvoa.cvoa_launcher([strain1, strain2, strain3], sgd_regressor_definition, sgd_regressor_fitness)

    # print('Distributed CVOA')
    # solution: Solution = cvoa_launcher([strain1, strain2, strain3], p1_domain, p1_fitness)
    # solution: Solution = cvoa_launcher([strain1, strain2, strain3], sgd_regressor_definition, sgd_regressor_fitness)

    print(f'\n\nRESULT: {solution}')