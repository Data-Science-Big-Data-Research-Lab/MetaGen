from collections import deque
from metagen.framework import Domain, Solution
from collections.abc import Callable
from typing import List, Tuple, Deque, Optional

from metagen.framework.solution.tools import local_search_with_tabu
from metagen.metaheuristics.base import Metaheuristic
from copy import deepcopy

from metagen.metaheuristics.gamma_schedules import GAMMA_FUNCTIONS, gamma_linear, GammaConfig, compute_gamma


class TabuSearch(Metaheuristic):
    """
    Tabu Search Algorithm for optimization problems.

    This class implements the Tabu Search metaheuristic which uses a memory structure (tabu list)
    to avoid revisiting recently explored solutions. The algorithm explores the neighborhood of
    the current solution while maintaining a list of forbidden (tabu) solutions.

    :param domain: The problem's domain to explore
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions
    :type fitness_function: Callable[[Solution], float]
    :param population_size: Size of the population (neighborhood) to maintain, defaults to 10
    :type population_size: int, optional
    :param max_iterations: Maximum number of iterations to run, defaults to 10
    :type max_iterations: int, optional
    :param tabu_size: Maximum size of the tabu list, defaults to 5
    :type tabu_size: int, optional
    :param alteration_limit: Maximum proportion of solution to alter in local search, defaults to 1.0
    :type alteration_limit: float, optional
    :param distributed: Whether to use distributed computation, defaults to False
    :type distributed: bool, optional
    :param log_dir: Directory for logging, defaults to "logs/TS"
    :type log_dir: str, optional

    :ivar max_iterations: Maximum number of iterations to run
    :vartype max_iterations: int
    :ivar tabu_size: Maximum size of the tabu list
    :vartype tabu_size: int
    :ivar tabu_list: List of recently visited solutions that are forbidden
    :vartype tabu_list: Deque[Solution]
    :ivar alteration_limit: Maximum proportion of solution to alter in local search
    :vartype alteration_limit: float
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float],
                 population_size: int = 10, warmup_iterations:int = 5,
                 max_iterations: int = 20, tabu_size: int = 5, alteration_limit: float = 1.0,
                 gamma_config: Optional[GammaConfig] = None, distributed=False, log_dir: str = "logs/TS"):
        """
        Initialize the Tabu Search algorithm.

        :param domain: The problem's domain to explore
        :type domain: Domain
        :param fitness_function: Function to evaluate solutions
        :type fitness_function: Callable[[Solution], float]
        :param population_size: Size of the population (neighborhood) to maintain, defaults to 10
        :type population_size: int, optional
        :param max_iterations: Maximum number of iterations to run, defaults to 10
        :type max_iterations: int, optional
        :param tabu_size: Maximum size of the tabu list, defaults to 5
        :type tabu_size: int, optional
        :param alteration_limit: Maximum proportion of solution to alter in local search, defaults to 1.0
        :type alteration_limit: float, optional
        :param distributed: Whether to use distributed computation, defaults to False
        :type distributed: bool, optional
        :param log_dir: Directory for logging, defaults to "logs/TS"
        :type log_dir: str, optional
        """
        super().__init__(domain, fitness_function, population_size, warmup_iterations, distributed, log_dir)
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.tabu_list:Deque[Solution] = deque(maxlen=tabu_size)
        self.alteration_limit: float = alteration_limit
        self.gamma_config = gamma_config

    def initialize(self, num_solutions: int=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the Tabu Search algorithm.

        Creates an initial solution and explores its neighborhood while respecting
        the tabu list constraints.

        :param num_solutions: Number of solutions in the neighborhood, defaults to 10
        :type num_solutions: int, optional
        :return: A tuple containing the neighborhood solutions and the initial solution
        :rtype: Tuple[List[Solution], Solution]
        """
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        first_solution = solution_type(self.domain, connector=self.domain.get_connector())
        first_solution.evaluate(self.fitness_function)

        current_neighborhood = local_search_with_tabu(first_solution, self.fitness_function, num_solutions, self.alteration_limit, list(self.tabu_list))[0]

        return current_neighborhood, first_solution

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the Tabu Search algorithm.

        Explores the neighborhood of the current best solution while respecting
        the tabu list constraints. The best solution found is added to the tabu list
        to prevent cycling.

        :param solutions: Current population of solutions
        :type solutions: List[Solution]
        :return: A tuple containing the new neighborhood solutions and the best solution found
        :rtype: Tuple[List[Solution], Solution]
        """
        # Ajustar dinámicamente el tamaño de la vecindad
        # Si hay configuración de gamma, calcular `l` dinámicamente
        if self.gamma_config:
            gamma = compute_gamma(self.gamma_config, iteration=self.current_iteration,
                                  max_iterations=self.max_iterations, num_solutions=len(solutions))
            l = max(1, round(gamma * len(solutions)))  # Asegurar al menos 1 vecino
        else:
            l = len(solutions)  # Sin gamma, se mantiene el número total de individuos

        # Aplicar búsqueda local con tabú respetando el tamaño `l`
        current_solutions, best_solution = local_search_with_tabu(
            self.best_solution, self.fitness_function, l, self.alteration_limit, list(self.tabu_list)
        )

        # Si no se generan soluciones válidas, mantener la población anterior
        if not current_solutions:
            current_solutions = solutions
            best_solution = deepcopy(self.best_solution)
        else:
            self.tabu_list.append(best_solution)  # Agregar mejor solución a la lista tabú

        return current_solutions, best_solution

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        The algorithm stops when the current iteration reaches the maximum number of iterations.

        :return: True if the maximum number of iterations is reached, False otherwise
        :rtype: bool
        """
        return self.current_iteration >= self.max_iterations
