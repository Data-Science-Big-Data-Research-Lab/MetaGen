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
import random

from metagen.framework import Domain

# Dummy categorical problem definition
categorical_example_definition = Domain()
categorical_example_definition.define_categorical(
    "c", ["level1", "level2", "level3", "level5"])


# Dummy categorical fitness function
def categorical_example_fitness(individual):
    level = individual["c"]
    if level == "level1":
        val = random.randint(0, 10)
    elif level == "level2":
        val = random.randint(10, 20)
    elif level == "level3":
        val = random.randint(20, 30)
    else:
        val = random.randint(30, 50)

    return val


# Dummy vector problem definition
vector_example_definition = Domain()
vector_example_definition.define_dynamic_structure("v", 2, 20, 1)
vector_example_definition.set_structure_to_integer("v", 1, 20, 1)


# Dummy vector fitness function
def vector_example_fitness(individual):
    v = individual["v"]
    return sum(v)


# Dummy all legacy problem definition
all_types_definition = Domain()
all_types_definition.define_integer("I", 1, 10, 1)
all_types_definition.define_real("R", 0.0, 5.0, 0.01)
all_types_definition.define_categorical("C", ["Label1", "Label2", "Label3"])
all_types_definition.define_group("L")
all_types_definition.define_integer("CompI", 25, 300, 20)
all_types_definition.link_variable_to_group("L", "CompI")
all_types_definition.define_real("CompR", 0.25, 4.5, 0.05)
all_types_definition.link_variable_to_group("L", "CompR")
all_types_definition.define_categorical("CompC", ["F1", "F2", "F3", "F4"])
all_types_definition.link_variable_to_group("L", "CompC")

all_types_definition.define_dynamic_structure("VI", 1, 5, 2)
all_types_definition.set_structure_to_integer("VI", 0, 5)
all_types_definition.link_variable_to_group("L", "VI")

all_types_definition.define_static_structure("VR", 3)
all_types_definition.set_structure_to_integer("VR", 0, 1)
all_types_definition.link_variable_to_group("L", "VR")

all_types_definition.define_static_structure("VC", 3)
all_types_definition.set_structure_to_categorical("VC", ["A", "B"])
all_types_definition.link_variable_to_group("L", "VC")


# Dummy all legacy fitness function
def all_types_fitness(individual):
    r = individual["R"]
    return r + 2
