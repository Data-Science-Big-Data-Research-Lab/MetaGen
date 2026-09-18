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

import heapq
from abc import ABC, abstractmethod

from .import_helper import is_package_installed
from typing import List, Tuple, Optional, Callable
from metagen.framework import Domain, Solution
from metagen.framework.rng import get_rng, set_seed, spawn_seed
from copy import deepcopy

from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.tools import random_exploration

IS_RAY_INSTALLED = is_package_installed("ray")

if is_package_installed("tensorboard"):
    from metagen.logging.tensorboard_logger import TensorBoardLogger

if IS_RAY_INSTALLED:
    import ray
    from .distributed_tools import assign_load_equally, call_distributed, distributed_random_exploration


#: The two ways the slices of a distributed run make up the next population.
DISTRIBUTION_MODELS = frozenset({"global", "islands"})


class Metaheuristic(ABC):
    """
    Abstract base class for metaheuristic algorithms.

    ``minimum_slice`` is the fewest individuals a distributed slice may hold: the
    population is split into one slice per CPU, and an algorithm that needs several
    individuals per step declares it here (the genetic ones need two to cross), so
    that a cluster with more CPUs than individuals does not hand it islands of one.

    :param domain: The problem domain.
    :type domain: Domain
    :param fitness_function: Function to evaluate solutions.
    :type fitness_function: Callable[[Solution], float]
    :param population_size: The size of the population (default is 20).
    :type population_size: int, optional
    :param warmup_iterations: Rounds of random exploration run before ``initialize``, each
        evaluating ``population_size`` solutions; the best solution they find is kept as
        the starting best (default is 0).
    :type warmup_iterations: int, optional
    :param distributed: Whether to run on Ray (default is False): the population is
        split into one slice per CPU of the cluster and each slice runs ``iterate`` on
        its own in a worker, every iteration. What happens to the slices afterwards is
        the ``distribution_model``. Two distributed runs with the same ``seed`` on the
        same number of CPUs reproduce each other, since every worker task is seeded
        from the driver's generator.
    :type distributed: bool, optional
    :param distribution_model: How the slices make up the next population, ``"global"``
        (the default) or ``"islands"``.

        With ``"global"`` the driver shuffles the population before splitting it, so
        that every iteration mixes the individuals across workers, and once the slices
        return it selects the next population **from the parents it sent and every
        candidate that came back**, all workers considered: a (μ+λ) survivor selection
        by fitness, ``population_size`` strong, which ``select_survivors`` implements
        and an algorithm may override (TPE merges the histories instead, HillClimbing,
        TabuSearch and SA keep the fresh candidates only). The budget per iteration
        does not grow with the CPU count: it is the sequential one for HillClimbing,
        TabuSearch and TPE, and for GA and Memetic when the slices have an even
        number of individuals (a slice breeds pairs, so an odd slice breeds one child
        fewer); ``RandomSearch`` keeps one elite per slice and mutates one individual
        fewer per slice, and ``SSGA`` breeds its two children in every slice.

        With ``"islands"`` the slices come back with the size they left with and are
        concatenated in order, so the next split hands the same individuals to the
        same worker: the islands never exchange individuals and share only the best
        solution the driver keeps. The algorithm each worker runs is the algorithm on
        a smaller population, and the number of evaluations, the elitism and the
        result depend on how many CPUs the cluster has.
    :type distribution_model: str, optional
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

    # minimum_slice exists since F-46: islands of one individual crashed GA and Memetic.
    # Worker tasks are seeded from the driver since A-06.
    minimum_slice: int = 1

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size=20,
                 warmup_iterations: int = 0, distributed=False,
                 log_dir: Optional[str] = None, seed: Optional[int] = None,
                 distribution_model: str = "global") -> None:
        super().__init__()

        if distribution_model not in DISTRIBUTION_MODELS:
            raise ValueError(f"distribution_model must be one of {sorted(DISTRIBUTION_MODELS)}, "
                             f"not {distribution_model!r}")

        self.domain = domain
        self.fitness_function = fitness_function
        if population_size < self.minimum_slice:
            raise ValueError(f"{type(self).__name__} needs a population of at least {self.minimum_slice} "
                             f"and population_size is {population_size}.")
        self.population_size = population_size
        self.warmup_iterations = warmup_iterations
        self.distributed = distributed
        self.distribution_model = distribution_model
        # How many slices the population was last split into, for an algorithm that
        # shares a per-iteration budget among them (TPE splits its candidate pool).
        self.distributed_slices: int = 1
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
        on that slice alone; the best of the per-slice bests is kept. What becomes of
        the slices is the ``distribution_model``: under ``"global"`` the population is
        shuffled before the cut and the next population is chosen by
        ``select_survivors`` out of the parents and everything that came back; under
        ``"islands"`` the slices are concatenated in order, so the same individuals go
        back to the same worker every iteration and with two CPUs a population of six
        is two independent runs of three for the whole execution. While initializing
        there is no population yet, so each worker builds its share from scratch.

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
            distribution = assign_load_equally(self.population_size, self.minimum_slice)
        else:
            distribution = assign_load_equally(
                len(self.current_solutions) if len(self.current_solutions) > 0 else self.population_size,
                self.minimum_slice)
        parents = deepcopy(self.current_solutions)
        iterating = self.current_iteration != -1
        # Shuffled before the cut, so that the slices are made of different
        # individuals every iteration: that is what lets them mix across workers.
        if iterating and self.distribution_model == "global":
            get_rng().shuffle(parents)
        self.distributed_slices = len(distribution)
        population = list(parents)
        futures = []

        if iterating:
            metagen_logger.info(
                f"[ITERATION {self.current_iteration}] Distributing with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")
        else:
            metagen_logger.info(
                f"Distributing the initialization with {ray.cluster_resources().get('CPU', 0)} CPUs -- {distribution}")

        for count in distribution:

            if iterating:
                futures.append(call_distributed.remote(spawn_seed(), method, population[:count]))
                population = population[count:]
            else:
                futures.append(call_distributed.remote(spawn_seed(), method, count))

        remote_results = ray.get(futures)
        offspring = [individual for subpopulation in remote_results for individual in subpopulation[0]]
        best_individual = min([result[1] for result in remote_results], key=lambda sol: sol.get_fitness())

        if iterating and self.distribution_model == "global":
            return self.select_survivors(parents, offspring), best_individual
        return offspring, best_individual

    def select_survivors(self, parents: List[Solution], offspring: List[Solution]) -> List[Solution]:
        """
        Choose the next population of a distributed run under the ``"global"`` model,
        on the driver, out of the parents that were sent to the workers and every
        candidate they returned. The default keeps the ``population_size`` best by
        fitness, without duplicates: a (μ+λ) selection. An algorithm whose population
        is not a set of competing individuals overrides it.

        :param parents: The population the workers received, before this iteration.
        :type parents: List[Solution]
        :param offspring: Everything the workers returned, all slices together.
        :type offspring: List[Solution]
        :return: The next population.
        :rtype: List[Solution]
        """
        unique = list({individual: None for individual in [*parents, *offspring]})
        return heapq.nsmallest(self.population_size, unique, key=Solution.get_fitness)

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
        reading it too early raises an error that says what happened.

        :return: The best solution so far.
        :rtype: Solution
        :raises RuntimeError: If read before the run has initialized it.
        """
        # P-11: reading it too early used to be an AttributeError on None.
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
        it stores on self stays in the worker and is lost; state that must
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
        between iterations. What it returns is what the next iteration gets.

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

        Abstract: every metaheuristic defines when it stops.

        :return: True if the algorithm should stop, False otherwise.
        :rtype: bool
        """
        # A-10: it used to return False, so a subclass that forgot to implement it
        # looped for ever with nothing to say why.

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
