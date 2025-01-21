import numpy as np
from scipy.optimize import rosen
import optuna
from ray import tune
from hyperopt import fmin, tpe, hp, STATUS_OK, Trials

# Define the Rosenbrock function
def rosenbrock(x):
    return rosen(x)

# Optuna
def optuna_objective(trial):
    x = [trial.suggest_uniform(f'x{i}', -5, 5) for i in range(2)]
    return rosenbrock(x)

def run_optuna():
    study = optuna.create_study(direction='minimize')
    study.optimize(optuna_objective, n_trials=100)
    print('Optuna best value:', study.best_value)
    print('Optuna best params:', study.best_params)

# Ray Tune
def raytune_objective(config):
    x = [config[f'x{i}'] for i in range(2)]
    tune.report(loss=rosenbrock(x))

def run_raytune():
    config = {f'x{i}': tune.uniform(-5, 5) for i in range(2)}
    analysis = tune.run(raytune_objective, config=config, num_samples=100)
    best_config = analysis.get_best_config(metric='loss', mode='min')
    print('Ray Tune best config:', best_config)

# Hyperopt
def hyperopt_objective(params):
    x = [params[f'x{i}'] for i in range(2)]
    return {'loss': rosenbrock(x), 'status': STATUS_OK}

def run_hyperopt():
    space = {f'x{i}': hp.uniform(f'x{i}', -5, 5) for i in range(2)}
    trials = Trials()
    best = fmin(hyperopt_objective, space, algo=tpe.suggest, max_evals=100, trials=trials)
    print('Hyperopt best params:', best)

if __name__ == '__main__':
    print("Running Optuna...")
    run_optuna()
    print("\nRunning Ray Tune...")
    run_raytune()
    print("\nRunning Hyperopt...")
    run_hyperopt()