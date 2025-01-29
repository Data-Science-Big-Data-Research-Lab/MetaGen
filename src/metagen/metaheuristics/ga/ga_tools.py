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
from __future__ import annotations

import random
from collections.abc import Callable
from copy import copy
from typing import Tuple, List, cast

import metagen.framework.solution as types
from metagen.framework import BaseConnector, Solution, Domain
from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                      DynamicStructureDefinition,
                                      IntegerDefinition, RealDefinition,
                                      StaticStructureDefinition)


class GAStructure(types.Structure):
    """
    Represents the custom Structure type for the Genetic Algorithm (GA).
    
    This class extends the base Structure type to add genetic algorithm specific operations
    like crossover.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
        """
        Performs crossover operation with another GAStructure instance.

        :param other: Another GAStructure instance to perform crossover with
        :type other: GAStructure
        :return: A tuple containing two new GAStructure instances (children)
        :rtype: Tuple[GAStructure, GAStructure]
        :raises NotImplementedError: If the definition is a DynamicStructureDefinition
        """

        child1 = GAStructure(self.get_definition(), connector=self.connector)
        child2 = GAStructure(self.get_definition(), connector=self.connector)

        current_size = min(len(self), len(other))
        number_of_changes = random.randint(1, current_size)
        indexes_to_change = random.sample(
            list(range(0, current_size)), number_of_changes)

        if isinstance(self.get_definition(), DynamicStructureDefinition):
            raise NotImplementedError()
        else:
            for i in range(current_size):
                if i in indexes_to_change:
                    child1[i], child2[i] = copy(other.get(i)), copy(self.get(i))
                else:
                    child1[i], child2[i] = copy(self.get(i)), copy(other.get(i))
        return child1, child2


class GASolution(Solution):
    """
    Represents a Solution type for the Genetic Algorithm (GA).

    This class extends the base Solution type to add genetic algorithm specific operations
    like crossover between solutions.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
        """
        Performs crossover operation with another GASolution instance.

        :param other: Another GASolution instance to perform crossover with
        :type other: GASolution
        :return: A tuple containing two new GASolution instances (children)
        :rtype: Tuple[GASolution, GASolution]
        :raises AssertionError: If the solutions have different variable keys
        """
        assert self.get_variables().keys() == other.get_variables().keys()

        basic_variables = []

        for variable_name, variable_value in self.get_variables().items():

            if isinstance(variable_value, GAStructure):
                variable_value = (variable_value, "static")

            if self.connector.get_builtin(variable_value) in [int, float, str]:
                basic_variables.append(variable_name)

        if len(basic_variables) > 1:
            n_variables_to_exchange = random.randint(
                1, len(basic_variables) - 1)

            variables_to_exchange = random.sample(
                basic_variables, n_variables_to_exchange)
        else:
            variables_to_exchange = []

        child1 = GASolution(self.get_definition(), connector=self.connector)
        child2 = GASolution(self.get_definition(), connector=self.connector)

        for variable_name, variable_value in self.get_variables().items():  # Iterate over all variables

            if variable_name not in basic_variables:
                variable_child1, variable_child2 = variable_value.crossover(
                    other.get(variable_name))
                child1.set(variable_name, copy(variable_child1))
                child2.set(variable_name, copy(variable_child2))
            elif variable_name in variables_to_exchange:
                child1.set(variable_name, copy(other.get(variable_name)))
                child2.set(variable_name, copy(variable_value))
            else:
                child1.set(variable_name, copy(self.get(variable_name)))
                child2.set(variable_name, copy(variable_value))

        return child1, child2


class GAConnector(BaseConnector):
    """
    Represents the custom Connector for the Genetic Algorithm (GA).

    This connector links the following classes:
    * BaseDefinition - GASolution - dict
    * IntegerDefinition - types.Integer - int
    * RealDefinition - types.Real - float
    * CategoricalDefinition - types.Categorical - str
    * StaticStructureDefinition - GAStructure - list

    The Solution and Structure original classes have been replaced by custom GA classes.
    When instantiating a StaticStructureDefinition, the GAStructure will be employed.
    """

    def __init__(self) -> None:
        """
        Initialize the GAConnector with predefined type mappings for GA operations.
        """
        super().__init__()

        self.register(BaseDefinition, GASolution, dict)
        self.register(IntegerDefinition, types.Integer, int)
        self.register(RealDefinition, types.Real, float)
        self.register(CategoricalDefinition, types.Categorical, str)
        self.register(StaticStructureDefinition, (GAStructure, "static"), list)


def yield_two_children(parents: Tuple[GASolution, GASolution], mutation_rate: float, 
                      fitness_function: Callable[[Solution], float]) -> Tuple[GASolution, GASolution]:
    """
    Generate two children solutions through crossover and mutation operations.

    :param parents: A tuple containing two parent solutions
    :type parents: Tuple[GASolution, GASolution]
    :param mutation_rate: The probability of mutation occurring in each child
    :type mutation_rate: float
    :param fitness_function: Function to evaluate the fitness of solutions
    :type fitness_function: Callable[[Solution], float]
    :return: A tuple containing two new solutions (children)
    :rtype: Tuple[GASolution, GASolution]
    """

    child1, child2 = parents[0].crossover(parents[1])

    if random.uniform(0, 1) <= mutation_rate:
        child1.mutate()
    if random.uniform(0, 1) <= mutation_rate:
        child2.mutate()

    child1.evaluate(fitness_function)
    child2.evaluate(fitness_function)

    return child1, child2
