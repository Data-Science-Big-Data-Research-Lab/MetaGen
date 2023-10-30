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
from copy import deepcopy
from typing import cast

from metagen.framework import BaseConnector
from metagen.framework.domain import (Base, BaseDefinition,
                                      BaseStructureDefinition)
from metagen.framework.domain.literals import CatVal
from metagen.framework.domain.bounds import BaseDefinitionClass, IntegerDefinitionClass, RealDefinitionClass, CategoricalDefinitionClass, DynamicStructureDefinitionClass, StaticStructureDefinitionClass
from metagen.framework.domain.preconditions import Messages


def _get_base_type(core: BaseDefinition, var: str | None, remember: bool = False) -> Base | None:
    res: Base | None = None
    if var is not None:
        if not remember:
            res = cast(Base, core.get(var))
            core.delete(var)
        else:
            res = cast(Base, deepcopy(core.get(var)))
    return res


def _check_base_type(core: BaseDefinition, var: str, remember: bool = False) -> Base:
    res: Base | None = _get_base_type(core, var, remember)
    if res is None:
        raise ValueError(Messages.definition(var, "d_n"))
    return cast(Base, res)

def _get_group_definition(name: str, variable: Base) -> BaseDefinition:
    if not isinstance(variable, BaseDefinition):
        raise ValueError(Messages.definition(name, "d_g"))
    return cast(BaseDefinition, variable)


def _get_structure_definition(name: str, variable: Base) -> BaseStructureDefinition:
    if not isinstance(variable, BaseStructureDefinition):
        raise ValueError(Messages.definition(name, "d_s"))
    return cast(BaseStructureDefinition, variable)


class Domain:

    def __init__(self, connector: BaseConnector = BaseConnector()):
        """
        This class encompasses the domain of the problem by defining a set of variables and its possible values.
        The user must instantiate the class, then, define the variables using the member methods of the class.

        **Example:**

        .. code-block:: python

            >>> new_domain = Domain()
            >>> new_domain.define_integer("IntegerValue", 0, 10)
            >>> new_domain.define_categorical("CategoricalValue", ["C1","C2","C3"])
            >>> new_domain.define_real("RealValue", 0, 1)
            >>> new_domain.define_group("Group")
            >>> new_domain.link_variable_to_group("Group", "RealValue")
        """
        self._connector = connector
        base_definition: type[BaseDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(dict))
        self._core: BaseDefinition = base_definition()

    def define_integer(self, name: str, min_value: int, max_value: int, step: int | None = None):
        """ It defines an **INTEGER** variable receiving a name as its identifier, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        :param name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        integer_definition: type[IntegerDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(int))
        self._core.define(name, integer_definition(min_value, max_value, step))

    def define_real(self, name: str, min_value: float, max_value: float, step: float | None = None):
        """ It defines a **REAL** variable receiving a name as its identifier, the minimum and maximum values that it will be
        able to have, and the step size to traverse the interval.

        :param name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        real_definition: type[RealDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(float))
        self._core.define(name, real_definition(min_value, max_value, step))

    def define_categorical(self, name: str, categories: CatVal):
        """ It defines a **CATEGORICAL** variable receiving a name as its identifier, and a list with the categories that it
        will be able to have.

        :param name: The variable name.
        :param categories: The list of categories.
        :type name: str
        :type categories: list of int, float or str
        """
        categorical_definition: type[CategoricalDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(str))
        self._core.define(name, categorical_definition(categories))

    def define_group(self, name: str):
        """ It defines a **GROUP** variable receiving a name as its identifier, and a list with the categories that it will be able to have.

        :param name: The group name.
        :type name: str
        """
        base_definition: type[BaseDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(dict))

        self._core.define(name, base_definition())

    def define_integer_in_group(self, group: str, name: str, min_value: int, max_value: int,
                                step: int | None = None):
        """ It defines an **INTEGER** variable in an already defined group, receiving a name as its identifier, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        :param group: The group name.
        :param name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type group: str
        :type name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        group_def: BaseDefinition = _get_group_definition(
            group, self._core.get(group))
        integer_definition: type[IntegerDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(int))
        group_def.define(name, integer_definition(min_value, max_value, step))

    def define_real_in_group(self, group: str, name: str, min_value: float, max_value: float,
                             step: float | None = None):
        """ It defines an **REAL** variable in an already defined group, receiving a name as its identifier, the minimum and maximum values that it will
        be able to have, and the step size to traverse the interval.

        :param group: The group name.
        :param name: The variable name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type group: str
        :type name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        group_def: BaseDefinition = _get_group_definition(
            group, self._core.get(group))
        real_definition: type[RealDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(float))
        group_def.define(name, real_definition(min_value, max_value, step))

    def define_categorical_in_group(self, group: str, name: str, categories: CatVal):
        """ It defines a **CATEGORICAL** variable in an already defined group, receiving a name as its identifier, and a list with the categories that it
        will be able to have.

        :param group: The group name.
        :param name: The variable name.
        :param categories: The list of categories.
        :type group: str
        :type name: str
        :type categories: list of int, float or str
        """
        group_def: BaseDefinition = _get_group_definition(
            group, self._core.get(group))
        categorical_definition: type[CategoricalDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(str))
        group_def.define(name, categorical_definition(categories))

    def link_variable_to_group(self, group: str, var: str, remember: bool = False):
        """ Include a defined variable to a defined group. Note that only one level of grouping is allowed.

        :param group: The group name.
        :param var: The variable name.
        :param remember: TODO
        :type group: str
        :type remember: bool
        """
        group_def: BaseDefinition = _get_group_definition(
            group, self._core.get(group))
        base_type: Base = _check_base_type(self._core, var, remember)
        group_def.define(var, base_type)

    def define_dynamic_structure(self, name: str, min_len: int, max_len: int, step_len: int | None = None,
                                 var: str | None = None, remember: bool = False):
        """ It defines an **DynamicStructure** variable receiving a name as its identifier, the minimum and maximum size that it will
        be able to have, and the step size to traverse the size.

        TODO: No entiendo qué significa var o remember.

        :param name: The variable name.
        :param min_len: The minimum length of the Structure.
        :param max_len: The maximum length of the Structure.
        :param step_len: The step size.
        :type name: str
        :type min_len: int
        :type max_len: int
        :type step_len: int
        """
        base_type: Base | None = _get_base_type(self._core, var, remember)
        dynamic_structure_definition: type[DynamicStructureDefinitionClass] = self._connector.get_definition(
            (self._connector.get_type(list), 'dynamic'))
        self._core.define(name, dynamic_structure_definition(
            name, base_type, min_len, max_len, step_len))

    def define_static_structure(self, name: str, length: int,
                                var: str | None = None, remember: bool = False):
        """ It defines an **StaticStructure** variable receiving a name as its identifier, the size that it will
        be able to have, and the step size to traverse the size.

        :param name: The variable name.
        :param length: The length of the Structure.
        :type name: str
        :type length: int
        """
        base_type: Base | None = _get_base_type(self._core, var, remember)
        static_structure_definition: type[StaticStructureDefinitionClass] = self._connector.get_definition(
            (self._connector.get_type(list), 'static'))
        self._core.define(name, static_structure_definition(
            name, base_type, length))

    def set_structure_to_integer(self, name: str, min_value: int, max_value: int, step: int | None = None):
        """ It defines an **INTEGER** as the base type for a Static or Dynamic Structure, receiving the name of the structure, the minimum and maximum values that the values will
        be able to have, and the step size to traverse the interval.

        :param name: The structure name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        structure: BaseStructureDefinition = _get_structure_definition(
            name, self._core.get(name))
        integer_definition: type[IntegerDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(int))
        structure.set_base(integer_definition(min_value, max_value, step))

    def set_structure_to_categorical(self, name: str, categories: CatVal):
        """ It defines an **CATEGORICAL** as the base type for a Static or Dynamic Structure, and a list with the categories that it
        will be able to have.

        :param name: The structure name.
        :param categories: The list of categories.
        :type name: str
        :type categories: list of int, float or str
        """
        structure: BaseStructureDefinition = _get_structure_definition(
            name, self._core.get(name))
        categorical_definition: type[CategoricalDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(str))
        structure.set_base(categorical_definition(categories))

    def set_structure_to_real(self, name: str, min_value: float, max_value: float,
                              step: float | None = None):
        """ It defines an **REAL** as the base type for a Static or Dynamic Structure, receiving the name of the structure, the minimum and maximum values that the values will
        be able to have, and the step size to traverse the interval.

        :param name: The structure name.
        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param step: The step size.
        :type name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        structure: BaseStructureDefinition = _get_structure_definition(
            name, self._core.get(name))
        real_definition: type[RealDefinitionClass] = self._connector.get_definition(
            self._connector.get_type(float))
        structure.set_base(real_definition(min_value, max_value, step))

    def set_structure_to_variable(self, name: str, var: str, remember: bool = False):
        """ It defines an already defined variable the base type for a Static or Dynamic Structure, receiving the name of the structure and the variable.
        :param name: The structure name.
        :param var: The variable value.
        :type name: str
        :type var: str
        """
        structure: BaseStructureDefinition = _get_structure_definition(
            name, self._core.get(name))
        base_type: Base = _check_base_type(self._core, var, remember)
        structure.set_base(base_type)

    def get_core(self) -> BaseDefinition:
        """ It returns the core which contains the all the defined variables.
        """
        return self._core

    def get_connector(self) -> BaseConnector:
        """ It returns the defined connector for this domain. 
        """
        return self._connector

    def to_string(self, level: int) -> str:
        return self.get_core().to_string(level)

    def __str__(self) -> str:
        return self.get_core().to_string(0)

    def __repr__(self) -> str:
        return self.get_core().to_string(0)
