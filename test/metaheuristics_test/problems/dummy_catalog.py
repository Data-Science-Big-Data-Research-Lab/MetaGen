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
from metagen.framework.connector import BaseConnector

# dummy-1
def get_dummy1_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_categorical(
        "c", ["level1", "level2", "level3", "level5"])
    return domain

def dummy1_fitness(individual):
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

# dummy-2
def get_dummy2_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("I", 1, 10, 1)
    domain.define_real("R", 0.0, 5.0, 0.01)
    domain.define_categorical("C", ["Label1", "Label2", "Label3"])

    domain.define_group("L")
    domain.define_integer("CompI", 25, 300, 20)
    domain.link_variable_to_group("L", "CompI")
    domain.define_real("CompR", 0.25, 4.5, 0.05)
    domain.link_variable_to_group("L", "CompR")
    domain.define_categorical("CompC", ["F1", "F2", "F3", "F4"])
    domain.link_variable_to_group("L", "CompC")

    domain.define_static_structure("VR", 3)
    domain.set_structure_to_integer("VR", 0, 1)
    domain.link_variable_to_group("L", "VR")

    domain.define_static_structure("VC", 3)
    domain.set_structure_to_categorical("VC", ["A", "B"])
    domain.link_variable_to_group("L", "VC")

    return domain

def dummy2_fitness(individual):
    r = individual["R"]
    return r + 2

 # dummy-3
def get_dummy3_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_integer("I", 1, 10, 1)
    domain.define_real("R", 0.0, 5.0, 0.01)
    domain.define_categorical("C", ["Label1", "Label2", "Label3"])
    
    domain.define_group("L")
    domain.define_integer("CompI", 25, 300, 20)
    domain.link_variable_to_group("L", "CompI")
    domain.define_real("CompR", 0.25, 4.5, 0.05)
    domain.link_variable_to_group("L", "CompR")
    domain.define_categorical("CompC", ["F1", "F2", "F3", "F4"])
    domain.link_variable_to_group("L", "CompC")

    domain.define_dynamic_structure("VI", 1, 5, 2)
    domain.set_structure_to_integer("VI", 0, 5)
    domain.link_variable_to_group("L", "VI")

    domain.define_static_structure("VR", 3)
    domain.set_structure_to_integer("VR", 0, 1)
    domain.link_variable_to_group("L", "VR")

    domain.define_static_structure("VC", 3)
    domain.set_structure_to_categorical("VC", ["A", "B"])
    domain.link_variable_to_group("L", "VC")
    
    return domain


def dummy3_fitness(individual):
    r = individual["R"]
    return r + 2
