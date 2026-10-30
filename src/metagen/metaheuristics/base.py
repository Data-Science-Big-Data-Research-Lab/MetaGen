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
import json
import math
import numbers
import os
import pickle
import statistics
import time
from abc import ABC, abstractmethod
from importlib import metadata

from .import_helper import is_package_installed
from typing import Any, Dict, List, Mapping, Sequence, Tuple, Optional, Callable, cast
from metagen.framework import Domain, Solution
from metagen.framework import rng as rng_state
from metagen.framework.rng import get_rng, set_seed, spawn_seed
from copy import deepcopy

from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.racing import Racing
from metagen.metaheuristics.tools import CountingFitness, add_calls, random_exploration, solution_class

IS_RAY_INSTALLED = is_package_installed("ray")

if is_package_installed("tensorboard"):
    from metagen.logging.tensorboard_logger import TensorBoardLogger

if IS_RAY_INSTALLED:
    import ray
    from .distributed_tools import assign_load_equally, call_distributed, distributed_random_exploration


#: What a checkpoint does not keep: the fitness function, which may be a lambda or a
#: nested function and cannot be pickled, the TensorBoard writer, and where and how
#: often to save, which the resumed run is given again.
_NOT_CHECKPOINTED = frozenset({"fitness_function", "logger", "checkpoint", "checkpoint_every",
                               "_stop_requested"})


def _package_version() -> str:
    try:
        return metadata.version("pymetagen-datalabupo")
    except metadata.PackageNotFoundError:
        return "unknown"


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
    :param checkpoint: File the run saves its state to every ``checkpoint_every``
        iterations, and continues from if it exists when ``run()`` starts: a run cut
        short by a power failure or a job scheduler goes on where it was saved, with
        the same result it would have reached uninterrupted. The file is removed when
        the run ends. None, the default, saves nothing. See :py:meth:`resume` and
        :py:meth:`request_stop`.
    :type checkpoint: str or None, optional
    :param checkpoint_every: Iterations between two saves (default is 1).
    :type checkpoint_every: int, optional
    :param history: File the run writes its history to, one JSON line per iteration,
        which ``pandas.read_json(history, lines=True)`` reads as a table. None, the
        default, writes nothing; the records are in ``history`` either way.
    :type history: str or None, optional
    :param max_evaluations: Stop once the run has evaluated the fitness at least this many
        times, warmup included. None, the default, sets no limit.
    :type max_evaluations: int or None, optional
    :param timeout: Stop once the run has lasted at least this many seconds. None, the
        default, sets no limit.
    :type timeout: float or None, optional
    :param initial_solutions: Solutions to start from, such as a configuration known to
        work: each a mapping from variable names to values, with any variable left out
        drawn at random. They take the place of as many solutions of the initial
        population, so the cost of the run does not change, and count as any other: the
        best of the run may be one of them. At most ``population_size`` of them. None, the
        default, starts from random solutions only.
    :type initial_solutions: Sequence[Mapping[str, Any]] or None, optional
    :param racing: Stop evaluating a candidate as soon as it is significantly worse than
        the population, for a fitness function that yields its steps one at a time; see
        :py:class:`~metagen.metaheuristics.racing.Racing`. None, the default, evaluates
        every candidate whole. With it, ``max_evaluations`` counts the steps taken: a
        candidate stopped after 3 of 10 spends 0.3 of an evaluation.
    :type racing: Racing or None, optional

    The run stops at whichever comes first: the algorithm's own stopping criterion,
    ``max_evaluations``, ``timeout`` or :py:meth:`request_stop`. The limits are checked
    after each round of the warmup, after the initialization and at the end of every
    iteration, never in the middle of one, so a run may go past them by up to one round
    of the warmup and the initial population, which is always evaluated whole, or by one
    iteration, and past ``timeout`` by the time those evaluations take; ``stop_reason``
    says which one stopped it, and ``evaluations`` and ``seconds`` what it spent. A run
    resumed from a checkpoint carries on with what it had spent.

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
    :ivar history: One record per iteration: ``iteration``; ``evaluations``, counted from
        the start of the run, warmup included, those of the workers too in a distributed
        run; ``seconds`` since the start; ``best``, the
        best fitness so far; the ``iteration_best``, ``mean``, ``std`` and ``worst``
        fitness of the population and its ``population_size``; and ``best_solution``,
        the values of the best solution so far.
    :vartype history: List[dict]
    :ivar stop_reason: What stopped the last run: ``"criterion"``, the algorithm's own,
        ``"max_evaluations"``, ``"timeout"`` or ``"request_stop"``; None before any run.
    :vartype stop_reason: Optional[str]
    """

    # minimum_slice exists since F-46: islands of one individual crashed GA and Memetic.
    # Worker tasks are seeded from the driver since A-06.
    minimum_slice: int = 1

    #: Whether every solution the warmup evaluates joins the population ``initialize``
    #: builds, for an algorithm whose population is its model; otherwise the warmup only
    #: hands on the best solution it found.
    keeps_warmup: bool = False

    def __init__(self, domain: Domain, fitness_function: Callable[[Solution], float], population_size=20,
                 warmup_iterations: int = 0, distributed=False,
                 log_dir: Optional[str] = None, seed: Optional[int] = None,
                 distribution_model: str = "global", checkpoint: Optional[str] = None,
                 checkpoint_every: int = 1, history: Optional[str] = None,
                 max_evaluations: Optional[int] = None, timeout: Optional[float] = None,
                 initial_solutions: Optional[Sequence[Mapping[str, Any]]] = None,
                 racing: Optional[Racing] = None) -> None:
        super().__init__()

        if max_evaluations is not None and (isinstance(max_evaluations, bool)
                                            or not isinstance(max_evaluations, numbers.Integral)
                                            or max_evaluations < 1):
            raise ValueError(f"max_evaluations must be a positive integer or None, not {max_evaluations!r}")
        if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, numbers.Real)
                                    or not math.isfinite(timeout) or timeout <= 0):
            raise ValueError(f"timeout must be a positive number of seconds or None, not {timeout!r}")
        self.max_evaluations: Optional[int] = None
        if max_evaluations is not None:
            self.max_evaluations = int(cast(Any, max_evaluations))
        self.timeout: Optional[float] = None
        if timeout is not None:
            self.timeout = float(cast(Any, timeout))
        self.stop_reason: Optional[str] = None
        if racing is not None and not isinstance(racing, Racing):
            raise ValueError(f"racing must be a Racing or None, not {racing!r}")
        self.racing = racing
        # The steps a whole evaluation takes, for a fitness function that yields them, and
        # the steps taken so far: what max_evaluations counts then.
        self._step_count: Optional[int] = None
        self._steps = 0
        # Checked here, against the domain, without drawing anything: the solutions are
        # built in run(), once the seed is set, so that the variables left out are drawn
        # from the seeded generators.
        self.initial_solutions: List[Dict[str, Any]] = [dict(values) for values in initial_solutions or []]
        if len(self.initial_solutions) > population_size:
            raise ValueError(f"{type(self).__name__} takes at most population_size={population_size} initial "
                             f"solutions, not {len(self.initial_solutions)}.")
        core = domain.get_core()
        for index, values in enumerate(self.initial_solutions):
            for name, value in values.items():
                if not core.is_variable(name):
                    raise ValueError(f"Initial solution {index}: {name!r} is not a variable of the domain.")
                if not core.check(name, value):
                    raise ValueError(f"Initial solution {index}: {value!r} is not a valid value of {name!r}.")
        # The iterations the algorithm's own criterion allows, which _iterations() sets:
        # None is no limit, for a run bounded by its budget alone.
        self._iteration_limit: Optional[int] = None

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
        self.log_dir = log_dir
        self.logger = (TensorBoardLogger(log_dir=log_dir)
                       if log_dir is not None and is_package_installed("tensorboard")
                       else None)
        if checkpoint_every < 1:
            raise ValueError(f"checkpoint_every must be at least 1, not {checkpoint_every}")
        self.checkpoint = checkpoint
        self.checkpoint_every = checkpoint_every
        self._stop_requested = False
        self.history_file = history
        self.history: List[Dict[str, Any]] = []
        self._evaluations = 0
        self._seconds = 0.0

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
            distribution = assign_load_equally(self.population_size - len(self.initial_solutions),
                                               self.minimum_slice)
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

        answers = ray.get(futures)
        # Each worker evaluates on a copy of the fitness function and says how many.
        add_calls(self.fitness_function, sum(calls for _, calls in answers))
        remote_results = [result for result, _ in answers]
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
        given = self._initial_population()
        drawn = self.population_size - len(given)
        population: List[Solution] = []
        best_individual: Optional[Solution] = None
        if drawn > 0:
            if self.distributed:
                if not IS_RAY_INSTALLED:
                    raise ImportError("Ray must be installed to use distributed initialization")
                population, best_individual = self._launch_distributed_method(self.initialize)
            else:
                population, best_individual = self.initialize(drawn)
        # What initialize returns as its best is kept (HillClimbing returns its starting
        # point), and only an initial solution better than it takes its place.
        for solution in given:
            if best_individual is None or solution.get_fitness() < best_individual.get_fitness():
                best_individual = solution
        assert best_individual is not None
        population = given + population

        # F-53: the warmup kept one solution per round and this replaced them all, so a
        # model built on the population never saw what the warmup had evaluated.
        if self.keeps_warmup:
            population = self.current_solutions + population
        self.current_solutions = population

        # Merged rather than assigned: _warmup() runs first and may already hold a
        # better solution, which a plain assignment would throw away along with
        # every evaluation that produced it (F-03).
        if self.best_solution is None or best_individual.get_fitness() < self.best_solution.get_fitness():
            self.best_solution = best_individual

        return population, best_individual

    def _initial_population(self) -> List[Solution]:
        """The initial solutions given to the constructor, built and evaluated."""
        given = []
        for values in self.initial_solutions:
            solution = solution_class(self.domain)(self.domain, connector=self.domain.get_connector())
            for name, value in values.items():
                solution.set(name, value)
            solution.evaluate(self.fitness_function)
            given.append(solution)
        return given

    def _warmup(self, limit_reached: Optional[Callable[[], Optional[str]]] = None) -> None:
        """
        Executes the warmup phase before the main optimization loop.

        Generates `warmup_iterations` random solutions and updates the best solution found.
        This step ensures a good initial exploration of the search space before starting
        the main optimization process.

        :param limit_reached: Called after each round; the warmup ends early once it returns
            a reason, so that a budget smaller than the warmup is not exceeded by all of it.
        :type limit_reached: Callable[[], Optional[str]], optional
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
                    explored, best_candidate = distributed_random_exploration(self.domain, self.fitness_function,
                                                                       self.population_size)
                else:
                    metagen_logger.debug(
                        f'[WARMUP {warmup_step + 1}/{self.warmup_iterations}] Warmup step.'
                    )
                    explored, best_candidate = random_exploration(self.domain, self.fitness_function, self.population_size)

                # Every solution for an algorithm that keeps the warmup, the best one otherwise.
                if self.keeps_warmup:
                    self.current_solutions.extend(explored)
                else:
                    self.current_solutions.append(deepcopy(best_candidate))

                # Update the global best solution
                if self.best_solution is None or best_candidate.get_fitness() < self.best_solution.get_fitness():
                    self.best_solution = deepcopy(best_candidate)

                if limit_reached is not None and limit_reached() is not None:
                    break


            metagen_logger.info(f"Warmup phase completed. Proceeding to optimization.")

    def _iterate(self) -> Tuple[List[Solution], Solution]:
        """
        Private function to execute one iteration of the metaheuristic.

        :return: A tuple containing the population and the best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        if self.racing is not None and isinstance(self.fitness_function, CountingFitness):
            # The candidates of this iteration race against the population it starts from.
            step_count = self.fitness_function.step_count
            self.fitness_function.references = [
                getattr(solution, "step_values") for solution in self.current_solutions
                if not getattr(solution, "raced_out", False)
                and len(getattr(solution, "step_values", ())) == step_count]
        if self.distributed:
            if not IS_RAY_INSTALLED:
                    raise ImportError("Ray must be installed to use distributed initialization")
            population, best_individual = self._launch_distributed_method(self.iterate)
        else:
            population, best_individual = self.iterate(self.current_solutions)

        self.current_solutions = population

        # A candidate stopped by the race has an estimated fitness: never the best of the run.
        if getattr(best_individual, "raced_out", False):
            whole = [solution for solution in population if not getattr(solution, "raced_out", False)]
            best_individual = min(whole, key=Solution.get_fitness) if whole else self._best_so_far()

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

        With a ``checkpoint`` file that exists, the run continues from the state saved
        in it instead of starting over.

        :return: The best solution found, or the best found so far when
            :py:meth:`request_stop` stopped the run.
        :rtype: Solution
        """
        self.stop_reason = None
        resuming = self.checkpoint is not None and os.path.exists(self.checkpoint)
        if resuming:
            self._restore(self._read_checkpoint(cast(str, self.checkpoint)))
        # Seeded here rather than in __init__ so that every run() starts from
        # the same state: building two metaheuristics and running them later
        # would otherwise make the second one depend on the first.
        elif self.seed is not None:
            set_seed(self.seed)
        self._stop_requested = False
        if resuming:
            self._trim_history_file()
        else:
            self.history = []
            self._evaluations = 0
            self._steps = 0
            self._seconds = 0.0
            if self.history_file is not None and os.path.exists(self.history_file):
                os.remove(self.history_file)
        # Counted on the driver: the history's evaluations, from where a resumed run
        # left them.
        counted = CountingFitness(self.fitness_function, racing=self.racing, step_count=self._step_count)
        self.fitness_function = counted
        evaluations_before, seconds_before, started = self._evaluations, self._seconds, time.perf_counter()
        steps_before = self._steps

        def account() -> Optional[str]:
            """Bring what the run has spent up to date, and say which limit it reached."""
            self._evaluations = evaluations_before + counted.calls
            self._steps, self._step_count = steps_before + counted.steps, counted.step_count
            self._seconds = seconds_before + time.perf_counter() - started
            return self._limit_reached()

        # Remembered so that only the run() that started Ray stops it. Shutting it
        # down unconditionally took the runtime away from a cluster the user had
        # connected to, or from the other metaheuristics in a comparison (F-21).
        started_ray = False
        if self.distributed and IS_RAY_INSTALLED and not ray.is_initialized():
            ray.init()
            started_ray = True

        try:
            if not resuming:
                self.pre_execution()

                # A budget is also checked between the rounds of the warmup, which can
                # cost more than a small budget on its own (TPE's defaults are 200
                # evaluations); the initial population is always evaluated whole.
                self._warmup(account)

                self._initialize()

                self.current_iteration = 0
                account()

            while True:
                # Checked between iterations only, where the state is consistent: the
                # same point the checkpoint is saved at, so a resumed run stops where
                # an uninterrupted one would.
                reason = "criterion" if self.stopping_criterion() else self._limit_reached()
                if reason is not None:
                    self.stop_reason = reason
                    break
                self.pre_iteration()

                self._iterate()

                self.post_iteration()

                account()
                self._record_history()

                self.current_iteration += 1

                # Saved here, on the driver, once the iteration is complete: the only
                # point at which the state is consistent. A cut during an iteration
                # loses that iteration and never corrupts the file.
                if self.checkpoint is not None and (
                        self._stop_requested or self.current_iteration % self.checkpoint_every == 0):
                    self._write_checkpoint()
                if self._stop_requested:
                    self.stop_reason = "request_stop"
                    if self.logger:
                        self.logger.writer.flush()
                    return deepcopy(self._best_so_far())

            self.post_execution()
            if self.checkpoint is not None and os.path.exists(self.checkpoint):
                os.remove(self.checkpoint)
        finally:
            self.fitness_function = counted.function
            # Also on the way out of an exception: a runtime this run() started must
            # not outlive it, or the workers and their memory stay alive until the
            # interpreter exits (F-44).
            if started_ray and ray.is_initialized():
                ray.shutdown()

        return deepcopy(self._best_so_far())

    def _iterations(self, max_iterations: Optional[int], default: int,
                    horizon: Optional[Callable[[int], int]] = None) -> Optional[int]:
        """
        The ``max_iterations`` of an algorithm, and the limit of iterations its criterion
        enforces, kept in ``_iteration_limit``. Given, it is both. Not given, without a
        budget it is ``default``; with one, there is no limit of iterations. An algorithm
        that also plans its search over ``max_iterations`` (a cooling or a gamma schedule)
        passes ``horizon``, which turns ``max_evaluations`` into the iterations it buys:
        that is its ``max_iterations`` then, and only the budget stops the run. With a
        ``timeout`` alone it keeps ``default``, as limit and as horizon.

        :param max_iterations: The iterations the user gave, or None.
        :type max_iterations: int or None
        :param default: The iterations without a budget.
        :type default: int
        :param horizon: The iterations ``max_evaluations`` buys, for an algorithm that plans
            over its iterations.
        :type horizon: Callable[[int], int], optional
        :return: The ``max_iterations`` to keep: the limit, the horizon, or None.
        :rtype: int or None
        """
        if max_iterations is not None or (self.max_evaluations is None and self.timeout is None):
            chosen = default if max_iterations is None else max_iterations
            self._iteration_limit = chosen
            return chosen
        self._iteration_limit = None
        if horizon is None:
            return None
        if self.max_evaluations is None:
            self._iteration_limit = default
            return default
        return max(1, horizon(self.max_evaluations))

    def _iterations_done(self) -> bool:
        """Whether the run has made the iterations its criterion allows."""
        return self._iteration_limit is not None and self.current_iteration >= self._iteration_limit

    def _limit_reached(self) -> Optional[str]:
        """The budget the run has spent, ``"max_evaluations"`` or ``"timeout"``, or None."""
        if self.max_evaluations is not None and self._spent() >= self.max_evaluations:
            return "max_evaluations"
        if self.timeout is not None and self._seconds >= self.timeout:
            return "timeout"
        return None

    def _spent(self) -> float:
        """The evaluations a budget counts: whole ones, or steps over the steps of one for a
        fitness function that yields them, so that a candidate stopped early spends less."""
        if self._step_count:
            return self._steps / self._step_count
        return self._evaluations

    @property
    def evaluations(self) -> int:
        """
        The evaluations of the fitness the last run made, warmup included.

        :return: The count.
        :rtype: int
        """
        return self._evaluations

    @property
    def seconds(self) -> float:
        """
        The seconds the last run lasted.

        :return: The seconds.
        :rtype: float
        """
        return self._seconds

    def _record_history(self) -> None:
        """
        Add the record of the iteration just completed to ``history``, and to the
        ``history`` file if the run has one.
        """
        fitnesses = [solution.get_fitness() for solution in self.current_solutions]
        finite = [value for value in fitnesses if math.isfinite(value)]
        best = self._best_so_far()
        record = {
            "iteration": self.current_iteration,
            "evaluations": self._evaluations,
            **({"steps": self._steps} if self._step_count else {}),
            "seconds": self._seconds,
            "best": best.get_fitness(),
            "iteration_best": min(finite) if finite else None,
            "mean": statistics.fmean(finite) if finite else None,
            "std": statistics.pstdev(finite) if finite else None,
            "worst": max(finite) if finite else None,
            "population_size": len(self.current_solutions),
            "best_solution": {name: best[name] for name in best},
        }
        self.history.append(record)
        if self.history_file is not None:
            directory = os.path.dirname(os.path.abspath(self.history_file))
            os.makedirs(directory, exist_ok=True)
            with open(self.history_file, "a") as handle:
                handle.write(json.dumps(record) + "\n")

    def _trim_history_file(self) -> None:
        """
        On resuming, drop the lines a run wrote after its last checkpoint: they are
        written again as the run repeats those iterations.
        """
        if self.history_file is None or not os.path.exists(self.history_file):
            return
        with open(self.history_file) as handle:
            kept = [line for line in handle
                    if line.strip() and json.loads(line)["iteration"] < self.current_iteration]
        with open(self.history_file, "w") as handle:
            handle.writelines(kept)

    def request_stop(self) -> None:
        """
        Ask a running ``run()`` to stop after the iteration in progress. It saves the
        state if the run has a ``checkpoint`` file, and returns the best solution found
        so far; calling ``run()`` again, or :py:meth:`resume` in another process,
        continues from there. It only sets a flag, so it can be called from a callback,
        another thread or a signal handler, for instance the signal a job scheduler
        sends before stopping a job:

        .. code-block:: python

            import signal

            signal.signal(signal.SIGTERM, lambda signum, frame: algorithm.request_stop())

        :return: Nothing.
        :rtype: None
        """
        self._stop_requested = True

    @classmethod
    def resume(cls, checkpoint: str, fitness_function: Callable[[Solution], float]) -> "Metaheuristic":
        """
        Rebuild a metaheuristic from its checkpoint file, to continue it with ``run()``,
        for instance in a new process after the one that started it was stopped. The
        fitness function is not saved in the file and is given again here.

        .. code-block:: python

            algorithm = GA.resume("runs/ga.ckpt", fitness)
            best = algorithm.run()

        The file is a pickle: load only checkpoints you wrote or trust.

        :param checkpoint: The checkpoint file.
        :type checkpoint: str
        :param fitness_function: The fitness function of the run.
        :type fitness_function: Callable[[Solution], float]
        :return: The metaheuristic, ready to continue.
        :rtype: Metaheuristic
        :raises ValueError: if the file belongs to another class or version of the package.
        """
        state = cls._read_checkpoint(checkpoint)
        algorithm_class = state["class"]
        if not issubclass(algorithm_class, cls):
            raise ValueError(f"The checkpoint {checkpoint} is of {algorithm_class.__name__}, "
                             f"not of {cls.__name__}.")
        algorithm = algorithm_class.__new__(algorithm_class)
        algorithm.__dict__.update(state["algorithm"])
        algorithm.fitness_function = fitness_function
        algorithm.checkpoint = checkpoint
        algorithm.checkpoint_every = state["checkpoint_every"]
        algorithm._stop_requested = False
        algorithm.logger = None
        return algorithm

    def _checkpoint_state(self) -> Dict[str, Any]:
        """
        What a checkpoint holds: the algorithm's attributes but the ones in
        ``_NOT_CHECKPOINTED``, the state of both generators, the class, the version of
        the package and the TensorBoard run, so that its curves continue in the same
        directory. A subclass whose state is not all in its attributes extends it.
        """
        return {
            "version": _package_version(),
            "class": type(self),
            "algorithm": {name: value for name, value in self.__dict__.items()
                          if name not in _NOT_CHECKPOINTED},
            "rng": rng_state.get_state(),
            "checkpoint_every": self.checkpoint_every,
            "tensorboard_run": self.logger.run_id if self.logger else None,
        }

    def _restore(self, state: Dict[str, Any]) -> None:
        """
        Put the algorithm back in the state of a checkpoint: the inverse of
        :py:meth:`_checkpoint_state`.
        """
        if state["class"] is not type(self):
            raise ValueError(f"The checkpoint {self.checkpoint} is of {state['class'].__name__}, "
                             f"not of {type(self).__name__}.")
        self.__dict__.update(state["algorithm"])
        rng_state.set_state(state["rng"])
        if self.log_dir is not None and is_package_installed("tensorboard"):
            if self.logger:
                self.logger.close()
            self.logger = TensorBoardLogger(log_dir=self.log_dir, run_id=state["tensorboard_run"])

    def _write_checkpoint(self) -> None:
        """
        Write the checkpoint atomically: to a temporary file in the same directory,
        synced to disk, then renamed over the previous one, so that a cut while
        writing leaves the previous checkpoint whole.
        """
        path = cast(str, self.checkpoint)
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        temporary = path + ".tmp"
        with open(temporary, "wb") as handle:
            pickle.dump(self._checkpoint_state(), handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)

    @staticmethod
    def _read_checkpoint(path: str) -> Dict[str, Any]:
        with open(path, "rb") as handle:
            state: Dict[str, Any] = pickle.load(handle)
        if state.get("version") != _package_version():
            raise ValueError(f"The checkpoint {path} was written by version {state.get('version')} "
                             f"of the package and this is version {_package_version()}.")
        return state
