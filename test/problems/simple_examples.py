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
from metagen.framework import Domain
from metagen.framework.connector import BaseConnector

def get_x_raised_to_2_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_real("x", 0.0, 100.0, 0.05)
    return domain


def get_x_minus_15_raised_to_2_domain(connector = BaseConnector()) -> Domain:
    domain = Domain(connector)
    domain.define_real("x", 0.0, 100.0, 0.05)
    return domain


# x^2 fitness function
def x_raised_to_2_fitness(individual):
    x = individual["x"]
    return pow(x, 2)

# (x-15)^2 fitness function
def x_minus_15_raised_to_2_fitness(individual):
    x = individual["x"]
    return pow(x - 15, 2)
