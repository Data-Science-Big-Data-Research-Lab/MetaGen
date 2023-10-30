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

from abc import ABC, abstractmethod
from typing import Any, Dict, cast

from metagen.framework.domain.literals import (DF, METAGEN_TYPE, Attributes, C,
                                               CatAttr, CatVal, D, DefAttr,
                                               DefType, DymAttr, I, IntAttr,
                                               List, MetaVal, R, RealAttr, S,
                                               StaAttr, StrVal)
from metagen.framework.domain.preconditions import Messages, Preconditions


class Base(ABC):
    """
    Abstract base class for metagen definitions with a common interface.

    """

    def __init__(self, meta_type: METAGEN_TYPE):
        """
        Initializes a new instance assigning the metagen internal type.
        """
        self._meta_type: METAGEN_TYPE = meta_type

    @abstractmethod
    def check_value(self, value: Any) -> bool:
        """
        Abstract method to check the validity of the values in the definition.
        """
        pass

    @abstractmethod
    def get_attributes(self) -> Attributes:
        """
        Abstract method to obtain the internal attributes which constitutes the definition.
        """
        pass

    def get_type(self) -> METAGEN_TYPE:
        """
        Return the internal type of the definition which can be one of: I, R, C, D or S.
        """
        return self._meta_type


class IntegerDefinition(Base):
    """
    Represents an integer type with defined minimum, maximum and step values.

    :param min_value: The minimum value allowed for the integer type.
    :type min_value: int
    :param max_value: The maximum value allowed for the integer type.
    :type max_value: int
    :param step: The step value for the integer type. Defaults to None if not provided.
    :type step: int or None

    :raises ValueError: If the `min_value`, `max_value` or `step` values do not meet the integer range requirements.

    :ivar __min_value: The minimum value allowed for the integer type.
    :ivar __max_value: The maximum value allowed for the integer type.
    :ivar __step: The step value for the integer type. Defaults to None if not provided.

    :return: An instance of the IntegerDefinition class.
    :rtype: IntegerDefinition
    """

    def __init__(self, min_value: int, max_value: int, step: int | None = None):
        """
        Initializes an instance of the IntegerDefinition class with the provided minimum, maximum and step values.

        :param min_value: The minimum value allowed for the integer type.
        :type min_value: int
        :param max_value: The maximum value allowed for the integer type.
        :type max_value: int
        :param step: The step value for the integer type. Defaults to None if not provided.
        :type step: int or None

        :raises ValueError: If the `min_value`, `max_value` or `step` values do not meet the integer range requirements.
        """

        Preconditions.Integer.range(min_value, max_value, step)
        Base.__init__(self, I)
        self.__min_value: int = min_value
        self.__max_value: int = max_value
        self.__step: int | None = step

    def get_attributes(self) -> IntAttr:
        """
        Returns the integer attributes of the IntegerDefinition instance.

        :return: A tuple containing the integer type, minimum value, maximum value and step value of the IntegerDefinition instance.
        :rtype: IntAttr
        """
        return I, self.__min_value, self.__max_value, self.__step

    def check_value(self, value: Any) -> bool:
        """
        Checks if the provided value is a valid integer within the range of the IntegerDefinition instance.

        :param value: The value to be checked.
        :type value: Any

        :return: True if the value is a valid integer within the range of the IntegerDefinition instance, False otherwise.
        :rtype: bool
        """
        res: bool = True

        if not isinstance(value, int):
            res = False
        else:
            if value < self.__min_value or value > self.__max_value:
                res = False
        return res

    def __str__(self):
        """
        Returns a string representation of the IntegerDefinition instance.

        :return: A string representation of the IntegerDefinition instance, including its type and attribute values.
        :rtype: str
        """
        return "[" + super().get_type() + "] " + "{Minimum = " + str(self.__min_value) + \
            ", Maximum = " + str(self.__max_value) + \
            ", Step = " + str(self.__step) + "}"


class RealDefinition(Base):
    """
    Represents a real number type with defined minimum, maximum and step values.

    :param min_value: The minimum value allowed for the real number type.
    :type min_value: float
    :param max_value: The maximum value allowed for the real number type.
    :type max_value: float
    :param step: The step value for the real number type. Defaults to None if not provided.
    :type step: float or None

    :raises ValueError: If the `min_value`, `max_value` or `step` values do not meet the real number range requirements.

    :ivar __min_value: The minimum value allowed for the real number type.
    :ivar __max_value: The maximum value allowed for the real number type.
    :ivar __step: The step value for the real number type. Defaults to None if not provided.

    :return: An instance of the RealDefinition class.
    :rtype: RealDefinition
    """

    def __init__(self, min_value: float, max_value: float, step: float | None = None):
        """
        Initializes an instance of the RealDefinition class with the provided minimum, maximum and step values.

        :param min_value: The minimum value allowed for the real number type.
        :type min_value: float
        :param max_value: The maximum value allowed for the real number type.
        :type max_value: float
        :param step: The step value for the real number type. Defaults to None if not provided.
        :type step: float or None

        :raises ValueError: If the `min_value`, `max_value` or `step` values do not meet the real number range requirements.
        """
        Preconditions.Real.range(min_value, max_value, step)
        Base.__init__(self, R)
        self.__min_value: float = min_value
        self.__max_value: float = max_value
        self.__step: float | None = step

    def get_attributes(self) -> RealAttr:
        """
        Returns the real number attributes of the RealDefinition instance.

        :return: A tuple containing the real number type, minimum value, maximum value and step value of the RealDefinition instance.
        :rtype: RealAttr
        """
        return R, self.__min_value, self.__max_value, self.__step

    def check_value(self, value: Any) -> bool:
        """
        Checks if the provided value is a valid real number within the range of the RealDefinition instance.

        :param value: The value to be checked.
        :type value: Any

        :return: True if the value is a valid real number within the range of the RealDefinition instance, False otherwise.
        :rtype: bool
        """
        res: bool = True

        if not isinstance(value, float):
            res = False
        else:
            if value < self.__min_value or value > self.__max_value:
                res = False
        return res

    def __str__(self):
        """
        Returns a string representation of the RealDefinition instance.

        :return: A string representation of the RealDefinition instance, including its type and attribute values.
        :rtype: str
        """
        return "[" + super().get_type() + "] " + "{Minimum = " + str(self.__min_value) + \
            ", Maximum = " + str(self.__max_value) + \
            ", Step = " + str(self.__step) + "}"


class CategoricalDefinition(Base):
    """
    Represents a categorical attribute with a set of allowed categories.

    :param categories: a list or set of allowed categories.
    :type categories: CatVal
    :raises ValueError: if `categories` is empty or not a list or set.
    :return: An instance of the CategoricalDefinition class.
    :rtype: CategoricalDefinition
    """

    def __init__(self, categories: CatVal):
        """
        Initialize the CategoricalDefinition instance.

        :param categories: a list or set of allowed categories.
        :type categories: CatVal
        :raises ValueError: if `categories` is empty or not a list or set.
        """
        Preconditions.Categorical.categories(categories)
        Base.__init__(self, C)
        self.__categories: CatVal = categories

    def get_attributes(self) -> CatAttr:
        """
        Return the categorical type `C` and the allowed categories `__categories`.

        :return: a tuple containing the categorical type `C` and the allowed categories `__categories`.
        :rtype: CatAttr
        """
        return C, self.__categories

    def check_value(self, value: Any) -> bool:
        """
        Check if the given value is in the allowed categories.

        :param value: the value to be checked.
        :type value: Any
        :return: True if the value is in the allowed categories, False otherwise.
        :rtype: bool
        """
        res: bool = True

        if value not in self.__categories:
            res = False
        return res

    def __str__(self):
        return "[" + super().get_type() + "] " + "{Values = " + str(self.__categories) + "}"


class BaseDefinition(Base):
    """
    The BaseDefinition class represents a definition of a set of variables.

    :return: An instance of the BaseDefinition class.

    """

    def __init__(self):
        """
        Initializes a new instance of the BaseDefinition class.
        """
        super().__init__(DF)
        self.__var_list: List[str] = []
        self.__value: Dict[str, Base] = {}

    def __is_not_defined(self, name: str):
        """
        Helper function to check whether a variable is not defined.

        :param name: A string representing the name of the variable.
        """
        if self.is_variable(name):
            raise ValueError(Messages.definition(name, "d_a"))

    def check_value(self, value: Any) -> bool:
        """
        Checks whether a given value is valid based on the current definition.

        :param value: A dictionary representing the variable and its value.

        :return: A boolean indicating whether the given value is valid based on the current definition.
        """
        res: bool = True
        names: List[str] = list(value.keys())
        i: int = 0
        while res and i < len(names):
            if names[i] not in self.__value.keys():
                res = False
            else:
                value_to_check = value[names[i]]
                res = self.__value[names[i]].check_value(value_to_check)
            i += 1
        return res

    def get_attributes(self) -> DefAttr:
        """
        Returns the attributes of the current definition.

        :return: A tuple containing the type and attributes of the current definition.
        """
        attr: Dict = {}
        for k, v in self.__value.items():
            attr[k] = v.get_attributes()
        return DF, attr

    def define(self, name: str, definition: Base):
        """
        Defines a new variable and its definition.

        :param name: A string representing the name of the variable.
        :param definition: An instance of a Base class representing the definition of the variable.
        """
        self.__is_not_defined(name)
        self.__var_list.append(name)
        self.__value[name] = definition

    def delete(self, name: str):
        """
        Deletes a variable from the current definition.

        :param name: A string representing the name of the variable.
        """
        self.__var_list.remove(name)
        del self.__value[name]

    def get(self, name: str) -> Base:
        """
        Returns the definition of a variable.

        :param name: A string representing the name of the variable.

        :return: An instance of a Base class representing the definition of the variable.
        """
        return self.__value[name]

    def get_by_index(self, index: int) -> Base:
        """
        Returns the definition of a variable by its index in the variable list.

        :param index: An integer representing the index of the variable.

        :return: An instance of a Base class representing the definition of the variable.
        """
        return self.__value[self.__var_list[index]]

    def check(self, name: str, value: MetaVal) -> bool:
        """
        Checks whether a given value is valid for a variable.

        :param name: A string representing the name of the variable.
        :param value: A value representing the value of the variable.

        :return: A boolean indicating whether the given value is valid for the variable.
        """
        return self.__value[name].check_value(value)

    def is_variable(self, name: str) -> bool:
        """
        Check if a variable with the given name exists in the definition.

        :param name: The name of the variable to check.
        :type name: str
        :return: True if the variable exists, False otherwise.
        :rtype: bool
        """
        return name in self.__value.keys()

    def variable_list(self) -> List[str]:
        """
        Get a list of all variable names defined in the definition.

        :return: A list of all variable names.
        :rtype: List[str]
        """

        return self.__var_list

    def __str__(self):
        """
        Get a string representation of the definition.

        :return: A string representation of the definition.
        :rtype: str
        """
        return self.to_string(0)

    def to_string(self, level: int) -> str:
        """
        Get a string representation of the definition at the given level of indentation.

        :param level: The level of indentation to use.
        :type level: int
        :return: A string representation of the definition.
        :rtype: str
        """
        res: str = ""
        cnt: int = 1
        if level == 0:
            res += "[DEF]\n"
        for k, v in self.__value.items():
            for _ in range(0, level):
                res += "\t"
            res += "\t" + k
            if isinstance(v, BaseDefinition):
                res += ": [DEF]\n" + v.to_string(level + 1)
            else:
                res += ": " + v.__str__()
            if cnt != len(self.__value.items()):
                res += "\n"
            cnt += 1
        return res


class Definition(BaseDefinition):
    """
    A Definition is a named collection of variables with their respective definitions.

    Inherits from BaseDefinition.

    :param name: A string representing the name of the definition.
    """

    def __init__(self, name: str):
        """
        Initializes a Definition instance with the specified name.

        :param name: A string representing the name of the definition.
        """
        super().__init__()
        self.__name: str = name

    def __str__(self):
        """
        Returns a string representation of the Definition instance.

        :return: A string representation of the Definition instance.
        """
        return self.__name + ":\n" + super().__str__()

    def get_name(self) -> str:
        """
        Returns the name of the Definition instance.

        :return: A string representing the name of the Definition instance.
        """
        return self.__name

    def get_definition(self) -> DefType:
        """
        Returns a dictionary representing the attributes of the Definition instance.

        :return: A dictionary representing the attributes of the Definition instance.
        """
        return {self.__name: super().get_attributes()}


class BaseStructureDefinition(ABC):
    """
    A base abstract class that defines the structure of a definition
    with a base type.

    :param base: An instance of a base type.
    """

    def __init__(self, base: Base | None):
        self.__base: Base | None = base

    def __base_type_defined(self):
        """
        Private method to check if the base type is defined.
        """
        if self.__base is None:
            raise ValueError(Messages.BASE_TYPE_NOT_DEFINED)

    @abstractmethod
    def check_length(self, value: Any) -> bool:
        """
        Abstract method to check if the value has the correct length.

        :param value: The value to check the length for.
        :return: True if the length is correct, otherwise False.
        """
        pass

    def check_value(self, value: Any) -> bool:
        """
        Check if the value is valid in the definition.

        :param value: The value to check.
        :return: True if the value is valid, otherwise False.
        """
        self.__base_type_defined()
        res: bool = True
        if not self.check_length(value):
            res = False
        else:
            i: int = 0
            while res and i < len(value):
                value_to_check = value[i]
                res = cast(Base, self.__base).check_value(value_to_check)
                i += 1
        return res

    def get_base(self) -> Base:
        """
        Get the base type for the definition.

        :return: The base type.
        """
        self.__base_type_defined()
        return cast(Base, self.__base)

    def set_base(self, base: Base):
        """
        Set the base type.

        :param base: The base type to set.
        """
        self.__base = base

    def is_base(self):
        """
        Check if the base type is defined.

        :return: True if the base type is defined, otherwise False.
        """
        return self.__base is not None

    def check_base_value(self, val: MetaVal) -> bool:
        """
        Check if the base type value is valid.

        :param val: The value to check.
        :return: True if the value is valid, otherwise False.
        """
        self.__base_type_defined()
        return cast(Base, self.__base).check_value(val)


class DynamicStructureDefinition(Base, BaseStructureDefinition):
    """
    A class representing a dynamic structure definition.

    :param name: A string representing the name of the dynamic structure definition.
    :type name: str
    :param base: A Base representing the base type of the dynamic structure definition.
    :type base: Base or None
    :param min_length: An integer representing the minimum length of the dynamic structure definition.
    :type min_length: int
    :param max_length: An integer representing the maximum length of the dynamic structure definition.
    :type max_length: int
    :param step_length: An optional integer representing the step length of the dynamic structure definition.
    :type step_length: int or None

    :raises ValueError: If the base type is not defined.
    """

    def __init__(self, name: str, base: Base | None,
                 min_length: int, max_length: int, step_length: int | None = None):
        """
        Initializes a DynamicStructureDefinition object with the given name, base type, minimum length,
        maximum length, and step length.

        :param name: A string representing the name of the dynamic structure definition.
        :type name: str
        :param base: A Base representing the base type of the dynamic structure definition.
        :type base: Base or None
        :param min_length: An integer representing the minimum length of the dynamic structure definition.
        :type min_length: int
        :param max_length: An integer representing the maximum length of the dynamic structure definition.
        :type max_length: int
        :param step_length: An optional integer representing the step length of the dynamic structure definition.
        :type step_length: int or None
        """
        Base.__init__(self, D)
        BaseStructureDefinition.__init__(self, base)
        self.__name: str = name
        self.__min_length: int = min_length
        self.__max_length: int = max_length
        self.__step_length: int | None = step_length

    def check_value(self, value: StrVal) -> bool:
        """
        Checks whether the given value is a valid dynamic structure definition.

        :param value: A string value to be checked.
        :type value: StrVal

        :return: A boolean value indicating whether the given value is a valid dynamic structure definition.
        :rtype: bool
        """
        return BaseStructureDefinition.check_value(self, value)

    def get_attributes(self) -> DymAttr:
        """
        Returns the attributes of the dynamic structure definition.

        :return: A tuple representing the attributes of the dynamic structure definition.
        :rtype: DymAttr
        """
        return D, self.__min_length, self.__max_length, \
            self.__step_length, super().get_base().get_attributes()

    def check_length(self, value: StrVal) -> bool:
        """
        Checks whether the length of the given value is within the minimum and maximum length of the dynamic structure
        definition.

        :param value: A string value to be checked.
        :type value: StrVal

        :return: A boolean value indicating whether the length of the given value is within the minimum and maximum length of the dynamic structure definition.
        :rtype: bool
        """
        return self.__min_length <= len(value) <= self.__max_length

    def __str__(self):
        """
        Returns a string representation of the dynamic structure definition.

        :return: A string representing the dynamic structure definition.
        :rtype: str
        """
        base_type: Base = super().get_base()
        ext: str = ""
        if isinstance(base_type, BaseDefinition):
            ext = "\n"
        return self.__name + ": [" + super().get_type() + "] " + "{Min Length = " + str(self.__min_length) + \
            ", Max Length = " + str(self.__max_length) + ", Step = " + str(self.__step_length) + \
            ", Base Type = " + ext + str(base_type) + "}"


class StaticStructureDefinition(Base, BaseStructureDefinition):
    """
    Class representing a static structure definition.

    :param name: Name of the structure definition.
    :type name: str
    :param base: Base type of the structure definition.
    :type base: Base or None
    :param length: Length of the structure definition.
    :type length: int

    """

    def __init__(self, name: str, base: Base | None, length: int):
        """Constructs a new StaticStructureDefinition object.

        :param name: Name of the structure definition.
        :type name: str
        :param base: Base type of the structure definition.
        :type base: Base or None
        :param length: Length of the structure definition.
        :type length: int
        """
        Base.__init__(self, D)
        BaseStructureDefinition.__init__(self, base)
        self.__name: str = name
        self.__length: int = length

    def check_value(self, value: StrVal) -> bool:
        """
        Checks if the given value is a valid value for this StaticStructureDefinition.

        :param value: The value to check.
        :type value: StrVal
        :return: True if the given value is valid for this StaticStructureDefinition, False otherwise.
        :rtype: bool
        """
        return BaseStructureDefinition.check_value(self, value)

    def get_attributes(self) -> StaAttr:
        """
        Gets the attributes of this StaticStructureDefinition.

        :return: The attributes of this StaticStructureDefinition.
        :rtype: Tuple[str, int, Dict[str, Any]]
        """
        return S, self.__length, super().get_base().get_attributes()

    def check_length(self, value: StrVal) -> bool:
        """
        Checks if the given value has the correct length for this StaticStructureDefinition.

        :param value: The value to check.
        :type value: StrVal
        :return: True if the given value has the correct length for this StaticStructureDefinition, False otherwise.
        :rtype: bool
        """
        return len(value) == self.__length

    def __str__(self):
        """
        Returns a string representation of this StaticStructureDefinition.

        :return: A string representation of this StaticStructureDefinition.
        :rtype: str
        """
        return self.__name + ": [" + super().get_type() + "] " \
            + "{Length = " + str(self.__length) + \
            ", Base Type =" + str(super().get_base()) + "}"
