from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple
import numpy as np
from scipy.stats import norm
from metagen.framework import Domain, Solution
from copy import deepcopy
from metagen.framework.domain.literals import I

class TPE(Metaheuristic):
    """
    Tree-structured Parzen Estimator (TPE) algorithm for optimization problems.

    This class implements the TPE metaheuristic which uses kernel density estimation
    to model the probability of good and bad solutions. The algorithm iteratively
    samples new solutions from regions of the search space that are more likely to
    contain good solutions.

    :param domain: The problem domain that defines the solution space
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Size of the population to maintain, defaults to 10
    :type population_size: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 50
    :type max_iterations: int, optional
    :param gamma: Fraction of best solutions to consider when building models, defaults to 0.25
    :type gamma: float, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/TPE"
    :type log_dir: str, optional

    :ivar max_iterations: Maximum number of iterations
    :vartype max_iterations: int
    :ivar gamma: Fraction of best solutions for model building
    :vartype gamma: float

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain
        from metagen.metaheuristics import TPE
        
        domain = Domain()
        domain.defineInteger(0, 1)
        
        fitness_function = ...

        search = TPE(domain, fitness_function, population_size=50, max_iterations=100)
        optimal_solution = search.run()
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size: int = 10, 
                 max_iterations: int = 50, gamma: float = 0.25, distributed=False, log_dir: str = "logs/TPE") -> None:
        """
        Initialize the TPE algorithm.

        :param domain: The problem domain that defines the solution space
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param population_size: Size of the population to maintain, defaults to 10
        :type population_size: int, optional
        :param max_iterations: Maximum number of iterations to run, defaults to 50
        :type max_iterations: int, optional
        :param gamma: Fraction of best solutions to consider when building models, defaults to 0.25
        :type gamma: float, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory for logging, defaults to "logs/TPE"
        :type log_dir: str, optional
        """
        super().__init__(domain, fitness_function, population_size, distributed=distributed, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.gamma = gamma

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
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
        """
        Execute one iteration of the TPE algorithm.

        In each iteration, the algorithm:
        1. Splits solutions into good and bad sets using gamma threshold
        2. Fits probability models to both sets
        3. Samples new solutions favoring regions with high probability of good solutions

        :param solutions: Current population of solutions
        :type solutions: List[Solution]
        :return: A tuple containing the new population and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        l = round(self.gamma * len(solutions))
        best_solutions = sorted(solutions, key=lambda sol: sol.get_fitness())[:l]
        worst_solutions = sorted(solutions, key=lambda sol: sol.get_fitness())[l:]

        new_solutions = [deepcopy(self.best_solution)]
        
        for _ in range(len(solutions)-1):
            new_solution = self.sample_new_solution(best_solutions, worst_solutions)
            new_solution.evaluate(self.fitness_function)
            new_solutions.append(new_solution)

        best_solution = min(new_solutions, key=lambda sol: sol.get_fitness())
        return new_solutions, best_solution

    def sample_new_solution(self, best_solutions: List[Solution], worst_solutions: List[Solution]) -> Solution:
        """
        Sample a new solution based on probability models of good and bad solutions.

        For each variable, the method:
        1. Fits normal distributions to values from good and bad solutions
        2. Samples new values with higher probability from good regions

        :param best_solutions: List of solutions considered good
        :type best_solutions: List[Solution]
        :param worst_solutions: List of solutions considered bad
        :type worst_solutions: List[Solution]
        :return: A newly sampled solution
        :rtype: Solution
        """
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        new_solution = solution_type(self.domain, connector=self.domain.get_connector())

        for var in self.best_solution.get_variables():
            best_values = [sol[var] for sol in best_solutions]
            worst_values = [sol[var] for sol in worst_solutions]

            mu_best, sigma_best = norm.fit(best_values)
            mu_worst, sigma_worst = norm.fit(worst_values)

            p_best = norm.pdf(new_solution[var], mu_best, sigma_best)
            p_worst = norm.pdf(new_solution[var], mu_worst, sigma_worst)

            var_type = self.domain.get_core().get(var).get_attributes()[0]
            minumum = self.domain.get_core().get(var).get_attributes()[1]
            maximum = self.domain.get_core().get(var).get_attributes()[2]

            new_value = None
            
            if p_best / (p_best + p_worst) > np.random.rand():
                new_value = np.clip(np.random.normal(mu_best, sigma_best), minumum, maximum).item()
            else:
                new_value = np.clip(np.random.normal(mu_worst, sigma_worst), minumum, maximum).item()

            if var_type == I:
                new_value = int(new_value)
            new_solution[var] = new_value

        return new_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        The algorithm stops when the current iteration reaches the maximum number
        of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """Additional processing after each generation"""
        super().post_iteration()
        if self.logger:
            self.logger.writer.add_scalar('TPE/Population Size', len(self.current_solutions), self.current_iteration)