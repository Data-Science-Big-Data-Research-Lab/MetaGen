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
