import logging
import copy
import random
import math
from pycvoa import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR
from pycvoa.individual import Individual


def build_random_individual(problem_definition, fitness_function=None):
    """ It builds a random individual using a problem definition. If the fitness function has been passed,
    it is computed for the new individual.

    :param problem_definition: The problem definition to build the individual.
    :type problem_definition: :py:class:`~pycvoa.definition.ProblemDefinition`
    :param fitness_function: The fitness function to evaluate the individual, defaults to None.
    :type fitness_function: function
    :returns: A randomly built individual.
    :rtype: :py:class:`~pycvoa.individual.Individual`
    """

    # Build a void individual.
    new_individual = Individual()

    # For each variable on the problem definition:
    for variable, definition in problem_definition.get_definition_variables():

        # If the variable is INTEGER, REAL or CATEGORICAL, set it with a random value
        # using the get_random_value_for_simple_variable auxiliary method.
        if definition[0] is INTEGER or definition[0] is REAL or definition[0] is CATEGORICAL:
            new_individual.set_variable_value(variable, get_random_value_for_simple_variable(definition))

        # If the variable is LAYER, iterate over its elements and set them with a random value
        # using the get_random_value_for_simple_variable auxiliary method.
        elif definition[0] == LAYER:
            for element_name, element_definition in definition[1].items():
                new_individual.set_layer_element_value(variable, element_name,
                                                       get_random_value_for_simple_variable(element_definition))

        # If the variable is VECTOR:
        elif definition[0] == VECTOR:

            # Get a random size using the get_number_from_interval auxiliary method.
            vector_size = get_number_from_interval(definition[1], definition[2], definition[3])
            vector_component_type = definition[4]

            # For each element of the vector:
            for i in range(0, vector_size):

                # If the vector type is INTEGER, REAL or CATEGORICAL,
                # add a random value (using the get_random_value_for_simple_variable auxiliary method)
                # to the current element.
                if vector_component_type[0] is INTEGER or vector_component_type[0] is REAL or \
                        vector_component_type[0] is CATEGORICAL:

                    value = get_random_value_for_simple_variable(vector_component_type)
                    new_individual.add_vector_element(variable, value)

                # If the vector type is LAYER,
                # build a random value for each element of the layer (using the
                # get_random_value_for_simple_variable auxiliary method) and add it to the current element.
                elif vector_component_type[0] is LAYER:
                    layer_values = {}
                    for element_name, element_definition in vector_component_type[1].items():
                        layer_values[element_name] = get_random_value_for_simple_variable(element_definition)
                    new_individual.add_vector_element(variable, layer_values)

    # If the fitness function has been passed, it is computed for the new individual.
    if fitness_function is not None:
        new_individual.fitness = fitness_function(new_individual)

    return new_individual


def inoculate_individual(infected, variable, definition):
    """ Inoculate a change into an individual variable.

    :param infected: Individual to be changed.
    :param variable: Variable from the individual to be changed.
    :param definition: Internal definition of the variable from the individual to be changed.
    :type infected: :py:class:`~individual.Individual`
    :type variable: str
    :type definition: list
    """
    logging.debug("inoculate_individual")

    # If variable is an INTEGER or REAL apply inoculate_individual_simple_variable
    if definition[0] is INTEGER or definition[0] is REAL or definition[0] == CATEGORICAL:
        inoculate_individual_simple_variable(infected, variable, definition)

    # If variable is a LAYER
    elif definition[0] == LAYER:

        # Get the layer definition and select the elements of the layer to be changed
        layer_definition = definition[1]
        n_changed_elements = random.randint(1, len(layer_definition))
        selected_elements = random.sample(list(layer_definition.keys()), n_changed_elements)

        # For each selected element of the layer
        for element_name in selected_elements:

            logging.debug("Changing %s.%s", variable, element_name)
            element_definition = layer_definition[element_name]

            # If the element is an INTEGER or REAL set it with modify_number_from_interval_random_way
            if element_definition[0] is INTEGER or element_definition[0] is REAL:
                infected.set_layer_element_value(variable, element_name,
                                                 modify_number_from_interval_random_way(
                                                     infected.get_layer_element_value(variable, element_name),
                                                     element_definition[1], element_definition[2],
                                                     element_definition[3]))

            # If the element is an CATEGORICAL set it another random label
            elif element_definition[0] == CATEGORICAL:
                current_category = infected.get_layer_element_value(variable, element_name)
                categories = set(copy.deepcopy(element_definition[1]))
                categories.remove(current_category)
                infected.set_layer_element_value(variable, element_name, random.sample(list(categories), 1)[0])

    # If variable is a VECTOR
    elif definition[0] == VECTOR:

        # Select an action out of three: resizing (1), changing (2) and resizing and changing (3)
        action = random.choice([1, 2, 3])
        logging.debug(">>>> INPUT: %s", infected.get_variable_value(variable))

        # If the action is resizing, resize the vector with resize_vector_variable
        if action == 1:
            logging.debug("Resizing")
            resize_vector_variable(infected, variable, definition)

        # If the action is changing, change the vector with change_vector_variable
        elif action == 2:
            logging.debug("Changing")
            change_vector_variable(infected, variable, definition)

        # If the action is resizing and changing, resize the vector with resize_vector_variable
        # and change the vector with change_vector_variable
        else:
            logging.debug("Resizing and changing")
            resize_vector_variable(infected, variable, definition)
            logging.debug("Resized: %s", infected.get_variable_value(variable))
            change_vector_variable(infected, variable, definition)

        logging.debug(">>>> OUTPUT: %s", infected.get_variable_value(variable))


def change_vector_variable(individual, variable, definition):
    """ Change the values of a vector variable.

    :param individual: Individual to be changed.
    :param variable: Variable (type VECTOR) from the individual to be changed.
    :param definition: Definition of the variable from the individual to be changed.
    :type individual: :py:class:`~individual.Individual`
    :type variable: str
    :type definition: list
    """

    # Get a list of positions of the vector to be changed randomly
    current_size = individual.get_vector_size(variable)
    number_of_changes = random.randint(1, current_size)
    index_to_change = random.sample(list(range(0, current_size)), number_of_changes)
    vector_element_definition = definition[4]

    # For each position
    for i in index_to_change:

        logging.debug("[%s] vector_element_definition = %s", i, str(vector_element_definition))

        # If it is a vector of integer or real modify the value with modify_number_from_interval_random_way
        if vector_element_definition[0] is INTEGER or vector_element_definition[0] is REAL:
            individual.set_vector_element_by_index(variable,
                                                   i, modify_number_from_interval_random_way(
                    individual.get_vector_component_value(variable, i),
                    vector_element_definition[1], vector_element_definition[2],
                    vector_element_definition[3]))

        # If it is a vector of categorical modify the value with a new label randomly selected
        elif vector_element_definition[0] is CATEGORICAL:
            logging.debug("CAT")
            current_category = individual.get_vector_component_value(variable, i)
            categories = set(copy.deepcopy(vector_element_definition[1]))
            categories.remove(current_category)
            individual.set_vector_element_by_index(variable, i, random.sample(list(categories), 1)[0])

        # If it is a vector of layer
        elif vector_element_definition[0] == LAYER:
            logging.debug("LAYER")

            # Select a random set of elements of the layer to be changed
            layer_definition = vector_element_definition[1]
            n_changed_elements = random.randint(1, len(layer_definition))
            selected_elements = random.sample(list(layer_definition.keys()), n_changed_elements)

            # For each selected element
            for element_name in selected_elements:
                layer_element_definition = layer_definition[element_name]

                # If that element is an integer or a real modify its value with modify_number_from_interval_random_way
                if layer_element_definition[0] is INTEGER or layer_element_definition[0] is REAL:
                    individual.set_vector_layer_element_by_index(variable, i, element_name,
                                                                 modify_number_from_interval_random_way(
                                                                     individual.get_vector_layer_component_value(
                                                                         variable, i,
                                                                         element_name),
                                                                     layer_element_definition[1],
                                                                     layer_element_definition[2],
                                                                     layer_element_definition[3]))

                # If that element is a categorical one modify its value with a new label randomly selected
                elif layer_element_definition[0] == CATEGORICAL:
                    individual.set_vector_layer_element_by_index(variable, i, element_name,
                                                                 random.sample(layer_element_definition[1], 1)[0])


def resize_vector_variable(individual, variable, definition):
    """ Resize a vector variable.

    :param individual: Individual to be changed.
    :param variable: Variable (type VECTOR) from the individual to be changed.
    :param definition: Definition of the variable from the individual to be changed.
    :type individual: :py:class:`~individual.Individual`
    :type variable: str
    :type definition: list
    """
    current_size = individual.get_vector_size(variable)

    new_size = modify_number_from_interval_random_way(current_size, definition[1],
                                                      definition[2], definition[3])
    diff = abs(current_size - new_size)

    logging.debug("current_size = %s", current_size)
    logging.debug("new_size = %s", new_size)
    logging.debug("diff = %s", diff)

    vector_element_definition = definition[4]

    if new_size > current_size:
        for i in range(0, diff):
            selected_index = random.randint(0, current_size)
            logging.debug("add index %s", selected_index)
            if vector_element_definition[0] is INTEGER or vector_element_definition[0] is REAL or \
                    vector_element_definition[0] is CATEGORICAL:
                individual.add_vector_element_by_index(variable,
                                                       selected_index,
                                                       get_random_value_for_simple_variable(
                                                           vector_element_definition))

            elif vector_element_definition[0] == LAYER:
                layer_values = {}
                for element_name, element_definition in vector_element_definition[1].items():
                    layer_values[element_name] = get_random_value_for_simple_variable(element_definition)
                individual.add_vector_element_by_index(variable, selected_index, layer_values)

    elif new_size < current_size:
        for i in range(0, diff):
            current_size = individual.get_vector_size(variable)
            selected_index = random.randint(0, current_size - 1)
            logging.debug("current_size = %s, remove index = %s", current_size, selected_index)
            individual.remove_vector_element_by_index(variable, selected_index)


def inoculate_individual_simple_variable(infected, variable, definition):
    if definition[0] is INTEGER or definition[0] is REAL:
        infected.set_variable_value(variable,
                                    modify_number_from_interval_random_way(infected.get_variable_value(variable),
                                                                           definition[1], definition[2],
                                                                           definition[3]))
    elif definition[0] == CATEGORICAL:
        current_category = infected.get_variable_value(variable)
        categories = set(copy.deepcopy(definition[1]))
        categories.remove(current_category)
        infected.set_variable_value(variable, random.sample(list(categories), 1)[0])


def modify_number_from_interval_random_way(value, left, right, step_size):
    """ Compute a random value from a given interval centered in the input value.

    :param value: Value to be changed.
    :param left: Left value of the interval.
    :param right: Right value of the interval.
    :param step_size: Step size of the interval.
    :type value: int, float
    :type left: int, float
    :type right: int, float
    :type step_size: int, float
    :returns: A random value.
    :rtype: int, float
    """
    logging.debug("value = %s, left = %s, right = %s, step_size = %s", value, left, right, step_size)
    left_max_steps = math.floor((value - left) / step_size)
    right_max_steps = math.floor((right - value) / step_size)
    logging.debug("left_max_steps = %s, right_max_steps = %s", left_max_steps, right_max_steps)
    max_steps = 0
    way = 0

    if left_max_steps > 0 and right_max_steps > 0:
        way = random.randint(0, 1)
        if way == 0:
            max_steps = left_max_steps
        else:
            max_steps = right_max_steps
    elif left_max_steps <= 0:
        way = 1
        max_steps = right_max_steps
    elif right_max_steps <= 0:
        way = 0
        max_steps = left_max_steps

    logging.debug("way = %s", way)
    logging.debug("max_steps = %s", max_steps)

    step_radio = random.randint(1, int(max_steps))
    logging.debug("step_radio = %s", step_radio)

    if way == 0:
        res = value - (step_radio * step_size)
    else:
        res = value + (step_radio * step_size)

    logging.debug("res = %s", res)

    return res


def get_random_value_for_simple_variable(definition):
    """ Get a random value from a variable of type REAL, INTEGER OR CATEGORICAL.

    :param definition: Definition of the variable
    :type definition: list
    :returns: A random value.
    :rtype: int, float, str
    """
    res = 0
    if definition[0] == REAL:
        res = get_number_from_interval(definition[1], definition[2], definition[3])
    elif definition[0] == INTEGER:
        res = random.randrange(definition[1], definition[2], definition[3])
    elif definition[0] == CATEGORICAL:
        res = random.sample(definition[1], 1)[0]

    return res


def get_number_from_interval(left, right, step_size):
    """ Compute a random value from a given interval.

    :param left: Left value of the interval.
    :param right: Right value of the interval.
    :param step_size: Step size of the interval.
    :type left: float
    :type right: float
    :type step_size: float
    :returns: A random value.
    :rtype: float
    """
    max_steps = math.floor((right - left) / step_size)
    random_step = random.randint(0, int(max_steps))
    res = left + (random_step * step_size)
    return res


def variable_definition_to_string(variable_name, definition):
    """ Get a string representation of a variable.

    :param variable_name: Variable name.
    :param definition: Definition of the variable.
    :type variable_name: str
    :type definition: list
    :returns: A string representation of the input variable.
    :rtype: str
    """
    res = ""
    if definition[0] is VECTOR:
        res += vector_definition_to_string(variable_name, definition)
    elif definition[0] is LAYER:
        res += layer_definition_to_string(variable_name, definition)
    else:
        res += simple_definition_to_string(variable_name, definition)
    return res


def vector_definition_to_string(variable_name, definition):
    """ Get a string representation of a VECTOR variable.

    :param variable_name: Variable name.
    :param definition: Definition of the variable.
    :type variable_name: str
    :type definition: list
    :returns: A string representation of the input VECTOR variable.
    :rtype: str
    """
    res = "[" + definition[0] + "] " + variable_name + " {Minimum size = " + str(definition[1]) + \
          ", Maximum size = " + str(definition[2]) + ", Step size = " \
          + str(definition[3]) + "}"

    component_definition = definition[4]

    res += "  Component definition: [" + str(component_definition[0]) + "] "

    if component_definition[0] is INTEGER or component_definition[0] is REAL:
        res += "{Minimum = " + str(component_definition[1]) + ", Maximum = " + str(component_definition[2]) \
               + ", Step = " + str(
            component_definition[3]) + "}"
    elif component_definition[0] is CATEGORICAL:
        res += "{Values = " + str(component_definition[1]) + "}"
    elif component_definition[0] is LAYER:
        layer_definition = component_definition[1]
        res += "\n"
        cnt = 1
        for k, v in layer_definition.items():
            res += "\t" + simple_definition_to_string(k, v)
            if cnt != len(layer_definition.items()):
                res += "\n"
            cnt += 1
    return res


def layer_definition_to_string(variable_name, definition):
    """ Get a string representation of a LAYER variable.

    :param variable_name: Variable name.
    :param definition: Definition of the variable.
    :type variable_name: str
    :type definition: list
    :returns: A string representation of the input LAYER variable.
    :rtype: str
    """
    res = "[" + definition[0] + "] " + variable_name + " "
    res += "\n"
    cnt = 1
    for k, v in definition[1].items():
        res += "\t" + simple_definition_to_string(k, v)
        if cnt != len(definition[1].items()):
            res += "\n"
        cnt += 1
    return res


def simple_definition_to_string(variable_name, definition):
    """ Get a string representation of a REAL, INTEGER or CATEGORICAL variable.

    :param variable_name: Variable name.
    :param definition: Definition of the variable.
    :type variable_name: str
    :type definition: list
    :returns: A string representation of the input REAL, INTEGER or CATEGORICAL variable.
    :rtype: str
    """
    res = "[" + definition[0] + "] " + variable_name + " "
    if definition[0] is not CATEGORICAL:
        res += "{Minimum = " + str(definition[1]) + ", Maximum = " + str(definition[2]) + ", Step = " + str(
            definition[3]) + "}"
    else:
        res += "{Values = " + str(definition[1]) + "}"
    return res
