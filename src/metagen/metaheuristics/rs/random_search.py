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
from metagen.metaheuristics.tools import random_exploration
from metagen.metaheuristics.base import Metaheuristic
from typing import Optional, List, Tuple, Callable
from copy import deepcopy


class RandomSearch(Metaheuristic):
    """
    RandomSearch is a class for performing a random search optimization algorithm.

    It generates and evaluates random solutions in a search space to find an optimal solution.
    The algorithm maintains a population of solutions and in each iteration, it mutates all solutions
    except the best one from the previous iteration.

    :param domain: The search domain that defines the solution space
    :type domain: Domain
    :param fitness_function: The fitness function used to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: The size of the population to maintain, defaults to 1
    :type population_size: int, optional
    :param max_iterations: The maximum number of iterations to run, defaults to 20
    :type max_iterations: int, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional

    :ivar max_iterations: Maximum number of iterations to run
    :vartype max_iterations: int

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import RandomSearch

        domain = Domain()
        domain.define_integer("n", 0, 100)

        def fitness_function(solution: Solution) -> float:
            return abs(solution["n"] - 42)

        search = RandomSearch(domain, fitness_function, population_size=50, max_iterations=100)
        optimal_solution = search.run()
    """
    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size = 10, max_iterations: int = 20, distributed = False, log_dir: Optional[str] = None, seed: Optional[int] = None) -> None:
        """
        Initialize the RandomSearch algorithm.

        :param domain: The search domain that defines the solution space
        :type domain: Domain
        :param fitness_function: The fitness function used to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param population_size: The size of the population to maintain, defaults to 1
        :type population_size: int, optional
        :param max_iterations: The maximum number of iterations to run, defaults to 20
        :type max_iterations: int, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
        :type log_dir: str or None, optional
        """
        super().__init__(domain, fitness_function, population_size, distributed=distributed, log_dir=log_dir, seed=seed)
        self.max_iterations = max_iterations

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize a population of random solutions.

        :param num_solutions: Number of solutions to initialize, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the random search algorithm.
        
        In each iteration, the best solution from the previous iteration is preserved,
        while all other solutions are mutated and evaluated.

        :param solutions: The current population of solutions
        :type solutions: List[Solution]
        :return: A tuple containing the updated population and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        best_solution = deepcopy(self._best_so_far())
        current_solutions = [best_solution]

        # The elite copy above takes one slot, so one individual has to go, and it
        # should be the worst. This used to drop solutions[-1] whatever it was, which
        # is as often as not the best of the population (A-04).
        worst_index = max(range(len(solutions)),
                          key=lambda index: solutions[index].get_fitness())

        for index, individual in enumerate(solutions):
            if index == worst_index:
                continue
            individual.mutate()
            individual.evaluate(self.fitness_function)
            current_solutions.append(individual)
            if individual.get_fitness() < best_solution.get_fitness():
                best_solution = individual

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.
        
        The algorithm stops when the current iteration reaches the maximum number of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations
