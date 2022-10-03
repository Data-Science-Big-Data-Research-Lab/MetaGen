from pycvoa.use_cases.domains.support_domain import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ======================================= 1. Checking BASIC values =================================================== #
# ==================================================================================================================== #

# Values to check
basic_value_a = 2
basic_value_b = -1
basic_value_c = 0.001
basic_value_d = 1.2
basic_value_e = "C1"
basic_value_f = "V1"

# Value compatibility of the definition of I
I_comp_A = domain.check_value("I", basic_value_a)
I_comp_B = domain.check_value("I", basic_value_b)
I_comp_C = domain.check_value("I", basic_value_c)
I_comp_E = domain.check_value("I", basic_value_e)
print("Are these values compatible with the definition of I in this domain ? ")
print(str(basic_value_a) + " => " + str(I_comp_A) + " , " + str(basic_value_b) + " => " + str(I_comp_B) + " , "
      + str(basic_value_c) + " => " + str(I_comp_C) + " , " + str(basic_value_e) + " => " + str(I_comp_E) + "\n")

# Value compatibility of the definition of R
R_comp_C = domain.check_value("R", basic_value_c)
R_comp_D = domain.check_value("R", basic_value_d)
R_comp_A = domain.check_value("R", basic_value_a)
R_comp_E = domain.check_value("R", basic_value_e)
print("Are these values compatible with the definition of R in this domain ? ")
print(str(basic_value_c) + " => " + str(R_comp_C) + " , " + str(basic_value_d) + " => " + str(R_comp_D) + " , "
      + str(basic_value_a) + " => " + str(R_comp_A) + " , " + str(basic_value_e) + " => " + str(R_comp_E) + "\n")

# Value compatibility of the definition of C
C_comp_E = domain.check_value("C", basic_value_e)
C_comp_F = domain.check_value("C", basic_value_f)
C_comp_A = domain.check_value("C", basic_value_a)
C_comp_C = domain.check_value("C", basic_value_c)
print("Are these values compatible with the definition of C in this domain ? ")
print(str(basic_value_e) + " => " + str(C_comp_E) + " , " + str(basic_value_f) + " => " + str(C_comp_F) + " , "
      + str(basic_value_a) + " => " + str(C_comp_A) + " , " + str(basic_value_c) + " => " + str(C_comp_C) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# res = domain.check_value(1, 2)

# **** Argument type errors (dynamic, raise ValueError):
# - Element checking does not apply.
# res = domain.check_value("C", 1, "el-1")
# - The value must be int, float or str.
# res = domain.check_value("C", {"EI": 20, "ER": 1.8, "EC": "Lb2"})

# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# res = domain.check_value("J", 2)

# ==================================================================================================================== #
# ===================== 2. Checking layer or element values of a LAYER VARIABLE ====================================== #
# ==================================================================================================================== #

# Values to check
element_value_a = 20
element_value_b = 200
element_value_c = 1.8
element_value_d = 3.5
element_value_e = "Lb1"
element_value_f = "C1"
layer_value_a = {"EI": 20, "ER": 1.8, "EC": "Lb2"}
layer_value_b = {"EI": -1, "ER": 1.8, "EC": "Lb2"}
layer_value_c = {"EI": 20, "ER": 1.0, "EC": "Lb2"}
layer_value_d = {"EI": 20, "ER": 1.8, "EC": "Lb4"}
layer_value_e = {"EI": "1", "ER": 1.8, "EC": "Lb2"}
layer_value_f = {"EI": 20, "ER": 2, "EC": "Lb2"}
layer_value_g = {"EI": 20, "ER": 1.8, "EC": 1.2}
basic_vector_values_a = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]

# Value compatibility of the E_I element of L
L_E_I_comp_A = domain.check_value("L", element_value_a, "EI")
L_E_I_comp_B = domain.check_value("L", element_value_b, "EI")
L_E_I_comp_C = domain.check_value("L", element_value_c, "EI")
L_E_I_comp_E = domain.check_value("L", element_value_e, "EI")
print("Are these values compatible with the definition of EI of L in this domain ? ")
print(str(element_value_a) + " => " + str(L_E_I_comp_A) + " , " + str(element_value_b) + " => " + str(
    L_E_I_comp_B) + " , "
      + str(element_value_c) + " => " + str(L_E_I_comp_C) + " , " + str(element_value_e) + " => " + str(
    L_E_I_comp_E) + "\n")

# Value compatibility of the E_R element of L
L_E_R_comp_C = domain.check_value("L", element_value_c, "ER")
L_E_R_comp_D = domain.check_value("L", element_value_d, "ER")
L_E_R_comp_A = domain.check_value("L", element_value_a, "ER")
L_E_R_comp_E = domain.check_value("L", element_value_e, "ER")
print("Are these values compatible with the definition of ER of L in this domain ? ")
print(str(element_value_c) + " => " + str(L_E_R_comp_C) + " , " + str(element_value_d) + " => " + str(
    L_E_R_comp_D) + " , "
      + str(element_value_a) + " => " + str(L_E_R_comp_A) + " , " + str(element_value_e) + " => " + str(
    L_E_R_comp_E) + "\n")

# Value compatibility of the E_C element of L
L_E_C_comp_E = domain.check_value("L", element_value_e, "EC")
L_E_C_comp_F = domain.check_value("L", element_value_f, "EC")
L_E_C_comp_A = domain.check_value("L", element_value_a, "EC")
L_E_C_comp_C = domain.check_value("L", element_value_c, "EC")
print("Are these values compatible with the definition of EC of L in this domain ? ")
print(str(element_value_e) + " => " + str(L_E_C_comp_E) + " , " + str(element_value_f) + " => " + str(
    L_E_C_comp_F) + " , "
      + str(element_value_a) + " => " + str(L_E_C_comp_A) + " , " + str(element_value_c) + " => " + str(
    L_E_C_comp_C) + "\n")

L_layer_a = domain.check_value("L", layer_value_a)
L_layer_b = domain.check_value("L", layer_value_b)
L_layer_c = domain.check_value("L", layer_value_c)
L_layer_d = domain.check_value("L", layer_value_d)
L_layer_e = domain.check_value("L", layer_value_e)
L_layer_f = domain.check_value("L", layer_value_f)
L_layer_g = domain.check_value("L", layer_value_g)
print("Are these layers compatible with L ? ")
print(str(layer_value_a) + " => " + str(L_layer_a) + "\n" + str(layer_value_b) + " => " + str(L_layer_b) + "\n"
      + str(layer_value_c) + " => " + str(L_layer_c) + "\n" + str(layer_value_d) + " => " + str(L_layer_d) + "\n"
      + str(layer_value_e) + " => " + str(L_layer_e) + "\n" + str(layer_value_f) + " => " + str(L_layer_f) + "\n"
      + str(layer_value_g) + " => " + str(L_layer_g) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str. The value must be int, float or str.
# res = domain.check_value(1, element_a, "EI")
# res = domain.check_value("L", element_a, 2)

# **** Argument type errors (dynamic, raise ValueError):
# - The element is not provided.
# res = domain.check_value("L", element_c)
# - Trying to check an element's value with a value different from int, float, or str.
# res = domain.check_value("L", layer_value_a, "EC")
# - For LAYER variables, the values must be dict or int, float, or str specifying the element name.
# res = domain.check_value("L", basic_vector_values_a)
# - Trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.
# res = domain.check_value("I", element_value_a, "EI")

# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# res = domain.check_value("J", element_value_a, "EI")
# - The element is not defined in the LAYER variable
# res = domain.check_value("L", element_value_a, "EF")


# ==================================================================================================================== #
# =============================== 3. Checking values of a BASIC VECTOR variable ====================================== #
# ==================================================================================================================== #

# Values to check
basic_component_value_a = 5
basic_component_value_b = 11
basic_component_value_c = 0.0001
basic_component_value_d = 0.2
basic_component_value_e = "V1"
basic_component_value_f = "Lb1"
vector_values_a = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
vector_values_b = [1, 20, 3, 4, 5, 1, 20, 3, 4, 5]
vector_values_c = [0.001, 0.002, 0.003, 0.004, 0.005, 0.001, 0.002, 0.003, 0.004, 0.005]
vector_values_d = [0.001, 0.002, 0.003, 0.004, 5, 0.001, 0.002, 0.003, 0.004, 5]
vector_values_e = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
vector_values_f = ["V1", "V2", 1, "V1", "V2", "V3", "V1", "V2", "V3", "V1"]

# Value compatibility of the V_I components
V_I_comp_A = domain.check_value("VI", basic_component_value_a)
V_I_comp_B = domain.check_value("VI", basic_component_value_b)
V_I_comp_C = domain.check_value("VI", basic_component_value_c)
V_I_comp_E = domain.check_value("VI", basic_component_value_e)
print("Are these values compatible with the components definition of VI in this domain ? ")
print(str(basic_component_value_a) + " => " + str(V_I_comp_A) + " , " + str(basic_component_value_b) + " => "
      + str(V_I_comp_B) + " , " + str(basic_component_value_c) + " => " + str(V_I_comp_C) + " , "
      + str(basic_component_value_e) + " => " + str(V_I_comp_E) + "\n")

# Value compatibility of the V_R components
V_R_comp_C = domain.check_value("VR", basic_component_value_c)
V_R_comp_D = domain.check_value("VR", basic_component_value_d)
V_R_comp_A = domain.check_value("VR", basic_component_value_a)
V_R_comp_E = domain.check_value("VR", basic_component_value_e)
print("Are these values compatible with the components definition of VR in this domain ? ")
print(str(basic_component_value_c) + " => " + str(V_R_comp_C) + " , " + str(basic_component_value_d) + " => "
      + str(V_R_comp_D) + " , " + str(basic_component_value_a) + " => " + str(V_R_comp_A) + " , "
      + str(basic_component_value_e) + " => " + str(V_R_comp_E) + "\n")

# Value compatibility of the V_C components
V_C_comp_E = domain.check_value("VC", basic_component_value_e)
V_C_comp_F = domain.check_value("VC", basic_component_value_f)
V_C_comp_A = domain.check_value("VC", basic_component_value_a)
V_C_comp_C = domain.check_value("VC", basic_component_value_c)
print("Are these values compatible with the components definition of VC in this domain ? ")
print(str(basic_component_value_e) + " => " + str(V_C_comp_E) + " , " + str(basic_component_value_f) + " => "
      + str(V_C_comp_F) + " , " + str(basic_component_value_a) + " => " + str(V_C_comp_A) + " , "
      + str(basic_component_value_c) + " => " + str(V_C_comp_C) + "\n")

V_I_val_a = domain.check_value("VI", vector_values_a)
V_I_val_b = domain.check_value("VI", vector_values_b)
V_I_val_c = domain.check_value("VI", vector_values_c)
print("Are these values compatible with VI definition ? ")
print(str(vector_values_a) + " => " + str(V_I_val_a) + "\n" + str(vector_values_b) + " => " + str(V_I_val_b) + "\n"
      + str(vector_values_c) + " => " + str(V_I_val_c) + "\n")

V_R_val_c = domain.check_value("VR", vector_values_c)
V_R_val_d = domain.check_value("VR", vector_values_d)
V_R_val_a = domain.check_value("VR", vector_values_a)
V_R_val_e = domain.check_value("VR", vector_values_e)
print("Are these values compatible with VR definition ? ")
print(str(vector_values_c) + " => " + str(V_R_val_c) + "\n" + str(vector_values_d) + " => " + str(V_R_val_d) + "\n"
      + str(vector_values_a) + " => " + str(V_R_val_a) + "\n" + str(vector_values_e) + " => " + str(V_R_val_e) + "\n")

V_C_val_e = domain.check_value("VC", vector_values_e)
V_C_val_f = domain.check_value("VC", vector_values_f)
print("Are these values compatible with VC definition ? ")
print(str(vector_values_e) + " => " + str(V_C_val_e) + "\n" + str(vector_values_f) + " => " + str(V_C_val_f) + "\n")


# **** Argument type errors (dynamic, raise ValueError):
# - Trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.
res = domain.check_value("VI", basic_component_value_a, "EI")










# ==================================================================================================================== #
# ======================== 5. Checking elements values of a LAYER VECTOR variable ==================================== #
# ==================================================================================================================== #

# Values to check
component_element_a = 20
component_element_b = 25
component_element_c = 0.2
component_element_d = 0.001
component_element_e = 1
component_element_f = 30
component_element_g = "Tag1"

# # Value compatibility of the el1 element of VL
V_L_el_1_comp_A = domain.check_value("VL", component_element_a, "el1")
V_L_el_1_comp_B = domain.check_value("VL", component_element_b, "el1")
V_L_el_1_comp_C = domain.check_value("VL", component_element_c, "el1")
V_L_el_1_comp_G = domain.check_value("VL", component_element_g, "el1")
print("Are these values compatible with the el1 element definition of the components of VL ? ")
print(str(component_element_a) + " => " + str(V_L_el_1_comp_A) + " , "
      + str(component_element_b) + " => " + str(V_L_el_1_comp_B) + " , "
      + str(component_element_c) + " => " + str(V_L_el_1_comp_C) + " , "
      + str(component_element_g) + " => " + str(V_L_el_1_comp_G) + "\n")

# Value compatibility of the el2 element of VL
V_L_el_2_comp_C = domain.check_value("VL", component_element_c, "el2")
V_L_el_2_comp_D = domain.check_value("VL", component_element_d, "el2")
V_L_el_2_comp_A = domain.check_value("VL", component_element_a, "el2")
V_L_el_2_comp_G = domain.check_value("VL", component_element_g, "el2")
print("Are these values compatible with the el2 element definition of the components of VL ? ")
print(str(component_element_c) + " => " + str(V_L_el_2_comp_C) + " , "
      + str(component_element_d) + " => " + str(V_L_el_2_comp_D) + " , "
      + str(component_element_a) + " => " + str(V_L_el_2_comp_A) + " , "
      + str(component_element_g) + " => " + str(V_L_el_2_comp_G) + "\n")

# Value compatibility of the el3 element of VL
V_L_el_3_comp_E = domain.check_value("VL", component_element_e, "el3")
V_L_el_3_comp_F = domain.check_value("VL", component_element_f, "el3")
V_L_el_3_comp_C = domain.check_value("VL", component_element_c, "el3")
V_L_el_3_comp_G = domain.check_value("VL", component_element_g, "el3")
print("Are these values compatible with the el3 element definition of the components of VL ? ")
print(str(component_element_e) + " => " + str(V_L_el_3_comp_E) + " , "
      + str(component_element_f) + " => " + str(V_L_el_3_comp_F) + " , "
      + str(component_element_c) + " => " + str(V_L_el_3_comp_C) + " , "
      + str(component_element_g) + " => " + str(V_L_el_3_comp_G) + "\n")



# ==================================================================================================================== #
# ============================= 7. Checking layers for a LAYER VECTOR ================================================ #
# ==================================================================================================================== #

vector_layer_a = {"el1": 15, "el2": 0.2, "el3": 2}
vector_layer_b = {"el1": 8, "el2": 0.3, "el3": 1}
vector_layer_c = {"el1": 17, "el2": 0.05, "el3": 2}
vector_layer_d = {"el1": 14, "el2": 0.15, "el3": 4}

V_L_layer_a = domain.check_value("VL", vector_layer_a)
V_L_layer_b = domain.check_value("VL", vector_layer_b)
V_L_layer_c = domain.check_value("VL", vector_layer_c)
V_L_layer_d = domain.check_value("VL", vector_layer_d)
print("Are these layers compatible with VL definition ? ")
print(str(vector_layer_a) + " => " + str(V_L_layer_a) + "\n" + str(vector_layer_b) + " => " + str(V_L_layer_b) + "\n"
      + str(vector_layer_c) + " => " + str(V_L_layer_c) + "\n" + str(vector_layer_d) + " => " + str(V_L_layer_d) + "\n")

# ==================================================================================================================== #
# ========================= 8. Checking complete layer values for a LAYER VECTOR ===================================== #
# ==================================================================================================================== #

vector_layer_values_a = [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]
vector_layer_values_b = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]
vector_layer_values_c = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": "V1"}]
vector_layer_values_d = [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}
    , {"el1": 14, "el2": 0.15, "el3": 3}, {"el1": 17, "el2": 0.25, "el3": 2}]

V_L_vector_layer_a = domain.check_value("VL", vector_layer_values_a)
V_L_vector_layer_b = domain.check_value("VL", vector_layer_values_b)
V_L_vector_layer_c = domain.check_value("VL", vector_layer_values_c)
V_L_vector_layer_d = domain.check_value("VL", vector_layer_values_d)
print("Are these layer values compatible with VL definition ? ")
print(str(vector_layer_values_a) + " => " + str(V_L_vector_layer_a) + "\n"
      + str(vector_layer_values_b) + " => " + str(V_L_vector_layer_b) + "\n"
      + str(vector_layer_values_c) + " => " + str(V_L_vector_layer_c) + "\n"
      + str(vector_layer_values_d) + " => " + str(V_L_vector_layer_d) + "\n")

# ==================================================================================================================== #
# ============================================= 9. General errors ==================================================== #
# ==================================================================================================================== #

# **** Argument type errors (static):
# - The variable name must be str.
# res = domain.check_value(1, vector_layer_a)

# **** Argument type errors (dynamic, raise ValueError):
# - Values must be int, float or str when BASIC variable is checked
# res = domain.check_value("I", layer_a)
# - Element must not be None when an int, float or str value is checked with a LAYER variable
# res = domain.check_value("L", basic_a)


# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# domain.check_value("J", vector_layer_a)

# - The layer is not complete.
# L_layer_a = domain.check_layer("L",  {"EI": 20, "ER": 1.8})


# [Definition] The variable is not defined.
# V_L_layer_a = domain.check_value("J", vector_layer_a)

# If the checked variable type is BASIC:
# ###### [Argument type] The value must not be list or dict.
# I_comp_A = domain.check_value("I", [1, 2])
# I_comp_A = domain.check_value("I", {"e1": 2, "e2": 3})
# ###### [Argument value] The element must not be provided.
# I_comp_A = domain.check_value("I", 2, "el-1")

# If the checked variable type is LAYER:
# ###### [Argument type] The value must not be list.
# L_E_I_comp_A = domain.check_value("L", [1, 2], "E_I")
# L_E_I_comp_A = domain.check_value("L", [1, 2])
# ###### If the value parameter is dict.
# ******************** [Argument value] The element must not be provided.
# L_layer_a = domain.check_value("L", layer_a, "el-1")
# ########### If the value parameter is not dict.
# ******************** [Argument value] The element must be provided.
# L_E_I_comp_A = domain.check_value("L", 1)
# ******************** [Argument type] The variable element be str.
# L_E_I_comp_A = domain.check_value("L", 1, 1)

# If the checked variable type is VECTOR:
# ########### [Definition] The components are not defined.
# V_I_val_a = domain.check_value("V_N", values_a)
# ******************** If the value parameter is list.
# ============================== [Argument value] The element must not be provided.
# V_I_val_a = domain.check_value("V_I", values_a, "el-1")
# ============================== [Definition] The size of the values is note compatible with the variable definition.
# V_I_val_a = domain.check_value("V_I", [1])
# ============================== If the type of the list values is dict.
# ---------------------------------------- [Definition] The components of the variable are not LAYER.
# V_L_vector_layer_a = domain.check_value("V_I", vector_layer_values_a)
# ============================== If the type of the list values is not dict.
# ---------------------------------------- [Definition] The components of the variable are not BASIC.
# V_I_val_a = domain.check_value("V_L", [1, 2])
# ******************** If the value parameter is not list.
# ============================== If the components of the variable are BASIC.
# ---------------------------------------- [Argument value] The element must not be provided.
# V_I_val_a = domain.check_value("V_I", 2, "el-1")
# ---------------------------------------- [Argument type] The value must not be dict.
# V_I_val_a = domain.check_value("V_I", {"e1": 2, "e2": 3})
# ============================== If the components of the variable are LAYER.
# ---------------------------------------- If the value parameter is dict.
# ++++++++++++++++++++++++++++++++++++++++++++++++++ [Argument value] The element must not be provided.
# V_L_layer_a = domain.check_value("V_L", vector_layer_a, "el-1")
# ---------------------------------------- If the value parameter is not dict.
# ++++++++++++++++++++++++++++++++++++++++++++++++++ [Argument value] The element must be provided.
# V_L_el_1_comp_A = domain.check_value("V_L", component_element_a)
# ++++++++++++++++++++++++++++++++++++++++++++++++++ [Argument type] The variable element be str.
# V_L_el_1_comp_A = domain.check_value("V_L", component_element_a, 1)
# ++++++++++++++++++++++++++++++++++++++++++++++++++ [Definition] The element must be defined.
# V_L_el_1_comp_A = domain.check_value("V_L", component_element_a, "el-4")
