from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple
import numpy as np
from scipy.stats import norm
from metagen.framework import Domain, Solution
from copy import deepcopy

class TPE(Metaheuristic):
    """
    Tree-structured Parzen Estimator (TPE) class for optimization problems.

    :param domain: The domain representing the problem space.
    :type domain: Domain
    :param fitness_function: The fitness function used to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param population_size: The size of the population (default is 10).
    :type population_size: int, optional
    :param max_iterations: The number of iterations to run the algorithm (default is 50).
    :type max_iterations: int, optional
    :param gamma: The fraction of best solutions to consider (default is 0.25).
    :type gamma: float, optional
    :param log_dir: Directory to store logs (default is "logs/TPE").
    :type log_dir: str, optional

    **Code example**

    .. code-block:: python

        
        domain = Domain()

        domain.defineInteger(0, 1)

        fitness_function = ...

        search = TPE(domain, fitness_function, population_size=50, max_iterations=100)
        optimal_solution = search.run()
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size: int = 10, max_iterations: int = 50, gamma: float = 0.25, log_dir: str = "logs/TPE") -> None:
        super().__init__(domain, fitness_function, population_size, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.gamma = gamma

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """Initialize the population with random solutions"""
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
        """Perform one iteration of the TPE algorithm"""
        l = round(self.gamma * len(solutions))
        best_solutions = sorted(solutions, key=lambda sol: sol.get_fitness())[:l]
        worst_solutions = sorted(solutions, key=lambda sol: sol.get_fitness())[l:]

        new_solutions = []
        
        for _ in range(len(solutions)):
            new_solution = self.sample_new_solution(best_solutions, worst_solutions)
            new_solution.evaluate(self.fitness_function)
            new_solutions.append(new_solution)

        best_solution = min(new_solutions, key=lambda sol: sol.get_fitness())
        return new_solutions, best_solution

    def sample_new_solution(self, best_solutions: List[Solution], worst_solutions: List[Solution]) -> Solution:
        """Sample a new solution based on the best and worst solutions"""
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        new_solution = solution_type(self.domain, connector=self.domain.get_connector())

        for var in self.best_solution.get_variables():
            best_values = [sol[var] for sol in best_solutions]
            worst_values = [sol[var] for sol in worst_solutions]

            mu_best, sigma_best = norm.fit(best_values)
            mu_worst, sigma_worst = norm.fit(worst_values)

            p_best = norm.pdf(new_solution[var], mu_best, sigma_best)
            p_worst = norm.pdf(new_solution[var], mu_worst, sigma_worst)

            if p_best / (p_best + p_worst) > np.random.rand():
                new_solution[var] = np.random.normal(mu_best, sigma_best)
            else:
                new_solution[var] = np.random.normal(mu_worst, sigma_worst)

        return new_solution

    def stopping_criterion(self) -> bool:
        """Check if the stopping criterion has been reached"""
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """Additional processing after each generation"""
        super().post_iteration()
        if self.logger:
            self.logger.writer.add_scalar('TPE/Population Size', len(self.current_solutions), self.current_iteration)