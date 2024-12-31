from collections import deque

import ray

from metagen.framework import Domain, Solution
from collections.abc import Callable

from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.distributed_suite import local_yield_mutate_evaluate_population_from_the_best, \
    distributed_yield_mutate_evaluate_from_the_best


class TabuSearch(Metaheuristic):

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], log_dir: str = "logs/TS",
                 max_iterations: int = 10, neighbor_population_size:int = 10, tabu_size: int = 5, alteration_limit: float = 1.0):
        """
        Tabu Search Algorithm for optimization problems.

        Args:
            domain (Domain): The problem's domain to explore.
            max_iterations (int): The maximum number of iterations.
            tabu_size (int): Maximum size of the tabu list.
            aspiration_criteria (callable, optional): Function to override tabu restrictions.
        """
        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.neighbor_population_size = neighbor_population_size
        self.tabu_size = tabu_size
        self.tabu_list = deque(maxlen=tabu_size)
        self.alteration_limit: float = alteration_limit
        self.current_solution:Solution|None = None

    def initialize(self) -> None:
        """Initialize the Tabu Search algorithm."""
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        self.current_solution = solution_type(self.domain, connector=self.domain.get_connector())
        self.current_solution.evaluate(self.fitness_function)
        self.best_solution = self.current_solution

    def iterate(self) -> None:

        # Yield neighbors
        neighbors, best_neighbor = local_yield_mutate_evaluate_population_from_the_best(self.neighbor_population_size,
                                                                         self.current_solution, self.fitness_function,
                                                                         self.alteration_limit)
        # print(f'[{self.current_iteration}] N [{len(neighbors)}]: {neighbors}')


        # Filter candidates that are not in the tabu list or meet aspiration criteria
        valid_neighbors = [neighbor for neighbor in neighbors if neighbor not in self.tabu_list]
        # print(f'[{self.current_iteration}] VN [{len(valid_neighbors)}]: {valid_neighbors}')

        # Skip iteration if no valid neighbors
        if not valid_neighbors:
            print(f'[{self.current_iteration}] Skipped')
            self.current_iteration += 1
            self.skip_iteration()

        # Select the best neighbor
        next_solution = min(valid_neighbors, key=lambda sol: sol.get_fitness())

        # Update best solution
        if next_solution.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = next_solution

        # Update tabu list
        self.tabu_list.append(next_solution)
        self.current_solution = next_solution

        # Update iteration count
        self.current_solutions = neighbors

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('TS/Population Size',
                               len(self.current_solutions),
                               self.current_iteration)


class DistributedTabuSearch(Metaheuristic):

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], log_dir: str = "logs/TS",
                 max_iterations: int = 10, neighbor_population_size:int = 10, tabu_size: int = 5, alteration_limit: float = 1.0):
        """
        Tabu Search Algorithm for optimization problems.

        Args:
            domain (Domain): The problem's domain to explore.
            max_iterations (int): The maximum number of iterations.
            tabu_size (int): Maximum size of the tabu list.
            aspiration_criteria (callable, optional): Function to override tabu restrictions.
        """
        super().__init__(domain, fitness_function, log_dir=log_dir)
        self.max_iterations = max_iterations
        self.neighbor_population_size = neighbor_population_size
        self.tabu_size = tabu_size
        self.tabu_list = deque(maxlen=tabu_size)
        self.alteration_limit: float = alteration_limit
        self.current_solution:Solution|None = None

    def initialize(self) -> None:
        """Initialize the Tabu Search algorithm."""
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        self.current_solution = solution_type(self.domain, connector=self.domain.get_connector())
        self.current_solution.evaluate(self.fitness_function)
        self.best_solution = self.current_solution

    def iterate(self) -> None:

        # Yield neighbors
        neighbors = distributed_yield_mutate_evaluate_from_the_best(self.neighbor_population_size,
                                                                         self.current_solution, self.fitness_function,
                                                                         self.alteration_limit)


        # Filter candidates that are not in the tabu list or meet aspiration criteria
        valid_neighbors = [neighbor for neighbor in neighbors if neighbor not in self.tabu_list]
        # print(f'[{self.current_iteration}] VN [{len(valid_neighbors)}]: {valid_neighbors}')

        # Skip iteration if no valid neighbors
        if not valid_neighbors:
            print(f'[{self.current_iteration}] Skipped')
            self.current_iteration += 1
            self.skip_iteration()

        # Select the best neighbor
        next_solution = min(valid_neighbors, key=lambda sol: sol.get_fitness())

        # Update best solution
        if next_solution.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = next_solution

        # Update tabu list
        self.tabu_list.append(next_solution)
        self.current_solution = next_solution

        # Update iteration count
        self.current_solutions = neighbors

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.max_iterations

    def post_iteration(self) -> None:
        """
        Additional processing after each generation.
        """
        super().post_iteration()
        print(f'[{self.current_iteration}] {self.best_solution}')
        self.writer.add_scalar('TS/Population Size',
                               len(self.current_solutions),
                               self.current_iteration)

    def run(self) -> Solution:
        """
        Execute the distributed simulated annealing algorithm.

        Returns:
            The best solution found
        """
        # Initialize Ray at the start
        if not ray.is_initialized():
            ray.init()

        try:
            # Run the main loop of the metaheuristic
            super().run()
            return self.best_solution

        finally:
            # Ensure Ray is properly shut down after execution
            ray.shutdown()

