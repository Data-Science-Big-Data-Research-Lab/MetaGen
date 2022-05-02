import copy
import math
import random

from pycvoa.problem import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR
from pycvoa.problem.solution import Solution


def build_random_solution(domain, fitness_function=None):
    """ It builds a random solution using a domain and a fitness function (i.e. a problem definition).

    :param domain: The domain of the problem to build the solution.
    :type domain: :py:class:`~pycvoa.problem.domain.Domain`
    :param fitness_function: The fitness function to evaluate the solution, defaults to None.
    :type fitness_function: function
    :returns: A randomly built solution.
    :rtype: :py:class:`~pycvoa.problem.solution.Solution`
    """

    # Build a void solution.
    new_solution = Solution()

    # For each variable defined in the domain:
    for variable in domain.get_variable_list():

        variable_type = domain.get_variable_type(variable)
        variable_definition = domain.get_variable_definition(variable)

        # If the variable is INTEGER, REAL or CATEGORICAL, set it with a random value
        # using the get_random_value_for_simple_variable auxiliary method.
        if variable_type in (INTEGER, REAL, CATEGORICAL):
            new_solution.set_basic(variable, get_random_value_for_basic_variable(variable_definition))

        # If the variable is LAYER, iterate over its elements and set them with a random value
        # using the get_random_value_for_simple_variable auxiliary method.
        elif variable_type == LAYER:
            for element in domain.get_element_list(variable_type):
                element_definition = domain.get_element_definition(variable, element)
                new_solution.set_element(variable, element,
                                         get_random_value_for_basic_variable(element_definition))

        # If the variable is VECTOR:
        elif variable_type == VECTOR:

            # Get a random size using the get_number_from_interval auxiliary method.
            vector_size = get_number_from_interval(variable_definition[1], variable_definition[2],
                                                   variable_definition[3])
            vector_component_type = domain.get_vector_components_type(variable)
            vector_component_definition = domain.get_vector_component_definition(variable)

            # For each element of the vector:
            for i in range(0, vector_size):

                # If the vector type is INTEGER, REAL or CATEGORICAL,
                # add a random value (using the get_random_value_for_simple_variable auxiliary method)
                # to the current element.
                if vector_component_type in (INTEGER, REAL, CATEGORICAL):
                    new_solution.add_basic_component(variable,
                                                     get_random_value_for_basic_variable(vector_component_definition))

                # If the vector type is LAYER,
                # build a random value for each element of the layer (using the
                # get_random_value_for_simple_variable auxiliary method) and add it to the current element.
                elif vector_component_type == LAYER:
                    for element in domain.get_component_element_list(variable):
                        element_definition = domain.get_component_element_definition(element)
                        new_solution.set_component_element(variable, i, element,
                                                           get_random_value_for_basic_variable(
                                                                           element_definition))

    # If the fitness function has been passed, it is computed for the new solution.
    if fitness_function is not None:
        new_solution.fitness = fitness_function(new_solution)

    return new_solution


def alter_solution(solution, variable, definition):
    """ It yields a change into a solution variable value.

    :param solution: Solution to be changed.
    :param variable: Variable from the solution to be changed.
    :param definition: Definition of the variable from the solution to be changed.
    :type solution: :py:class:`~pycvoa.problem.solution.Solution`
    :type variable: str
    :type definition: Internal :py:class:`~pycvoa.domain.Domain` structure
    """
    # logging.debug("alter_solution")

    # If variable is an INTEGER or REAL apply alter_simple_variable
    if definition[0] is INTEGER or definition[0] is REAL or definition[0] == CATEGORICAL:
        alter_basic_variable(solution, variable, definition)

    # If variable is a LAYER
    elif definition[0] == LAYER:

        # Get the layer definition and select the elements of the layer to be changed
        layer_definition = definition[1]
        n_changed_elements = random.randint(1, len(layer_definition))
        selected_elements = random.sample(list(layer_definition.keys()), n_changed_elements)

        # For each selected element of the layer
        for element_name in selected_elements:

            # logging.debug("Changing %s.%s", variable, element_name)
            element_definition = layer_definition[element_name]

            # If the element is an INTEGER or REAL set it with modify_number_from_interval_random_way
            if element_definition[0] is INTEGER or element_definition[0] is REAL:
                solution.set_element(variable, element_name,
                                     modify_number_from_interval_random_way(
                                                     solution.get_element_value(variable, element_name),
                                                     element_definition[1], element_definition[2],
                                                     element_definition[3]))

            # If the element is an CATEGORICAL set it another random label
            elif element_definition[0] == CATEGORICAL:
                current_category = solution.get_element_value(variable, element_name)
                new_category = get_random_element_from_list_excluding_one(current_category, element_definition[1])
                solution.set_element(variable, element_name, new_category)

    # If variable is a VECTOR
    elif definition[0] == VECTOR:

        # Select an action out of three: resizing (1), changing (2) and resizing and changing (3)
        action = random.choice([1, 2, 3])
        # logging.debug(">>>> INPUT: %s", infected.get_variable_value(variable))

        # If the action is resizing, resize the vector with resize_vector_variable
        if action == 1:
            # logging.debug("Resizing")
            resize_vector_variable(solution, variable, definition)

        # If the action is changing, change the vector with change_vector_variable
        elif action == 2:
            # logging.debug("Changing")
            alter_vector_variable(solution, variable, definition)

        # If the action is resizing and changing, resize the vector with resize_vector_variable
        # and change the vector with change_vector_variable
        else:
            # logging.debug("Resizing and changing")
            resize_vector_variable(solution, variable, definition)
            # logging.debug("Resized: %s", infected.get_variable_value(variable))
            alter_vector_variable(solution, variable, definition)

        # logging.debug(">>>> OUTPUT: %s", infected.get_variable_value(variable))


def alter_basic_variable(solution, variable, definition):
    """ It yields a change in a **BASIC** variable of a solution.

    :param solution: Solution to be changed.
    :param variable: Variable from the solution to be changed.
    :param definition: Definition of the variable from the solution to be changed.
    :type solution: :py:class:`~pycvoa.problem.solution.Solution`
    :type variable: str
    :type definition: Internal :py:class:`~pycvoa.domain.Domain` structure
    """

    # If the variable is INTEGER or REAL set the variable with modify_number_from_interval_random_way.
    if definition[0] is INTEGER or definition[0] is REAL:
        solution.set_basic(variable,
                           modify_number_from_interval_random_way(solution.get_basic_value(variable),
                                                                           definition[1], definition[2],

                                                                           definition[3]))

    # If the variable is CATEGORICAL set the current category with another randomly selected one.
    elif definition[0] == CATEGORICAL:
        current_category = solution.get_basic_value(variable)
        new_category = get_random_element_from_list_excluding_one(current_category, definition[1])
        solution.set_basic(variable, new_category)


def alter_vector_variable(solution, variable, definition):
    """ It yields a change in a **VECTOR** variable of a solution.

    :param solution: Solution to be changed.
    :param variable: Variable from the solution to be changed.
    :param definition: Definition of the variable from the solution to be changed.
    :type solution: :py:class:`~pycvoa.problem.solution.Solution`
    :type variable: str
    :type definition: Internal :py:class:`~pycvoa.domain.Domain` structure
    """

    # Get a list of positions of the vector to be changed randomly
    current_size = solution.get_vector_size(variable)
    number_of_changes = random.randint(1, current_size)
    index_to_change = random.sample(list(range(0, current_size)), number_of_changes)
    vector_element_definition = definition[4]

    # For each position
    for i in index_to_change:

        # logging.debug("[%s] vector_element_definition = %s", i, str(vector_element_definition))

        # If it is a vector of integer or real modify the value with modify_number_from_interval_random_way
        if vector_element_definition[0] is INTEGER or vector_element_definition[0] is REAL:
            solution.set_basic_component(variable,
                                         i, modify_number_from_interval_random_way(
                    solution.get_basic_component_value(variable, i),
                    vector_element_definition[1], vector_element_definition[2],
                    vector_element_definition[3]))

        # If it is a vector of categorical modify the value with a new label randomly selected
        elif vector_element_definition[0] is CATEGORICAL:
            # logging.debug("CAT")
            current_category = solution.get_basic_component_value(variable, i)
            new_category = get_random_element_from_list_excluding_one(current_category, vector_element_definition[1])
            solution.set_basic_component(variable, i, new_category)

        # If it is a vector of layer
        elif vector_element_definition[0] == LAYER:
            # logging.debug("LAYER")

            # Select a random set of elements of the layer to be changed
            layer_definition = vector_element_definition[1]
            n_changed_elements = random.randint(1, len(layer_definition))
            selected_elements = random.sample(list(layer_definition.keys()), n_changed_elements)

            # For each selected element
            for element_name in selected_elements:
                layer_element_definition = layer_definition[element_name]

                # If that element is an integer or a real modify its value with modify_number_from_interval_random_way
                if layer_element_definition[0] is INTEGER or layer_element_definition[0] is REAL:
                    solution.set_component_element(variable, i, element_name,
                                                   modify_number_from_interval_random_way(
                                                                   solution.get_layer_component_value(
                                                                       variable, i,
                                                                       element_name),
                                                                   layer_element_definition[1],
                                                                   layer_element_definition[2],
                                                                   layer_element_definition[3]))

                # If that element is a categorical one modify its value with a new label randomly selected
                elif layer_element_definition[0] == CATEGORICAL:
                    current_category = solution.get_layer_component_value(variable, i, element_name)
                    new_category = get_random_element_from_list_excluding_one(current_category,
                                                                              layer_element_definition[1])
                    solution.set_component_element(variable, i, element_name, new_category)


def get_random_element_from_list_excluding_one(excluded_element, list_of_elements):
    """ Get a random element of a list excluding one of them.

    :param excluded_element: The element to exclude.
    :param list_of_elements: The list.
    :type excluded_element: Any
    :type list_of_elements: list
    :returns: A random element of the list excluding one of them.
    :rtype: Any
    """
    categories = set(copy.deepcopy(list_of_elements))
    categories.remove(excluded_element)
    return random.sample(list(categories), 1)[0]


def resize_vector_variable(solution, variable, definition):
    """ Resize a vector variable randomly.

    :param solution: Solution to be changed.
    :param variable: Variable from the solution to be changed.
    :param definition: Definition of the variable from the solution to be changed.
    :type solution: :py:class:`~pycvoa.problem.solution.Solution`
    :type variable: str
    :type definition: Internal :py:class:`~pycvoa.domain.Domain` structure
    """

    # Compute the new size and get the vector definition.
    current_size = solution.get_vector_size(variable)
    new_size = modify_number_from_interval_random_way(current_size, definition[1],
                                                      definition[2], definition[3])
    diff = abs(current_size - new_size)
    vector_element_definition = definition[4]

    # logging.debug("current_size = %s", current_size)
    # logging.debug("new_size = %s", new_size)
    # logging.debug("diff = %s", diff)

    # If the new size is greater than the current one, add new positions:
    if new_size > current_size:

        # For each new position to be added:
        for i in range(0, diff):

            # Select an index randomly
            selected_index = random.randint(0, current_size)
            # logging.debug("add index %s", selected_index)

            # If the vector is defined as a BASIC type use get_random_value_for_simple_variable to yield the new value.
            if vector_element_definition[0] is INTEGER or vector_element_definition[0] is REAL or \
                    vector_element_definition[0] is CATEGORICAL:
                solution.insert_basic_component(variable,
                                                selected_index,
                                                get_random_value_for_basic_variable(
                                                         vector_element_definition))

            # If the vector is defined as a LAYER type, build the internal LAYER structure
            # using get_random_value_for_simple_variable to yield the new elements values.
            elif vector_element_definition[0] == LAYER:
                layer_values = {}
                for element_name, element_definition in vector_element_definition[1].items():
                    layer_values[element_name] = get_random_value_for_basic_variable(element_definition)
                solution.insert_basic_component(variable, selected_index, layer_values)

    # If the new size is lower than the current one, remove its positions randomly:
    elif new_size < current_size:
        for i in range(0, diff):
            current_size = solution.get_vector_size(variable)
            selected_index = random.randint(0, current_size - 1)
            # logging.debug("current_size = %s, remove index = %s", current_size, selected_index)
            solution.delete_component(variable, selected_index)


def modify_number_from_interval_random_way(value, left, right, step_size):
    """ From a value in an interval compute a new random value by adding (to the rigth) or subtracting (to the left)
    a number of steps.

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

    # Compute the maximum steps from the value to the left and to the right.
    left_max_steps = math.floor((value - left) / step_size)
    right_max_steps = math.floor((right - value) / step_size)
    # logging.debug("value = %s, left = %s, right = %s, step_size = %s", value, left, right, step_size)
    # logging.debug("left_max_steps = %s, right_max_steps = %s", left_max_steps, right_max_steps)

    # ** Compute the maximum steps and the way **
    max_steps = 0
    way = 0

    # If there are steps to the left and to the right, set the way randomly, then set the properly maximum steps.
    if left_max_steps > 0 and right_max_steps > 0:
        way = random.randint(0, 1)
        if way == 0:
            max_steps = left_max_steps
        else:
            max_steps = right_max_steps
    # If only there are steps to the right, set the way to 1, then set the properly maximum steps.
    elif left_max_steps <= 0:
        way = 1
        max_steps = right_max_steps
    # If only there are steps to the left, set the way to 0, then set the properly maximum steps.
    elif right_max_steps <= 0:
        way = 0
        max_steps = left_max_steps

    # Compute the number of steps to take.
    step_radio = random.randint(1, int(max_steps))

    # If the way is left, subtract (step_radio * step_size) to the center value.
    # If the way is left, add (step_radio * step_size) to the center value.
    if way == 0:
        res = value - (step_radio * step_size)
    else:
        res = value + (step_radio * step_size)

    # logging.debug("way = %s", way)
    # logging.debug("step_radio = %s", step_radio)
    # logging.debug("max_steps = %s", max_steps)
    # logging.debug("res = %s", res)

    return res


def get_random_value_for_basic_variable(definition):
    """ Get a random value from a variable of type **REAL**, **INTEGER** or **CATEGORICAL**.

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
    """ It divides the interval in several values and return one of them randomly.

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




