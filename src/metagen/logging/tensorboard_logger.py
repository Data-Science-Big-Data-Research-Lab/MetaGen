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
from tensorboardX import SummaryWriter
from datetime import datetime
import uuid
import os
from typing import List
import numpy as np
from metagen.framework import Solution

class TensorBoardLogger:
    """
    Base class for TensorBoard logging in metaheuristics.

    This class provides a basic implementation for logging optimization experiments
    using TensorBoard, allowing detailed monitoring of optimization processes,
    solution evolution, and performance metrics.

    :param log_dir: Directory to store TensorBoard log files, defaults to "logs"
    :type log_dir: str, optional

    :ivar run_id: Unique identifier for the current experiment run
    :vartype run_id: str
    :ivar log_dir: Directory for storing TensorBoard log files
    :vartype log_dir: str
    :ivar writer: TensorBoard SummaryWriter instance
    :vartype writer: tensorboardX.SummaryWriter

    **Code Example**

    .. code-block:: python

        from metagen.logging.tensorboard_logger import TensorBoardLogger

        # Create a TensorBoard logger for an experiment
        logger = TensorBoardLogger(log_dir="./tb_logs")
        
        # Log metrics and other data
        logger.log_iteration(iteration=10, potential_solutions=potential_solutions, best_solution=best_solution)
        logger.log_final_results(best_solution=best_solution)
    """

    def __init__(self, log_dir: str = "logs"):
        """
        Initialize the TensorBoard Logger.

        :param log_dir: Directory to store TensorBoard log files, defaults to "logs"
        :type log_dir: str, optional
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        self.run_id = f"{timestamp}_{uuid.uuid4().hex[:6]}"
        self.log_dir = os.path.join(log_dir, self.run_id)
        self.writer = SummaryWriter(self.log_dir)

    def _log_solution_components(self, solutions: List[Solution], iteration: int, prefix: str = '') -> None:
        """
        Recursively log all components of solutions to TensorBoard.

        :param solutions: List of solutions to log
        :type solutions: List[Solution]
        :param iteration: Current iteration number
        :type iteration: int
        :param prefix: Prefix for logging, defaults to ''
        :type prefix: str, optional
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
                nested_solutions = [s[key] for s in solutions_dict]
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
        Log metrics for the current iteration.

        :param iteration: Current iteration number
        :type iteration: int
        :param potential_solutions: List of potential solutions
        :type potential_solutions: List[Solution]
        :param best_solution: Best solution found so far
        :type best_solution: Solution
        """
        # Log fitness statistics
        iteration_fitnesses = [ps.get_fitness() for ps in potential_solutions]
        len_iter_fit = len(iteration_fitnesses)
        # TODO: para evitar division por cero
        if len_iter_fit == 0:
            len_iter_fit = 1


        avg_fitness = sum(iteration_fitnesses) / len_iter_fit
        best_fitness = best_solution.get_fitness()

        self.writer.add_scalar('Fitness/Average', avg_fitness, iteration)
        self.writer.add_scalar('Fitness/Best', best_fitness, iteration)
        self.writer.add_histogram('Fitness/Distribution', np.array(iteration_fitnesses), iteration)
        
        # Log solution components
        self._log_solution_components(potential_solutions, iteration, prefix='Solutions/')

    def log_final_results(self, best_solution: Solution) -> None:
        """
        Log final results and metadata.

        :param best_solution: Best solution found
        :type best_solution: Solution
        """
        self.writer.add_text('Run Information', 
                            f'Run ID: {self.run_id}\n'
                            f'Best Fitness: {best_solution.get_fitness()}', 
                            0)

    def close(self) -> None:
        """Close the TensorBoard writer"""
        self.writer.close()
    
    def __getstate__(self):
        """Control which attributes are pickled"""
        state = self.__dict__.copy()
        # Remove unpicklable attributes
        state['writer'] = None
        return state

    def __setstate__(self, state):
        """Restore instance attributes when unpickling"""
        self.__dict__.update(state)

        self.writer = SummaryWriter(self.log_dir)
