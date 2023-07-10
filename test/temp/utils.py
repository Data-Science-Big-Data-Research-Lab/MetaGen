from typing import Tuple

domain = None
def str_test(test: Tuple[str, dict]):
    print("\n" + test[0] + " test ==> "
          + domain.str_variable_definition(test[0]))
    for t, v in test[1].items():
        print(str(t) + " => " + str(v))


def str_element_test(test: Tuple[str, str, dict]):
    print("\n" + test[0] + "." + test[1] + " test ==> "
          + domain.str_element_definition(test[0], test[1]))
    for t, v in test[2].items():
        print(str(t) + " => " + str(v))


def str_vector_element_test(test: Tuple[str, str, dict]):
    print("\n" + test[0] + "." + test[1] + " test ==> "
          + domain.str_layer_vector_element_definition(test[0], test[1]))
    for t, v in test[2].items():
        print(str(t) + " => " + str(v))


def get_basic_test(variable: str) -> Tuple[str, dict]:
    runs = {
        "2": domain.check_value(variable, 2),
        "-1": domain.check_value(variable, -1),
        "0.001": domain.check_value(variable, 0.001),
        "1.2": domain.check_value(variable, 1.2),
        "\"C1\"": domain.check_value(variable, "C1"),
        "\"V1\"": domain.check_value(variable, "V1"),
        "{\"EI\": 20, \"ER\": 1.8, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": 20, "ER": 1.8, "EC": "Lb2"}),
        "[1, 2, 3, 4, 5, 1, 2, 3, 4, 5]": domain.check_value(variable, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]),
        "[{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}]":
            domain.check_value(variable, [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}])
    }
    return variable, runs


def run_basic_test(variable: str):
    str_test(get_basic_test(variable))


def get_layer_test(variable: str) -> Tuple[str, dict]:
    runs = {
        "{\"EI\": 20, \"ER\": 1.8, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": 20, "ER": 1.8, "EC": "Lb2"}),
        "{\"EI\": -1, \"ER\": 1.8, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": -1, "ER": 1.8, "EC": "Lb2"}),
        "{\"EI\": 20, \"ER\": 1.0, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": 20, "ER": 1.0, "EC": "Lb2"}),
        "{\"EI\": 20, \"ER\": 1.8, \"EC\": \"Lb4\"}": domain.check_value(variable, {"EI": 20, "ER": 1.8, "EC": "Lb4"}),
        "{\"EI\": \"1\", \"ER\": 1.8, \"EC\": \"Lb2\"}":
            domain.check_value(variable, {"EI": "1", "ER": 1.8, "EC": "Lb2"}),
        "{\"EI\": 20, \"ER\": 2, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": 20, "ER": 2, "EC": "Lb2"}),
        "{\"EI\": 20, \"ER\": 1.8, \"EC\": 1.2}": domain.check_value(variable, {"EI": 20, "ER": 1.8, "EC": 1.2}),

        "[1, 2, 3, 4, 5, 1, 2, 3, 4, 5]": domain.check_value(variable, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]),
        "[{el1: 15, el2: 0.2, el3: 2}, {el1: 12, el2: 0.3, el3: 1}]": domain.check_value(variable, [
            {"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}])
    }
    return variable, runs


def run_layer_test(variable: str):
    str_test(get_layer_test(variable))


def get_layer_element_test(variable: str, element: str) -> Tuple[str, str, dict]:
    runs = {
        "20": domain.check_value(variable, 2, element),
        "200": domain.check_value(variable, 200, element),
        "1.8": domain.check_value(variable, 1.8, element),
        "3.5": domain.check_value(variable, 3.5, element),
        "\"Lb1\"": domain.check_value(variable, "Lb1", element),
        "\"C1\"": domain.check_value(variable, "C1", element),
        "[1, 2, 3, 4, 5, 1, 2, 3, 4, 5]":
            domain.check_value(variable, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5], element),
        "[{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}]":
            domain.check_value(variable,
                               [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}], element)
    }
    return variable, element, runs


def run_layer_element_test(variable: str, element: str):
    str_element_test(get_layer_element_test(variable, element))


def get_basic_vector_test(variable: str) -> Tuple[str, dict]:
    runs = {
        "[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]": domain.check_value(variable, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
        "[1, 20, 3, 4, 5, 1, 20, 3, 4, 5]": domain.check_value(variable, [1, 20, 3, 4, 5, 1, 20, 3, 4, 5]),
        "[0.001, 0.002, 0.003, 0.004, 0.005, 0.001, 0.002, 0.003, 0.004, 0.005]":
            domain.check_value(variable, [0.001, 0.002, 0.003, 0.004, 0.005, 0.001, 0.002, 0.003, 0.004, 0.005]),
        "[0.001, 0.002, 0.003, 0.004, 5.0, 0.001, 0.002, 0.003, 0.004, 5]":
            domain.check_value(variable, [0.001, 0.002, 0.003, 0.004, 5.0, 0.001, 0.002, 0.003, 0.004, 5]),
        "[\"V1\", \"V2\", \"V3\", \"V1\", \"V2\", \"V3\", \"V1\", \"V2\", \"V3\", \"V1\"]":
            domain.check_value(variable, ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]),
        "[\"V1\", \"V2\", 1, \"V1\", \"V2\", \"V3\", \"V1\", \"V2\", \"V3\", \"V1\"]":
            domain.check_value(variable, ["V1", "V2", 1, "V1", "V2", "V3", "V1", "V2", "V3", "V1"]),
        "8": domain.check_value(variable, 8),
        "0.001": domain.check_value(variable, 0.001),
        "1.2": domain.check_value(variable, 1.2),
        "\"C1\"": domain.check_value(variable, "C1"),
        "\"V1\"": domain.check_value(variable, "V1"),
        "[{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}]":
            domain.check_value(variable,
                               [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]),
        "{\"EI\": 20, \"ER\": 1.8, \"EC\": \"Lb2\"}": domain.check_value(variable, {"EI": 20, "ER": 1.8, "EC": "Lb2"})
    }
    return variable, runs


def run_basic_vector_test(variable: str):
    str_test(get_basic_vector_test(variable))


def get_vector_layer_element_test(variable: str, element: str) -> Tuple[str, str, dict]:
    runs = {
        "20": domain.check_value(variable, 20, element),
        "25": domain.check_value(variable, 25, element),
        "0.2": domain.check_value(variable, 0.2, element),
        "0.001": domain.check_value(variable, 0.001, element),
        "1": domain.check_value(variable, 1, element),
        "30": domain.check_value(variable, 30, element),
        "\"Tag1\"": domain.check_value(variable, "Tag1", element)
    }
    return variable, element, runs


def run_vector_layer_element_test(variable: str, element: str):
    str_vector_element_test(get_vector_layer_element_test(variable, element))


def get_vector_layer_test(variable: str) -> Tuple[str, dict]:
    runs = {
        "{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}":
            domain.check_value(variable, {"el1": 15, "el2": 0.2, "el3": 2}),
        "{\"el1\": 8, \"el2\": 0.3, \"el3\": 1}":
            domain.check_value(variable, {"el1": 8, "el2": 0.3, "el3": 1}),
        "{\"el1\": 17, \"el2\": 0.05, \"el3\": 2}":
            domain.check_value(variable, {"el1": 17, "el2": 0.05, "el3": 2}),
        "{\"el1\": 14, \"el2\": 0.15, \"el3\": 4}":
            domain.check_value(variable, {"el1": 14, "el2": 0.15, "el3": 4}),
        "[{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}]":
            domain.check_value(variable,
                               [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]),
        "[{\"el1\": 25, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}]":
            domain.check_value(variable,
                               [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]),
        "[{\"el1\": 25, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": \"V1\"}]":
            domain.check_value(variable,
                               [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": "V1"}]),
        "[{\"el1\": 15, \"el2\": 0.2, \"el3\": 2}, {\"el1\": 12, \"el2\": 0.3, \"el3\": 1}, "
        "{\"el1\": 14, \"el2\": 0.15, \"el3\": 3}, {\"el1\": 17, \"el2\": 0.25, \"el3\": 2}]":
            domain.check_value(variable,
                               [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}
                                   , {"el1": 14, "el2": 0.15, "el3": 3}, {"el1": 17, "el2": 0.25, "el3": 2}]),
        "[1, 2, 3, 4, 5, 1, 2, 3, 4, 5]":
            domain.check_value(variable, [1, 2, 3, 4, 5, 1, 2, 3, 4, 5])
    }
    return variable, runs


def run_vector_layer_test(variable: str):
    str_test(get_vector_layer_test(variable))
