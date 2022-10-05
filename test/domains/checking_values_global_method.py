from utils import run_basic_test, run_layer_test, domain, run_layer_element_test, run_basic_vector_test, \
    get_vector_layer_element_test, run_vector_layer_element_test, run_vector_layer_test

# ==================================================================================================================== #
# ======================================= 1. Checking BASIC values =================================================== #
# ==================================================================================================================== #

run_basic_test("I")
run_basic_test("R")
run_basic_test("C")

# ==================================================================================================================== #
# ===================== 2. Checking layer or element values of a LAYER VARIABLE ====================================== #
# ==================================================================================================================== #

run_layer_test("L")
run_layer_element_test("L", "EI")
run_layer_element_test("L", "ER")
run_layer_element_test("L", "EC")

# ==================================================================================================================== #
# =============================== 3. Checking values of a BASIC VECTOR variable ====================================== #
# ==================================================================================================================== #

run_basic_vector_test("VI")
run_basic_vector_test("VR")
run_basic_vector_test("VC")

# ==================================================================================================================== #
# ======================== 4. Checking layer or element values of a LAYER VECTOR variable ============================ #
# ==================================================================================================================== #

run_vector_layer_test("VL")
run_vector_layer_element_test("VL", "el1")
run_vector_layer_element_test("VL", "el2")
run_vector_layer_element_test("VL", "el3")

# ==================================================================================================================== #
# =============================================== General errors ===================================================== #
# ==================================================================================================================== #

# **** Argument type errors (static):
# - The variable must and the element be str.
# res = domain.check_value(1, 2)
# res = domain.check_value(1, 2, "el1")
# res = domain.check_value(1, 2, 1)

# **** Argument type errors (dynamic, raise ValueError):
# - With BASIC variables, element checking does not apply.
# res = domain.check_value("C", 1, "el-1")
# - Trying to check an element's value without specifying the element name.
# res = domain.check_value("L", 2)
# res = domain.check_value("VL", 2)
#  - Trying to check an element's value with a value different from int, float, or str.
# res = domain.check_value("L", {"EI": 20, "ER": 1.8, "EC": "Lb2"}, "EI")
# res = domain.check_value("VL", {"el1": 14, "el2": 0.15, "el3": 4}, "el1")

# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# res = domain.check_value("J", 2)
# res = domain.check_value("J", 2, "el1")
# - The element is not defined.
# domain.check_value("L", 1, "an_element")
# domain.check_value("VL", 1, "an_element")
#  - The components of the VECTOR variable are not defined.
# res = domain.check_value("VN", 2)
# - The size of the values is not compatible with the vector definition.
# res = domain.check_value("VI", [1, 2])


