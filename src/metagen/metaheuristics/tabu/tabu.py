from collections import deque
from metagen.framework import Domain, Solution
from collections.abc import Callable
from copy import deepcopy
import random
import math

class TabuSearch:
    def __init__(self, domain: Domain, fitness_func: Callable[[Solution], float],  max_iterations: int, tabu_size: int, alteration_limit: float =0.1):
        """
        Tabu Search Algorithm for optimization problems.

        Args:
            domain (Domain): The problem's domain to explore.
            max_iterations (int): The maximum number of iterations.
            tabu_size (int): Maximum size of the tabu list.
            aspiration_criteria (callable, optional): Function to override tabu restrictions.
        """
        self.domain = domain
        self.max_iterations = max_iterations
        self.tabu_size = tabu_size
        self.fitness_func = fitness_func if fitness_func else self.default_aspiration_criteria
        self.alteration_limit: float = alteration_limit
        self.tabu_list = deque(maxlen=tabu_size)

    @staticmethod
    def default_aspiration_criteria(current_solution, candidate_solution):
        """Default aspiration criteria: accept candidate if it's better."""
        return candidate_solution.fitness > current_solution.fitness

    def run(self):
        """Run the Tabu Search optimization process."""
        # Generate initial solution
        solution_type: type[Solution] = self.domain.get_connector().get_type(self.domain.get_core())
        current_solution = solution_type(self.domain, connector=self.domain.get_connector())
        best_solution = current_solution

        for iteration in range(self.max_iterations):
            # Generate neighborhood solutions
            neighbors = []
            for i in range(5):
                neighbour = deepcopy(current_solution)
                neighbour.mutate(alteration_limit=self.alteration_limit)
                neighbour.evaluate(self.fitness_func)
                neighbors.append(neighbour)

            # Filter candidates that are not in the tabu list or meet aspiration criteria
            valid_neighbors = [
                neighbor for neighbor in neighbors
                if neighbor not in self.tabu_list or current_solution < neighbor
            ]

            # Skip iteration if no valid neighbors
            if not valid_neighbors:
                continue

            # Select the best neighbor
            next_solution = min(valid_neighbors, key=lambda sol: sol.fitness)

            # Update tabu list
            self.tabu_list.append(next_solution)

            # Update current and best solutions
            current_solution = next_solution
            if current_solution < best_solution:
                best_solution = current_solution

        return best_solution