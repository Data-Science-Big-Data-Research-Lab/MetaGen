# from pycvoa.use_cases.domains.support_domain import example_domain as domain
#
# print("The example domain:\n")
# print(str(domain) + "\n\n")
#
# # ==================================================================================================================== #
# # ======================================= 1. Checking BASIC values =================================================== #
# # ==================================================================================================================== #
#
# # Values to check
# basic_a = 2
# basic_b = -1
# basic_c = 0.001
# basic_d = 1.2
# basic_e = "C1"
# basic_f = "V1"
#
# # Value compatibility of the definition of I
# I_comp_A = domain.check_basic("I", basic_a)
# I_comp_B = domain.check_basic("I", basic_b)
# I_comp_C = domain.check_basic("I", basic_c)
# I_comp_E = domain.check_basic("I", basic_e)
# print("Are these values compatible with the definition of I in this domain ? ")
# print(str(basic_a) + " => " + str(I_comp_A) + " , " + str(basic_b) + " => " + str(I_comp_B) + " , "
#       + str(basic_c) + " => " + str(I_comp_C) + " , " + str(basic_e) + " => " + str(I_comp_E) + "\n")
#
# # Value compatibility of the definition of R
# R_comp_C = domain.check_basic("R", basic_c)
# R_comp_D = domain.check_basic("R", basic_d)
# R_comp_A = domain.check_basic("R", basic_a)
# R_comp_E = domain.check_basic("R", basic_e)
# print("Are these values compatible with the definition of R in this domain ? ")
# print(str(basic_c) + " => " + str(R_comp_C) + " , " + str(basic_d) + " => " + str(R_comp_D) + " , "
#       + str(basic_a) + " => " + str(R_comp_A) + " , " + str(basic_e) + " => " + str(R_comp_E) + "\n")
#
# # Value compatibility of the definition of C
# C_comp_E = domain.check_basic("C", basic_e)
# C_comp_F = domain.check_basic("C", basic_f)
# C_comp_A = domain.check_basic("C", basic_a)
# C_comp_C = domain.check_basic("C", basic_c)
# print("Are these values compatible with the definition of C in this domain ? ")
# print(str(basic_e) + " => " + str(C_comp_E) + " , " + str(basic_f) + " => " + str(C_comp_F) + " , "
#       + str(basic_a) + " => " + str(C_comp_A) + " , " + str(basic_c) + " => " + str(C_comp_C) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable must be str.
# # I_comp_A = domain.check_basic(1, 2)
# # 2. Definition errors:
# # 2.1. The  variable is not defined.
# # I_comp_A = domain.check_basic("J", 2)
#
# # ==================================================================================================================== #
# # ============================== 2. Checking element values of a LAYER VARIABLE ====================================== #
# # ==================================================================================================================== #
#
# # Values to check
# element_a = 20
# element_b = 200
# element_c = 1.8
# element_d = 3.5
# element_e = "Lb1"
# element_f = "C1"
#
# # Value compatibility of the E_I element of L
# L_E_I_comp_A = domain.check_element("L", "E_I", element_a)
# L_E_I_comp_B = domain.check_element("L", "E_I", element_b)
# L_E_I_comp_C = domain.check_element("L", "E_I", element_c)
# L_E_I_comp_E = domain.check_element("L", "E_I", element_e)
# print("Are these values compatible with the definition of E_I of L in this domain ? ")
# print(str(element_a) + " => " + str(L_E_I_comp_A) + " , " + str(element_b) + " => " + str(L_E_I_comp_B) + " , "
#       + str(element_c) + " => " + str(L_E_I_comp_C) + " , " + str(element_e) + " => " + str(L_E_I_comp_E) + "\n")
#
# # Value compatibility of the E_R element of L
# L_E_R_comp_C = domain.check_element("L", "E_R", element_c)
# L_E_R_comp_D = domain.check_element("L", "E_R", element_d)
# L_E_R_comp_A = domain.check_element("L", "E_R", element_a)
# L_E_R_comp_E = domain.check_element("L", "E_R", element_e)
# print("Are these values compatible with the definition of E_R of L in this domain ? ")
# print(str(element_c) + " => " + str(L_E_R_comp_C) + " , " + str(element_d) + " => " + str(L_E_R_comp_D) + " , "
#       + str(element_a) + " => " + str(L_E_R_comp_A) + " , " + str(element_e) + " => " + str(L_E_R_comp_E) + "\n")
#
# # Value compatibility of the E_C element of L
# L_E_C_comp_E = domain.check_element("L", "E_C", element_e)
# L_E_C_comp_F = domain.check_element("L", "E_C", element_f)
# L_E_C_comp_A = domain.check_element("L", "E_C", element_a)
# L_E_C_comp_C = domain.check_element("L", "E_C", element_c)
# print("Are these values compatible with the definition of E_C of L in this domain ? ")
# print(str(element_e) + " => " + str(L_E_C_comp_E) + " , " + str(element_f) + " => " + str(L_E_C_comp_F) + " , "
#       + str(element_a) + " => " + str(L_E_C_comp_A) + " , " + str(element_c) + " => " + str(L_E_C_comp_C))
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable and the element must be str.
# # L_E_I_comp_A = domain.check_element(1, "E_I", element_a)
# # L_E_I_comp_A = domain.check_element("L", 1, element_a)
# # 2. Definition errors:
# # 2.1. The  variable is not defined.
# # L_E_I_comp_A = domain.check_element("J", "E_I", element_a)
# # 2.2. The variable is not defined as LAYER type.
# # L_E_I_comp_A = domain.check_element("I", "E_I", element_a)
# # 2.3. The element is not defined in the LAYER variable
# # L_E_I_comp_A = domain.check_element("L", "E_F", element_a)
#
# # ==================================================================================================================== #
# # ============================= 3. Checking complete LAYER values ==================================================== #
# # ==================================================================================================================== #
#
# # Layers to check
# layer_a = {"E_I": 20, "E_R": 1.8, "E_C": "Lb2"}
# layer_b = {"E_I": -1, "E_R": 1.8, "E_C": "Lb2"}
# layer_c = {"E_I": 20, "E_R": 1.0, "E_C": "Lb2"}
# layer_d = {"E_I": 20, "E_R": 1.8, "E_C": "Lb4"}
# layer_e = {"E_I": "1", "E_R": 1.8, "E_C": "Lb2"}
# layer_f = {"E_I": 20, "E_R": 2, "E_C": "Lb2"}
# layer_g = {"E_I": 20, "E_R": 1.8, "E_C": 1.2}
#
# L_layer_a = domain.check_layer("L", layer_a)
# L_layer_b = domain.check_layer("L", layer_b)
# L_layer_c = domain.check_layer("L", layer_c)
# L_layer_d = domain.check_layer("L", layer_d)
# L_layer_e = domain.check_layer("L", layer_e)
# L_layer_f = domain.check_layer("L", layer_f)
# L_layer_g = domain.check_layer("L", layer_g)
# print("Are these layers compatible with L ? ")
# print(str(layer_a) + " => " + str(L_layer_a) + "\n" + str(layer_b) + " => " + str(L_layer_b) + "\n"
#       + str(layer_c) + " => " + str(L_layer_c) + "\n" + str(layer_d) + " => " + str(L_layer_d) + "\n"
#       + str(layer_e) + " => " + str(L_layer_e) + "\n" + str(layer_f) + " => " + str(L_layer_f) + "\n"
#       + str(layer_g) + " => " + str(L_layer_g) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable and must be str.
# # L_layer_a = domain.check_layer(1, layer_a)
# # 2. Definition errors:
# # 2.1. The  variable is not defined.
# # L_layer_a = domain.check_layer("J", layer_a)
# # 2.2. The variable is not defined as LAYER type.
# # L_layer_a = domain.check_layer("I", layer_a)
#
# # ==================================================================================================================== #
# # ======================== 4. Checking BASIC component values of a VECTOR variable =================================== #
# # ==================================================================================================================== #
#
# # Values to check
# component_a = 5
# component_b = 11
# component_c = 0.0001
# component_d = 0.2
# component_e = "V1"
# component_f = "Lb1"
#
# # Value compatibility of the V_I components
# V_I_comp_A = domain.check_vector_basic_value("V_I", component_a)
# V_I_comp_B = domain.check_vector_basic_value("V_I", component_b)
# V_I_comp_C = domain.check_vector_basic_value("V_I", component_c)
# V_I_comp_E = domain.check_vector_basic_value("V_I", component_e)
# print("Are these values compatible with the components definition of V_I in this domain ? ")
# print(str(component_a) + " => " + str(V_I_comp_A) + " , " + str(component_b) + " => " + str(V_I_comp_B) + " , "
#       + str(component_c) + " => " + str(V_I_comp_C) + " , " + str(component_e) + " => " + str(V_I_comp_E) + "\n")
#
# # Value compatibility of the V_R components
# V_R_comp_C = domain.check_vector_basic_value("V_R", component_c)
# V_R_comp_D = domain.check_vector_basic_value("V_R", component_d)
# V_R_comp_A = domain.check_vector_basic_value("V_R", component_a)
# V_R_comp_E = domain.check_vector_basic_value("V_R", component_e)
# print("Are these values compatible with the components definition of V_R in this domain ? ")
# print(str(component_c) + " => " + str(V_R_comp_C) + " , " + str(component_d) + " => " + str(V_R_comp_D) + " , "
#       + str(component_a) + " => " + str(V_R_comp_A) + " , " + str(component_e) + " => " + str(V_R_comp_E) + "\n")
#
# # Value compatibility of the V_C components
# V_C_comp_E = domain.check_vector_basic_value("V_C", component_e)
# V_C_comp_F = domain.check_vector_basic_value("V_C", component_f)
# V_C_comp_A = domain.check_vector_basic_value("V_C", component_a)
# V_C_comp_C = domain.check_vector_basic_value("V_C", component_c)
# print("Are these values compatible with the components definition of V_C in this domain ? ")
# print(str(component_e) + " => " + str(V_C_comp_E) + " , " + str(component_f) + " => " + str(V_C_comp_F) + " , "
#       + str(component_a) + " => " + str(V_C_comp_A) + " , " + str(component_c) + " => " + str(V_C_comp_C) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable must be str.
# # V_I_comp_A = domain.check_vector_basic_value(1, component_a)
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_I_comp_A = domain.check_vector_basic_value("J", component_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_I_comp_A = domain.check_vector_basic_value("I", component_a)
# # 2.3. The components of the VECTOR variable are not defined.
# # V_I_comp_A = domain.check_vector_basic_value("V_N", component_a)
# # 2.4. The components of the VECTOR variable are not defined as BASIC.
# # V_I_comp_A = domain.check_vector_basic_value("V_L", component_a)
#
#
# # ==================================================================================================================== #
# # ======================== 5. Checking elements values of a LAYER VECTOR variable ==================================== #
# # ==================================================================================================================== #
#
# # Values to check
# component_element_a = 20
# component_element_b = 25
# component_element_c = 0.2
# component_element_d = 0.001
# component_element_e = 1
# component_element_f = 30
# component_element_g = "Tag1"
#
# # Value compatibility of the el-1 element of V_L
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_L", "el-1", component_element_a)
# V_L_el_1_comp_B = domain.check_vector_layer_element_value("V_L", "el-1", component_element_b)
# V_L_el_1_comp_C = domain.check_vector_layer_element_value("V_L", "el-1", component_element_c)
# V_L_el_1_comp_G = domain.check_vector_layer_element_value("V_L", "el-1", component_element_g)
# print("Are these values compatible with the el-1 element definition of the components of V_L ? ")
# print(str(component_element_a) + " => " + str(V_L_el_1_comp_A) + " , "
#       + str(component_element_b) + " => " + str(V_L_el_1_comp_B) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_1_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_1_comp_G) + "\n")
#
# # Value compatibility of the el-2 element of V_L
# V_L_el_2_comp_C = domain.check_vector_layer_element_value("V_L", "el-2", component_element_c)
# V_L_el_2_comp_D = domain.check_vector_layer_element_value("V_L", "el-2", component_element_d)
# V_L_el_2_comp_A = domain.check_vector_layer_element_value("V_L", "el-2", component_element_a)
# V_L_el_2_comp_G = domain.check_vector_layer_element_value("V_L", "el-2", component_element_g)
# print("Are these values compatible with the el-2 element definition of the components of V_L ? ")
# print(str(component_element_c) + " => " + str(V_L_el_2_comp_C) + " , "
#       + str(component_element_d) + " => " + str(V_L_el_2_comp_D) + " , "
#       + str(component_element_a) + " => " + str(V_L_el_2_comp_A) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_2_comp_G) + "\n")
#
# # Value compatibility of the el-3 element of V_L
# V_L_el_3_comp_E = domain.check_vector_layer_element_value("V_L", "el-3", component_element_e)
# V_L_el_3_comp_F = domain.check_vector_layer_element_value("V_L", "el-3", component_element_f)
# V_L_el_3_comp_C = domain.check_vector_layer_element_value("V_L", "el-3", component_element_c)
# V_L_el_3_comp_G = domain.check_vector_layer_element_value("V_L", "el-3", component_element_g)
# print("Are these values compatible with the el-3 element definition of the components of V_L ? ")
# print(str(component_element_e) + " => " + str(V_L_el_3_comp_E) + " , "
#       + str(component_element_f) + " => " + str(V_L_el_3_comp_F) + " , "
#       + str(component_element_c) + " => " + str(V_L_el_3_comp_C) + " , "
#       + str(component_element_g) + " => " + str(V_L_el_3_comp_G) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable and the element must be str.
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value(1, "el-1", component_element_a)
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_L", 1, component_element_a)
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("J", "el-1", component_element_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("I", "el-1", component_element_a)
# # 2.3. The components of the VECTOR variable are not defined.
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_N", "el-1", component_element_a)
# # 2.4. The components of the VECTOR variable are not defined as LAYER.
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_I", "el-1", component_element_a)
# # 2.5. The element is not defined in the VECTOR LAYER variable
# # V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_L", "el-4", component_element_a)
#
#
# # ==================================================================================================================== #
# # ============================= 6. Checking the size of complete VECTOR values ======================================= #
# # ==================================================================================================================== #
#
# # Values to check
# integer_values_a = [1, 2, 3, 4, 5]
# integer_values_b = []
# integer_values_c = [1, 2, 3, 4, 5, 6, 7, 8]
# real_values_a = [0.001, 0.002, 0.003, 0.004, 0.005]
# real_values_b = [0.001]
# real_values_c = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010, 0.011]
# categorical_values_a = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
# categorical_values_b = ["V1", "V2", "V3"]
# categorical_values_c = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1", "V1", "V2",
#                         "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
# layer_values_a = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
# layer_values_b = [{"el-1": 15, "el-2": 0.2, "el-3": 2}]
# layer_values_c = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1},
#                   {"el-1": 17, "el-2": 0.5, "el-3": 2}, {"el-1": 14, "el-2": 0.15, "el-3": 3},
#                   {"el-1": 11, "el-2": 0.12, "el-3": 3}]
#
# V_I_size_i_a = domain.check_vector_values_size("V_I", integer_values_a)
# V_I_size_l_b = domain.check_vector_values_size("V_I", layer_values_b)
# print("Are these sizes compatible with V_I definition ? ")
# print(str(integer_values_a) + " => " + str(V_I_size_i_a) + "\n"
#       + str(layer_values_b) + " => " + str(V_I_size_l_b) + "\n")
#
# V_R_size_r_a = domain.check_vector_values_size("V_R", real_values_a)
# V_R_size_i_b = domain.check_vector_values_size("V_R", integer_values_b)
# print("Are these sizes compatible with V_R definition ? ")
# print(str(real_values_c) + " => " + str(V_R_size_r_a) + "\n"
#       + str(integer_values_b) + " => " + str(V_R_size_i_b) + "\n")
#
# V_C_size_c_a = domain.check_vector_values_size("V_C", categorical_values_a)
# V_C_size_l_c = domain.check_vector_values_size("V_C", layer_values_c)
# print("Are these sizes compatible with V_C definition ? ")
# print(str(categorical_values_a) + " => " + str(V_C_size_c_a) + "\n"
#       + str(layer_values_c) + " => " + str(V_C_size_l_c) + "\n")
#
# V_L_size_l_a = domain.check_vector_values_size("V_L", layer_values_a)
# V_L_size_i_c = domain.check_vector_values_size("V_L", integer_values_c)
# print("Are these sizes compatible with V_L definition ? ")
# print(str(layer_values_a) + " => " + str(V_L_size_l_a) + "\n"
#       + str(integer_values_c) + " => " + str(V_L_size_i_c) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable must be str. The values must be a list.
# # V_I_size_i_a = domain.check_vector_values_size(1, integer_values_a)
# # V_I_size_i_a = domain.check_vector_values_size("V_I", 1)
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_I_size_i_a = domain.check_vector_values_size("J", integer_values_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_I_size_i_a = domain.check_vector_values_size("I", integer_values_a)
#
#
# # ==================================================================================================================== #
# # ============================= 7. Checking complete values of BASIC VECTOR ========================================== #
# # ==================================================================================================================== #
#
# # Values to check
# values_a = [1, 2, 3, 4, 5]
# values_b = [1, 20, 3, 4, 5]
# values_c = [0.001, 0.002, 0.003, 0.004, 0.005]
# values_d = [0.001, 0.002, 0.003, 0.004, 5]
# values_e = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
# values_f = ["V1", "V2", 1, "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
#
# V_I_val_a = domain.check_vector_basic_values("V_I", values_a)
# V_I_val_b = domain.check_vector_basic_values("V_I", values_b)
# V_I_val_c = domain.check_vector_basic_values("V_I", values_c)
# print("Are these values compatible with V_I definition ? ")
# print(str(values_a) + " => " + str(V_I_val_a) + "\n" + str(values_b) + " => " + str(V_I_val_b) + "\n"
#       + str(values_c) + " => " + str(V_I_val_c) + "\n")
#
# V_R_val_c = domain.check_vector_basic_values("V_R", values_c)
# V_R_val_d = domain.check_vector_basic_values("V_R", values_d)
# V_R_val_a = domain.check_vector_basic_values("V_R", values_a)
# V_R_val_e = domain.check_vector_basic_values("V_R", values_e)
# print("Are these values compatible with V_R definition ? ")
# print(str(values_c) + " => " + str(V_R_val_c) + "\n" + str(values_d) + " => " + str(V_R_val_d) + "\n"
#       + str(values_a) + " => " + str(V_R_val_a) + "\n" + str(values_e) + " => " + str(V_R_val_e) + "\n")
#
# V_C_val_e = domain.check_vector_basic_values("V_C", values_e)
# V_C_val_f = domain.check_vector_basic_values("V_C", values_f)
# print("Are these values compatible with V_C definition ? ")
# print(str(values_e) + " => " + str(V_C_val_e) + "\n" + str(values_f) + " => " + str(V_C_val_f) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable name must be str. The values must be list.
# # V_I_val_a = domain.check_vector_basic_values(1, values_a)
# # V_I_val_a = domain.check_vector_basic_values("V_I", 1)
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_I_val_a = domain.check_vector_basic_values("J", values_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_I_val_a = domain.check_vector_basic_values("I", values_a)
# # 2.3. The components of the VECTOR variable are not defined.
# # V_I_val_a = domain.check_vector_basic_values("V_N", values_a)
# # 2.4. The components of the VECTOR variable are not defined as BASIC.
# # V_I_val_a = domain.check_vector_basic_values("V_L", values_a)
# # 2.5. The size of the values is not compatible with the vector definition.
# # V_I_val_a = domain.check_vector_basic_values("V_I", values_e)
#
# # ==================================================================================================================== #
# # ============================= 8. Checking layers for a LAYER VECTOR ================================================ #
# # ==================================================================================================================== #
#
# vector_layer_a = {"el-1": 15, "el-2": 0.2, "el-3": 2}
# vector_layer_b = {"el-1": 8, "el-2": 0.3, "el-3": 1}
# vector_layer_c = {"el-1": 17, "el-2": 0.05, "el-3": 2}
# vector_layer_d = {"el-1": 14, "el-2": 0.15, "el-3": 4}
#
# V_L_layer_a = domain.check_vector_layer_elements_values("V_L", vector_layer_a)
# V_L_layer_b = domain.check_vector_layer_elements_values("V_L", vector_layer_b)
# V_L_layer_c = domain.check_vector_layer_elements_values("V_L", vector_layer_c)
# V_L_layer_d = domain.check_vector_layer_elements_values("V_L", vector_layer_d)
# print("Are these layers compatible with V_L definition ? ")
# print(str(vector_layer_a) + " => " + str(V_L_layer_a) + "\n" + str(vector_layer_b) + " => " + str(V_L_layer_b) + "\n"
#       + str(vector_layer_c) + " => " + str(V_L_layer_c) + "\n" + str(vector_layer_d) + " => " + str(V_L_layer_d) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable name must be str. The values must be dict.
# # V_L_layer_a = domain.check_vector_layer_elements_values(1, vector_layer_a)
# # V_L_layer_a = domain.check_vector_layer_elements_values("V_L", [1,2])
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_L_layer_a = domain.check_vector_layer_elements_values("J", vector_layer_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_L_layer_a = domain.check_vector_layer_elements_values("I", vector_layer_a)
# # 2.3. The components of the VECTOR variable are not defined.
# # V_L_layer_a = domain.check_vector_layer_elements_values("V_N", vector_layer_a)
# # 2.4. The components of the VECTOR variable are not defined as LAYER.
# # V_L_layer_a = domain.check_vector_layer_elements_values("V_I", vector_layer_a)
# # 2.5. The element of the values is not defined in the VECTOR LAYER variable.
# # V_L_layer_a = domain.check_vector_layer_elements_values("V_L", {"el-1": 15, "el-2": 0.2, "el-3": 2, "el-4": 3})
# # 2.6. The layer is not complete.
# # V_L_layer_a = domain.check_vector_layer_elements_values("V_L", {"el-1": 14, "el-2": 0.15})
#
# # ==================================================================================================================== #
# # ========================= 9. Checking complete layer values for a LAYER VECTOR ===================================== #
# # ==================================================================================================================== #
#
# vector_layer_values_a = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
# vector_layer_values_b = [{"el-1": 25, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
# vector_layer_values_c = [{"el-1": 25, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": "V1"}]
# vector_layer_values_d = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}
#                          , {"el-1": 14, "el-2": 0.15, "el-3": 3}, {"el-1": 17, "el-2": 0.25, "el-3": 2}]
#
# V_L_vector_layer_a = domain.check_vector_layer_values("V_L", vector_layer_values_a)
# V_L_vector_layer_b = domain.check_vector_layer_values("V_L", vector_layer_values_b)
# V_L_vector_layer_c = domain.check_vector_layer_values("V_L", vector_layer_values_c)
# V_L_vector_layer_d = domain.check_vector_layer_values("V_L", vector_layer_values_d)
# print("Are these layer values compatible with V_L definition ? ")
# print(str(vector_layer_values_a) + " => " + str(V_L_vector_layer_a) + "\n"
#       + str(vector_layer_values_b) + " => " + str(V_L_vector_layer_b) + "\n"
#       + str(vector_layer_values_c) + " => " + str(V_L_vector_layer_c) + "\n"
#       + str(vector_layer_values_d) + " => " + str(V_L_vector_layer_d) + "\n")
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable name must be str. The values must be list.
# # V_L_vector_layer_a = domain.check_vector_layer_values(1, vector_layer_values_a)
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_L", 1)
# # 2. Definition errors:
# # 2.1. The variable is not defined.
# # V_L_vector_layer_a = domain.check_vector_layer_values("J", vector_layer_values_a)
# # 2.2. The variable is not defined as VECTOR type.
# # V_L_vector_layer_a = domain.check_vector_layer_values("I", vector_layer_values_a)
# # 2.3. The components of the VECTOR variable are not defined.
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_N", vector_layer_values_a)
# # 2.4. The components of the VECTOR variable are not defined as LAYER.
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_I", vector_layer_values_a)
# # 2.5. The size of the values is not compatible with the vector definition.
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_L", [{"el-1": 15, "el-2": 0.2, "el-3": 2}])
# # 2.6. The element a component of the values not defined in the VECTOR LAYER variable.
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_L", [{"el-1": 15, "el-2": 0.2, "el-3": 2},
# #                                                               {"el-1": 12, "el-2": 0.3, "el-5": 1}])
# # 2.7. A layer of the components of the VECTOR LAYER variable is not complete.
# # V_L_vector_layer_a = domain.check_vector_layer_values("V_L", [{"el-1": 15, "el-2": 0.2, "el-3": 2},
# #                                                               {"el-1": 12, "el-2": 0.3}])
