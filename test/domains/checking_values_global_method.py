from utils import run_basic_test, run_layer_test, domain, run_layer_element_test, run_basic_vector_test

# ==================================================================================================================== #
# ============================================= 0. General errors ==================================================== #
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
#  - Trying to check an element's value with a value different from int, float, or str.
# res = domain.check_value("L", {"EI": 20, "ER": 1.8, "EC": "Lb2"}, "EI")

# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# res = domain.check_value("J", 2)
# res = domain.check_value("J", 2, "el1")
# - The element is not defined.
# domain.check_value("L", 1, "an_element")
#  - The components of the VECTOR variable are not defined.
# res = domain.check_value("VN", 2)
# - The size of the values is not compatible with the vector definition.
# res = domain.check_value("VI", [1, 2])

# ==================================================================================================================== #
# ======================================= 1. Checking BASIC values =================================================== #
# ==================================================================================================================== #

# run_basic_test("I")
# run_basic_test("R")
# run_basic_test("C")

# ==================================================================================================================== #
# ===================== 2. Checking layer or element values of a LAYER VARIABLE ====================================== #
# ==================================================================================================================== #

# run_layer_test("L")
# run_layer_element_test("L", "EI")
# run_layer_element_test("L", "ER")
# run_layer_element_test("L", "EC")

# ==================================================================================================================== #
# =============================== 3. Checking values of a BASIC VECTOR variable ====================================== #
# ==================================================================================================================== #

run_basic_vector_test("VI")
run_basic_vector_test("VR")
run_basic_vector_test("VC")

# ==================================================================================================================== #
# ======================== 5. Checking elements values of a LAYER VECTOR variable ==================================== #
# ==================================================================================================================== #

# Values to check
# component_element_a = 20
# component_element_b = 25
# component_element_c = 0.2
# component_element_d = 0.001
# component_element_e = 1
# component_element_f = 30
# component_element_g = "Tag1"
#
# # # Value compatibility of the el1 element of VL
# V_L_el_1_comp_A = domain.check_value("VL", component_element_a, "el1")
# V_L_el_1_comp_B = domain.check_value("VL", component_element_b, "el1")
# V_L_el_1_comp_C = domain.check_value("VL", component_element_c, "el1")
# V_L_el_1_comp_G = domain.check_value("VL", component_element_g, "el1")
# print("Are these values compatible with the el1 element definition of the components of VL ? ")
# print(str(component_element_a) + " => " + str(V_L_el_1_comp_A) + " , "
#       + str(component_element_b) + " => " + str(V_L_el_1_comp_B) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_1_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_1_comp_G) + "\n")
#
# # Value compatibility of the el2 element of VL
# V_L_el_2_comp_C = domain.check_value("VL", component_element_c, "el2")
# V_L_el_2_comp_D = domain.check_value("VL", component_element_d, "el2")
# V_L_el_2_comp_A = domain.check_value("VL", component_element_a, "el2")
# V_L_el_2_comp_G = domain.check_value("VL", component_element_g, "el2")
# print("Are these values compatible with the el2 element definition of the components of VL ? ")
# print(str(component_element_c) + " => " + str(V_L_el_2_comp_C) + " , "
#       + str(component_element_d) + " => " + str(V_L_el_2_comp_D) + " , "
#       + str(component_element_a) + " => " + str(V_L_el_2_comp_A) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_2_comp_G) + "\n")
#
# # Value compatibility of the el3 element of VL
# V_L_el_3_comp_E = domain.check_value("VL", component_element_e, "el3")
# V_L_el_3_comp_F = domain.check_value("VL", component_element_f, "el3")
# V_L_el_3_comp_C = domain.check_value("VL", component_element_c, "el3")
# V_L_el_3_comp_G = domain.check_value("VL", component_element_g, "el3")
# print("Are these values compatible with the el3 element definition of the components of VL ? ")
# print(str(component_element_e) + " => " + str(V_L_el_3_comp_E) + " , "
#       + str(component_element_f) + " => " + str(V_L_el_3_comp_F) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_3_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_3_comp_G) + "\n")

# ==================================================================================================================== #
# ============================= 7. Checking layers for a LAYER VECTOR ================================================ #
# ==================================================================================================================== #

# vector_layer_a = {"el1": 15, "el2": 0.2, "el3": 2}
# vector_layer_b = {"el1": 8, "el2": 0.3, "el3": 1}
# vector_layer_c = {"el1": 17, "el2": 0.05, "el3": 2}
# vector_layer_d = {"el1": 14, "el2": 0.15, "el3": 4}
#
# V_L_layer_a = domain.check_value("VL", vector_layer_a)
# V_L_layer_b = domain.check_value("VL", vector_layer_b)
# V_L_layer_c = domain.check_value("VL", vector_layer_c)
# V_L_layer_d = domain.check_value("VL", vector_layer_d)
# print("Are these layers compatible with VL definition ? ")
# print(str(vector_layer_a) + " => " + str(V_L_layer_a) + "\n" + str(vector_layer_b) + " => " + str(V_L_layer_b) + "\n"
#       + str(vector_layer_c) + " => " + str(V_L_layer_c) + "\n" + str(vector_layer_d) + " => " + str(V_L_layer_d) + "\n")

# ==================================================================================================================== #
# ========================= 8. Checking complete layer values for a LAYER VECTOR ===================================== #
# ==================================================================================================================== #


# vector_layer_values_b = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]
# vector_layer_values_c = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": "V1"}]
# vector_layer_values_d = [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}
#     , {"el1": 14, "el2": 0.15, "el3": 3}, {"el1": 17, "el2": 0.25, "el3": 2}]
#
# V_L_vector_layer_a = domain.check_value("VL", vector_layer_values_a)
# V_L_vector_layer_b = domain.check_value("VL", vector_layer_values_b)
# V_L_vector_layer_c = domain.check_value("VL", vector_layer_values_c)
# V_L_vector_layer_d = domain.check_value("VL", vector_layer_values_d)
# print("Are these layer values compatible with VL definition ? ")
# print(str(vector_layer_values_a) + " => " + str(V_L_vector_layer_a) + "\n"
#       + str(vector_layer_values_b) + " => " + str(V_L_vector_layer_b) + "\n"
#       + str(vector_layer_values_c) + " => " + str(V_L_vector_layer_c) + "\n"
#       + str(vector_layer_values_d) + " => " + str(V_L_vector_layer_d) + "\n")
