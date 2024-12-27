from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Tuple
import ray
from metagen.framework import Domain, Solution
from metagen.logging import TensorBoardLogger
from copy import deepcopy

class Metaheuristic(TensorBoardLogger, ABC):
    """
    Abstract base class for metaheuristic algorithms.
    """
    def __init__(self, domain: Domain, fitness_function, log_dir: str = "logs") -> None:
        """
        Initialize the metaheuristic.
        
        Args:
            domain: The problem domain
            fitness_function: Function to evaluate solutions
            algorithm_name: Name of the algorithm for logging
            max_iterations: Maximum number of iterations
        """
        super().__init__(log_dir=log_dir)
        self.domain = domain
        self.fitness_function = fitness_function
        self.current_iteration = 0
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the population/solutions for the metaheuristic.
        Must set self.current_solutions and self.best_solution
        """
        pass

    @abstractmethod
    def iterate(self) -> None:
        """
        Execute one iteration of the metaheuristic.
        Must update self.current_solutions and self.best_solution if better found
        """
        pass

    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.
        Override this method to implement custom stopping criteria.
        """
        return False

    def pre_execution(self) -> None:
        """
        Callback executed before algorithm execution starts.
        Override this method to add custom pre-execution setup.
        """
        pass

    def post_execution(self) -> None:
        """
        Callback executed after algorithm execution completes.
        Override this method to add custom post-execution cleanup.
        """
        # Log final results
        self.log_final_results(self.best_solution)
        self.close()

    def pre_iteration(self) -> None:
        """
        Callback executed before each iteration.
        Override this method to add custom pre-iteration processing.
        """
        pass

    def post_iteration(self) -> None:
        """
        Callback executed after each iteration.
        Override this method to add custom post-iteration processing.
        """
        # Log iteration metrics
        self.log_iteration(
            self.current_iteration,
            self.current_solutions,
            self.best_solution
        )

    def run(self) -> Solution:
        """
        Execute the metaheuristic algorithm.
        """
        # Pre-execution callback
        self.pre_execution()

        # Initialize the algorithm
        self.initialize()

        # Main loop
        while not self.stopping_criterion():
            # Pre-iteration callback
            self.pre_iteration()

            # Execute one iteration
            self.iterate()

            # Post-iteration callback
            self.post_iteration()

            # Increment iteration counter
            self.current_iteration += 1

        # Post-execution callback
        self.post_execution()

        return deepcopy(self.best_solution)

# Distribuido

# Común para todos
def assign_load_equally(neighbor_population_size: int) -> List[int]:
    num_cpus = int(ray.available_resources().get("CPU", 1))
    num_cpus = min(num_cpus, neighbor_population_size)
    base_count = neighbor_population_size // num_cpus
    remainder = neighbor_population_size % num_cpus
    distribution = [base_count + 1 if i < remainder else base_count for i in range(num_cpus)]
    return distribution

# Para RS:

def distributed_base_population(population_size: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> [List[Solution], Solution]:
    distribution = assign_load_equally(population_size)
    futures = []
    for count in distribution:
        futures.append(remote_yield_mutate_and_evaluate_individuals.remote(count, domain, fitness_function))
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best)
    return population, best_individual

def local_yield_mutate_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> Tuple[List[Solution],Solution]:
    solution_type: type[Solution] = domain.get_connector().get_type(domain.get_core())
    best_subpopulation_individual = solution_type(domain, connector=domain.get_connector())
    best_subpopulation_individual.evaluate(fitness_function)
    subpopulation:List[Solution] = [best_subpopulation_individual]
    for _ in range(num_individuals-1):
            individual = solution_type(domain, connector=domain.get_connector())
            individual.evaluate(fitness_function)
            subpopulation.append(individual)
            if individual.fitness < best_subpopulation_individual.fitness:
                best_subpopulation_individual = individual
    return subpopulation, best_subpopulation_individual

@ray.remote
def remote_yield_mutate_and_evaluate_individuals(num_individuals: int, domain:Domain, fitness_function: Callable[[Solution], float]) -> [List[Solution],Solution]:
    return local_yield_mutate_and_evaluate_individuals(num_individuals, domain, fitness_function)




def distributed_mutation_and_evaluation(population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Tuple[List[Solution],Solution]:
    distribution = assign_load_equally(len(population))
    futures = []
    for count in distribution:
        futures.append(remote_mutate_and_evaluate_population.remote(population[:count], fitness_function, alteration_limit=alteration_limit))
        population = population[count:]
    remote_results = ray.get(futures)
    all_subpopulations = [result[0] for result in remote_results]
    population = [individual for subpopulation in all_subpopulations for individual in subpopulation]
    partial_best = [result[1] for result in remote_results]
    best_individual = min(partial_best)
    return population, best_individual

def local_mutate_and_evaluate_population(population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> [List[Solution],Solution]:
    # print('Population = ' + str(population))
    first_individual = population[0]
    # print('First individual = '+str(first_individual))
    first_individual.mutate(alteration_limit=alteration_limit)
    first_individual.evaluate(fitness_function)
    best_subpopulation_individual = first_individual
    for individual in population[1:]:
        individual.mutate(alteration_limit=alteration_limit)
        individual.evaluate(fitness_function)
        if individual.fitness < best_subpopulation_individual.fitness:
            best_subpopulation_individual = individual
    return population, best_subpopulation_individual

@ray.remote
def remote_mutate_and_evaluate_population (population:List[Solution], fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> [List[Solution],Solution]:
    return local_mutate_and_evaluate_population(population, fitness_function, alteration_limit=alteration_limit)




# Para SA:
def distributed_yield_mutate_evaluate_from_the_best(population_size: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> List[Solution]:
    distribution = assign_load_equally(population_size)
    futures= []
    for count in distribution:
        futures.append(remote_yield_mutate_and_evaluate_individuals_from_best.remote(count, best_solution, fitness_function, alteration_limit=alteration_limit))
    return ray.get(futures)


def local_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Solution:
        best_neighbor = deepcopy(best_solution)
        best_neighbor.mutate(alteration_limit=alteration_limit)
        best_neighbor.evaluate(fitness_function)
        for _ in range(num_individuals - 1):
            neighbor = deepcopy(best_solution)
            neighbor.mutate(alteration_limit=alteration_limit)
            neighbor.evaluate(fitness_function)
            if neighbor.fitness < best_neighbor.fitness:
                best_neighbor = neighbor
        return best_neighbor

@ray.remote
def remote_yield_mutate_and_evaluate_individuals_from_best(num_individuals: int, best_solution: Solution, fitness_function: Callable[[Solution], float], alteration_limit: Optional[float] = None) -> Solution:
    return local_yield_mutate_and_evaluate_individuals_from_best(num_individuals, best_solution, fitness_function, alteration_limit=alteration_limit)


