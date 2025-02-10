from typing import Callable, Tuple

from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, SSGA, TPE
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.gamma_schedules import GammaConfig
from metagen.metaheuristics.mm.memetic import Memetic


def get_metaheuristic(code: str,
                      domain: Domain, fitness_function: Callable[[Solution], float],
                      distributed: bool, log_dir: str, **kwargs) -> Tuple[str, Metaheuristic]:

    result: Metaheuristic | None = None
    message: str = ""

    if code == 'rs':
        message = 'Running Random Search'
        result = RandomSearch(domain, fitness_function,
                              population_size=kwargs.get('population_size', 10),
                              max_iterations=kwargs.get('max_iterations', 20),
                              distributed=distributed, log_dir=log_dir)

    elif code == 'sa':
        message = 'Running Simulated Annealing'
        result = SA(domain, fitness_function,
                    warmup_iterations=kwargs.get('warmup_iterations', 5),
                    max_iterations=kwargs.get('max_iterations', 20),
                    alteration_limit=kwargs.get('alteration_limit', 5),
                    initial_temp=kwargs.get('initial_temp', 50),
                    cooling_rate=kwargs.get('cooling_rate', 0.99),
                    neighbor_population_size=kwargs.get('neighbor_population_size', 1),
                    distributed=distributed, log_dir=log_dir)

    elif code == 'ts':
        message = 'Running Tabu Search'
        gamma_config = None
        if kwargs.get('gamma') and kwargs.get('gamma') != "-":
            gamma_config = GammaConfig(
                gamma_function=kwargs.get('gamma'),
                minimum=kwargs.get('gamma_min', 0.1),
                maximum=kwargs.get('gamma_max', 0.3),
                alpha=kwargs.get('gamma_alpha', 5.0)
            )

        result = TabuSearch(domain, fitness_function,
                            population_size=kwargs.get('population_size', 10),
                            warmup_iterations=kwargs.get('warmup_iterations', 5),
                            max_iterations=kwargs.get('max_iterations', 10),
                            tabu_size=kwargs.get('tabu_size', 5),
                            alteration_limit=kwargs.get('alteration_limit', 1.0),
                            gamma_config=gamma_config,
                            distributed=distributed, log_dir=log_dir)

    elif code == 'ga':
        message = 'Running Genetic Algorithm'
        result = GA(domain, fitness_function,
                    population_size=kwargs.get('population_size', 10),
                    max_iterations=kwargs.get('max_iterations', 20),
                    mutation_rate=kwargs.get('mutation_rate', 0.1),
                    distributed=distributed, log_dir=log_dir)

    elif code == 'ssga':
        message = 'Running Steady-State Genetic Algorithm'
        result = SSGA(domain, fitness_function,
                      population_size=kwargs.get('population_size', 10),
                      max_iterations=kwargs.get('max_iterations', 20),
                      mutation_rate=kwargs.get('mutation_rate', 0.1),
                      distributed=distributed, log_dir=log_dir)

    elif code == 'mm':
        message = 'Running Memetic Algorithm'
        result = Memetic(domain, fitness_function,
                         population_size=kwargs.get('population_size', 10),
                         max_iterations=kwargs.get('max_iterations', 20),
                         mutation_rate=kwargs.get('mutation_rate', 0.1),
                         neighbor_population_size=kwargs.get('neighbor_population_size', 10),
                         alteration_limit=kwargs.get('alteration_limit', 1.0),
                         distributed=distributed, log_dir=log_dir,
                         distribution_level=kwargs.get('distribution_level', 0))

    elif code == 'tpe':
        message = 'Running Tree-structured Parzen Estimator'
        gamma_config = None
        if kwargs.get('gamma') and kwargs.get('gamma') != "-":
            gamma_config = GammaConfig(
                gamma_function=kwargs.get('gamma'),
                minimum=kwargs.get('gamma_min', 0.1),
                maximum=kwargs.get('gamma_max', 0.3),
                alpha=kwargs.get('gamma_alpha', 5.0)
            )

        result = TPE(domain, fitness_function,
                     max_iterations=kwargs.get('max_iterations', 20),
                     warmup_iterations=kwargs.get('warmup_iterations', 5),
                     candidate_pool_size=kwargs.get('candidate_pool_size', 24),
                     gamma_config=gamma_config,
                     distributed=distributed, log_dir=log_dir)

    else:
        raise ValueError(f"Metaheuristic '{code}' is not recognized")

    return message, result