from pycvoa.use_cases.domains.support_domain import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ======================================= 1. Checking BASIC values =================================================== #
# ==================================================================================================================== #

# Values to check
basic_a = 2
basic_b = -1
basic_c = 0.001
basic_d = 1.2
basic_e = "C1"
basic_f = "V1"

# Value compatibility of the definition of I
I_comp_A = domain.check_value("I", basic_a)
I_comp_B = domain.check_value("I", basic_b)
I_comp_C = domain.check_value("I", basic_c)
I_comp_E = domain.check_value("I", basic_e)
print("Are these values compatible with the definition of I in this domain ? ")
print(str(basic_a) + " => " + str(I_comp_A) + " , " + str(basic_b) + " => " + str(I_comp_B) + " , "
      + str(basic_c) + " => " + str(I_comp_C) + " , " + str(basic_e) + " => " + str(I_comp_E) + "\n")

# Value compatibility of the definition of R
R_comp_C = domain.check_value("R", basic_c)
R_comp_D = domain.check_value("R", basic_d)
R_comp_A = domain.check_value("R", basic_a)
R_comp_E = domain.check_value("R", basic_e)
print("Are these values compatible with the definition of R in this domain ? ")
print(str(basic_c) + " => " + str(R_comp_C) + " , " + str(basic_d) + " => " + str(R_comp_D) + " , "
      + str(basic_a) + " => " + str(R_comp_A) + " , " + str(basic_e) + " => " + str(R_comp_E) + "\n")

# Value compatibility of the definition of C
C_comp_E = domain.check_value("C", basic_e)
C_comp_F = domain.check_value("C", basic_f)
C_comp_A = domain.check_value("C", basic_a)
C_comp_C = domain.check_value("C", basic_c)
print("Are these values compatible with the definition of C in this domain ? ")
print(str(basic_e) + " => " + str(C_comp_E) + " , " + str(basic_f) + " => " + str(C_comp_F) + " , "
      + str(basic_a) + " => " + str(C_comp_A) + " , " + str(basic_c) + " => " + str(C_comp_C) + "\n")

# ==================================================================================================================== #
# ============================== 2. Checking element values of a LAYER VARIABLE ====================================== #
# ==================================================================================================================== #

# Values to check
element_a = 20
element_b = 200
element_c = 1.8
element_d = 3.5
element_e = "Lb1"
element_f = "C1"

# Value compatibility of the E_I element of L
L_E_I_comp_A = domain.check_value("L", element_a, "EI")
L_E_I_comp_B = domain.check_value("L", element_b, "EI")
L_E_I_comp_C = domain.check_value("L", element_c, "EI")
L_E_I_comp_E = domain.check_value("L", element_e, "EI")
print("Are these values compatible with the definition of EI of L in this domain ? ")
print(str(element_a) + " => " + str(L_E_I_comp_A) + " , " + str(element_b) + " => " + str(L_E_I_comp_B) + " , "
      + str(element_c) + " => " + str(L_E_I_comp_C) + " , " + str(element_e) + " => " + str(L_E_I_comp_E) + "\n")

# Value compatibility of the E_R element of L
L_E_R_comp_C = domain.check_value("L", element_c, "ER")
L_E_R_comp_D = domain.check_value("L", element_d, "ER")
L_E_R_comp_A = domain.check_value("L", element_a, "ER")
L_E_R_comp_E = domain.check_value("L", element_e, "ER")
print("Are these values compatible with the definition of ER of L in this domain ? ")
print(str(element_c) + " => " + str(L_E_R_comp_C) + " , " + str(element_d) + " => " + str(L_E_R_comp_D) + " , "
      + str(element_a) + " => " + str(L_E_R_comp_A) + " , " + str(element_e) + " => " + str(L_E_R_comp_E) + "\n")

# Value compatibility of the E_C element of L
L_E_C_comp_E = domain.check_value("L", element_e, "EC")
L_E_C_comp_F = domain.check_value("L", element_f, "EC")
L_E_C_comp_A = domain.check_value("L", element_a, "EC")
L_E_C_comp_C = domain.check_value("L", element_c, "EC")
print("Are these values compatible with the definition of EC of L in this domain ? ")
print(str(element_e) + " => " + str(L_E_C_comp_E) + " , " + str(element_f) + " => " + str(L_E_C_comp_F) + " , "
      + str(element_a) + " => " + str(L_E_C_comp_A) + " , " + str(element_c) + " => " + str(L_E_C_comp_C) + "\n")

# ==================================================================================================================== #
# ============================= 3. Checking complete LAYER values ==================================================== #
# ==================================================================================================================== #

# Layers to check
layer_a = {"EI": 20, "ER": 1.8, "EC": "Lb2"}
layer_b = {"EI": -1, "ER": 1.8, "EC": "Lb2"}
layer_c = {"EI": 20, "ER": 1.0, "EC": "Lb2"}
layer_d = {"EI": 20, "ER": 1.8, "EC": "Lb4"}
layer_e = {"EI": "1", "ER": 1.8, "EC": "Lb2"}
layer_f = {"EI": 20, "ER": 2, "EC": "Lb2"}
layer_g = {"EI": 20, "ER": 1.8, "EC": 1.2}

L_layer_a = domain.check_value("L", layer_a)
L_layer_b = domain.check_value("L", layer_b)
L_layer_c = domain.check_value("L", layer_c)
L_layer_d = domain.check_value("L", layer_d)
L_layer_e = domain.check_value("L", layer_e)
L_layer_f = domain.check_value("L", layer_f)
L_layer_g = domain.check_value("L", layer_g)
print("Are these layers compatible with L ? ")
print(str(layer_a) + " => " + str(L_layer_a) + "\n" + str(layer_b) + " => " + str(L_layer_b) + "\n"
       + str(layer_c) + " => " + str(L_layer_c) + "\n" + str(layer_d) + " => " + str(L_layer_d) + "\n"
       + str(layer_e) + " => " + str(L_layer_e) + "\n" + str(layer_f) + " => " + str(L_layer_f) + "\n"
       + str(layer_g) + " => " + str(L_layer_g) + "\n")

# ==================================================================================================================== #
# ======================== 4. Checking BASIC component values of a VECTOR variable =================================== #
# ==================================================================================================================== #

# Values to check
# component_a = 5
# component_b = 11
# component_c = 0.0001
# component_d = 0.2
# component_e = "V1"
# component_f = "Lb1"
#
# # Value compatibility of the V_I components
# V_I_comp_A = domain.check_value("V_I", component_a)
# V_I_comp_B = domain.check_value("V_I", component_b)
# V_I_comp_C = domain.check_value("V_I", component_c)
# V_I_comp_E = domain.check_value("V_I", component_e)
# print("Are these values compatible with the components definition of V_I in this domain ? ")
# print(str(component_a) + " => " + str(V_I_comp_A) + " , " + str(component_b) + " => " + str(V_I_comp_B) + " , "
#       + str(component_c) + " => " + str(V_I_comp_C) + " , " + str(component_e) + " => " + str(V_I_comp_E) + "\n")
#
# # Value compatibility of the V_R components
# V_R_comp_C = domain.check_value("V_R", component_c)
# V_R_comp_D = domain.check_value("V_R", component_d)
# V_R_comp_A = domain.check_value("V_R", component_a)
# V_R_comp_E = domain.check_value("V_R", component_e)
# print("Are these values compatible with the components definition of V_R in this domain ? ")
# print(str(component_c) + " => " + str(V_R_comp_C) + " , " + str(component_d) + " => " + str(V_R_comp_D) + " , "
#       + str(component_a) + " => " + str(V_R_comp_A) + " , " + str(component_e) + " => " + str(V_R_comp_E) + "\n")
#
# # Value compatibility of the V_C components
# V_C_comp_E = domain.check_value("V_C", component_e)
# V_C_comp_F = domain.check_value("V_C", component_f)
# V_C_comp_A = domain.check_value("V_C", component_a)
# V_C_comp_C = domain.check_value("V_C", component_c)
# print("Are these values compatible with the components definition of V_C in this domain ? ")
# print(str(component_e) + " => " + str(V_C_comp_E) + " , " + str(component_f) + " => " + str(V_C_comp_F) + " , "
#       + str(component_a) + " => " + str(V_C_comp_A) + " , " + str(component_c) + " => " + str(V_C_comp_C) + "\n")

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
# # Value compatibility of the el-1 element of V_L
# V_L_el_1_comp_A = domain.check_value("V_L", component_element_a, "el-1")
# V_L_el_1_comp_B = domain.check_value("V_L", component_element_b, "el-1")
# V_L_el_1_comp_C = domain.check_value("V_L", component_element_c, "el-1")
# V_L_el_1_comp_G = domain.check_value("V_L", component_element_g, "el-1")
# print("Are these values compatible with the el-1 element definition of the components of V_L ? ")
# print(str(component_element_a) + " => " + str(V_L_el_1_comp_A) + " , "
#       + str(component_element_b) + " => " + str(V_L_el_1_comp_B) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_1_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_1_comp_G) + "\n")
#
# # Value compatibility of the el-2 element of V_L
# V_L_el_2_comp_C = domain.check_value("V_L", component_element_c, "el-2")
# V_L_el_2_comp_D = domain.check_value("V_L", component_element_d, "el-2")
# V_L_el_2_comp_A = domain.check_value("V_L", component_element_a, "el-2")
# V_L_el_2_comp_G = domain.check_value("V_L", component_element_g, "el-2")
# print("Are these values compatible with the el-2 element definition of the components of V_L ? ")
# print(str(component_element_c) + " => " + str(V_L_el_2_comp_C) + " , "
#       + str(component_element_d) + " => " + str(V_L_el_2_comp_D) + " , "
#       + str(component_element_a) + " => " + str(V_L_el_2_comp_A) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_2_comp_G) + "\n")
#
# # Value compatibility of the el-3 element of V_L
# V_L_el_3_comp_E = domain.check_value("V_L", component_element_e, "el-3")
# V_L_el_3_comp_F = domain.check_value("V_L", component_element_f, "el-3")
# V_L_el_3_comp_C = domain.check_value("V_L", component_element_c, "el-3")
# V_L_el_3_comp_G = domain.check_value("V_L", component_element_g, "el-3")
# print("Are these values compatible with the el-3 element definition of the components of V_L ? ")
# print(str(component_element_e) + " => " + str(V_L_el_3_comp_E) + " , "
#       + str(component_element_f) + " => " + str(V_L_el_3_comp_F) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_3_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_3_comp_G) + "\n")

# ==================================================================================================================== #
# ============================= 6. Checking complete values of BASIC VECTOR ========================================== #
# ==================================================================================================================== #

# Values to check
# values_a = [1, 2, 3, 4, 5]
# values_b = [1, 20, 3, 4, 5]
# values_c = [0.001, 0.002, 0.003, 0.004, 0.005]
# values_d = [0.001, 0.002, 0.003, 0.004, 5]
# values_e = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
# values_f = ["V1", "V2", 1, "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
#
# V_I_val_a = domain.check_value("V_I", values_a)
# V_I_val_b = domain.check_value("V_I", values_b)
# V_I_val_c = domain.check_value("V_I", values_c)
# print("Are these values compatible with V_I definition ? ")
# print(str(values_a) + " => " + str(V_I_val_a) + "\n" + str(values_b) + " => " + str(V_I_val_b) + "\n"
#       + str(values_c) + " => " + str(V_I_val_c) + "\n")
#
# V_R_val_c = domain.check_value("V_R", values_c)
# V_R_val_d = domain.check_value("V_R", values_d)
# V_R_val_a = domain.check_value("V_R", values_a)
# V_R_val_e = domain.check_value("V_R", values_e)
# print("Are these values compatible with V_R definition ? ")
# print(str(values_c) + " => " + str(V_R_val_c) + "\n" + str(values_d) + " => " + str(V_R_val_d) + "\n"
#       + str(values_a) + " => " + str(V_R_val_a) + "\n" + str(values_e) + " => " + str(V_R_val_e) + "\n")
#
# V_C_val_e = domain.check_value("V_C", values_e)
# V_C_val_f = domain.check_value("V_C", values_f)
# print("Are these values compatible with V_C definition ? ")
# print(str(values_e) + " => " + str(V_C_val_e) + "\n" + str(values_f) + " => " + str(V_C_val_f) + "\n")

# ==================================================================================================================== #
# ============================= 7. Checking layers for a LAYER VECTOR ================================================ #
# ==================================================================================================================== #

# vector_layer_a = {"el-1": 15, "el-2": 0.2, "el-3": 2}
# vector_layer_b = {"el-1": 8, "el-2": 0.3, "el-3": 1}
# vector_layer_c = {"el-1": 17, "el-2": 0.05, "el-3": 2}
# vector_layer_d = {"el-1": 14, "el-2": 0.15, "el-3": 4}
#
# V_L_layer_a = domain.check_value("V_L", vector_layer_a)
# V_L_layer_b = domain.check_value("V_L", vector_layer_b)
# V_L_layer_c = domain.check_value("V_L", vector_layer_c)
# V_L_layer_d = domain.check_value("V_L", vector_layer_d)
# print("Are these layers compatible with V_L definition ? ")
# print(str(vector_layer_a) + " => " + str(V_L_layer_a) + "\n" + str(vector_layer_b) + " => " + str(V_L_layer_b) + "\n"
#       + str(vector_layer_c) + " => " + str(V_L_layer_c) + "\n" + str(vector_layer_d) + " => " + str(V_L_layer_d) + "\n")

# ==================================================================================================================== #
# ========================= 8. Checking complete layer values for a LAYER VECTOR ===================================== #
# ==================================================================================================================== #

# vector_layer_values_a = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
# vector_layer_values_b = [{"el-1": 25, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
# vector_layer_values_c = [{"el-1": 25, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": "V1"}]
# vector_layer_values_d = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}
#     , {"el-1": 14, "el-2": 0.15, "el-3": 3}, {"el-1": 17, "el-2": 0.25, "el-3": 2}]
#
# V_L_vector_layer_a = domain.check_value("V_L", vector_layer_values_a)
# V_L_vector_layer_b = domain.check_value("V_L", vector_layer_values_b)
# V_L_vector_layer_c = domain.check_value("V_L", vector_layer_values_c)
# V_L_vector_layer_d = domain.check_value("V_L", vector_layer_values_d)
# print("Are these layer values compatible with V_L definition ? ")
# print(str(vector_layer_values_a) + " => " + str(V_L_vector_layer_a) + "\n"
#       + str(vector_layer_values_b) + " => " + str(V_L_vector_layer_b) + "\n"
#       + str(vector_layer_values_c) + " => " + str(V_L_vector_layer_c) + "\n"
#       + str(vector_layer_values_d) + " => " + str(V_L_vector_layer_d) + "\n")

# ==================================================================================================================== #
# ============================================= 9. Possible errors =================================================== #
# ==================================================================================================================== #

# If the checked variable is not str:
# [Argument type] The variable must be str.
# V_L_layer_a = domain.check_value(1, vector_layer_a)
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
