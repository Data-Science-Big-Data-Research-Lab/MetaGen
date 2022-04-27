import pycvoa.problem.domain


def is_string(variable_element_name):
    if type(variable_element_name) != str:
        raise TypeError("The variable_name/element_name/variable/element parameter must be <str>.")


def is_int(value):
    if type(value) != int:
        raise TypeError("The value parameter must be <int>.")


def is_float(value):
    if type(value) != float:
        raise TypeError("The value parameter must be <float>.")


def is_dict(values):
    if type(values) != dict:
        raise TypeError("The values parameter must be <dict>.")


def is_list(values):
    if type(values) != list:
        raise TypeError("The values parameter must be <list>.")


def are_int(min_value_size, max_value_size, step_size):
    if type(min_value_size) != int:
        raise TypeError("The min_value/min_size parameter must be <int>.")
    if type(max_value_size) != int:
        raise TypeError("The max_value/max_size parameter must be <int>.")
    if type(step_size) != int:
        raise TypeError("The step/step_size parameter must be <int>.")


def are_float(min_value, max_value, step):
    if type(min_value) != float:
        raise TypeError("The min_value parameter must be <float>.")
    if type(max_value) != float:
        raise TypeError("The max_value parameter must be <float>.")
    if type(step) != float:
        raise TypeError("The step parameter must be <float>.")


def are_dict(values):
    for e in values:
        if type(e) != dict:
            raise TypeError("The " + values.index(e) + "-nh value must be <dict>.")


def is_list_of_dict(values):
    is_list(values)
    are_dict(values)


def same_python_type(categories, value):
    categories_type = type(categories[0])
    if type(value) != categories_type:
        raise TypeError(
            "The value parameter be the same Python type than categories (" + str(categories_type) + ").")


def list_all_int_float_str(categories):
    if len(categories) < 2:
        raise TypeError("The categories parameter must have al least two elements.")
    for el in categories:
        if type(el) not in (int, float, str):
            raise TypeError(
                "The " + str(categories.index(
                    el)) + "-nh element of the categories parameter must be <int>, <float> or <str>.")
        categories_type = type(categories[0])
        if type(el) != categories_type:
            raise TypeError(
                "All the elements of the categories parameter must have the same type (<int>, <float> or <str>).")


def is_domain_class(domain):
    if domain is not None:
        if type(domain) is not pycvoa.problem.domain.Domain:
            raise TypeError("The " + domain + " parameter is not instantiate from <Domain> class.")


def element_is_none(variable, element):
    if element is not None:
        raise ValueError(
            "The variable/component type of " + variable + " is BASIC, therefore, the element must not "
                                                           "be provided.")


def element_not_none(variable, element_index):
    if element_index is None:
        raise ValueError(
            "The variable/component type of " + variable + " is LAYER, therefore, the element must "
                                                           "be provided.")


def index_is_none(variable, index):
    if index is not None:
        raise ValueError(
            "The " + variable + "variable is not defined as VECTOR, therefore, an index must not be provided.")


def index_not_none(variable, index):
    if index is None:
        raise ValueError(
            "The " + variable + "variable is defined as VECTOR, therefore an index to access a component name "
                                "must be provided.")


def are_index_element_none(layer_vector_variable, index, element):
    index_is_none(layer_vector_variable, index)
    element_is_none(layer_vector_variable, element)
