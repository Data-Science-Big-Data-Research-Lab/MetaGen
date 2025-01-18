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
import json
import pathlib
import sys
import pytest
from pytest_csv_params.decorator import csv_params
from os import path

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
from utils import solution


def parse_input(type_col, value):
    if type_col == "int":
        value = int(value)
    elif type_col == "float":
        value = float(value)
    elif type_col == "vector-int":
        value = [int(v) for v in value.split(";") if v != ""]
    elif type_col == "vector-float":
        value = [float(v) for v in value.split(";") if v != ""]
    elif type_col == "vector-str":
        value = [v for v in value.split(";") if v != ""]
    elif type_col == "layer":
        value = json.loads(value)

    return value


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix() + "/resources/positive.csv",
    data_casts={
        "variable": str,
        "type_var": str,
        "value": str
    },
)
def test_set_raw_positive(variable: str, type_var: str, value: str) -> None:
    value = parse_input(type_var, value)
    # To build an internal best solution, instantiate the Solution class with best=True and legacy_domain=legacy_domain
    # TODO: El dominio debería ser el primer parámetro

    solution.set(variable, value)

    assert solution.get(variable).value == value
    assert solution.is_available(variable)


@csv_params(
    data_file=pathlib.Path(__file__).parents[0].resolve(
    ).as_posix() + "/resources/negative.csv",
    data_casts={
        "variable": str,
        "type_var": str,
        "value": str
    },
)
def test_define_integer_domain_negative(variable: str, type_var: str, value: str) -> None:
    value = parse_input(type_var, value)
    # To build an internal best solution, instantiate the Solution class with best=True and legacy_domain=legacy_domain

    with pytest.raises(ValueError):
        solution.set(variable, value)


def test_define_integer_domain_negative_common_mistakes() -> None:
    value = "EXAMPLE"
    # To build an internal best solution, instantiate the Solution class with best=True and legacy_domain=legacy_domain

    with pytest.raises(ValueError):
        solution.set("THISVALUEDOESNOTEXISTS", value)

    with pytest.raises(ValueError):
        solution.set(None, value)

    with pytest.raises(ValueError):
        solution.set(-1, value)

    with pytest.raises(ValueError):
        solution.set("L", {"THISVALUEDOESNOTEXISTS": value})

    with pytest.raises(ValueError):
        solution.set("L", {"ER": value})
