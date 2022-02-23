import logging
from copy import *
from math import *
from random import *
from typing import Final

REAL: Final = "real"
INTEGER: Final = "integer"
CATEGORICAL: Final = "categorical"
LAYER: Final = "layer"
VECTOR: Final = "vector"


def inoculate_individual(infected, variable, definition):
    logging.debug("inoculate_individual")
    if definition[0] is INTEGER or definition[0] is REAL or definition[0] == CATEGORICAL:
        inoculate_individual_simple_variable(infected, variable, definition)

    elif definition[0] == LAYER:

        layer_definition = definition[1]
        n_changed_elements = randint(1, len(layer_definition))
        selected_elements = sample(list(layer_definition.keys()), n_changed_elements)

        for element_name in selected_elements:
            logging.debug("Changing %s.%s", variable, element_name)
            element_definition = layer_definition[element_name]
            if element_definition[0] is INTEGER or element_definition[0] is REAL:
                infected.set_layer_element_value(variable, element_name,
                                                 modify_number_from_interval_random_way(
                                                     infected.get_layer_element_value(variable, element_name),
                                                     element_definition[1], element_definition[2],
                                                     element_definition[3]))
            elif element_definition[0] == CATEGORICAL:
                current_category = infected.get_layer_element_value(variable, element_name)
                categories = set(deepcopy(element_definition[1]))
                categories.remove(current_category)
                infected.set_layer_element_value(variable, element_name, sample(list(categories), 1)[0])

    elif definition[0] == VECTOR:
        action = choice([1, 2, 3])
        # action = 2

        logging.debug(">>>> INPUT: %s", infected.get_variable_value(variable))

        if action == 1:
            logging.debug("Resizing")
            resize_vector_variable(infected, variable, definition)
        elif action == 2:
            logging.debug("Changing")
            change_vector_variable(infected, variable, definition)
        else:
            logging.debug("Resizing and changing")
            resize_vector_variable(infected, variable, definition)
            logging.debug("Resized: %s", infected.get_variable_value(variable))
            change_vector_variable(infected, variable, definition)

        logging.debug(">>>> OUTPUT: %s", infected.get_variable_value(variable))


def change_vector_variable(individual, variable, definition):
    current_size = individual.get_vector_size(variable)
    number_of_changes = randint(1, current_size)
    index_to_change = sample(list(range(0, current_size)), number_of_changes)
    vector_element_definition = definition[4]
    for i in index_to_change:
        logging.debug("[%s] vector_element_definition = %s", i, str(vector_element_definition))
        if vector_element_definition[0] is INTEGER or vector_element_definition[0] is REAL:
            individual.set_vector_element_by_index(variable,
                                                   i, modify_number_from_interval_random_way(
                    individual.get_vector_component_value(variable, i),
                    vector_element_definition[1], vector_element_definition[2],
                    vector_element_definition[3]))
        elif vector_element_definition[0] is CATEGORICAL:
            logging.debug("CAT")
            current_category = individual.get_vector_component_value(variable, i)
            categories = set(deepcopy(vector_element_definition[1]))
            categories.remove(current_category)
            individual.set_vector_element_by_index(variable, i, sample(list(categories), 1)[0])
        elif vector_element_definition[0] == LAYER:
            logging.debug("LAYER")
            layer_definition = vector_element_definition[1]
            n_changed_elements = randint(1, len(layer_definition))
            selected_elements = sample(list(layer_definition.keys()), n_changed_elements)
            for element_name in selected_elements:
                layer_element_definition = layer_definition[element_name]
                if layer_element_definition[0] is INTEGER or layer_element_definition[0] is REAL:
                    individual.set_vector_layer_element_by_index(variable, i, element_name,
                                                                 modify_number_from_interval_random_way(
                                                                     individual.get_vector_layer_component_value(
                                                                         variable, i,
                                                                         element_name),
                                                                     layer_element_definition[1],
                                                                     layer_element_definition[2],
                                                                     layer_element_definition[3]))
                elif layer_element_definition[0] == CATEGORICAL:
                    individual.set_vector_layer_element_by_index(variable, i, element_name,
                                                                 sample(layer_element_definition[1], 1)[0])


def resize_vector_variable(individual, variable, definition):
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
            selected_index = randint(0, current_size)
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
            selected_index = randint(0, current_size - 1)
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
        categories = set(deepcopy(definition[1]))
        categories.remove(current_category)
        infected.set_variable_value(variable, sample(list(categories), 1)[0])


# ***********************************************************************
# ********************* Auxiliary methods *******************************
# ***********************************************************************
def modify_number_from_interval_random_way(value, left, right, step_size):
    logging.debug("value = %s, left = %s, right = %s, step_size = %s", value, left, right, step_size)
    left_max_steps = floor((value - left) / step_size)
    right_max_steps = floor((right - value) / step_size)
    logging.debug("left_max_steps = %s, right_max_steps = %s", left_max_steps, right_max_steps)
    max_steps = 0
    way = 0

    if left_max_steps > 0 and right_max_steps > 0:
        way = randint(0, 1)
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

    step_radio = randint(1, int(max_steps))
    logging.debug("step_radio = %s", step_radio)

    if way == 0:
        res = value - (step_radio * step_size)
    else:
        res = value + (step_radio * step_size)

    logging.debug("res = %s", res)

    return res


def get_number_from_interval(left, right, step_size):
    max_steps = floor((right - left) / step_size)
    rstep = randint(0, int(max_steps))
    res = left + (rstep * step_size)
    # print("left = " + str(left) + " right = " + str(right) + " step_size = " + str(step_size) + " max_steps = " +
    # str(max_steps)+" res = " + str(res))
    return res


def get_random_value_for_simple_variable(definition):
    res = 0

    if definition[0] == REAL:
        res = get_number_from_interval(definition[1], definition[2], definition[3])
    elif definition[0] == INTEGER:
        res = randrange(definition[1], definition[2], definition[3])
    elif definition[0] == CATEGORICAL:
        res = sample(definition[1], 1)[0]

    return res


def vector_definition_to_string(variable_name, definition):
    res = "[" + definition[0] + "] " + variable_name + " {Minimum size = " + str(definition[1]) + \
          ", Maximum size = " + str(definition[2]) + ", Step size = " \
          + str(definition[3]) + "}"
    # print("NAME: "+str(definition[4])+" DEF:"+str(self.__definitions[definition[4]]))

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
    res = "[" + definition[0] + "] " + variable_name + " "
    res += "\n"
    cnt = 1
    for k, v in definition[1].items():
        res += "\t" + simple_definition_to_string(k, v)
        if cnt != len(definition[1].items()):
            res += "\n"
        cnt += 1
    return res


def variable_definition_to_string(variable_name, definition):
    res = ""
    if definition[0] is VECTOR:
        res += vector_definition_to_string(variable_name, definition)
    elif definition[0] is LAYER:
        res += layer_definition_to_string(variable_name, definition)
    else:
        res += simple_definition_to_string(variable_name, definition)
    return res


def simple_definition_to_string(variable_name, definition):
    res = "[" + definition[0] + "] " + variable_name + " "
    if definition[0] is not CATEGORICAL:
        res += "{Minimum = " + str(definition[1]) + ", Maximum = " + str(definition[2]) + ", Step = " + str(
            definition[3]) + "}"
    else:
        res += "{Values = " + str(definition[1]) + "}"
    return res
