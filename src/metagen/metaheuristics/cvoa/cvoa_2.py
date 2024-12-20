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
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager, Process, Queue
import numpy as np
import copy
from typing import Set, Optional, Callable, List

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.metaheuristics.base import Metaheuristic
import random
import math
from time import time
from datetime import timedelta


class SharedSolution:
    """Proxy class to handle Solution objects in shared memory"""
    def __init__(self, manager, lock, domain: Domain):
        self.variables = manager.dict()
        self.fitness = manager.Value('d', float('inf'))
        self.domain = domain
        self.lock = lock

    def update(self, solution: Solution):
        """Update from a Solution object"""
        self.variables.clear()
        variables = solution.get_variables()
        self.variables.update(variables)
        self.fitness.value = solution.fitness

    def to_solution(self) -> Optional[Solution]:
        """Convert back to a Solution object"""
        with self.lock:
            if self.domain is not None:
                solution = Solution(self.domain)
                solution.value = dict(self.variables)
                solution.fitness = self.fitness.value
                return solution
            return None

class SharedSet:
    def __init__(self, manager, lock):
        self._items = manager.list()
        self._lock = lock
    
    def add(self, item):
        with self._lock:
            if item not in self._items:
                self._items.append(item)

    def remove(self, item):
        with self._lock:
            if item in self._items:
                self._items.remove(item)

    def __contains__(self, item):
        with self._lock:
            return item in self._items 
    
    def get_items(self):
        with self._lock:
            return self._items
    
    def __len__(self):
        with self._lock:
            return len(self._items)
        
    def clear(self):
        with self._lock:
            while len(self._items) > 0:
                self._items.pop()

class CVOAState:
    """Manages shared state between processes"""
    def __init__(self, manager, domain: Domain):
        self.lock = manager.Lock()
        self.recovered = SharedSet(manager, self.lock)
        self.deaths = SharedSet(manager, self.lock)
        self.isolated = SharedSet(manager, self.lock)
        self.best_fitness = manager.Value('d', float('inf'))
        self.best_individual = SharedSolution(manager, self.lock, domain)

    def update_best_individual(self, solution: Solution):
        """Thread-safe update of best individual"""
        with self.lock:
            if solution.fitness < self.best_individual.fitness.value:
                self.best_individual.update(solution)
  
    
    
class CVOA(Metaheuristic):
    """ 
    
    This class implements the *CVOA* algorithm. It uses the :py:class:`~metagen.framework.Solution` class as an
    abstraction of an individual for the meta-heuristic.

    It solves an optimization problem defined by a :py:class:`~metagen.framework.Domain` object and an
    implementation of a fitness function.

    By instantiate :py:class:`~metagen.metaheuristics.CVOA` object, i.e. a strain, the configuration parameters must be provided.

    This class supports multiple strain execution by means of multy-threading. Each strain
    (:py:class:`~metagen.metaheuristics.CVOA` object) will execute its *CVOA* algorithm (:py:meth:`~metagen.metaheuristics.CVOA.cvoa`)
    in a thread and, finally, the best :py:class:`~metagen.framework.Solution` (i.e. the best fitness function
    is obtained).

    To launch a multi-strain execution, this module provides the :py:meth:`~metagen.metaheuristics.cvoa_launcher`
    method.

    :param domain: The domain of the problem
    :param fitness_function: The fitness function to optimize
    :param strain_id: The strain name
    :param pandemic_duration: The pandemic duration, defaults to 10
    :param spreading_rate: The spreading rate, defaults to 6
    :param min_super_spreading_rate: The minimum super spreading rate, defaults to 6
    :param max_super_spreading_rate: The maximum super spreading rate, defaults to 15
    :param social_distancing: The distancing stablished between the individuals, defaults to 10
    :param p_isolation: The probability of an individual being isolated, defaults to 0.7
    :param p_travel: The probability that an individual will travel, defaults to 0.1
    :param p_re_infection: The probability of an individual being re-infected, defaults to 0.0014
    :param p_superspreader: The probability of an individual being a super-spreader, defaults to 0.1
    :param p_die: The probability that an individual will die, defaults to 0.05
    :param verbose: The verbosity option, defaults to True
    :type domain: Domain
    :type fitness_function: Callable[[Solution], float]
    :type strain_id: str
    :type pandemic_duration: int
    :type spreading_rate: int
    :type min_super_spreading_rate: int
    :type max_super_spreading_rate: int
    :type social_distancing: int
    :type p_isolation: float
    :type p_travel: float
    :type p_re_infection: float
    :type p_superspreader: float
    :type p_die: float
    :type verbose: bool

    **Code example**

    .. code-block:: python

        from metagen.framework import Domain, Solution
        from metagen.metaheuristics import CVOA, cvoa_launcher
        domain = Domain()
        multithread = True

        domain.defineInteger(0, 1)

        fitness_function = ...

        if multithread: # For multiple thread excecution
            
            CVOA.initialize_pandemic(domain, fitness_function)
            strain1 = CVOA("Strain1", pandemic_duration=100)
            strain2 = CVOA("Strain2",  pandemic_duration=100)
            ...

            strains = [strain1, strain2, ...]
            optimal_solution = cvoa_launcher(strains)
        else: # For individual thread excecution

            CVOA.initialize_pandemic(domain, fitness_function)
            search = CVOA(pandemic_duration=100) 
            optimal_solution = search.run()            
    """
    def __init__(self, 
                 domain: Domain, 
                 fitness_function: Callable[[Solution], float],
                 strain_id: str = "Strain 1",
                 pandemic_duration: int = 10,
                 spreading_rate: int = 5,
                 min_super_spreading_rate: int = 6,
                 max_super_spreading_rate: int = 15,
                 social_distancing: int = 7,
                 p_isolation: float = 0.5,
                 p_travel: float = 0.1,
                 p_re_infection: float = 0.001,
                 p_superspreader: float = 0.1,
                 p_die: float = 0.05,
                 verbose: bool = True,
                 update_isolated: bool = False,
                 log_dir: str = "logs/CVOA",
                 shared_state: Optional[CVOAState] = None):
        
        super().__init__(domain, fitness_function, log_dir=log_dir)
        
        # Use provided shared state or create local state for single-process execution
        self.shared_state = shared_state or self._create_local_state(self.domain)
        
        # Algorithm parameters
        self.strain_id = strain_id
        self.pandemic_duration = pandemic_duration
        self.spreading_rate = spreading_rate
        self.min_super_spreading_rate = min_super_spreading_rate
        self.max_super_spreading_rate = max_super_spreading_rate
        self.social_distancing = social_distancing
        self.p_isolation = p_isolation
        self.p_travel = p_travel
        self.p_re_infection = p_re_infection
        self.p_superspreader = p_superspreader
        self.p_die = p_die
        self.verbose = verbose
        self.update_isolated = update_isolated

        # Local state
        self.solution_type = domain.get_connector().get_type(domain.get_core())
        self.current_solutions = set()
        self.super_spreader_strain = set()
        self.death_strain = set()
        self.best_solution = self.solution_type(domain, connector=domain.get_connector())
        self.time = 0
        self.epidemic = True

    @staticmethod
    def _create_local_state(domain: Domain):
        """Create state for single-process execution"""
        manager = Manager()
        return CVOAState(manager, domain)

    def initialize(self):
        """Initialize the strain with patient zero"""
        pz = self._infect_pz()
        if self.verbose:
            print(f"\nPatient Zero ({self.strain_id}): \n{str(pz)}")

        self.current_solutions.add(pz)
        self.best_solution = pz
        self.time = 0
        self.epidemic = True

        # Update shared state if better than current best
        with self.shared_state.lock:
            if pz.fitness < self.shared_state.best_fitness.value:
                self.shared_state.best_individual.update(pz)

                self.shared_state.best_fitness = pz.fitness

    def _infect_pz(self) -> Solution:
        """Create patient zero"""
        pz = self.solution_type(self.domain, connector=self.domain.get_connector())
        pz.initialize()
        pz.fitness = self.fitness_function(pz)
        return pz

    def _process_individual(self, individual: Solution) -> List[Solution]:
        """Process a single individual in parallel"""
        new_individuals = []
        
        # Determine number of infections
        if individual in self.super_spreader_strain:
            n_infected = np.random.randint(
                self.min_super_spreading_rate,
                self.max_super_spreading_rate + 1
            )
        else:
            n_infected = np.random.randint(0, self.spreading_rate + 1)

        # Determine travel distance
        travel_distance = np.random.randint(
            0, len(self.domain.get_core().variable_list())
        ) if random.random() < self.p_travel else 1

        # Generate new infections
        for _ in range(n_infected):
            if self.time < self.social_distancing or random.random() >= self.p_isolation:
                new_individual = copy.deepcopy(individual)
                new_individual.mutate(travel_distance)
                new_individual.fitness = self.fitness_function(new_individual)
                new_individuals.append(new_individual)
            elif self.update_isolated:
                with self.shared_state.lock:
                    self.shared_state.isolated.add(individual)

        return new_individuals

    def propagate_disease(self):
        """Main disease propagation logic using parallel processing"""
        new_infected_population = set()
        
        # Update strain sets
        self._update_strain_sets()
        new_infected_population.add(self.best_solution)

        for individual in self.current_solutions:
            new_infected_population.update(self._process_individual(individual))
        
        for new_individual in new_infected_population:
            self._update_population(new_individual, new_infected_population)

        # Update for next iteration
        self.current_solutions = new_infected_population

    def _update_strain_sets(self):
        """Update strain-specific sets and global shared state"""
        n_super_spreaders = math.ceil(self.p_superspreader * len(self.current_solutions))
        n_deaths = math.ceil(self.p_die * len(self.current_solutions))

        for individual in self.current_solutions:
            # Update super spreaders
            if n_super_spreaders > 0:
                self.super_spreader_strain.add(individual)
                n_super_spreaders -= 1

            # Update deaths
            if n_deaths > 0 and not individual in self.shared_state.deaths:
                self.death_strain.add(individual)
                self.shared_state.deaths.add(individual)
                n_deaths -= 1
            else:
                self.shared_state.recovered.add(individual)

            # Update best individual
            self.shared_state.update_best_individual(individual)


    def _update_population(self, individual: Solution, new_population: Set[Solution]):
        """Update population with thread-safe access to shared state"""
        if not individual in self.shared_state.deaths:
            if not individual in self.shared_state.deaths:
                new_population.add(individual)
            elif random.random() < self.p_re_infection:
                new_population.add(individual)
                self.shared_state.recovered.remove(individual)


    def iterate(self):
        """Single iteration of the algorithm"""
        self.propagate_disease()
        
        if not self.current_solutions:
            self.epidemic = False
            if self.verbose:
                print(f"No new infected individuals in {self.strain_id}")
        
        self.time += 1

    def stopping_criterion(self) -> bool:
        """Check if the algorithm should stop"""
        return not self.epidemic or self.time > self.pandemic_duration

    def post_execution(self):
        super().post_execution()
        """Cleanup after execution"""
        if self.verbose:
            print(f"\n\n{self.strain_id} converged after {self.time} iterations.")
            print(f"Best individual: {self.best_solution}")

def cvoa_launcher(strains: List[CVOA], verbose: bool = True) -> Solution:
    """Launch multiple CVOA instances using multiprocessing"""
    
    manager = Manager()
    shared_state = CVOAState(manager, strains[0].domain)
    processes = []
    result_queue = manager.Queue()  
    
    try:
        t1 = time()
        
        # Initialize strains with shared state
        for strain in strains:
            strain.shared_state = shared_state
            p = Process(target=run_strain, 
                       args=(strain, result_queue))
            processes.append(p)
            p.start()

        # Wait for completion
        for p in processes:
            p.join()

        t2 = time()
        execution_time = timedelta(seconds=t2-t1)

        # Get best solution before cleanup
        best_solution = shared_state.best_individual.to_solution()

        if verbose:
            print("\n********** Results **********")
            print(f"Total execution time: {execution_time}")
            if best_solution:
                print(f"Best fitness: {best_solution.fitness}")
                print(f"Best solution: {best_solution}")
            print(f"Recovered: {len(shared_state.recovered)}")
            print(f"Deaths: {len(shared_state.deaths)}")
            print(f"Isolated: {len(shared_state.isolated)}")

        return best_solution
    
    finally:
        # Cleanup processes
        for p in processes:
            if p.is_alive():
                p.terminate()
        
        # Clear shared resources
        shared_state.recovered.clear()
        shared_state.deaths.clear()
        shared_state.isolated.clear()
        
        # Shutdown manager
        manager.shutdown()


def run_strain(strain: CVOA, result_queue: Queue):
    """Helper function to run a strain and put result in queue"""
    try:
        result = strain.run()
        result_queue.put(result)
    except Exception as e:
        print(f"Error in strain {strain.strain_id}: {e}")
        result_queue.put(None)