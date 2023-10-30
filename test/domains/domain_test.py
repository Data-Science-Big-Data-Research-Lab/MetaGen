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

import pathlib

import pytest
from pytest_csv_params.decorator import csv_params

from metagen.framework import Domain
from metagen.framework.domain.core import (CategoricalDefinition,
                                           IntegerDefinition, RealDefinition)
from metagen.framework.solution.literals import CATEGORICAL, INTEGER, REAL

# ******** INTEGER TESTS ********


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/integer_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "minimum": int,
        "maximum": int
    },
)
def test_define_integer_domain_positive(variable: str, minimum: int, maximum: int, step: int | None) -> None:
    if step == '':
        step = None
    else:
        step = int(step)
    domain: Domain = Domain()
    domain.define_integer(variable, minimum, maximum, step)

    assert domain is not None
    assert domain.get_core().is_variable(variable)

    variable_definition: IntegerDefinition = domain.get_core().get(variable)
    assert variable_definition is not None
    attributes = variable_definition.get_attributes()
    assert attributes is not None
    assert attributes[0] == INTEGER
    assert attributes[1] == minimum
    assert attributes[2] == maximum
    assert variable_definition.check_value(minimum)
    assert variable_definition.check_value(maximum)
    assert variable_definition.check_value((maximum - minimum) // 2)
    assert variable_definition.check_value(maximum - 1)
    assert variable_definition.check_value(minimum + 1)


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/integer_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "minimum": int,
        "maximum": int
    },
)
def test_define_integer_domain_negative(variable: str, minimum: int, maximum: int, step: int | None) -> None:
    if step == '':
        step = None
    else:
        step = int(step)

    domain: Domain = Domain()

    with pytest.raises(KeyError):
        domain.get_core().get(variable)

    assert not domain.get_core().is_variable(variable)

    domain.define_integer(variable, minimum, maximum)

    assert domain.get_core().is_variable(variable)

    assert not domain.get_core().get(variable).check_value(minimum-1)
    assert not domain.get_core().get(variable).check_value(maximum+1)


# ******** REAL TESTS ********
@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/real_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "minimum": float,
        "maximum": float
    },
)
def test_define_real_domain_positive(variable: str, minimum: float, maximum: float, step: float | None) -> None:
    if step == '':
        step = None
    else:
        step = float(step)
    domain: Domain = Domain()
    domain.define_real(variable, minimum, maximum, step)

    assert domain is not None
    assert domain.get_core().is_variable(variable)

    variable_definition: RealDefinition = domain.get_core().get(variable)
    assert variable_definition is not None
    attributes = variable_definition.get_attributes()
    assert attributes is not None
    assert attributes[0] == REAL
    assert attributes[1] == minimum
    assert attributes[2] == maximum
    assert variable_definition.check_value(minimum)
    assert variable_definition.check_value(maximum)
    assert variable_definition.check_value((maximum - minimum) // 2)
    assert variable_definition.check_value(maximum - 1)
    assert variable_definition.check_value(minimum + 1)


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/real_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "minimum": float,
        "maximum": float
    },
)
def test_define_real_domain_negative(variable: str, minimum: float, maximum: float, step: float | None) -> None:
    if step == '':
        step = None
    else:
        step = float(step)

    domain: Domain = Domain()

    with pytest.raises(KeyError):
        domain.get_core().get(variable)

    assert not domain.get_core().is_variable(variable)

    domain.define_real(variable, minimum, maximum)

    assert domain.get_core().is_variable(variable)

    assert not domain.get_core().get(variable).check_value(minimum-0.001)
    assert not domain.get_core().get(variable).check_value(maximum+0.001)


# ******** CATEGORICAL TESTS ********
@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/categorical_positive_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "categories": str
    },
)
def test_define_categorical_domain_positive(variable: str, categories: str) -> None:
    categories = categories.split(';')
    domain: Domain = Domain()
    domain.define_categorical(variable, categories)

    assert domain is not None
    assert domain.get_core().is_variable(variable)

    variable_definition: CategoricalDefinition = domain.get_core().get(variable)
    assert variable_definition is not None
    attributes = variable_definition.get_attributes()
    assert attributes is not None
    assert attributes[0] == CATEGORICAL
    assert attributes[1] == categories

    for category in categories:
        assert variable_definition.check_value(category)

    for category in categories:
        assert not variable_definition.check_value(category+"$random_string%")