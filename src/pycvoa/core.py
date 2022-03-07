import threading
from concurrent.futures.thread import ThreadPoolExecutor
from datetime import timedelta
from time import time

from pycvoa.individual import *
from pycvoa.support import *

logging.basicConfig(level=logging.INFO)


class CVOA:
    # Shared properties for multi-threading execution
    __recovered = None
    __deaths = None
    __isolated = None
    __bestSolution = None
    __bestSolutionFound = None
    __lock = threading.Lock()

    # Common properties to all strains
    __fitnessFunction = None
    __individualDefinition = None
    __update_isolated = None
    __verbosity = None

    def __init__(self, strain_id, max_time=10, max_spread=5, min_super_spread=6, max_super_spread=15,
                 social_distancing=10, p_isolation=0.7, p_travel=0.1, p_re_infection=0.0014, super_spreader_perc=0.1,
                 death_perc=0.05):

        # Specific properties for each strain.
        self.__strainID = strain_id
        self.__max_time = max_time
        self.__infectedStrain = set()
        self.__superSpreaderStrain = set()
        self.__deathStrain = set()
        self.__time = None
        self.__bestSolutionStrain = Individual()
        self.__bestDeadIndividualStrain = None
        self.__worstSuperSpreaderIndividualStrain = None
        self.__infected_strain_super_spreader_strain = set()

        # Strain parameters
        self.__MAX_SPREAD = max_spread
        self.__MIN_SUPERSPREAD = min_super_spread
        self.__MAX_SUPERSPREAD = max_super_spread
        self.__SOCIAL_DISTANCING = social_distancing
        self.__P_ISOLATION = p_isolation
        self.__P_TRAVEL = p_travel
        self.__P_REINFECTION = p_re_infection
        self.__SUPERSPREADER_PERC = super_spreader_perc
        self.__DEATH_PERC = death_perc

    @staticmethod
    def initialize_pandemic(individual_definition, fitness_function, update_isolated=False):

        CVOA.__recovered = set()
        CVOA.__deaths = set()
        CVOA.__isolated = set()
        CVOA.__bestSolution = Individual(False)
        CVOA.__bestSolutionFound = False

        CVOA.__fitnessFunction = fitness_function
        CVOA.__individualDefinition = individual_definition
        CVOA.__update_isolated = update_isolated

    @staticmethod
    def pandemic_report():
        res = "Best solution = " + str(CVOA.__bestSolution) + "\n"
        res += "Recovered: " + str(len(CVOA.__recovered)) + "\n"
        res += "Death: " + str(len(CVOA.__deaths)) + "\n"
        res += "Isolated: " + str(len(CVOA.__isolated)) + "\n"
        return res

    @staticmethod
    def get_best_solution():
        return CVOA.__bestSolution

    @staticmethod
    def set_verbosity(verbosity):
        CVOA.__verbosity = verbosity

    def get_strain_id(self):
        return self.__strainID

    def cvoa(self):

        epidemic = True

        # Step 1. Infect patient zero (PZ)
        pz = self.__infect_pz()

        # Step 2. Initialize strain: infected and best solution.
        self.__infectedStrain.add(pz)
        self.__bestSolutionStrain = pz
        self.__infected_strain_super_spreader_strain.add(pz)
        CVOA.__verbosity("\nPatient Zero (" + self.__strainID + "): \n" + str(pz))
        self.__worstSuperSpreaderIndividualStrain = Individual(best=True)
        self.__bestDeadIndividualStrain = Individual()

        # Step 3. The main loop for the disease propagation
        self.__time = 0

        # Suggestion: add another stop criterion if bestSolution does not change after X consecutive iterations
        while epidemic and self.__time < self.__max_time and not CVOA.__bestSolutionFound:

            self.__propagate_disease()

            # Stopping criteria
            if not self.__infectedStrain:
                # Stop if no new infected individuals
                epidemic = False
                CVOA.__verbosity("No new infected individuals in " + self.__strainID)
            # elif self.__bestSolutionStrain.fitness == 0.0:
            #     # Stop if best known fitness is found ( or fitness satisfying your requirements)
            #     CVOA.__lock.acquire()
            #     CVOA.__bestSolutionFound = True
            #     CVOA.__lock.release()
            #     CVOA.__verbose print("Best solution (by fitness) found by " + self.__strainID)

            self.__time += 1

        CVOA.__verbosity("\n\n" + self.__strainID + " converged after " + str(self.__time) + " iterations.")
        CVOA.__verbosity("Best individual: " + str(self.__bestSolutionStrain))

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
                n_infected = randint(self.__MIN_SUPERSPREAD, self.__MAX_SUPERSPREAD)
            else:
                n_infected = randint(0, self.__MAX_SUPERSPREAD)

            # 2. Determine the travel distance, which is how far is the new infected individual
            if random() < self.__P_TRAVEL:
                travel_distance = randint(0, len(CVOA.__individualDefinition.get_definition().keys()))
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
                    if random() < self.__P_ISOLATION:
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
        infected = deepcopy(individual)

        infected_variables = sample(list(definition.keys()), travel_distance)
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
            if random() < self.__P_REINFECTION:
                new_infected_population.add(new_infected_individual)
                CVOA.__recovered.remove(new_infected_individual)

    # Update isolated population
    def __update_isolated_population(self, individual):
        if individual not in CVOA.__deaths and individual not in CVOA.__recovered and individual not in CVOA.__isolated:
            CVOA.__isolated.add(individual)

    def __update_death_super_spreader_strain(self):

        # Superspreader and deaths strain sets for each iteration
        number_of_super_spreaders = ceil(self.__SUPERSPREADER_PERC * len(self.__infectedStrain))
        number_of_deaths = ceil(self.__DEATH_PERC * len(self.__infectedStrain))

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
        res += "Max time = " + str(self.__max_time) + "\n"
        res += "Infected strain = " + str(self.__infectedStrain) + "\n"
        res += "Super spreader strain = " + str(self.__superSpreaderStrain) + "\n"
        res += "Death strain = " + str(self.__deathStrain) + "\n"
        res += "MAX_SPREAD = " + str(self.__MAX_SPREAD) + "\n"
        res += "MIN_SUPERSPREAD = " + str(self.__MIN_SUPERSPREAD) + "\n"
        res += "MAX_SUPERSPREAD = " + str(self.__MAX_SUPERSPREAD) + "\n"
        res += "SOCIAL_DISTANCING = " + str(self.__SOCIAL_DISTANCING) + "\n"
        res += "P_ISOLATION = " + str(self.__P_ISOLATION) + "\n"
        res += "P_TRAVEL = " + str(self.__P_TRAVEL) + "\n"
        res += "P_REINFECTION = " + str(self.__P_REINFECTION) + "\n"
        res += "SUPERSPREADER_PERC = " + str(self.__SUPERSPREADER_PERC) + "\n"
        res += "DEATH_PERC = " + str(self.__DEATH_PERC) + "\n"
        return res


def cvoa_launcher(strains, verbose=True):
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
