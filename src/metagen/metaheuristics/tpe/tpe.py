import heapq

from metagen.framework.solution.tools import random_exploration
from metagen.metaheuristics.base import Metaheuristic
from typing import Callable, List, Tuple, Optional
import numpy as np
from scipy.stats import norm
from metagen.framework import Domain, Solution
from copy import deepcopy
from metagen.framework.domain.literals import I
from metagen.metaheuristics.gamma_schedules import GAMMA_FUNCTIONS, gamma_linear, gamma_sqrt, gamma_sample_based, \
    GammaConfig, compute_gamma


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
                 max_iterations: int = 50, warmup_iterations:int = 10, candidate_pool_size: int = 5,
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: str = "logs/TPE") -> None:
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
        super().__init__(domain, fitness_function, population_size, warmup_iterations, distributed=distributed, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.candidate_pool_size = candidate_pool_size
        self.gamma_config = gamma_config if gamma_config else GammaConfig(
            gamma_function="linear", minimum=0.1, maximum=0.3
        )

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population with random solutions.

        :param num_solutions: Number of initial solutions to generate, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the list of solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """

        current_solutions, best_solution = random_exploration(self.domain, self.fitness_function, num_solutions)
        return current_solutions, best_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:

        # Seleccionar el número de mejores soluciones a considerar
        # Obtener `gamma` de acuerdo con la estrategia configurada
        gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                              max_iterations=self.max_iterations, num_solutions=len(solutions))

        # Determinar el número de mejores soluciones a considerar
        l = round(gamma * len(solutions))

        # Seleccionar mejores y peores soluciones usando `heapq`
        best_solutions = heapq.nsmallest(l, solutions, key=lambda sol: sol.get_fitness())
        worst_solutions = heapq.nlargest(len(solutions) - l, solutions, key=lambda sol: sol.get_fitness())

        # Generar nueva población
        new_solutions = [deepcopy(self.best_solution)]
        local_best = new_solutions[0]

        for _ in range(len(solutions) - 1):
            best_candidate = self.sample_new_solution(best_solutions, worst_solutions)
            best_candidate.evaluate(self.fitness_function)

            for _ in range(self.candidate_pool_size - 1):
                candidate = self.sample_new_solution(best_solutions, worst_solutions)
                candidate.evaluate(self.fitness_function)

                if candidate.get_fitness() < best_candidate.get_fitness():
                    best_candidate = candidate

            new_solutions.append(best_candidate)

            if best_candidate.get_fitness() < local_best.get_fitness():
                local_best = best_candidate

        return new_solutions, local_best


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