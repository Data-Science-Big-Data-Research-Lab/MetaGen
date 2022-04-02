import threading
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from time import time
from pycvoa.individual import *
from pycvoa.support import *

logging.basicConfig(level=logging.INFO)


class CVOA:
    """ This class implements the *CVOA* algorithm. It uses the :py:class:`~pycvoa.individual.Individual` class as an
    abstraction of an individual for the meta-heuristic.

    It solves an optimization problem defined by a :py:class:`~pycvoa.definition.ProblemDefinition` object and an
    implementation of a fitness function.

    By instantiate :py:class:`~pycvoa.cvoa.CVOA` object, i.e. a strain, the configuration parameters must be provided.

    This class supports multiple strain execution by means of multy-threading. Each strain
    (:py:class:`~pycvoa.cvoa.CVOA` object) will execute its *CVOA* algorithm (:py:meth:`~pycvoa.cvoa.CVOA.cvoa`)
    in a thread and, finally, the best :py:class:`~pycvoa.individual.Individual` (i.e. the best fitness function
    is obtained).

    To launch a multi-strain execution, this module provides the :py:meth:`~pycvoa.cvoa.cvoa_launcher`
    method.

    :param strain_id: The strain name
    :param pandemic_duration: The pandemic duration, defaults to 10
    :param spreading_rate: The spreading rate, defaults to 6
    :param min_super_spreading_rate: The minimum super spreading rate, defaults to 6
    :param max_super_spreading_rate: The maximum super spreading rate, defaults to 15
    :param social_distancing: , defaults to 10
    :param p_isolation: The probability of an individual being isolated, defaults to 0.7
    :param p_travel: The probability that an individual will travel, defaults to 0.1
    :param p_re_infection: The probability of an individual being re-infected, defaults to 0.0014
    :param p_superspreader: The probability of an individual being a super-spreader, defaults to 0.1
    :param p_die: The probability that an individual will die, defaults to 0.05
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
    """

    # ** Common and shared properties to all strains for multi-spreading (multi-threading) execution
    # These stores the recovered, deaths and isolated individuals respectively for all the launched strains.
    __recovered = None
    __deaths = None
    __isolated = None
    # It stores the global best solution found among all the launched strains.
    __bestSolution = None
    # If true, a best solution has been found.
    __bestSolutionFound = None
    # Lock fot multi-threading safety access to the shared structures.
    __lock = threading.Lock()
    # Fitness function to apply to the individuals.
    __fitnessFunction = None
    # Problem definition object.
    __individualDefinition = None
    # If true, the isolated set is updated.
    __update_isolated = None
    # If true show log messages.
    __verbosity = None

    def __init__(self, strain_id, pandemic_duration=10, spreading_rate=6, min_super_spreading_rate=6,
                 max_super_spreading_rate=15, social_distancing=10, p_isolation=0.7, p_travel=0.1,
                 p_re_infection=0.0014, p_superspreader=0.1, p_die=0.05):
        """ The constructor of the :py:class:`~pycvoa.cvoa.CVOA` class. It set the specific properties
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
        # Best strain individual. It is initialized to a empty one.
        self.__bestSolutionStrain = Individual()
        # Best dead individual and worst superspreader individuals. For debug and pandemic analysis purposes.
        # They are initialized to None.
        self.__bestDeadIndividualStrain = None
        self.__worstSuperSpreaderIndividualStrain = None


    @staticmethod
    def initialize_pandemic(problem_definition, fitness_function, update_isolated=False):
        """ It initializes a **CVOA** pandemic. A pandemic can be composed by one or more strains. Each strain is
        built by instantiate the :py:class:`~pycvoa.cvoa.CVOA` class. The common characteristic of all strains are
        the problem definition (:py:class:`~pycvoa.definition.ProblemDefinition` class) and the implementation
        of a fitness function.

        :param problem_definition: The problem definition.
        :param fitness_function: The fitness function.
        :param update_isolated: If true the isolated set will be updated on each iteration.
        :type problem_definition: :py:class:`~pycvoa.definition.ProblemDefinition`
        :type fitness_function: function
        :type update_isolated: bool
        """

        # The recovered, death and isolated sets are initialized to a void set
        CVOA.__recovered = set()
        CVOA.__deaths = set()
        CVOA.__isolated = set()

        # The best solution individual is initialized to the worst one
        # And the best solution condition is initialized to false
        # It is a standard search scheme.
        CVOA.__bestSolution = Individual(False)
        CVOA.__bestSolutionFound = False

        # Properties set by arguments.
        CVOA.__fitnessFunction = fitness_function
        CVOA.__individualDefinition = problem_definition
        CVOA.__update_isolated = update_isolated

    @staticmethod
    def pandemic_report():
        """ It provides a report of the running pandemic as a string representation. It includes information about
        the best solution found and the content of the recovered, death and isolated sets.

        :returns: A report of the running pandemic.
        :rtype: str
        """
        res = "Best solution = " + str(CVOA.__bestSolution) + "\n"
        res += "Recovered: " + str(len(CVOA.__recovered)) + "\n"
        res += "Death: " + str(len(CVOA.__deaths)) + "\n"
        res += "Isolated: " + str(len(CVOA.__isolated)) + "\n"
        return res

    @staticmethod
    def get_best_solution():
        """ It provides the best solution found by the **CVOA** algorithm.

        :returns: The best solution found by the **CVOA** algorithm
        :rtype: :py:class:`~pycvoa.individual.Individual`
        """
        return CVOA.__bestSolution

    @staticmethod
    def set_verbosity(verbosity):
        """ It sets the verbosity of the **CVOA** algorithm execution. If True, when the
        :py:meth:`~pycvoa.cvoa.CVOA.cvoa` method is running, messages about the status of the pandemic
        will be shown in the standard output console.

        :param verbosity: The verbosity option
        :type verbosity: bool
        """
        CVOA.__verbosity = verbosity

    def get_strain_id(self):
        """ It returns the identification of the strain.

        :returns: The identification of the strain.
        :rtype: str
        """
        return self.__strainID

    def cvoa(self):
        """ This function runs the **CVOA** algorithm. Before run the algorithm, two taks must be accomplished:

        #. Initialize the pandemic (:py:meth:`~pycvoa.cvoa.CVOA.initialize_pandemic` method)

            * Set the problem definition (:py:class:`~pycvoa.definition.ProblemDefinition` class)
            * Implements the fitness function

        #. Initialize a strain (instantiate a :py:class:`~pycvoa.cvoa.CVOA` class)

        **NOTE**
        If a mult-strain experiment is performed, the global best solution must be obtained by
        the:py:meth:`~pycvoa.cvoa.CVOA.get_best_solution` method after the algorithm finishes.

        :returns: The best solution found by the **CVOA** algorithm for the specific strain.
        :rtype: :py:class:`~pycvoa.individual.Individual`
        """

        # ***** STEP 1. PATIENT ZERO (PZ) GENERATION. *****

        pz = self.__infect_pz()
        CVOA.__verbosity("\nPatient Zero (" + self.__strainID + "): \n" + str(pz))

        # Initialize strain:
        # Add the patient zero to the strain-specific infected set.
        self.__infectedStrain.add(pz)
        self.__infected_strain_super_spreader_strain.add(pz)
        # The best strain-specific solution will initially be the patient zero.
        self.__bestSolutionStrain = pz
        # The worst strain-specific superspreader individual will initially be the best individual.
        self.__worstSuperSpreaderIndividualStrain = Individual(best=True)
        # The best strain-specific death individual will initially be the worst individual.
        self.__bestDeadIndividualStrain = Individual()

        # Logical condition to control the epidemic (main iteration).
        # If True, the iteration continues.
        # When there are no infected individuals, the epidemic finishes.
        epidemic = True

        # The iteration counter will be initially set to 0
        self.__time = 0

        # Stopping criterion: there are no new infected individuals or the pandemic duration is over
        # or a solution has been found.
        # Suggestion to third-party developers: add another stop criterion if bestSolution does not change after X
        # consecutive iterations
        while epidemic and self.__time < self.__pandemic_duration and not CVOA.__bestSolutionFound:

            # ***** STEP 2. SPREADING THE DISEASE. *****
            self.__propagate_disease()

            # ***** STEP 4. STOP CRITERION. *****
            # Stop if no new infected individuals
            if not self.__infectedStrain:
                epidemic = False
                CVOA.__verbosity("No new infected individuals in " + self.__strainID)

            # Legacy:
            # elif self.__bestSolutionStrain.fitness == 0.0:
            #     # Stop if best known fitness is found ( or fitness satisfying your requirements)
            #     CVOA.__lock.acquire()
            #     CVOA.__bestSolutionFound = True
            #     CVOA.__lock.release()
            #     CVOA.__verbose print("Best solution (by fitness) found by " + self.__strainID)

            # Update the elapsed pandemic time
            self.__time += 1

        CVOA.__verbosity("\n\n" + self.__strainID + " converged after " + str(self.__time) + " iterations.")
        CVOA.__verbosity("Best individual: " + str(self.__bestSolutionStrain))

        # When the CVOA algorithm finishes, returns the best solution found for the specific strain.
        # If a mult-strain experiment is performed, the global best solution
        # must be obtained by the get_best_solution method
        return self.__bestSolutionStrain

    def __propagate_disease(self):

        # New infected people will be stored here (from infectedStrain)
        new_infected_population = set()
        travel_distance = 1

        # This condition replaces the instruction "Collections.sort(infected)" from the previous version with the aim
        # of reducing the execution time
        self.__update_death_super_spreader_strain()

        # Ensure the best solutions by strains are kept in the next iteration
        new_infected_population.add(self.__bestSolutionStrain)

        # Each individual infects new ones and add them to newInfectedPopulation
        for individual in self.__infectedStrain:
            # Calculation of number of new infected and whether they travel or not
            # 1. Determine the number of new individuals depending on SuperSpreader or Common
            if individual in self.__superSpreaderStrain:
                n_infected = random.randint(self.__MIN_SUPERSPREADING_RATE, self.__MAX_SUPERSPREADING_RATE)
            else:
                n_infected = random.randint(0, self.__MAX_SUPERSPREADING_RATE)

            # 2. Determine the travel distance, which is how far is the new infected individual
            if random.random() < self.__P_TRAVEL:
                travel_distance = random.randint(0, len(CVOA.__individualDefinition.get_definition().keys()))
                # travel_distance = randint(1, ceil(len(CVOA.__individualDefinition.keys())*self.__P_TRAVEL))

            # 3. Every individual infects as many times as indicated by n_infected
            for i in range(0, n_infected):
                # Propagate with no social distancing measures
                if self.__time < self.__SOCIAL_DISTANCING:
                    new_infected_individual = self.__infect(individual, travel_distance)
                    self.__update_new_infected_population(new_infected_population, new_infected_individual)
                # After SOCIAL_DISTANCING iterations, there is a P_ISOLATION of not being infected
                # travel_distance is set to 1, simulating an individual cannot travel anymore
                else:
                    new_infected_individual = self.__infect(individual, 1)
                    if random.random() < self.__P_ISOLATION:
                        self.__update_new_infected_population(new_infected_population, new_infected_individual)
                    # This effect is similar to sending them to the deaths set
                    else:
                        if CVOA.__update_isolated:
                            self.__update_isolated_population(individual)

        # Just one print to ensure it is printed without interfering with other threads
        CVOA.__verbosity("\n" + str(threading.current_thread()) +
                         "\n[" + self.__strainID + "] - Iteration #" + str(self.__time + 1) +
                         "\n\tBest global individual: " + str(CVOA.__bestSolution)
                         + "\n\tBest strain individual: " + str(self.__bestSolutionStrain)
                         + "\n\t#NewInfected = " + str(len(new_infected_population))
                         + "\n\tR0 = " + str(len(new_infected_population) / len(self.__infectedStrain)))

        # Update infected populations for the next iteration
        self.__infectedStrain.clear()
        self.__infectedStrain.update(new_infected_population)

    def __infect_pz(self):
        # logging.debug("Infect PZ")
        patient_zero = Individual()

        for variable, definition in CVOA.__individualDefinition.get_definition().items():
            logging.debug(">>>>>>>> Variable = " + str(variable) + " definition = " + str(definition))

            if definition[0] is INTEGER or definition[0] is REAL or definition[0] is CATEGORICAL:
                logging.debug(">INTEGER")
                patient_zero.set_variable_value(variable, get_random_value_for_simple_variable(definition))

            elif definition[0] == LAYER:
                logging.debug(">LAYER")
                for element_name, element_definition in definition[1].items():
                    patient_zero.set_layer_element_value(variable, element_name,
                                                         get_random_value_for_simple_variable(element_definition))
            elif definition[0] == VECTOR:
                logging.debug(">VECTOR")
                vector_size = get_number_from_interval(definition[1], definition[2], definition[3])
                vector_component_type = definition[4]

                logging.debug(">VECTOR, vector_component_type: %s", vector_component_type)
                for i in range(0, vector_size):
                    if vector_component_type[0] is INTEGER or vector_component_type[0] is REAL or \
                            vector_component_type[0] is CATEGORICAL:

                        value = get_random_value_for_simple_variable(vector_component_type)
                        patient_zero.add_vector_element(variable, value)
                        logging.debug(">VECTOR, variable: %s, value = %s", variable, value)
                    elif vector_component_type[0] is LAYER:
                        layer_values = {}
                        for element_name, element_definition in vector_component_type[1].items():
                            layer_values[element_name] = get_random_value_for_simple_variable(element_definition)
                        patient_zero.add_vector_element(variable, layer_values)

        # logging("Individual = %s"+str(patient_zero))
        patient_zero.fitness = CVOA.__fitnessFunction(patient_zero)

        return patient_zero

    def __infect(self, individual, travel_distance):
        # logging.debug("Infect")
        definition = CVOA.__individualDefinition.get_definition()
        infected = copy.deepcopy(individual)

        infected_variables = random.sample(list(definition.keys()), travel_distance)
        infected_variables_set = set(infected_variables)

        for variable in infected_variables_set:
            inoculate_individual(infected, variable, definition[variable])

        infected.fitness = CVOA.__fitnessFunction(infected)

        return infected

    def __update_recovered_death_strain(self, bag, to_insert, remaining):

        dead = self.__insert_into_set_strain(bag, to_insert, remaining, 'd')

        if not dead:
            CVOA.__lock.acquire()
            if to_insert not in CVOA.__deaths:
                CVOA.__recovered.add(to_insert)
            CVOA.__lock.release()

        return dead

    # Insert the individual in the strain sets (death or superspreader)
    # Code re-utilization needs to be improved
    def __insert_into_set_strain(self, bag, to_insert, remaining, ty):

        r = False

        if remaining > 0:

            bag.add(to_insert)
            r = True

            if ty == 's':
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    self.__worstSuperSpreaderIndividualStrain = to_insert
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    self.__bestDeadIndividualStrain = to_insert

        else:

            if ty == 's':
                if to_insert > self.__worstSuperSpreaderIndividualStrain:
                    bag.remove(self.__worstSuperSpreaderIndividualStrain)
                    bag.add(to_insert)
                    r = True
                    self.__worstSuperSpreaderIndividualStrain = to_insert
            elif ty == 'd':
                if to_insert < self.__bestDeadIndividualStrain:
                    bag.remove(self.__bestDeadIndividualStrain)
                    bag.add(to_insert)
                    r = True
                    self.__bestDeadIndividualStrain = to_insert

        return r

    def __update_new_infected_population(self, new_infected_population, new_infected_individual):

        if new_infected_individual not in CVOA.__deaths and new_infected_individual not in CVOA.__recovered:
            new_infected_population.add(new_infected_individual)
        elif new_infected_individual in CVOA.__recovered:
            if random.random() < self.__P_REINFECTION:
                new_infected_population.add(new_infected_individual)
                CVOA.__recovered.remove(new_infected_individual)

    # Update isolated population
    def __update_isolated_population(self, individual):
        if individual not in CVOA.__deaths and individual not in CVOA.__recovered and individual not in CVOA.__isolated:
            CVOA.__isolated.add(individual)

    def __update_death_super_spreader_strain(self):

        # Superspreader and deaths strain sets for each iteration
        number_of_super_spreaders = math.ceil(self.__P_SUPERSPREADER * len(self.__infectedStrain))
        number_of_deaths = math.ceil(self.__P_DIE * len(self.__infectedStrain))

        if len(self.__infectedStrain) != 1:

            for individual in self.__infectedStrain:

                if self.__insert_into_set_strain(self.__superSpreaderStrain, individual, number_of_super_spreaders,
                                                 "s"):
                    number_of_super_spreaders -= 1

                if self.__update_recovered_death_strain(self.__deathStrain, individual, number_of_deaths):
                    number_of_deaths -= 1

                if individual.fitness < CVOA.__bestSolution.fitness:
                    CVOA.__lock.acquire()
                    CVOA.__bestSolution = individual
                    CVOA.__lock.release()
                    CVOA.__verbosity("\nNew best solution found by " + self.__strainID + "!")

                if individual.fitness < self.__bestSolutionStrain.fitness:
                    self.__bestSolutionStrain = individual

            self.__bestSolutionStrain.discovering_iteration_time = self.__time + 1

            CVOA.__lock.acquire()
            CVOA.__deaths.update(self.__deathStrain)
            CVOA.__lock.release()

        CVOA.__lock.acquire()
        CVOA.__recovered.difference_update(CVOA.__deaths)
        CVOA.__lock.release()

    def __str__(self):

        res = ""
        res += self.__strainID + "\n"
        res += "Max time = " + str(self.__pandemic_duration) + "\n"
        res += "Infected strain = " + str(self.__infectedStrain) + "\n"
        res += "Super spreader strain = " + str(self.__superSpreaderStrain) + "\n"
        res += "Death strain = " + str(self.__deathStrain) + "\n"
        res += "MAX_SPREAD = " + str(self.__SPREADING_RATE) + "\n"
        res += "MIN_SUPERSPREAD = " + str(self.__MIN_SUPERSPREADING_RATE) + "\n"
        res += "MAX_SUPERSPREAD = " + str(self.__MAX_SUPERSPREADING_RATE) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.__SOCIAL_DISTANCING) + "\n"
        res += "P_ISOLATION = " + str(self.__P_ISOLATION) + "\n"
        res += "P_TRAVEL = " + str(self.__P_TRAVEL) + "\n"
        res += "P_REINFECTION = " + str(self.__P_REINFECTION) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.__P_SUPERSPREADER) + "\n"
        res += "DEATH_PERC = " + str(self.__P_DIE) + "\n"
        return res


def cvoa_launcher(strains, verbose=True):
    """
         Return a list of random ingredients as strings.
    """
    verbosity = print if verbose else lambda *a, **k: None
    CVOA.set_verbosity(verbosity)

    t1 = time()
    with ThreadPoolExecutor(max_workers=len(strains)) as executor:
        futures = {strain.get_strain_id(): executor.submit(strain.cvoa) for strain in strains}
    t2 = time()

    verbosity("\n********** Results by strain **********")
    for strain_id, future in futures.items():
        verbosity("[" + strain_id + "] Best solution: " + str(future.result()))

    verbosity("\n********** Best result **********")
    verbosity("Best individual: " + str(CVOA.get_best_solution()))

    verbosity("\n********** Performance **********")
    verbosity("Execution time: " + str(timedelta(milliseconds=t2 - t1)))
    verbosity(CVOA.pandemic_report())

    return CVOA.get_best_solution()
