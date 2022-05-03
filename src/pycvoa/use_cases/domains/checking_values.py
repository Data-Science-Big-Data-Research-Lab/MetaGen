
# ============================ 11. Checking BASIC values ==============================================================

# To check if a value is compatible with a BASIC variable definition, use the "check_basic" method

# Are 2 and -1 compatible with the definition of I ?
# I_comp_A = domain.check_basic("I", 2)
# I_comp_B = domain.check_basic("I", -1)
# print("Is 2 compatible with the definition of I in this domain ? " + str(I_comp_A))
# print("Is -1 compatible with the definition of I in this domain ? " + str(I_comp_B))

# Are 0.001 and 1.2 compatible with the definition of R ?
# R_comp_A = domain.check_basic("R", 0.001)
# R_comp_B = domain.check_basic("R", 1.2)
# print("Is 0.001 compatible with the definition of R in this domain ? " + str(R_comp_A))
# print("Is 1.2 compatible with the definition of R in this domain ? " + str(R_comp_B))

# Are C2 and C5 compatible with the definition of C_A ?
# C_A_comp_A = domain.check_basic("C_A", "C1")
# C_A_comp_B = domain.check_basic("C_A", "C5")
# print("Is C1 compatible with the definition of C_A in this domain ? " + str(C_A_comp_A))
# print("Is C5 compatible with the definition of C_A in this domain ? " + str(C_A_comp_B))

# **** Possible errors
# 1. The variable is not defined
# I_comp_A = domain_A.check_basic("J", 2)
# 2. The variable is not defined as a BASIC type
# sI_comp_A = domain_A.check_basic("L", 2)

# ============================ 12. Checking element values ============================================================

# To check if a value is compatible with an element of a LAYER variable definition, use the "check_element" method

# Are 2 and -1 compatible with the E_I definition in the L LAYER variable ?
# L_E_I_comp_A = domain.check_element("L", "E_I", 2)
# L_E_I_comp_B = domain.check_element("L", "E_I", -1)
# print("Is 2 compatible with the definition of E_I in the LAYER L ? " + str(L_E_I_comp_A))
# print("Is -1 compatible with the definition of E_I in the LAYER L ? " + str(L_E_I_comp_B))

# Are 1.8 and 4.5 compatible with the E_I definition in the L LAYER variable ?
# L_E_R_comp_A = domain.check_element("L", "E_R", 1.8)
# L_E_R_comp_B = domain.check_element("L", "E_R", 4.5)
# print("Is 1.8 compatible with the definition of E_R in the LAYER L ? " + str(L_E_R_comp_A))
# print("Is 4.5 compatible with the definition of E_R in the LAYER L ? " + str(L_E_R_comp_B))

# Are Lb1 and C1 compatible with the E_C definition in the L LAYER variable ?
# L_E_C_comp_A = domain.check_element("L", "E_C", "Lb1")
# L_E_C_comp_B = domain.check_element("L", "E_C", "C1")
# print("Is Lb1 compatible with the definition of E_C in the LAYER L ? " + str(L_E_C_comp_A))
# print("Is C1 compatible with the definition of E_C in the LAYER L ? " + str(L_E_C_comp_B))

# **** Possible errors
# 1. The LAYER variable is not defined
# L_E_I_comp_A = domain_A.check_element("Y","E_I",2)
# 2. The LAYER variable is not defined as a LAYER variable
# L_E_I_comp_A = domain_A.check_element("I","E_I",2)
# 3. The element is not defined in the LAYER variable
# L_E_I_comp_A = domain_A.check_element("L","E_C_",2)

# ============================ 13. Checking component values ==========================================================

# To check if a value is compatible with the BASIC definition of the components of a VECTOR variable,
# use "check_basic_component" method

# Are 2 and -1 compatible with the components of the V_I VECTOR variable ?
# V_I_comp_A = domain.check_vector_basic_value("V_I", 2)
# V_I_comp_B = domain.check_vector_basic_value("V_I", -1)
# print("Is 2 compatible with the components of the V_I VECTOR variable ? " + str(V_I_comp_A))
# print("Is -1 compatible with the components of the V_I VECTOR variable ? " + str(V_I_comp_B))

# Are 0.001 and 1.2 compatible with the components of the V_R VECTOR variable ?
# V_R_comp_A = domain.check_vector_basic_value("V_R", 0.001)
# V_R_comp_B = domain.check_vector_basic_value("V_R", 1.2)
# print("Is 0.001 compatible with the components of the V_R VECTOR variable ? " + str(V_R_comp_A))
# print("Is 1.2 compatible with the components of the V_R VECTOR variable ? " + str(V_R_comp_B))

# Are C2 and C5 compatible with the components of the V_C VECTOR variable ?
# V_C_comp_A = domain.check_vector_basic_value("V_C", "V2")
# V_C_comp_B = domain.check_vector_basic_value("V_C", "C5")
# print("Is V2 compatible with the components of the V_C VECTOR variable ? " + str(V_C_comp_A))
# print("Is C5 compatible with the components of the V_C VECTOR variable ? " + str(V_C_comp_B))

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_I_comp_A = domain_A.check_basic_component("V_Y", 2)
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_I_comp_A = domain_A.check_basic_component("I", 2)
# 3. The components of the VECTOR variable are not defined
# V_I_comp_A = domain_A.check_basic_component("V_I_", 2)
# 4. The components of the VECTOR variable are not defined as BASIC
# V_I_comp_A = domain_A.check_basic_component("V_L", 2)

# To check if a value is compatible with an element of the LAYER components of a VECTOR variable,
# use "check_element_component" method

# Are 15 and -1 compatible with the E_I definition in the V_L VECTOR variable ?
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("V_L", "el-1", 15)
# V_L_el_1_comp_B = domain.check_vector_layer_element_value("V_L", "el-1", -1)
# print("Is 15 compatible with the definition of el-1 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_1_comp_A))
# print("Is -1 compatible with the definition of el-1 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_1_comp_B))

# Are 0.25 and 4.5 compatible with the E_I definition in the V_L VECTOR variable ?
# V_L_el_2_comp_A = domain.check_vector_layer_element_value("V_L", "el-2", 0.25)
# V_L_el_2_comp_B = domain.check_vector_layer_element_value("V_L", "el-2", 4.5)
# print("Is 0.25 compatible with the definition of el-2 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_2_comp_A))
# print("Is 4.5 compatible with the definition of el-2 in the LAYER components of the V_L VECTOR variable ? " + str(
#    V_L_el_2_comp_B))

# Are 1 and C1 compatible with the E_C definition in the V_L VECTOR variable ?
# V_L_el_3_comp_A = domain.check_vector_layer_element_value("V_L", "el-3", 1)
# V_L_el_3_comp_B = domain.check_vector_layer_element_value("V_L", "el-3", 8)
# print("Is 1 compatible with the definition of el-3 in the LAYER components of the V_L VECTOR variable ? " + str(
#    V_L_el_3_comp_A))
# print("Is 8 compatible with the definition of el-3 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_3_comp_B))

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_L_el_1_comp_A = domain_A.check_element_component("Y","el-1",15)
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_L_el_1_comp_A = domain_A.check_element_component("I","el-1",15)
# 3. The components of the VECTOR variable are not defined
# V_L_el_1_comp_A = domain_A.check_element_component("V_I_","el-1",15)
# 4. The components of the VECTOR variable are not defined as LAYER
# V_L_el_1_comp_A = domain_A.check_element_component("V_I","el-1",15)

# ============================ 14. General purpose checking method =====================================================

# The Domain class provides a method called "check_value" to check a value of any variable type.

# Are 2 and -1 compatible with the definition of I ?
# I_ack_A = domain.check_value("I", 2)
# I_ack_B = domain.check_value("I", -1)
# print("Is 2 compatible with the definition of I in this domain ? " + str(I_ack_A))
# print("Is -1 compatible with the definition of I in this domain ? " + str(I_ack_B))
#
# # Are 0.001 and 1.2 compatible with the definition of R ?
# R_ack_A = domain.check_value("R", 0.001)
# R_ack_B = domain.check_value("R", 1.2)
# print("Is 0.001 compatible with the definition of R in this domain ? " + str(R_ack_A))
# print("Is 1.2 compatible with the definition of R in this domain ? " + str(R_ack_B))
#
# # Are C2 and C5 compatible with the definition of C_A ?
# C_A_ack_A = domain.check_value("C_A", "C1")
# C_A_ack_B = domain.check_value("C_A", "C5")
# print("Is C1 compatible with the definition of C_A in this domain ? " + str(C_A_ack_A))
# print("Is C5 compatible with the definition of C_A in this domain ? " + str(C_A_ack_B))
#
# # Are 2 and -1 compatible with the E_I definition in the L LAYER variable ?
# L_E_I_ack_A = domain.check_value("L", 2, "E_I")
# L_E_I_ack_B = domain.check_value("L", -1, "E_I")
# print("Is 2 compatible with the definition of E_I in the LAYER L ? " + str(L_E_I_ack_A))
# print("Is -1 compatible with the definition of E_I in the LAYER L ? " + str(L_E_I_ack_B))
#
# # Are 1.8 and 4.5 compatible with the E_I definition in the L LAYER variable ?
# L_E_R_ack_A = domain.check_value("L", 1.8, "E_R")
# L_E_R_ack_B = domain.check_value("L", 4.5, "E_R")
# print("Is 1.8 compatible with the definition of E_R in the LAYER L ? " + str(L_E_R_ack_A))
# print("Is 4.5 compatible with the definition of E_R in the LAYER L ? " + str(L_E_R_ack_B))
#
# # Are Lb1 and C1 compatible with the E_C definition in the L LAYER variable ?
# L_E_C_ack_A = domain.check_value("L", "Lb1", "E_C")
# L_E_C_ack_B = domain.check_value("L", "C1", "E_C")
# print("Is Lb1 compatible with the definition of E_C in the LAYER L ? " + str(L_E_C_ack_A))
# print("Is C1 compatible with the definition of E_C in the LAYER L ? " + str(L_E_C_ack_B))
#
# # Are 2 and -1 compatible with the components of the V_I VECTOR variable ?
# V_I_ack_A = domain.check_value("V_I", 2)
# V_I_ack_B = domain.check_value("V_I", -1)
# print("Is 2 compatible with the components of the V_I VECTOR variable ? " + str(V_I_ack_A))
# print("Is -1 compatible with the components of the V_I VECTOR variable ? " + str(V_I_ack_B))
#
# # Are 0.001 and 1.2 compatible with the components of the V_R VECTOR variable ?
# V_R_ack_A = domain.check_value("V_R", 0.001)
# V_R_ack_B = domain.check_value("V_R", 1.2)
# print("Is 0.001 compatible with the components of the V_R VECTOR variable ? " + str(V_R_ack_A))
# print("Is 1.2 compatible with the components of the V_R VECTOR variable ? " + str(V_R_ack_B))
#
# # Are C2 and C5 compatible with the components of the V_C VECTOR variable ?
# V_C_ack_A = domain.check_value("V_C", "V2")
# V_C_ack_B = domain.check_value("V_C", "C5")
# print("Is V2 compatible with the components of the V_C VECTOR variable ? " + str(V_C_ack_A))
# print("Is C5 compatible with the components of the V_C VECTOR variable ? " + str(V_C_ack_B))
#
# # Are 15 and -1 compatible with the E_I definition in the V_L VECTOR variable ?
# V_L_el_1_ack_A = domain.check_value("V_L", 15, "el-1")
# V_L_el_1_ack_B = domain.check_value("V_L", -1, "el-1")
# print("Is 15 compatible with the definition of el-1 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_1_ack_A))
# print("Is -1 compatible with the definition of el-1 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_1_ack_B))
#
# # Are 0.25 and 4.5 compatible with the E_I definition in the V_L VECTOR variable ?
# V_L_el_2_ack_A = domain.check_value("V_L", 0.25, "el-2")
# V_L_el_2_ack_B = domain.check_value("V_L", 4.5, "el-2")
# print("Is 0.25 compatible with the definition of el-2 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_2_ack_A))
# print("Is 4.5 compatible with the definition of el-2 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_2_ack_B))
#
# # Are 1 and C1 compatible with the E_C definition in the V_L VECTOR variable ?
# V_L_el_3_ack_A = domain.check_value("V_L", 1, "el-3")
# V_L_el_3_ack_B = domain.check_value("V_L", 8, "el-3")
# print("Is 1 compatible with the definition of el-3 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_3_ack_A))
# print("Is 8 compatible with the definition of el-3 in the LAYER components of the V_L VECTOR variable ? " + str(
#     V_L_el_3_ack_B))

# **** Possible errors
# 1. The variable is not defined
# I_ack_A = domain_A.check_value("Y", 2)
# L_E_I_ack_A = domain_A.check_value("Y", 2, "E_I")
# V_I_ack_A = domain_A.check_value("Y", 2)
# V_L_el_1_ack_A = domain_A.check_value("Y", 15, "el-1")
# 2. The element is not defined in the LAYER variable
# L_E_I_ack_A = domain_A.check_value("L",2,"E_C_")
# 3. The components of the VECTOR variable are not defined
# V_I_ack_A = domain_A.check_value("V_I_",15)
# V_I_ack_A = domain_A.check_value("V_I_","el-1",15)
# 4. Provide an element name and the variable is defined as BASIC type
# L_E_I_ack_A = domain_A.check_value("I", 2, "E_I")
# 5. Provide an element name and the components of the VECTOR variables are defined as BASIC type
# V_L_el_1_ack_A = domain_A.check_value("V_I", 15, "el-1")
# 6. Checking a value of a LAYER variable without providing an element name
# L_E_I_ack_A = domain_A.check_value("L", 2)
# 7. Checking a value of a VECTOR variable, whose components are defines as LAYER, without providing an element name
# V_L_el_1_ack_A = domain_A.check_value("V_L", 15)
