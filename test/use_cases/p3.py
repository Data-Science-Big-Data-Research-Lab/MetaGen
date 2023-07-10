import warnings

from sklearn.datasets import make_regression
from sklearn.linear_model import SGDRegressor
from sklearn.model_selection import cross_val_score

from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch

# P3 legacy_domain
p3_domain = Domain()
p3_domain.define_real("alpha", 0.0001, 0.001)
p3_domain.define_integer("iterations", 5, 200)
p3_domain.define_categorical(
    "loss", ["squared_error", "huber", "epsilon_insensitive"])

# P3 fitness function
X, y = make_regression(n_samples=1000, n_features=4)


def p3_fitness(solution: Solution):
    # In this case, we get the builtin by getting the value property.
    loss = solution["loss"].value
    iterations = solution["iterations"].value
    alpha = solution["alpha"].value
    model = SGDRegressor(loss=loss, alpha=alpha, max_iter=iterations)
    mape = -cross_val_score(model, X, y,
                            scoring="neg_mean_absolute_percentage_error").mean()
    return mape


# P3 resolution
warnings.filterwarnings('ignore')
p3_solution: Solution = RandomSearch(p3_domain, p3_fitness).run()

# P3 result
print(p3_solution)
