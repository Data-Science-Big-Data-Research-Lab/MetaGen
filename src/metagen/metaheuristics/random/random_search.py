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
from copy import deepcopy
from metagen.framework import Domain, Solution
from metagen.metaheuristics.base import Metaheuristic


class RandomSearch(Metaheuristic):

    """
    RandomSearch is a class for performing a random search optimization algorithm.

    It generates and evaluates random solutions in a search space to find an optimal solution.

    :param domain: The search domain that defines the solution space.
    :type domain: Domain
    :param fitness: The fitness function used to evaluate solutions.
    :type fitness: Callable[[Solution], float]
    :param search_space_size: The size of the search space. Default is 30.
    :type search_space_size: int, optional
    :param iterations: The number of optimization iterations. Default is 20.
    :type iterations: int, optional

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
        super().__init__(domain, fitness_function, log_dir)
        self.search_space_size = search_space_size
        self.max_iterations = max_iterations
    

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def initialize(self) -> None:
        """Initialize random solutions"""
        solution_type: type[Solution] = self.domain.get_connector().get_type(
            self.domain.get_core())
        
        # Create initial solutions
        self.current_solutions = [
            solution_type(self.domain, connector=self.domain.get_connector())
            for _ in range(self.search_space_size)
        ]
        
        # Evaluate initial solutions
        for solution in self.current_solutions:
            solution.evaluate(self.fitness_function)
        
        # Set initial best solution
        self.best_solution = deepcopy(min(self.current_solutions))

    def iterate(self) -> None:
        """Execute one iteration of random search"""
        for solution in self.current_solutions:
            # Mutate and evaluate
            solution.mutate()
            solution.evaluate(self.fitness_function)
            
            # Update best solution if better found
            if solution < self.best_solution:
                self.best_solution = deepcopy(solution)
