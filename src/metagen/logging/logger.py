# src/metagen/utils/tensorboard_logger.py
from tensorboardX import SummaryWriter
from datetime import datetime
import uuid
import os
from typing import List
import numpy as np
from metagen.framework import Solution

class TensorBoardLogger:
    """Base class for TensorBoard logging in metaheuristics"""
    
    def __init__(self, log_dir: str = "logs"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_id = f"{timestamp}_{uuid.uuid4().hex[:6]}"
        self.log_dir = os.path.join(log_dir, self.run_id)
        self.writer = SummaryWriter(self.log_dir)

    def _log_solution_components(self, solutions: List[Solution], iteration: int, prefix: str = '') -> None:
        """
        Recursively log all components of solutions to TensorBoard.
        """
        if not solutions:
            return
        
        solutions_dict = [s.get_variables() for s in solutions]
        # Get the structure from the first solution
        first_solution = solutions_dict[0]
        
        for key, solution_type in first_solution.items():
            value = solution_type.value
            
            if isinstance(value, dict):
                # Recursively log nested dictionaries
                nested_solutions = [s[key].value for s in solutions_dict]
                self._log_solution_components(nested_solutions, iteration, f"{prefix}{key}/")
            elif isinstance(value, (int, float)):
                # Log numeric values as distribution/histogram
                value = sum([s[key].value for s in solutions_dict]) / len(solutions_dict)
                self.writer.add_scalar(f"{prefix}average_{key}", value, iteration)
            elif isinstance(value, (list, tuple)):
                # Log collection metrics
                values = [s[key].value for s in solutions_dict]
                avg_length = sum(len(v) for v in values) / len(values)
                self.writer.add_scalar(f"{prefix}average_length_{key}", avg_length, iteration)
                # Log the values in the collections
                if value and isinstance(value[0].value, (int, float)):
                    value = sum(value) / len(value)
                    self.writer.add_scalar(f"{prefix}average_{key}", value, iteration)

    def log_iteration(self, iteration: int, potential_solutions: List[Solution], 
                     best_solution: Solution) -> None:
        """
        Log metrics for the current iteration
        """

        # Log fitness statistics
        iteration_fitnesses = [ps.get_fitness() for ps in potential_solutions]

        avg_fitness = sum(iteration_fitnesses) / len(iteration_fitnesses)
        best_fitness = best_solution.get_fitness()

        self.writer.add_scalar('Fitness/Average', avg_fitness, iteration)
        self.writer.add_scalar('Fitness/Best', best_fitness, iteration)
        self.writer.add_histogram('Fitness/Distribution', np.array(iteration_fitnesses), iteration)
        
        # Log solution components
        self._log_solution_components(potential_solutions, iteration, prefix='Solutions/')

    def log_final_results(self, best_solution: Solution) -> None:
        """
        Log final results and metadata
        """
        self.writer.add_text('Run Information', 
                            f'Run ID: {self.run_id}\n'
                            f'Best Fitness: {best_solution.get_fitness()}', 
                            0)

    def close(self) -> None:
        """Close the TensorBoard writer"""
        self.writer.close()