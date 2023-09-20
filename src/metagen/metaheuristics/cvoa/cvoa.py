import copy
import logging
import math
import random
import threading
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from time import time
from typing import Callable, Set

from metagen.framework import Domain
from metagen.framework.solution import Solution
from metagen.framework.solution.bounds import SolutionClass


class CVOA:
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

    # ** Global properties to all strains for multi-spreading (multi-threading) execution
    # These stores the recovered, deaths and isolated individuals respectively for all the launched strains.
    __recovered: Set | None = None
    __deaths: Set | None = None
    __isolated: Set | None = None
    # It stores the global best individual found among all the launched strains.
    __bestIndividual: Solution | None = None
    # If true, a best individual has been found.
    __bestIndividualFound: Solution | None = None
    # Lock fot multi-threading safety access to the shared structures.
    __lock = threading.Lock()
    # Fitness function to apply to the individuals.
    __fitnessFunction: Callable[[Solution], float] | None = None
    # Problem definition object.
    __problemDefinition: Domain | None = None
    # If true, the isolated set is updated.
    __update_isolated: bool | None = None
    # If true show log messages.
    __verbosity: Callable[[str], None] | None = None

    def __init__(self, strain_id="Strain 1", pandemic_duration=10, spreading_rate=5, min_super_spreading_rate=6,
                 max_super_spreading_rate=15, social_distancing=7, p_isolation=0.5, p_travel=0.1,
                 p_re_infection=0.001, p_superspreader=0.1, p_die=0.05, verbose=True):
        """ The constructor of the :py:class:`~metagen.metaheuristics.CVOA` class. It set the specific properties
        of a strain.
        """

        # Properties set by arguments.
        self.__strainID = strain_id
        self.__pandemic_duration = pandemic_duration
        self.__SPREADING_RATE = spreading_rate
        self.__MIN_SUPERSPREADING_RATE = min_super_spreading_rate
        self.__MAX_SUPERSPREADING_RATE = max_super_spreading_rate
        self.__SOCIAL_DISTANCING = social_distancing
        self.__P_ISOLATION = p_isolation
        self.__P_TRAVEL = p_travel
        self.__P_REINFECTION = p_re_infection
        self.__P_SUPERSPREADER = p_superspreader
        self.__P_DIE = p_die

        # Main strain sets: infected, superspreaders, infected superspreaders and deaths.
        self.__infectedStrain = set()
        self.__superSpreaderStrain = set()
        self.__infected_strain_super_spreader_strain = set()
        self.__deathStrain = set()

        # Other specific properties:
        # Iteration counter.
        self.__time = None
        self.solution_type: type[SolutionClass] = CVOA.__problemDefinition.get_connector().get_type(
            CVOA.__problemDefinition.get_core())
        # Best strain individual. It is initialized to the worst solution.
        self.__bestStrainIndividual = self.solution_type(
            CVOA.__problemDefinition, connector=CVOA.__problemDefinition.get_connector())
        # Best dead individual and worst superspreader individuals. For debug and pandemic analysis purposes.
        # They are initialized to None.
        self.__bestDeadIndividualStrain = None
        self.__worstSuperSpreaderIndividualStrain = None

        self.set_verbosity(verbose)

    @staticmethod
    def initialize_pandemic(problem_definition, fitness_function, update_isolated=False):
        """ It initializes a **CVOA** pandemic. A pandemic can be composed by one or more strains. Each strain is
        built by instantiate the :py:class:`~metagen.metaheuristics.CVOA` class. The common characteristic of all strains are
        the problem definition (:py:class:`~metagen.framework.Domain` class) and the implementation
        of a fitness function.

        :param problem_definition: The problem definition.
        :param fitness_function: The fitness function.
        :param update_isolated: If true the isolated set will be updated on each iteration.
        :type problem_definition: :py:class:`~metagen.framework.Domain`
        :type fitness_function: function
        :type update_isolated: bool
        """

        # The recovered, death and isolated sets are initialized to a void set.
        CVOA.__recovered = set()
        CVOA.__deaths = set()
        CVOA.__isolated = set()

        # The best individual is initialized to the worst solution and the best individual condition
        # is initialized to false. It is a standard search scheme.

        CVOA.__bestIndividualFound = False

        # Properties set by arguments.
        CVOA.__fitnessFunction = fitness_function
        CVOA.__problemDefinition = problem_definition
        CVOA.__update_isolated = update_isolated
        solution_type: type[SolutionClass] = problem_definition.get_connector().get_type(
            problem_definition.get_core())
        CVOA.__bestIndividual = solution_type(problem_definition, connector=problem_definition.get_connector())

    @staticmethod
    def pandemic_report():
        """ It provides a report of the running pandemic as a string representation. It includes information about
        the best individual found and the content of the recovered, death and isolated sets.

        :returns: A report of the running pandemic.
        :rtype: str
        """
        res = "Best individual: " + str(CVOA.__bestIndividual) + "\n"
        res += "Recovered: " + str(len(CVOA.__recovered)) + "\n"
        res += "Death: " + str(len(CVOA.__deaths)) + "\n"
        res += "Isolated: " + str(len(CVOA.__isolated)) + "\n"
        return res

    @staticmethod
    def get_best_individual():
        """ It provides the best individual found by the **CVOA** algorithm.

        :returns: The best individual found by the **CVOA** algorithm
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        return CVOA.__bestIndividual

    @staticmethod
    def set_verbosity(verbose):
        """ It sets the verbosity of the **CVOA** algorithm execution. If True, when the
        :py:meth:`~metagen.metaheuristics.CVOA.cvoa` method is running, messages about the status of the pandemic
        will be shown in the standard output console.

        :param verbose: The verbosity option
        :type verbose: bool
        """
        CVOA.__verbosity = \
            print if verbose else lambda *a, **k: None  # Cabrón esto hay que pasarlo al paquete logging o algo así

    def get_strain_id(self):
        """ It returns the identification of the strain.

        :returns: The identification of the strain.
        :rtype: str
        """
        return self.__strainID

    def run(self):
        """ This function runs the **CVOA** algorithm. Before run the algorithm, two taks must be accomplished:

        #. Initialize the pandemic (:py:meth:`~metagen.metaheuristics.CVOA.initialize_pandemic` method)

            * Set the problem definition (:py:class:`~metagen.framework.Domain` class)
            * Implements the fitness function

        #. Initialize a strain (instantiate a :py:class:`~metagen.metaheuristics.CVOA` class)

        **NOTE**
        If a mult-strain experiment is performed, the global best individual must be obtained by
        the :py:meth:`~metagen.metaheuristics.CVOA.get_best_solution` method after the algorithm finishes.

        :returns: The best individual found by the **CVOA** algorithm for the specific strain.
        :rtype: :py:class:`~metagen.framework.Solution`
        """

        # ***** STEP 1. PATIENT ZERO (PZ) GENERATION. *****

        pz = self.__infect_pz()
        CVOA.__verbosity(
            "\nPatient Zero (" + self.__strainID + "): \n" + str(pz))

        # Initialize strain:
        # Add the patient zero to the strain-specific infected set.
        self.__infectedStrain.add(pz)
        self.__infected_strain_super_spreader_strain.add(pz)
        # The best strain-specific individual will initially be the patient zero.
        self.__bestStrainIndividual = pz
        # The worst strain-specific superspreader individual will initially be the best solution.
        self.__worstSuperSpreaderIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, best=True, connector=CVOA.__problemDefinition.get_connector())
        # The best strain-specific death individual will initially be the worst solution.
        self.__bestDeadIndividualStrain = self.solution_type(
            CVOA.__problemDefinition, connector=CVOA.__problemDefinition.get_connector())

        # Logical condition to ctrl the epidemic (main iteration).
        # If True, the iteration continues.
        # When there are no infected individuals, the epidemic finishes.
        epidemic = True

        # The iteration counter will be initially set to 0.
        self.__time = 0

        # Stopping criterion: there are no new infected individuals or the pandemic duration is over
        # or an individual has been found.
        # Suggestion to third-party developers: add another stop criterion if bestSolution does not change after X
        # consecutive iterations.
        while epidemic and self.__time < self.__pandemic_duration and not CVOA.__bestIndividualFound:

            # ***** STEP 2. SPREADING THE DISEASE. *****
            self.__propagate_disease()

            # ***** STEP 4. STOP CRITERION. *****
            # Stop if no new infected individuals.
            if not self.__infectedStrain:
                epidemic = False
                CVOA.__verbosity(
                    "No new infected individuals in " + self.__strainID)

            # Legacy:
            # elif self.__bestSolutionStrain.fitness == 0.0:
            #     # Stop if best known fitness is found ( or fitness satisfying your requirements)
            #     CVOA.__lock.acquire()
            #     CVOA.__bestSolutionFound = True
            #     CVOA.__lock.release()
            #     CVOA.__verbose print("Best individual (by fitness) found by " + self.__strainID)

            # Update the elapsed pandemic time.
            self.__time += 1

        CVOA.__verbosity("\n\n" + self.__strainID +
                         " converged after " + str(self.__time) + " iterations.")
        CVOA.__verbosity("Best individual: " +
                         str(self.__bestStrainIndividual))

        # When the CVOA algorithm finishes, returns the best individual found for the specific strain.
        # If a mult-strain experiment is performed, the global best individual
        # must be obtained by the get_best_solution method.
        return self.__bestStrainIndividual

    def __propagate_disease(self):
        """ It spreads the disease through the individuals of the population.
        """
        # Initialize the new infected population set and the travel distance.
        # Each new infected individual will be added to this set.
        new_infected_population = set()
        travel_distance = 1

        # Before the new propagation, update the strain (superspreader, death) and global (death, recovered) sets.
        # Then, add the best individual of the strain to the next population.
        self.__update_strain_global_sets()
        new_infected_population.add(self.__bestStrainIndividual)

        # For each infected individual in the strain:
        for individual in self.__infectedStrain:

            # ** 1. Determine the number of infections. **
            # If the current individual is superspreader the number of infected ones will be in
            # (MIN_SUPERSPREADING_RATE, MAX_SUPERSPREADING_RATE).
            # If the current individual is common the number of infected ones will be in
            # (0, MAX_SUPERSPREADING_RATE).
            if individual in self.__superSpreaderStrain:
                n_infected = random.randint(
                    self.__MIN_SUPERSPREADING_RATE, self.__MAX_SUPERSPREADING_RATE)
            else:
                n_infected = random.randint(0, self.__SPREADING_RATE)
                # n_infected = random.randint(0, self.__MAX_SUPERSPREADING_RATE)

            # ** 2. Determine the travel distance. **
            # If the current individual is a traveler, the travel distance will be in
            # (0, number of variable defined in the problem), otherwise the travel distance will be 1.
            if random.random() < self.__P_TRAVEL:
                travel_distance = random.randint(
                    0, len(CVOA.__problemDefinition.get_core().variable_list()))
                # travel_distance = randint(1, ceil(len(CVOA.__individualDefinition.keys())*self.__P_TRAVEL))

            # ** 3. Infect the new individuals. **
            # For each n_infected new individuals:
            for _ in range(0, n_infected):
                # If the current disease time is not affected by the SOCIAL DISTANCING policy, the current
                # individual infects another with a travel distance (using __infect), and it is added
                # to the newly infected population.
                if self.__time < self.__SOCIAL_DISTANCING:
                    new_infected_individual = self.__infect(
                        individual, travel_distance)
                    self.__update_new_infected_population(
                        new_infected_population, new_infected_individual)

                # After SOCIAL_DISTANCING iterations (when the SOCIAL DISTANCING policy is applied),
                # the current individual infects another with a travel distance of one (using __infect) then,
                # the newly infected individual can be isolated or not.
                else:
                    new_infected_individual = self.__infect(individual, 1)
                    if random.random() < self.__P_ISOLATION:
                        self.__update_new_infected_population(
                            new_infected_population, new_infected_individual)
                    else:
                        # If the new individual is isolated, and __update_isolated is true, this is sent to the
                        # __update_isolated_population.
                        if CVOA.__update_isolated:
                            self.__update_isolated_population(individual)

        # Just one print to ensure it is printed without interfering with other threads
        CVOA.__verbosity("\n" + str(threading.current_thread()) +
                         "\n[" + self.__strainID + "] - Iteration #" + str(self.__time + 1) +
                         "\n\tBest global individual: " +
                         str(CVOA.__bestIndividual)
                         + "\n\tBest strain individual: " +
                         str(self.__bestStrainIndividual)
                         + "\n" + self.__r0_report(len(new_infected_population)))
        # + "\n\tR0 = " + str(len(new_infected_population) / len(self.__infectedStrain)))

        # Update the infected strain population for the next iteration
        self.__infectedStrain.clear()
        self.__infectedStrain.update(new_infected_population)

    # @staticmethod
    def __infect_pz(self):
        """ It builds the *patient zero*, **PZ**, for the **CVOA** algorithm.

        :returns: The *patient zero*, **PZ**
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        # patient_zero = build_random_solution(self.__problemDefinition, CVOA.__fitnessFunction)

        patient_zero = self.solution_type(
            self.__problemDefinition, connector=self.__problemDefinition.get_connector())
        patient_zero.initialize()

        patient_zero.fitness = CVOA.__fitnessFunction(patient_zero)

        # logging.debug("Infect PZ")

        return patient_zero

    def __r0_report(self, new_infections: int):
        recovered = len(self.__recovered)
        r0 = new_infections
        if recovered != 0:
            r0 = new_infections / recovered
        report = "\tNew infected = " + \
            str(new_infections) + ", Recovered = " + \
            str(recovered) + ", R0 = " + str(r0)
        return report

    @staticmethod
    def __infect(individual, travel_distance):
        """ The individual infects another one located at a specific distance from it.

        :returns: The newly infected individual.
        :rtype: :py:class:`~metagen.framework.Solution`
        """
        # logging.debug("Infect")
        # Initially, the infected individual will be a copy of the original one.
        # definition = CVOA.__problemDefinition.get_definitions()
        infected = copy.deepcopy(individual)

        # TODO: Añadir entrada travel_distance
        infected.mutate(travel_distance)

        # Select a random set of variables that will be altered based on the travel distance.
        # infected_variables = random.sample(list(definition.keys()), travel_distance)
        # infected_variables_set = set(infected_variables)

        # For each selected variables, inoculate the disease with the inoculate_individual auxiliary function.
        # for variable in infected_variables_set:
        # alter_solution(infected, variable, definition[variable])

        # Compute the fitness function of the new individual.
        infected.fitness = CVOA.__fitnessFunction(infected)

        return infected

    def __update_strain_global_sets(self):
        """ It updates the specific strain death and superspreader's sets and the global death and recovered sets.
        """

        # A percentage,__P_SUPERSPREADER, of the infected individuals in the strain (__infectedStrain)
        # will be superspreaders.
        # A percentage, __P_DIE, of the infected individuals in the strain (__infectedStrain)
        # will die.
        number_of_super_spreaders = math.ceil(
            self.__P_SUPERSPREADER * len(self.__infectedStrain))
        number_of_deaths = math.ceil(self.__P_DIE * len(self.__infectedStrain))
        # If there are at least two infected individuals in the strain:
        # TODO: lo cambio a >= 1 (!=1 puede lanzar excepción)
        if len(self.__infectedStrain) >= 1:

            # For each infected individual:
            for individual in self.__infectedStrain:

                # Insert the current individual into superspreader set; if the insertion was successful, decrement
                # the superspreader's counter.
                if self.__insert_into_set_strain(self.__superSpreaderStrain, individual, number_of_super_spreaders,
                                                 "s"):
                    number_of_super_spreaders -= 1

                # Update the recovered and death sets.
                if self.__update_recovered_death_strain(individual, number_of_deaths):
                    number_of_deaths -= 1

                # If the current individual is better than the current global one, a new global best individual is
                # found, and its global variable is updated.
                if individual.fitness < CVOA.__bestIndividual.fitness:
                    CVOA.__lock.acquire()
                    CVOA.__bestIndividual = individual
                    print(CVOA.__bestIndividual)
                    CVOA.__lock.release()
                    CVOA.__verbosity(
                        "\nNew best Individual found by " + self.__strainID + "!")

                # If the current individual is better than the current strain one, a new strain the best individual is
                # found, and its variable is updated.
                if individual.fitness < self.__bestStrainIndividual.fitness:
                    self.__bestStrainIndividual = individual

            # Increment the discovering iteration time.
            self.__bestStrainIndividual.discovery_iteration = self.__time + 1

            # Update the global death set with the strain death set.
            CVOA.__lock.acquire()
            CVOA.__deaths.update(self.__deathStrain)
            CVOA.__lock.release()

        # Remove the global dead individuals from the global recovered set.
        CVOA.__lock.acquire()
        CVOA.__recovered.difference_update(CVOA.__deaths)
        CVOA.__lock.release()

    def __update_recovered_death_strain(self, to_insert, remaining):
        """ It updates the specific strain death set and the global recovered set.

        :param to_insert: The individual that has to be inserted in the death set.
        :param remaining: The number of individuals remaining to be added in the death set.
        :type to_insert: :py:class:`~metagen.framework.Solution`
        :type remaining: int
        :returns: True, if the individual has been successfully inserted in the death set; otherwise False.
        :rtype: bool
        """

        # Insert the current individual into death set; if the insertion was successful, the dead variable
        # will be set to True; otherwise False.
        dead = self.__insert_into_set_strain(
            self.__deathStrain, to_insert, remaining, 'd')

        # If the current individual is not dead, it is added to the recovered set.
        if not dead:
            CVOA.__lock.acquire()
            if to_insert not in CVOA.__deaths:
                CVOA.__recovered.add(to_insert)
            CVOA.__lock.release()

        return dead

    def __insert_into_set_strain(self, bag, to_insert, remaining, ty):
        """ Insert an individual in the strain sets (death or superspreader).

        :param bag: The set where the individual has to be inserted.
        :param to_insert: The individual that has to be inserted.
        :param remaining: The number of individuals remaining to be added in the set.
        :param ty: The set where the individual will be inserted ('s' if it is the superspreader set, 'd' if it is the
        death set.
        :type bag: set of :py:class:`~metagen.framework.Solution`
        :type to_insert: :py:class:`~metagen.framework.Solution`
        :type remaining: int
        :type ty: str
        :returns: True, if the individual has been successfully inserted; otherwise False
        :rtype: bool
        """

        # Initialization of the returned value.
        inserted = False

        # If there are still individuals to be added to the set:
        if remaining > 0:
            # The individual is inserted and the returned value is True.
            bag.add(to_insert)
            inserted = True

            # The worst superspreader individual (in the case of an insertion in the superspreader set) or the best
            # death individual (in the case of an insertion in the death set) are updated considering the previous
            # insertion. That is for the efficient updating of strain sets.
            if ty == 's':
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    self.__worstSuperSpreaderIndividualStrain = to_insert
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    self.__bestDeadIndividualStrain = to_insert

        # If there are no individuals left to add to the set:
        else:

            # If the current individual is worse than the worst in the superspreader set, the current individual
            # replaces the worst. This operation ensures that the worst new individual will be a superspreader.
            # This action adds more diversification to the metaheuristic.
            if ty == 's':
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    if self.__worstSuperSpreaderIndividualStrain in bag:
                        bag.remove(self.__worstSuperSpreaderIndividualStrain)
                    bag.add(to_insert)
                    inserted = True
                    self.__worstSuperSpreaderIndividualStrain = to_insert

            # If the current individual is better than the best in the death set, the current individual
            # replaces the best. This operation ensures that the best new individual will be death.
            # This action adds more diversification to the metaheuristic.
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    logging.debug("bag: %s", str(bag))
                    logging.debug("__bestDeadIndividualStrain: %s",
                                  str(self.__bestDeadIndividualStrain))
                    logging.debug("contains?: %s", str(
                        self.__bestDeadIndividualStrain in bag))

                    bag.remove(self.__bestDeadIndividualStrain)
                    bag.add(to_insert)
                    inserted = True
                    self.__bestDeadIndividualStrain = to_insert

        return inserted

    def __update_new_infected_population(self, new_infected_population, new_infected_individual):
        """ It updates the next infected population with a new infected individual.

        :param new_infected_population: The population of the next iteration.
        :param new_infected_individual: The new infected individual that will be inserted into the netx iteration set.
        :type new_infected_population: set of :py:class:`~metagen.framework.Solution`
        :type new_infected_individual: :py:class:`~metagen.framework.Solution`
        """

        # If the new individual is not in global death and recovered sets, then insert it in the next population.
        if new_infected_individual not in CVOA.__deaths and new_infected_individual not in CVOA.__recovered:
            new_infected_population.add(new_infected_individual)

        # If the new individual is in the global recovered set, then check if it can be reinfected with
        # __P_REINFECTION. If it can be reinfected, insert it into the new population and remove it from the global
        # recovered set.
        elif new_infected_individual in CVOA.__recovered:
            if random.random() < self.__P_REINFECTION:
                new_infected_population.add(new_infected_individual)
                CVOA.__lock.acquire()
                CVOA.__recovered.remove(new_infected_individual)
                CVOA.__lock.release()

    @staticmethod
    def __update_isolated_population(individual):
        """ It updates the global isolated set with an individual.

        :param individual: The individual that will be inserted into the global isolated set.
        :type individual: :py:class:`~metagen.framework.Solution`
        """

        # If the individual is not in global death, recovered and isolation sets, then insert it in the isolated set.
        if individual not in CVOA.__deaths and individual not in CVOA.__recovered and individual not in CVOA.__isolated:
            CVOA.__lock.acquire()
            CVOA.__isolated.add(individual)
            CVOA.__lock.release()

    def __str__(self):
        """ String representation of a :py:class:`~metagen.metaheuristics.CVOA` object (a strain).
        """
        res = ""
        res += self.__strainID + "\n"
        res += "Max time = " + str(self.__pandemic_duration) + "\n"
        res += "Infected strain = " + str(self.__infectedStrain) + "\n"
        res += "Super spreader strain = " + \
               str(self.__superSpreaderStrain) + "\n"
        res += "Death strain = " + str(self.__deathStrain) + "\n"
        res += "MAX_SPREAD = " + str(self.__SPREADING_RATE) + "\n"
        res += "MIN_SUPERSPREAD = " + \
               str(self.__MIN_SUPERSPREADING_RATE) + "\n"
        res += "MAX_SUPERSPREAD = " + \
               str(self.__MAX_SUPERSPREADING_RATE) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.__SOCIAL_DISTANCING) + "\n"
        res += "P_ISOLATION = " + str(self.__P_ISOLATION) + "\n"
        res += "P_TRAVEL = " + str(self.__P_TRAVEL) + "\n"
        res += "P_REINFECTION = " + str(self.__P_REINFECTION) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.__P_SUPERSPREADER) + "\n"
        res += "DEATH_PERC = " + str(self.__P_DIE) + "\n"
        return res


def cvoa_launcher(strains, verbose=True):
    """ It launches a multi-strain execution of the *CVOA* algorithm. Each strain
    (:py:class:`~metagen.metaheuristics.CVOA` object) will execute its *CVOA* algorithm (:py:meth:`~metagen.metaheuristics.CVOA.cvoa`)
    in a thread and, finally, the best :py:class:`~metagen.framework.Solution` (i.e. the best fitness function
    is obtained).

    Before call this function, the pandemic must be initialized using the
    :py:meth:`~metagen.metaheuristics.CVOA.initialize_pandemic` method of the :py:class:`~metagen.metaheuristics.CVOA` class. A problem
    definition (using the :py:class:`~metagen.framework.Domain` class) and a fitness function must
    be provided.

    :param strains: The strain configurations (:py:class:`~metagen.metaheuristics.CVOA` objects)
    :param verbose: If true, the status of the pandemic will be shown in the standard output console, defaults to True.
    :type strains: list of :py:class:`~metagen.metaheuristics.CVOA` objects
    :type verbose: bool
    :returns: The best Individual of the *CVOA* multi-strain run
    :rtype: :py:class:`~metagen.framework.Solution`
    """

    CVOA.set_verbosity(verbose)

    t1 = time()
    with ThreadPoolExecutor(max_workers=len(strains)) as executor:
        futures = {strain.get_strain_id(): executor.submit(strain.run)
                   for strain in strains}
    t2 = time()

    print("\n********** Results by strain **********")
    for strain_id, future in futures.items():
        print("[" + strain_id + "] Best individual: " + str(future.result()))

    print("\n********** Best result **********")
    print("Best individual: " + str(CVOA.get_best_individual()))

    print("\n********** Performance **********")
    print("Execution time: " + str(timedelta(milliseconds=t2 - t1)))
    print(CVOA.pandemic_report())

    return CVOA.get_best_individual()
