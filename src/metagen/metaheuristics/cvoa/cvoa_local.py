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
import math
import threading
from typing import Callable, List, Optional, Tuple

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.logging.metagen_logger import DETAILED_INFO, MetaGenLogger, get_remote_metagen_logger, metagen_logger

from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.cvoa.common_tools import (IndividualState, PandemicState, SolutionSet, StrainProperties,
                                                     compute_n_infected_travel_distance, infect)
from metagen.framework.rng import get_rng


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

    :param strain_id: The strain name
    :param pandemic_duration: The pandemic duration, defaults to 30
    :param spreading_rate: The spreading rate, defaults to 5
    :param min_super_spreading_rate: The minimum super spreading rate, defaults to 6
    :param max_super_spreading_rate: The maximum super spreading rate, defaults to 15
    :param social_distancing: The iteration from which social distancing applies, defaults to 7
    :param p_isolation: The probability of an individual being isolated, defaults to 0.7
    :param p_travel: The probability that an individual will travel, defaults to 0.1
    :param p_re_infection: The probability of an individual being re-infected, defaults to 0.02
    :param p_superspreader: The probability of an individual being a super-spreader, defaults to 0.1
    :param p_die: The probability that an individual will die, defaults to 0.05
    :param verbose: The verbosity option, defaults to True
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
        from metagen.metaheuristics import cvoa_launcher
        from metagen.metaheuristics.cvoa.common_tools import StrainProperties

        domain = Domain()
        domain.define_real("x", -5.0, 5.0)

        def fitness_function(solution: Solution) -> float:
            return solution["x"] ** 2

        # One strain per concurrent thread, each with its own properties.
        strains = [
            StrainProperties(strain_id="Strain1", pandemic_duration=10),
            StrainProperties(strain_id="Strain2", pandemic_duration=10),
        ]
        optimal_solution = cvoa_launcher(strains, domain, fitness_function)
    """

    def __init__(self, global_state: PandemicState, domain: Domain, fitness_function: Callable[[Solution], float],
                 strain_properties: StrainProperties = StrainProperties(), update_isolated: bool = False,
                 log_dir: Optional[str] = None, distributed: bool = False, detailed_info: bool = False):
        """
        :param global_state: The state every strain of the pandemic shares. With
            ``distributed=True`` it may be the handle of the RemotePandemicState actor,
            which is wrapped here.
        :param distributed: Whether the contagion step runs on Ray, one task per carrier
            (default is False: it runs in this thread). This is CVOA's own switch and is
            not handed to Metaheuristic, whose distributed mode splits a population into
            one slice per CPU and is not what a strain does.
        :param detailed_info: Whether the remote logger of a Ray strain reports at the
            DETAILED_INFO level (default is False). Ignored in thread mode, where the
            package logger decides.
        """
        # 1. Initialize the base class. Its own distributed mode stays off: see above.
        super().__init__(domain, fitness_function, log_dir=log_dir)

        # 2. The pandemic global state and the strain properties. On Ray the strain
        # holds a proxy of the actor with the same methods as the local state (A-09).
        self.spread_on_ray: bool = distributed
        if distributed:
            from metagen.metaheuristics.cvoa.distributed_tools import RemotePandemicStateProxy
            if not isinstance(global_state, RemotePandemicStateProxy):
                global_state = RemotePandemicStateProxy(global_state)
            self._logger: MetaGenLogger = (get_remote_metagen_logger(DETAILED_INFO) if detailed_info
                                           else get_remote_metagen_logger())
        else:
            self._logger = metagen_logger
        self.global_state: PandemicState = global_state
        self.strain_properties: StrainProperties = strain_properties

        # 3. Auxiliary strain control variables. update_isolated is kept for
        # compatibility and has no effect since F-45: every isolated individual counts.
        self.update_isolated: bool = update_isolated
        self.solution_type: type[Solution] = solution_class(self.domain)

        # 4. Strain control flow variables.

        # 4.1. Logical condition to ctrl the epidemic (main iteration).
        # If True, the iteration continues. When there are no infected individuals, the epidemic finishes.
        self.epidemic: bool = True

        # 4.2. The current iteration. The iteration counter will be initially set to 0.
        self.time: int = 0

        # 4.3. The best solution found by the strain.
        self.best_strain_solution: Solution | None = None
        self.best_strain_solution_found: bool = False

        # Iterations gone by without a new global best. The flag above used to be
        # the stopping condition on its own and was never cleared (F-23).
        self.iterations_without_improvement: int = 0

        # 5. Main strain sets: infected, superspreaders and deaths. There used to be a
        # fourth, infected_superspreaders, that only ever received the patient zero and
        # was never read: the superspreaders' role is played by the superspreaders set.
        self.infected: SolutionSet = SolutionSet()
        self.superspreaders: SolutionSet = SolutionSet()
        self.dead: SolutionSet = SolutionSet()

    def _log(self, message: str) -> None:
        """
        Report at the DETAILED_INFO level, prefixed with the strain and, in thread
        mode, the thread. The two former twins differed only in which logger and
        which prefix (A-09).
        """
        if self.spread_on_ray:
            self._logger.detailed_info(f"[{self.strain_properties.strain_id}] {message}")
        else:
            self._logger.detailed_info(f"[{self.strain_properties.strain_id}, {threading.get_ident()}] {message}")

    def _best_of_strain(self) -> Solution:
        """
        The best solution the strain has found, once initialized.

        ``best_strain_solution`` is None until ``initialize()`` names the patient zero,
        which is before anything reads it; this narrows it there, the way the base
        class does with ``_best_so_far()`` (P-11).

        :return: The best solution of the strain.
        :rtype: Solution
        :raises RuntimeError: If read before the strain has a patient zero.
        """
        if self.best_strain_solution is None:
            raise RuntimeError("best_strain_solution is not available yet: initialize() has not run")
        return self.best_strain_solution

    def initialize(self, num_solutions=10) -> Tuple[List[Solution], Solution]:

        # 1. Yield the patient zero (pz).
        pz: Solution = self.solution_type(self.domain, connector=self.domain.get_connector())
        pz.evaluate(self.fitness_function)
        self._log(f"Patient zero: {pz}")

        # 2. Add the patient zero to the strain-specific infected set.
        self.infected.add(pz)

        # 3. The best strain-specific individual will initially be the patient zero.
        self.best_strain_solution = pz

        return list(self.infected), self._best_of_strain()

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:

        # 1. Spreading the disease.

        # 1.1. Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        self.update_pandemic_global_state()

        # 1.2. Every infected individual infects new ones, in this thread or on Ray.
        new_infected_population: SolutionSet = self.spread()
        self.after_spreading()

        # 1.3. Then, add the best individual of the strain to the next population.
        new_infected_population.add(self._best_of_strain())

        # 1.4. Update the infected strain population for the next iteration
        self.infected.clear()
        self.infected.update(new_infected_population)

        # 2. Stop if no new infected individuals.
        if not self.infected:
            self.epidemic = False
            self._log(f"No new infected individuals at {self.time}")

        self._log(f"Iteration #{self.time} - {self.r0_report(len(new_infected_population))}"
                  f" - Best strain individual: {self.best_strain_solution} , "
                  f"Best global individual: {self.global_state.get_best_individual()} ")

        # 3. Update the elapsed pandemic time.
        # The improvement flag becomes a stagnation count here, and is cleared. Left
        # standing, it ended the strain on the iteration after its first improvement:
        # the strain stopped because it was working (F-23).
        if self.best_strain_solution_found:
            self.iterations_without_improvement = 0
            self.best_strain_solution_found = False
        else:
            self.iterations_without_improvement += 1

        self.time += 1

        return list(self.infected), self._best_of_strain()

    def after_spreading(self) -> None:
        """
        What happens to the carriers once they have infected. Nothing here: MetaGen's
        CVOA settles their fate in update_pandemic_global_state, before they spread.
        The paper's variant recovers them at this point instead.
        """

    def spread(self) -> SolutionSet:
        """
        The contagion step of one iteration: the population every current carrier
        infects, before the strain's best is added.

        In thread mode it runs infect_from_carrier for each carrier here; on Ray,
        spread_on_ray runs the same function in one task per carrier. There used to be
        three copies of this step, one per way of dispatching it (A-09).

        :return: The newly infected population.
        :rtype: SolutionSet
        """
        if self.spread_on_ray:
            from metagen.metaheuristics.cvoa.distributed_tools import spread_on_ray
            return spread_on_ray(type(self), self.global_state, self.domain, self.fitness_function,
                                 self.strain_properties, self.infected, self.superspreaders, self.time)

        new_infected_population: SolutionSet = SolutionSet()
        for carrier in self.infected:
            new_infected_population.update(
                type(self).infect_from_carrier(self.global_state, self.domain, self.fitness_function,
                                               self.strain_properties, carrier, self.superspreaders, self.time))
        return new_infected_population

    @classmethod
    def infect_from_carrier(cls, state: PandemicState, domain: Domain, fitness_function: Callable[[Solution], float],
                            strain_properties: StrainProperties, carrier: Solution, superspreaders: SolutionSet,
                            time: int) -> SolutionSet:
        """
        Everything one carrier does in one iteration: draw how many it infects and how
        far, then infect. A function of its arguments alone, so that a Ray task can run
        it on a copy of the class (F-40); the class is what carries the variant, since
        a subclass may change what isolation or admission mean.

        :return: The individuals this carrier infected that enter the next population.
        :rtype: SolutionSet
        """
        n_infected, travel_distance = compute_n_infected_travel_distance(domain, strain_properties, carrier,
                                                                         superspreaders)
        return cls.infect_individuals_from(state, fitness_function, strain_properties, carrier, travel_distance,
                                           n_infected, time)

    @classmethod
    def infect_individuals_from(cls, state: PandemicState, fitness_function: Callable[[Solution], float],
                                strain_properties: StrainProperties, carrier: Solution, travel_distance: int,
                                n_infected: int, time: int) -> SolutionSet:
        """
        Infect ``n_infected`` individuals from a carrier. Before social distancing they
        are placed at the travel distance; from then on at distance one, and each is
        isolated with probability p_isolation.
        """
        infected_population: SolutionSet = SolutionSet()

        for _ in range(0, n_infected):

            # If the current disease time is not affected by the social_distancing policy, the current
            # individual infects another with a travel distance (using infect), and it is added
            # to the newly infected population.
            if time < strain_properties.social_distancing:
                new_infected_individual = infect(carrier, fitness_function, travel_distance)
                cls.admit(state, strain_properties, infected_population, new_infected_individual)

            # After social_distancing iterations (when the social_distancing policy is applied),
            # the current individual infects another with a travel distance of one (using infect) then,
            # the newly infected individual is isolated with probability p_isolation. The
            # comparison used to run the other way, infecting when the draw fell below
            # p_isolation, so the parameter meant the probability of NOT isolating: the
            # published pseudocode reads that way, but the paper's text and its Figure 5 do
            # not, and more isolation made the pandemic grow (F-27).
            else:
                new_infected_individual = infect(carrier, fitness_function, 1)
                if get_rng().random() < strain_properties.p_isolation:
                    cls.isolate(state, new_infected_individual)
                else:
                    cls.admit(state, strain_properties, infected_population, new_infected_individual)
        return infected_population

    @classmethod
    def isolate(cls, state: PandemicState, individual: Solution) -> None:
        """
        What happens to an individual that isolates. In MetaGen's CVOA it is counted
        and the point stays open to be infected again: this departs from the paper's
        Algorithm 3 on purpose, measured (F-45). The paper's variant overrides it.
        """
        state.isolate(individual)

    @classmethod
    def admit(cls, state: PandemicState, strain_properties: StrainProperties,
              new_infected_population: SolutionSet, new_infected_individual: Solution) -> None:
        """
        Let a newly infected individual into the next population unless the pandemic
        already knows it: a dead one never enters, a recovered one only with
        p_re_infection, leaving the recovered when it does.
        """
        # Get the global individual state.
        individual_state: IndividualState = state.get_individual_state(new_infected_individual)

        # If the new individual is not in global death and recovered sets, then insert it in the next population.
        if not individual_state.dead and not individual_state.recovered:
            new_infected_population.add(new_infected_individual)

        # If the new individual is in the global recovered set, then check if it can be reinfected with
        # p_reinfection. If it can be reinfected, insert it into the new population and remove it from the global
        # recovered set.
        elif individual_state.recovered:
            if get_rng().random() < strain_properties.p_re_infection:
                new_infected_population.add(new_infected_individual)
                state.get_infected_again(new_infected_individual)

    def infect_individuals(self, carrier_individual: Solution, travel_distance: int, n_infected: int) -> SolutionSet:
        """The contagion of one carrier with the strain's own state, properties and time."""
        return type(self).infect_individuals_from(self.global_state, self.fitness_function, self.strain_properties,
                                                  carrier_individual, travel_distance, n_infected, self.time)

    def update_new_infected_population(self, new_infected_population: SolutionSet,
                                       new_infected_individual: Solution) -> None:
        """ It updates the next infected population with a new infected individual.

        :param new_infected_population: The population of the next iteration.
        :param new_infected_individual: The new infected individual that will be inserted into the netx iteration set.
        :type new_infected_population: set of :py:class:`~metagen.framework.Solution`
        :type new_infected_individual: :py:class:`~metagen.framework.Solution`
        """
        type(self).admit(self.global_state, self.strain_properties, new_infected_population, new_infected_individual)

    def update_pandemic_global_state(self) -> None:
        """
        Settle the fate of this iteration's carriers before they spread: the worst die,
        the best become the superspreaders, the rest recover; and keep the strain's and
        the pandemic's best up to date.

        This is MetaGen's variant, and what the original Java did before its ``sets``
        branch: a share ``p_die`` of the carriers, the worst ones, dies, and a share
        ``p_superspreader`` of the survivors, the best ones, superspreads. Both are
        picked with a heap in ``n log k``, which is the saving that branch was after
        when it replaced sorting the population with bounded sets filled in order of
        arrival; that replacement also inverted the selection, so the best died and
        the worst superspread, and MetaGen inherited it (F-48). A lone carrier never
        dies, as in the Java. The paper draws death and superspreading per individual
        instead; its variant overrides this method.
        """
        carriers = list(self.infected)
        number_of_deaths = math.ceil(self.strain_properties.p_die * len(carriers)) if len(carriers) > 1 else 0
        number_of_superspreaders = math.ceil(self.strain_properties.p_superspreader * len(carriers))

        dying = SolutionSet(heapq.nlargest(number_of_deaths, carriers, key=Solution.get_fitness))
        survivors = [carrier for carrier in carriers if carrier not in dying]
        self.superspreaders = SolutionSet(heapq.nsmallest(number_of_superspreaders, survivors,
                                                          key=Solution.get_fitness))
        self.dead.update(dying)

        for individual in carriers:
            if individual not in dying:
                self.global_state.recover_if_not_dead(individual)

            if individual.get_fitness() < self.global_state.get_best_individual().get_fitness():
                self.global_state.update_best_individual(individual)
                self.best_strain_solution_found = True
                self._log(f"New global best individual found at {self.time}! ({individual})")

            if individual.get_fitness() < self._best_of_strain().get_fitness():
                self.best_strain_solution = individual

        self.global_state.update_deaths(self.dead)
        self.global_state.update_recovered_with_deaths()

    def stopping_criterion(self) -> bool:

        # When the strain is stopped?

        # First condition: When there are no infected individuals
        first_condition: bool = self.epidemic == False

        # Second condition: When the pandemic duration has been reached
        second_condition: bool = self.time > self.strain_properties.pandemic_duration

        # Third condition: when the strain has spent too long without improving.
        # This used to be "best_strain_solution_found and self.time > 1", with a
        # flag nothing ever cleared, so a strain died right after its first
        # improvement (F-23). Off unless the strain asks for it.
        stagnation_limit = self.strain_properties.max_iterations_without_improvement
        third_condition = (stagnation_limit is not None
                           and self.iterations_without_improvement >= stagnation_limit)

        return first_condition or second_condition or third_condition

    def post_execution(self) -> None:
        self._log(f"Pandemic finished at {self.time} with best individual: {self.best_strain_solution}")
        super().post_execution()

    def r0_report(self, new_infections: int) -> str:
        recovered = self.global_state.get_recovered_len()
        r0: float = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "New infected = " + str(new_infections) + ", Recovered = " + str(recovered) + ", R0 = " + str(r0)
        return report

    def __str__(self):
        """ String representation of a :py:class:`~metagen.metaheuristics.CVOA` object (a strain).
        """
        res = ""
        res += self.strain_properties.strain_id + "\n"
        res += "Max time = " + str(self.strain_properties.pandemic_duration) + "\n"
        res += "Infected strain = " + str(self.infected) + "\n"
        res += "Super spreader strain = " + \
               str(self.superspreaders) + "\n"
        res += "Death strain = " + str(self.dead) + "\n"
        res += "MAX_SPREAD = " + str(self.strain_properties.spreading_rate) + "\n"
        res += "MIN_SUPERSPREAD = " + \
               str(self.strain_properties.min_superspreading_rate) + "\n"
        res += "MAX_SUPERSPREAD = " + \
               str(self.strain_properties.max_superspreading_rate) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.strain_properties.social_distancing) + "\n"
        res += "P_ISOLATION = " + str(self.strain_properties.p_isolation) + "\n"
        res += "P_TRAVEL = " + str(self.strain_properties.p_travel) + "\n"
        res += "P_REINFECTION = " + str(self.strain_properties.p_re_infection) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.strain_properties.p_superspreader) + "\n"
        res += "DEATH_PERC = " + str(self.strain_properties.p_die) + "\n"
        return res
