from typing import Callable, Tuple

from metagen.framework import Domain, Solution
from metagen.metaheuristics import RandomSearch, SA, TabuSearch, GA, SSGA
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.mm.memetic import Memetic


def get_metaheuristic(code:str,
                      domain:Domain, fitness_function: Callable[[Solution], float],
                      distributed:bool,log_dir:str,**kwargs) -> Tuple[str, Metaheuristic]:

    result:Metaheuristic|None = None
    message:str = ""

    if code == 'rs':
        population_size = kwargs.get('population_size', 10)
        max_iterations = kwargs.get('max_iterations', 20)
        message = 'Running Random Search'
        result = RandomSearch(domain, fitness_function, population_size, max_iterations, distributed, log_dir)

    elif code == 'sa':
        max_iterations = kwargs.get('max_iterations', 20)
        alteration_limit = kwargs.get('alteration_limit', 0.1)
        initial_temp = kwargs.get('initial_temp', 50.0)
        cooling_rate = kwargs.get('cooling_rate', 0.99)
        neighbor_population_size = kwargs.get('neighbor_population_size', 1)
        message = 'Running Simulated Annealing'
        result = SA(domain, fitness_function, max_iterations, alteration_limit, initial_temp,
                    cooling_rate, neighbor_population_size, distributed, log_dir)

    elif code == 'ts':
        population_size = kwargs.get('population_size', 10)
        max_iterations = kwargs.get('max_iterations', 10)
        tabu_size = kwargs.get('tabu_size', 5)
        alteration_limit = kwargs.get('alteration_limit', 1.0)
        message = 'Running Tabu Search'
        result = TabuSearch(domain, fitness_function, population_size, max_iterations, tabu_size, alteration_limit,
                            distributed, log_dir)

    elif code == 'ga':
        population_size = kwargs.get('population_size', 10)
        max_iterations = kwargs.get('max_iterations', 20)
        mutation_rate = kwargs.get('mutation_rate', 0.1)
        message = 'Running Genetic Algorithm'
        result = GA(domain, fitness_function, population_size, max_iterations, mutation_rate, distributed, log_dir)

    elif code == 'ssga':
        population_size = kwargs.get('population_size', 10)
        max_iterations = kwargs.get('max_iterations', 20)
        mutation_rate = kwargs.get('mutation_rate', 0.1)
        message = 'Running Steady-State Genetic Algorithm'
        result = SSGA(domain, fitness_function, population_size, max_iterations, mutation_rate, distributed, log_dir)

    elif code == 'mm':
        population_size = kwargs.get('population_size', 10)
        max_iterations = kwargs.get('max_iterations', 20)
        mutation_rate = kwargs.get('mutation_rate', 0.1)
        neighbor_population_size = kwargs.get('neighbor_population_size', 10)
        alteration_limit = kwargs.get('alteration_limit', 1.0)
        distribution_level = kwargs.get('distribution_level', 0)
        message = 'Running Memetic Algorithm'
        result = Memetic(domain, fitness_function, population_size, max_iterations, mutation_rate,
                         neighbor_population_size,alteration_limit, distributed, log_dir, distribution_level)

    return message, result

