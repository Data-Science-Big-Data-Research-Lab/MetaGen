from random import randint

from src.pycvoa import ProblemDefinition

"""
Example problem: (x-15)^2 
"""
x_minus_15_raised_to_2_definition = ProblemDefinition()
x_minus_15_raised_to_2_definition.register_real_variable("x", 0.0, 100.0, 0.05)


def x_minus_15_raised_to_2_fitness(individual):
    x = individual.get_variable_value("x")
    return pow(x - 15, 2)


"""
Example problem: x^2 
"""
x_raised_to_2_definition = ProblemDefinition()
x_raised_to_2_definition.register_real_variable("x", 0.0, 100.0, 0.05)


def x_raised_to_2_fitness(individual):
    x = individual.get_variable_value("x")
    return pow(x, 2)


"""
Example problem: categorical
"""
categorical_example_definition = ProblemDefinition()
categorical_example_definition.register_categorical_variable("c", ["level1", "level2", "level3", "level5"])


def categorical_example_fitness(individual):
    level = individual.get_variable_value("c")
    if level == "level1":
        val = randint(0, 10)
    elif level == "level2":
        val = randint(0, 20)
    elif level == "level3":
        val = randint(0, 30)
    else:
        val = randint(0, 50)

    return val


"""
Example problem: sum of the elements of a vector
"""
vector_example_definition = ProblemDefinition()
vector_example_definition.register_vector_variable("v", 2, 20, 1)
vector_example_definition.set_vector_component_to_integer("v", 1, 20, 1)


def vector_example_fitness(individual):
    v = individual.get_variable_value("v")
    return sum(v)


"""
Example problem: defining a single problem with all types of variables.
"""
all_types_definition = ProblemDefinition()

all_types_definition.register_integer_variable("I", 1, 10, 1)
all_types_definition.register_real_variable("R", 0.0, 5.0, 0.01)
all_types_definition.register_categorical_variable("C", ["Label1", "Label2", "Label3"])

all_types_definition.register_layer_variable("L")
all_types_definition.insert_layer_integer("L", "CompI", 25, 300, 20)
all_types_definition.insert_layer_real("L", "CompR", 0.25, 4.5, 0.05)
all_types_definition.insert_layer_categorical("L", "CompC", ["F1", "F2", "F3", "F4"])

all_types_definition.register_vector_variable("VI", 1, 5, 2)
all_types_definition.set_vector_component_to_integer("VI", 200, 1000, 50)

all_types_definition.register_vector_variable("VR", 5, 40, 4)
all_types_definition.set_vector_component_to_real("VR", 5.2, 20.0, 0.1)

all_types_definition.register_vector_variable("VC", 4, 8, 1)
all_types_definition.set_vector_component_to_categorical("VC", ["A", "B", "C"])

all_types_definition.register_vector_variable("VL", 2, 8, 2)
all_types_definition.set_vector_component_to_layer("VL")
all_types_definition.insert_integer_in_vector_layer_component("VL", "ElCompI", 1, 4, 1)
all_types_definition.insert_real_in_vector_layer_component("VL", "ElCompR", 0.001, 0.1, 0.0001)
all_types_definition.insert_categorical_in_vector_layer_component("VL", "ElCompC", ["Cat1", "Cat2", "Cat3",
                                                                                    "Cat4", "Cat5"])


def all_types_fitness(individual):
    c = individual.get_variable_value("C")
    r = individual.get_variable_value("R")
    i = individual.get_variable_value("I")

    lc = individual.get_layer_element_value("L", "LC")
    lr = individual.get_layer_element_value("L", "LR")
    li = individual.get_layer_element_value("L", "LI")

    vi_size = individual.get_vector_size("VI")
    vi0 = individual.get_vector_component_value("VI", 0)

    vr_size = individual.get_vector_size("VR")
    vr0 = individual.get_vector_component_value("VR", 0)

    vc_size = individual.get_vector_size("VC")
    vc0 = individual.get_vector_component_value("VC", 0)

    vl_size = individual.get_vector_size("VL")
    vl0_vl1 = individual.get_vector_layer_component_value("VL", 0, "vl1")
    vl0_vl2 = individual.get_vector_layer_component_value("VL", 0, "vl2")
    vl0_vl3 = individual.get_vector_layer_component_value("VL", 0, "vl3")

    return r + 2
