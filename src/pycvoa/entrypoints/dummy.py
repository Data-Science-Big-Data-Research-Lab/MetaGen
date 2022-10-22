import random
from pycvoa.problem.domain import Domain


# Dummy categorical problem definition
categorical_example_definition = Domain()
categorical_example_definition.define_categorical("c", ["level1", "level2", "level3", "level5"])


# Dummy categorical fitness function
def categorical_example_fitness(individual):
    level = individual.get_basic_value("c")
    if level == "level1":
        val = random.randint(0, 10)
    elif level == "level2":
        val = random.randint(0, 20)
    elif level == "level3":
        val = random.randint(0, 30)
    else:
        val = random.randint(0, 50)

    return val


# Dummy vector problem definition
vector_example_definition = Domain()
vector_example_definition.define_vector("v", 2, 20, 1)
vector_example_definition.define_components_as_integer("v", 1, 20, 1)


# Dummy vector fitness function
def vector_example_fitness(individual):
    v = individual.get_basic_value("v")
    return sum(v)


# Dummy all types problem definition
all_types_definition = Domain()
all_types_definition.define_integer("I", 1, 10, 1)
all_types_definition.define_real("R", 0.0, 5.0, 0.01)
all_types_definition.define_categorical("C", ["Label1", "Label2", "Label3"])
all_types_definition.define_layer("L")
all_types_definition.define_integer_element("L", "CompI", 25, 300, 20)
all_types_definition.define_real_element("L", "CompR", 0.25, 4.5, 0.05)
all_types_definition.define_categorical_element("L", "CompC", ["F1", "F2", "F3", "F4"])
all_types_definition.define_vector("VI", 1, 5, 2)
all_types_definition.define_components_as_integer("VI", 200, 1000, 50)
all_types_definition.define_vector("VR", 5, 40, 4)
all_types_definition.define_components_as_real("VR", 5.2, 20.0, 0.1)
all_types_definition.define_vector("VC", 4, 8, 1)
all_types_definition.define_components_as_categorical("VC", ["A", "B", "C"])
all_types_definition.define_vector("VL", 2, 8, 2)
all_types_definition.define_components_as_layer("VL")
all_types_definition.define_layer_vector_integer_element("VL", "ElCompI", 1, 4, 1)
all_types_definition.define_layer_vector_real_element("VL", "ElCompR", 0.001, 0.1, 0.0001)
all_types_definition.define_layer_vector_categorical_element("VL", "ElCompC", ["Cat1", "Cat2", "Cat3",
                                                                                    "Cat4", "Cat5"])


# Dummy all types fitness function
def all_types_fitness(individual):
    c = individual.get_basic_value("C")
    r = individual.get_basic_value("R")
    i = individual.get_basic_value("I")
    lc = individual.get_element_value("L", "LC")
    lr = individual.get_element_value("L", "LR")
    li = individual.get_element_value("L", "LI")
    vi_size = individual.get_vector_size("VI")
    vi0 = individual.get_basic_component_value("VI", 0)
    vr_size = individual.get_vector_size("VR")
    vr0 = individual.get_basic_component_value("VR", 0)
    vc_size = individual.get_vector_size("VC")
    vc0 = individual.get_basic_component_value("VC", 0)
    vl_size = individual.get_vector_size("VL")
    vl0_vl1 = individual.get_layer_component_element("VL", 0, "vl1")
    vl0_vl2 = individual.get_layer_component_element("VL", 0, "vl2")
    vl0_vl3 = individual.get_layer_component_element("VL", 0, "vl3")
    return r + 2
