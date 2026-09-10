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

from abc import ABC, abstractmethod

from .import_helper import is_package_installed
from typing import List, Tuple, Optional, Callable
from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed
from copy import deepcopy

from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.tools import random_exploration

IS_RAY_INSTALLED = is_package_installed("ray")

if is_package_installed("tensorboard"):
    from metagen.logging.tensorboard_logger import TensorBoardLogger

if IS_RAY_INSTALLED:
    import ray
    from .distributed_tools import assign_load_equally, call_distributed, distributed_random_exploration


class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.

    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param population_size: The size of the population (default is 1).
    :type population_size: int, optional
    :param distributed: Whether to run on Ray (default is False). This is an island
        model, not a parallel evaluation of the same search: the population is split
        into one slice per CPU of the cluster, each slice runs ``iterate`` on its own
        in a worker, and the slices are merged and split again every iteration. The
        algorithm each worker runs is therefore the algorithm on a smaller population,
        and the number of evaluations, the elitism and the result all depend on how
        many CPUs the cluster has. Distributed and sequential runs are not comparable
        value by value, and the workers' random generators are not seeded (A-06).
    :type distributed: bool, optional
    :param log_dir: Directory the TensorBoard logs are written to. None, the default, writes nothing.
    :type log_dir: str or None, optional
    :param seed: Seed making the run reproducible (default is None, a different
        run every time). It seeds MetaGen's own generators, so it does not
        disturb the random state of the calling application.
    :type seed: Optional[int], optional

    :ivar domain: The problem domain.
    :vartype domain: Domain
    :ivar fitness_function: Function to evaluate solutions.
    :vartype fitness_function: Callable[[Solution], float]
    :ivar population_size: The size of the population.
    :vartype population_size: int
    :ivar distributed: Whether distributed computation is enabled.
    :vartype distributed: bool
    :ivar logger: Logger instance for TensorBoard, if available.
    :vartype logger: Optional[TensorBoardLogger]
    :ivar current_iteration: The current iteration of the algorithm.
    :vartype current_iteration: int
    :ivar best_solution: The best solution found so far.
    :vartype best_solution: Optional[Solution]
    :ivar current_solutions: The current population of solutions.
    :vartype current_solutions: List[Solution]
    :ivar best_solution_fitnesses: List of fitness values of the best solutions per iteration.
    :vartype best_solution_fitnesses: List[float]
    """

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size=20,
                 warmup_iterations: int = 0, distributed=False,
                 log_dir: Optional[str] = None, seed: Optional[int] = None) -> None:
        super().__init__()

        self.domain = domain
        self.fitness_function = fitness_function
        self.population_size = population_size
        self.warmup_iterations = warmup_iterations
        self.distributed = distributed
        self.seed = seed
        # TensorBoard used to switch itself on for the mere fact of being
        # installed, with no way to turn it off, so a sweep of hundreds of
        # configurations left hundreds of directories behind (A-12). It is opt-in
        # now: log_dir is where to write, and None means do not write.
        self.logger = (TensorBoardLogger(log_dir=log_dir)
                       if log_dir is not None and is_package_installed("tensorboard")
                       else None)

        self.current_iteration = -1
        self.best_solution: Optional[Solution] = None
        self.current_solutions: List[Solution] = []
        self.best_solution_fitnesses: List[float] = []

    def _launch_distributed_method(self, method: Callable) -> Tuple[List[Solution], Solution]:
        """
        Run ``initialize`` or ``iterate`` on Ray, one task per CPU of the cluster.

        The population is split with assign_load_equally and each slice is handed
        to a pickled copy of the algorithm in a worker, which runs the whole method
        on that slice alone; the slices that come back are concatenated and the best
        of the per-slice bests is kept. So with two CPUs a population of six is two
        independent runs of three that get remixed every iteration: an island model
        whose islands change with the CPU count. While initializing there is no
        population yet, so each worker builds its share from scratch.

        :param method: The method to distribute.
        :type method: Callable
        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        # While initializing there is no population to split yet, so the load is
        # population_size. Reading len(current_solutions) here would size the run
        # after whatever _warmup() left behind, which is one entry per warmup
        # round and has nothing to do with the population being built (F-03).
        if self.current_iteration == -1:
            distribution = assign_load_equally(self.population_size)
        else:
            distribution = assign_load_equally(
                len(self.current_solutions) if len(self.current_solutions) > 0 else self.population_size)
        population = deepcopy(self.current_solutions)
        futures = []

        if self.current_iteration != -1:
            metagen_logger.info(
                f"[ITERATION {self.current_iteration}] Distributing with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")
        else:
            metagen_logger.info(
                f"Distributing the initialization with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")

        for count in distribution:

            if self.current_iteration != -1:
                futures.append(call_distributed.remote(method, population[:count]))
                population = population[count:]
            else:
                futures.append(call_distributed.remote(method, count))

        remote_results = ray.get(futures)
        population = [individual for subpopulation in remote_results for individual in subpopulation[0]]
        best_individual = min([result[1] for result in remote_results], key=lambda sol: sol.get_fitness())

        return population, best_individual

    def _initialize(self) -> Tuple[List[Solution], Solution]:
        """
        Private function to initialize the population/solutions for the metaheuristic.

        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        if self.distributed:
            if not IS_RAY_INSTALLED:
                raise ImportError("Ray must be installed to use distributed initialization")

            population, best_individual = self._launch_distributed_method(self.initialize)
        else:
            population, best_individual = self.initialize(self.population_size)

        self.current_solutions = population

        # Merged rather than assigned: _warmup() runs first and may already hold a
        # better solution, which a plain assignment would throw away along with
        # every evaluation that produced it (F-03).
        if self.best_solution is None or best_individual.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_individual

        return population, best_individual

    def _warmup(self) -> None:
        """
        Executes the warmup phase before the main optimization loop.

        Generates `warmup_iterations` random solutions and updates the best solution found.
        This step ensures a good initial exploration of the search space before starting
        the main optimization process.
        """
        if self.warmup_iterations > 0:
            metagen_logger.info(f"Starting warmup phase with {self.warmup_iterations} iterations.")

            for warmup_step in range(self.warmup_iterations):
                if self.distributed:
                    if not IS_RAY_INSTALLED:
                        raise ImportError("Ray must be installed to use distributed execution")
                    metagen_logger.debug(
                        f'[WARMUP {warmup_step + 1}/{self.warmup_iterations}] Distributed warmup step.'
                    )
                    _, best_candidate = distributed_random_exploration(self.domain, self.fitness_function,
                                                                       self.population_size)
                else:
                    metagen_logger.debug(
                        f'[WARMUP {warmup_step + 1}/{self.warmup_iterations}] Warmup step.'
                    )
                    _, best_candidate = random_exploration(self.domain, self.fitness_function, self.population_size)

                # Store only the best solution found in each warmup iteration
                self.current_solutions.append(deepcopy(best_candidate))

                # Update the global best solution
                if self.best_solution is None or best_candidate.get_fitness() < self.best_solution.get_fitness():
                    self.best_solution = deepcopy(best_candidate)


            metagen_logger.info(f"Warmup phase completed. Proceeding to optimization.")

    def _iterate(self) -> Tuple[List[Solution], Solution]:
        """
        Private function to execute one iteration of the metaheuristic.

        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        if self.distributed:
            if not IS_RAY_INSTALLED:
                    raise ImportError("Ray must be installed to use distributed initialization")
            population, best_individual = self._launch_distributed_method(self.iterate)
        else:
            population, best_individual = self.iterate(self.current_solutions)

        self.current_solutions = population

        # Merged, not assigned, the same way _initialize does since F-03. Assigning
        # made elitism the responsibility of each subclass: one that returns the best
        # of its current population, as SSGA does, would hand back something worse
        # than the best already found and lose it (A-10).
        if self.best_solution is None or best_individual.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_individual

        return population, self.best_solution

    def _best_so_far(self) -> Solution:
        """
        The best solution found, once the run is under way.

        ``best_solution`` is declared Optional because it is None until
        ``_initialize()`` sets it, and that is true of the object's whole life. It
        is not true of any point a subclass reads it from -- ``iterate()`` and the
        callbacks only run after initialization -- so this narrows it there, and
        turns the AttributeError on None that reading it too early used to raise
        into an error that says what happened (P-11).

        :return: The best solution so far.
        :rtype: Solution
        :raises RuntimeError: If read before the run has initialized it.
        """
        if self.best_solution is None:
            raise RuntimeError(
                "best_solution is not available yet: run() has not initialized it")
        return self.best_solution

    def pre_execution(self) -> None:
        """
        Callback executed before algorithm execution starts.
        Override this method to add custom pre-execution setup.
        """
        pass

    @abstractmethod
    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:
        """
        Initialize the population/solutions for the metaheuristic.

        Everything the algorithm needs later has to be in what this returns. In
        distributed mode Ray runs it on a pickled copy of the algorithm, so anything
        it stores on self stays in the worker and is lost (F-40); state that must
        persist is rebuilt on the driver, in post_iteration, from what came back.

        :param num_solutions: The number of solutions to initialize.
        :type num_solutions: int
        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        pass

    def pre_iteration(self) -> None:
        """
        Callback executed before each iteration.
        Override this method to add custom pre-iteration processing.
        """
        pass

    @abstractmethod
    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        Execute one iteration of the metaheuristic.

        Same contract as initialize: in distributed mode this runs on a pickled copy,
        on a slice of the population, so it must not rely on storing anything on self
        between iterations (F-40). What it returns is what the next iteration gets.

        :param solutions: The current population of solutions.
        :type solutions: List[Solution]
        :return: A tuple containing the updated population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        pass

    @abstractmethod
    def stopping_criterion(self) -> bool:
        """
        Check if the algorithm should stop.

        Abstract on purpose: it used to return False, so a subclass that forgot to
        implement it looped for ever with nothing to say why (A-10).

        :return: True if the algorithm should stop, False otherwise.
        :rtype: bool
        """

    def post_iteration(self) -> None:
        """
        Callback executed after each iteration.
        Override this method to add custom post-iteration processing.
        """
        metagen_logger.debug(f'[ITERATION {self.current_iteration}] POPULATION ({len(self.current_solutions)}): {self.current_solutions}')
        metagen_logger.info(f'[ITERATION {self.current_iteration}] BEST SOLUTION: {self.best_solution}')
        self.best_solution_fitnesses.append(self._best_so_far().get_fitness())
        if self.logger: 
            # Log iteration metrics
            self.logger.writer.add_scalar('Population Size',
                                          len(self.current_solutions),
                                          self.current_iteration)
            self.logger.log_iteration(
                self.current_iteration, 
                self.current_solutions, 
                self._best_so_far()
            )

    def post_execution(self) -> None:
        """
        Callback executed after algorithm execution completes.
        Override this method to add custom post-execution cleanup.
        """
        if self.logger:
            # Log final results
            self.logger.log_final_results(self._best_so_far())
            self.logger.close()

    def run(self) -> Solution:
        """
        Execute the metaheuristic algorithm.

        :return: The best solution found.
        :rtype: Solution
        """
        # Seeded here rather than in __init__ so that every run() starts from
        # the same state: building two metaheuristics and running them later
        # would otherwise make the second one depend on the first.
        if self.seed is not None:
            set_seed(self.seed)

        # Remembered so that only the run() that started Ray stops it. Shutting it
        # down unconditionally took the runtime away from a cluster the user had
        # connected to, or from the other metaheuristics in a comparison (F-21).
        started_ray = False
        if self.distributed and IS_RAY_INSTALLED and not ray.is_initialized():
            ray.init()
            started_ray = True

        try:
            self.pre_execution()

            self._warmup()

            self._initialize()

            self.current_iteration = 0

            while not self.stopping_criterion():
                self.pre_iteration()

                self._iterate()

                self.post_iteration()
                    
                self.current_iteration += 1

            self.post_execution()
        finally:
            # Also on the way out of an exception: a runtime this run() started must
            # not outlive it, or the workers and their memory stay alive until the
            # interpreter exits (F-44).
            if started_ray and ray.is_initialized():
                ray.shutdown()

        return deepcopy(self._best_so_far())
