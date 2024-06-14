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
from copy import copy
from typing import Tuple

import metagen.framework.solution as types
from metagen.framework import BaseConnector, Solution
from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                      DynamicStructureDefinition,
                                      IntegerDefinition, RealDefinition,
                                      StaticStructureDefinition)


class GAStructure(types.Structure):
    """
    Represents the custom Structure type for the Genetic Algorithm (GA).
    
    Methods:
        mutate(): Modify the Structure by performing an action selected randomly from three options. Inherited from :py:class:`~metagen.framework.solution.Structure`.
        _resize(): Resizes the vector based on the definition provided at initialization. Inherited from :py:class:`~metagen.framework.solution.Structure`.
        _alterate(): Randomly alters a certain number of elements in the vector by calling their `mutate` method. Inherited from :py:class:`~metagen.framework.solution.Structure`.
        crossover(other: GAStructure) -> Tuple[GAStructure, GAStructure]: Performs crossover operation with another GAStructure instance.
    """

    def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
        """
         Performs crossover operation with another GAStructure instance by randomly modifying list positions. Note that this operation does not support an `DynamicStructureDefinition`.
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

    Methods:
        mutate(alterations_number: int = None): Modify a random subset of the solution's variables calling its mutate method. Inherited from :py:class:`~metagen.framework.solution.Solution`.
        crossover(other: GASolution) -> Tuple[GASolution, GASolution]: Performs crossover operation with another GASolution instance.
    """

    def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
        """
        Performs crossover operation with another GASolution instance by randomly exchanging variables.
        """
        assert self.get_variables().keys() == other.get_variables().keys()

        basic_variables = []

        for variable_name, variable_value in self.get_variables().items():

            if isinstance(variable_value, GAStructure):
                variable_value = (variable_value, "static")
                
            if self.connector.get_builtin(variable_value) in [int, float, str]:
                basic_variables.append(variable_name)

        if len(basic_variables) > 0:
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
    Represents the custom Connector for the Genetic Algorithm (GA) which link the following classes:

    * `BaseDefinition` - `GASolution` - `dict`
    * `IntegerDefinition` - `types.Integer` - `int`
    * `RealDefinition` - `types.Real` - `float`
    * `CategoricalDefinition` - `types.Categorical` - `str`
    * `StaticStructureDefinition`- `GAStructure` - `list`

    Note that the `Solution` and `Structure` original classes has been replaced by the custom classes. Therefore, when instantiating an `StaticStructureDefinition`, the `GAStructure` will be employed.

    Methods:
        __init__(): Initializes the GAConnector instance.
    """

    def __init__(self) -> None:

        super().__init__()

        self.register(BaseDefinition, GASolution, dict)
        self.register(IntegerDefinition, types.Integer, int)
        self.register(RealDefinition, types.Real, float)
        self.register(CategoricalDefinition, types.Categorical, str)
        self.register(StaticStructureDefinition, (GAStructure, "static"), list)
