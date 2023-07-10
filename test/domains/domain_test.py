
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


"""
# ******** VECTOR TESTS ********

# ****** INTEGER ******
@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_integer_positive_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "min_value": int,
        "max_value": int,
        "values": str,
        "remaining": int
    },
)
def test_define_vector_integer_domain_positive(variable: str, min_size: int, max_size: int, step_size: int, min_value: int, max_value: int, step_val: int | None, values: str, remaining: int) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    if step_val == '':
        step_val = None
    else:
        step_val = int(step_val)

    values = [int(v) for v in values.split(";")]

    domain: Domain = Domain()
    domain.define_vector(variable, min_size, max_size)
    domain.define_components_as_integer(
        variable, min_value, max_value, step_val)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(variable)[0] == VECTOR
    assert domain.get_variable_definition(variable)[1] == min_size
    assert domain.get_variable_definition(variable)[2] == max_size
    assert domain.get_variable_definition(variable)[4][0] == INTEGER
    assert domain.get_variable_definition(variable)[4][1] == min_value
    assert domain.get_variable_definition(variable)[4][2] == max_value
    assert domain.get_vector_components_type(variable) == INTEGER
    assert domain.are_defined_components(variable)
    assert domain.get_variable_type(variable) == VECTOR
    assert domain.check_value(variable, values)
    assert domain.get_remaining_available_complete_components(
        variable, len(values)) == remaining
    assert len(domain.get_vector_variable_attributes(variable)) == 3
    assert domain.check_vector_basic_values(variable, values)


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_integer_negative_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "min_value": int,
        "max_value": int,
        "values": str,
    },
)
def test_define_vector_integer_domain_negative(variable: str, min_size: int, max_size: int, step_size: int, min_value: int, max_value: int, step_val: int | None, values: str) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    if step_val == '':
        step_val = None
    else:
        step_val = int(step_val)

    values = [int(v) for v in values.split(";") if v != '']

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    with pytest.raises(TypeError):
        domain.define_vector(variable, float(min_size), max_size, step_size)

    with pytest.raises(TypeError):
        domain.define_vector(variable, min_size, float(max_size), step_size)

    with pytest.raises(TypeError):
        domain.define_vector(variable, min_size, max_size, float(step_size))

    with pytest.raises(TypeError):
        domain.define_vector(variable, min_size, None, step_size)

    with pytest.raises(TypeError):
        domain.define_vector(variable, None, max_size, step_size)

    with pytest.raises(ValueError):
        domain.define_vector(variable, max_size, min_size, step_size)

    domain.define_vector(variable, min_size, max_size, step_size)

    with pytest.raises(TypeError):
        domain.define_components_as_integer(
            variable, float(min_value), max_value, step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_integer(
            variable, min_value, float(max_value), step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_integer(
            variable, min_value, max_value, float(step_val))

    with pytest.raises(TypeError):
        domain.define_components_as_integer(
            variable, min_value, None, step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_integer(
            variable, None, max_value, step_val)

    with pytest.raises(ValueError):
        domain.define_components_as_integer(
            variable, max_value, min_value, step_val)

    domain.define_components_as_integer(
        variable, min_value, max_value, step_val)

    try:
        assert not domain.check_value(variable, values)
    except Exception as e:
        if type(e) != AssertionError:
            assert type(e) == DefinitionError

# ****** REAL ******


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_real_positive_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "min_value": float,
        "max_value": float,
        "values": str,
        "remaining": float
    },
)
def test_define_vector_real_domain_positive(variable: str, min_size: int, max_size: int, step_size: int, min_value: float, max_value: float, step_val: float | None, values: str, remaining: float) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    if step_val == '':
        step_val = None
    else:
        step_val = float(step_val)

    values = [float(v) for v in values.split(";")]

    domain: Domain = Domain()
    domain.define_vector(variable, min_size, max_size)
    domain.define_components_as_real(
        variable, min_value, max_value, step_val)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(variable)[0] == VECTOR
    assert domain.get_variable_definition(variable)[1] == min_size
    assert domain.get_variable_definition(variable)[2] == max_size
    assert domain.get_variable_definition(variable)[4][0] == REAL
    assert domain.get_variable_definition(variable)[4][1] == min_value
    assert domain.get_variable_definition(variable)[4][2] == max_value
    assert domain.get_vector_components_type(variable) == REAL
    assert domain.are_defined_components(variable)
    assert domain.get_variable_type(variable) == VECTOR
    print(values)
    assert domain.check_value(variable, values)
    assert domain.get_remaining_available_complete_components(
        variable, len(values)) == remaining
    assert len(domain.get_vector_variable_attributes(variable)) == 3
    assert domain.check_vector_basic_values(variable, values)


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_real_negative_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "min_value": float,
        "max_value": float,
        "values": str,
    },
)
def test_define_vector_real_domain_negative(variable: str, min_size: int, max_size: int, step_size: int, min_value: float, max_value: float, step_val: float | None, values: str) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    if step_val == '':
        step_val = None
    else:
        step_val = float(step_val)

    values = [float(v) for v in values.split(";") if v != '']

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    domain.define_vector(variable, min_size, max_size, step_size)

    with pytest.raises(TypeError):
        domain.define_components_as_real(
            variable, int(min_value), max_value, step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_real(
            variable, min_value, int(max_value), step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_real(
            variable, min_value, max_value, int(step_val))

    with pytest.raises(TypeError):
        domain.define_components_as_real(
            variable, min_value, None, step_val)

    with pytest.raises(TypeError):
        domain.define_components_as_real(
            variable, None, max_value, step_val)

    with pytest.raises(ValueError):
        domain.define_components_as_real(
            variable, max_value, min_value, step_val)

    domain.define_components_as_real(
        variable, min_value, max_value, step_val)

    try:
        assert not domain.check_value(variable, values)
    except Exception as e:
        if type(e) != AssertionError:
            assert type(e) == DefinitionError


# ****** CATEGORICAL ******
@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_categorical_positive_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "categories": str
    },
)
def test_define_vector_categorical_domain_positive(variable: str, min_size: int, max_size: int, step_size: int, categories: str) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    categories = categories.split(";")

    domain: Domain = Domain()
    domain.define_vector(variable, min_size, max_size)
    domain.define_components_as_categorical(
        variable, categories)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(variable)[0] == VECTOR
    assert domain.get_variable_definition(variable)[1] == min_size
    assert domain.get_variable_definition(variable)[2] == max_size
    assert domain.get_variable_definition(variable)[4][0] == CATEGORICAL
    assert domain.get_variable_definition(variable)[4][1] == categories
    assert domain.get_vector_components_type(variable) == CATEGORICAL
    assert domain.are_defined_components(variable)
    assert domain.check_value(variable, categories[:max_size])
    assert len(domain.get_vector_variable_attributes(variable)) == 3
    assert domain.check_vector_basic_values(variable, categories[:max_size])


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/vector_categorical_negative_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "min_size": int,
        "max_size": int,
        "categories": str
    },
)
def test_define_vector_categorical_domain_negative(variable: str, min_size: int, max_size: int, step_size: int, categories: str) -> None:
    if step_size == '':
        step_size = None
    else:
        step_size = int(step_size)

    categories = categories.split(";")

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    domain.define_vector(variable, min_size, max_size, step_size)

    with pytest.raises(ValueError):
        domain.define_components_as_categorical(
            variable, categories)

# ******** LAYER ********

# ****** INTEGER *******


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/layer_integer_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "minimum": int,
        "maximum": int
    },
)
def test_define_layer_integer_domain_positive(variable: str, layer_variable: str, minimum: int, maximum: int, step: int) -> None:
    if step == '':
        step = None
    else:
        step = int(step)

    domain: Domain = Domain()
    domain.define_layer(variable)
    domain.define_integer_element(
        variable, layer_variable, minimum, maximum, step)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(variable)[0] == LAYER
    assert domain.get_variable_definition(
        variable)[1][layer_variable][0] == INTEGER
    assert domain.get_variable_definition(
        variable)[1][layer_variable][1] == minimum
    assert domain.get_variable_definition(
        variable)[1][layer_variable][2] == maximum

    assert domain.get_layer_element_type(variable, layer_variable) == INTEGER
    assert domain.is_defined_element(variable, layer_variable)
    assert domain.check_value(variable, {layer_variable: minimum})
    assert len(domain.get_element_definition(variable, layer_variable)) == 4


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/layer_integer_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "minimum": int,
        "maximum": int
    },
)
def test_define_layer_integer_domain_negative(variable: str, layer_variable: str, minimum: int, maximum: int, step: int) -> None:
    if step == '':
        step = None
    else:
        step = int(step)

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    domain.define_layer(variable)

    with pytest.raises(DefinitionError):
        domain.get_element_definition(variable, layer_variable)

    assert not domain.is_defined_element(variable, layer_variable)

    # Revisar excepciones, quizás todo debería ser DefinitionError
    with pytest.raises(ValueError):
        domain.define_integer_element(
            variable, layer_variable, maximum, minimum, step)

    with pytest.raises(DefinitionError):
        domain.define_integer_element(
            variable, layer_variable, minimum, maximum, 0)

# ****** REAL *******


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/layer_real_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "minimum": float,
        "maximum": float
    },
)
def test_define_layer_real_domain_positive(variable: str, layer_variable: str, minimum: float, maximum: float, step: float) -> None:
    if step == '':
        step = None
    else:
        step = float(step)

    domain: Domain = Domain()
    domain.define_layer(variable)
    domain.define_real_element(
        variable, layer_variable, minimum, maximum, step)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(
        variable)[1][layer_variable][0] == REAL
    assert domain.get_variable_definition(
        variable)[1][layer_variable][1] == minimum
    assert domain.get_variable_definition(
        variable)[1][layer_variable][2] == maximum

    assert domain.get_layer_element_type(variable, layer_variable) == REAL
    assert domain.is_defined_element(variable, layer_variable)
    assert domain.check_value(variable, {layer_variable: minimum})
    # TODO: Los gets no tienen nombres muy intuitivos y además aquí se devuelve el tipo cuando en las otras propiedades no
    assert len(domain.get_element_definition(variable, layer_variable)) == 4


@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/layer_real_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "minimum": float,
        "maximum": float
    },
)
def test_define_layer_real_domain_negative(variable: str, layer_variable: str, minimum: float, maximum: float, step: float) -> None:
    if step == '':
        step = None
    else:
        step = float(step)

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    domain.define_layer(variable)

    with pytest.raises(DefinitionError):
        domain.get_element_definition(variable, layer_variable)

    assert not domain.is_defined_element(variable, layer_variable)

    with pytest.raises(ValueError):
        domain.define_real_element(
            variable, layer_variable, maximum, minimum, step)

    with pytest.raises(DefinitionError):
        domain.define_real_element(
            variable, layer_variable, minimum, maximum, 0.)


# ****** CATEGORICAL *******
@csv_params(
    data_file=pathlib.Path(
        __file__).parents[0].resolve().as_posix()+"/resources/layer_categorical_positive_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "categories": str,
    },
)
def test_define_layer_categorical_domain_positive(variable: str, layer_variable: str, categories: str) -> None:
    categories = categories.split(";")

    domain: Domain = Domain()

    domain.define_layer(variable)
    domain.define_categorical_element(
        variable, layer_variable, categories)

    assert domain is not None
    assert domain.is_defined_variable(variable)
    assert domain.get_variable_definition(variable)[0] == LAYER
    assert domain.get_variable_definition(
        variable)[1][layer_variable][0] == CATEGORICAL
    assert domain.get_variable_definition(
        variable)[1][layer_variable][1] == categories
    assert domain.get_layer_element_type(
        variable, layer_variable) == CATEGORICAL
    assert domain.is_defined_element(variable, layer_variable)
    for category in categories:
        assert domain.check_value(variable, category, layer_variable)
    assert len(domain.get_element_definition(variable, layer_variable)) == 2


@csv_params(
    data_file=pathlib.Path(__file__).parents[0].resolve(
    ).as_posix()+"/resources/layer_categorical_negative_test.csv",
    id_col="ID#",
    data_casts={
        "variable": str,
        "layer_variable": str,
        "categories": str
    },
)
def test_define_layer_categorical_domain_negative(variable: str, layer_variable: str, categories: str) -> None:
    categories = categories.split(";")

    domain: Domain = Domain()

    with pytest.raises(DefinitionError):
        domain.get_variable_definition(variable)

    assert not domain.is_defined_variable(variable)

    domain.define_layer(variable)

    with pytest.raises(DefinitionError):
        domain.get_element_definition(variable, layer_variable)

    assert not domain.is_defined_element(variable, layer_variable)

    with pytest.raises(ValueError):
        domain.define_categorical_element(variable, layer_variable, categories)
"""
