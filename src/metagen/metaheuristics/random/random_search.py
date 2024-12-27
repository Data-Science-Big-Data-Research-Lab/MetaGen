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
from metagen.framework import Domain, Solution
from metagen.metaheuristics.base import Metaheuristic
import ray

from metagen.metaheuristics.distributed_suite import local_yield_and_evaluate_individuals, \
    local_mutate_and_evaluate_population, distributed_base_population, distributed_mutation_and_evaluation


class RandomSearch(Metaheuristic):

    """
    RandomSearch is a class for performing a random search optimization algorithm.

    It generates and evaluates random solutions in a search space to find an optimal solution.

    :param domain: The search domain that defines the solution space.
    :type domain: Domain
    :param fitness_function: The fitness function used to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param search_space_size: The size of the search space. Default is 30.
    :type search_space_size: int, optional
    :param max_iterations: The number of optimization iterations. Default is 20.
    :type max_iterations: int, optional

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import RandomSearch
        
        domain = Domain()

        domain.defineInteger(0, 1)

        fitness_function = ...

        search = RandomSearch(domain, fitness_function, search_space_size=50, iterations=100)
        optimal_solution = search.run()

    """

    def __init__(self, domain: Domain, fitness_function, log_dir: str = "logs/RS",
                 search_space_size: int = 30, max_iterations: int = 20) -> None:
        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.search_space_size = search_space_size
        self.max_iterations = max_iterations
    

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def initialize(self) -> None:
        """Initialize random solutions"""
        population, best_individual = local_yield_and_evaluate_individuals(self.search_space_size, self.domain, self.fitness_function)
        self.current_solutions = population
        self.best_solution = best_individual

    def iterate(self) -> None:
        population, best_individual = local_mutate_and_evaluate_population(self.current_solutions, self.fitness_function)
        self.current_solutions = population
        self.best_solution = best_individual


class DistributedRS(Metaheuristic):
    """
    RandomSearch is a class for performing a random search optimization algorithm.

    It generates and evaluates random solutions in a search space to find an optimal solution.

    :param domain: The search domain that defines the solution space.
    :type domain: Domain
    :param fitness_function: The fitness function used to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param search_space_size: The size of the search space. Default is 30.
    :type search_space_size: int, optional
    :param max_iterations: The number of optimization iterations. Default is 20.
    :type max_iterations: int, optional

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import RandomSearch

        domain = Domain()

        domain.defineInteger(0, 1)

        fitness_function = ...

        search = RandomSearch(domain, fitness_function, search_space_size=50, iterations=100)
        optimal_solution = search.run()

    """

    def __init__(self, domain: Domain, fitness_function, log_dir: str = "logs/RS",
                 search_space_size: int = 30, max_iterations: int = 20) -> None:
        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.search_space_size = search_space_size
        self.max_iterations = max_iterations

    def initialize(self) -> None:
        """
        Initialize random solutions and evaluate them in parallel using Ray.
        """
        # print('initialize')
        population, best_individual = distributed_base_population(self.search_space_size, self.domain, self.fitness_function)
        self.current_solutions = population
        self.best_solution = best_individual
        # print('Population: ' + str(self.current_solutions))
        # print('Best: ' + str(self.best_solution))

    def iterate(self) -> None:
        """
        Perform one iteration of the distributed random search.
        """
        # Mutate solutions before evaluating them
        # print('iterate')
        population, best_individual = distributed_mutation_and_evaluation(self.current_solutions, self.fitness_function)
        self.current_solutions = population
        self.best_solution = best_individual
        # print('Best: '+str(self.best_solution))

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def run(self) -> Solution:

        # print('Running')
        if not ray.is_initialized():
            ray.init()

        try:
            # Flujo estándar
            return super().run()
        finally:
            # Asegurarse de que Ray se cierre al finalizar
            ray.shutdown()