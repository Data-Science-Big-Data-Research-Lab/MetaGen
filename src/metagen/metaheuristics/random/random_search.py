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
from typing import List, Tuple
from copy import deepcopy

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
                 population_size: int = 5, max_iterations: int = 20, **kargs) -> None:
        super().__init__(domain, fitness_function, population_size=population_size, log_dir=log_dir, **kargs)
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """Initialize random solutions"""

        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        best_solution = None 
        current_solutions = []
        for _ in range(num_solutions):
            individual = solution_type(self.domain, connector=self.domain.get_connector())
            individual.evaluate(self.fitness_function)
            current_solutions.append(individual)
            if best_solution is None or individual.get_fitness() < best_solution.get_fitness():
                best_solution = individual
        
        return current_solutions, best_solution


    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        
        best_solution = deepcopy(self.best_solution)
        current_solutions = [best_solution]

        for individual in solutions[:-1]:
            individual.mutate()
            individual.evaluate(self.fitness_function)
            current_solutions.append(individual)
            if individual.get_fitness() < best_solution.get_fitness():
                best_solution = individual
        
        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations
