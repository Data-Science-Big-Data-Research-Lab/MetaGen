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
I_comp_A = domain.check_basic("I", basic_a)
I_comp_B = domain.check_basic("I", basic_b)
I_comp_C = domain.check_basic("I", basic_c)
I_comp_E = domain.check_basic("I", basic_e)
# print("Are these values compatible with the definition of I in this domain ? ")
# print(str(basic_a) + " => " + str(I_comp_A) + " , " + str(basic_b) + " => " + str(I_comp_B) + " , "
#       + str(basic_c) + " => " + str(I_comp_C) + " , " + str(basic_e) + " => " + str(I_comp_E) + "\n")

# Value compatibility of the definition of R
R_comp_C = domain.check_basic("R", basic_c)
R_comp_D = domain.check_basic("R", basic_d)
R_comp_A = domain.check_basic("R", basic_a)
R_comp_E = domain.check_basic("R", basic_e)
# print("Are these values compatible with the definition of R in this domain ? ")
# print(str(basic_c) + " => " + str(R_comp_C) + " , " + str(basic_d) + " => " + str(R_comp_D) + " , "
#       + str(basic_a) + " => " + str(R_comp_A) + " , " + str(basic_e) + " => " + str(R_comp_E) + "\n")

# Value compatibility of the definition of C
C_comp_E = domain.check_basic("C", basic_e)
C_comp_F = domain.check_basic("C", basic_f)
C_comp_A = domain.check_basic("C", basic_a)
C_comp_C = domain.check_basic("C", basic_c)
# print("Are these values compatible with the definition of C in this domain ? ")
# print(str(basic_e) + " => " + str(C_comp_E) + " , " + str(basic_f) + " => " + str(C_comp_F) + " , "
#       + str(basic_a) + " => " + str(C_comp_A) + " , " + str(basic_c) + " => " + str(C_comp_C) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# res = domain.check_basic(1, 2)
# - The value must be int, float or str.
# res = domain.check_basic("C", {"EI": 20, "ER": 1.8, "EC": "Lb2"})
# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# I_comp_A = domain.check_basic("J", 2)



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
L_E_I_comp_A = domain.check_element("L", "EI", element_a)
L_E_I_comp_B = domain.check_element("L", "EI", element_b)
L_E_I_comp_C = domain.check_element("L", "EI", element_c)
L_E_I_comp_E = domain.check_element("L", "EI", element_e)
# print("Are these values compatible with the definition of EI of L in this domain ? ")
# print(str(element_a) + " => " + str(L_E_I_comp_A) + " , " + str(element_b) + " => " + str(L_E_I_comp_B) + " , "
#       + str(element_c) + " => " + str(L_E_I_comp_C) + " , " + str(element_e) + " => " + str(L_E_I_comp_E) + "\n")

# Value compatibility of the E_R element of L
L_E_R_comp_C = domain.check_element("L", "ER", element_c)
L_E_R_comp_D = domain.check_element("L", "ER", element_d)
L_E_R_comp_A = domain.check_element("L", "ER", element_a)
L_E_R_comp_E = domain.check_element("L", "ER", element_e)
# print("Are these values compatible with the definition of ER of L in this domain ? ")
# print(str(element_c) + " => " + str(L_E_R_comp_C) + " , " + str(element_d) + " => " + str(L_E_R_comp_D) + " , "
#       + str(element_a) + " => " + str(L_E_R_comp_A) + " , " + str(element_e) + " => " + str(L_E_R_comp_E) + "\n")

# Value compatibility of the E_C element of L
L_E_C_comp_E = domain.check_element("L", "EC", element_e)
L_E_C_comp_F = domain.check_element("L", "EC", element_f)
L_E_C_comp_A = domain.check_element("L", "EC", element_a)
L_E_C_comp_C = domain.check_element("L", "EC", element_c)
# print("Are these values compatible with the definition of EC of L in this domain ? ")
# print(str(element_e) + " => " + str(L_E_C_comp_E) + " , " + str(element_f) + " => " + str(L_E_C_comp_F) + " , "
#       + str(element_a) + " => " + str(L_E_C_comp_A) + " , " + str(element_c) + " => " + str(L_E_C_comp_C))

# **** Argument type errors (static):
# - The variable and the element must be str. The value must be int, float or str.
# L_E_I_comp_A = domain.check_element(1, "EI", element_a)
# L_E_I_comp_A = domain.check_element("L", 1, element_a)
# L_E_I_comp_A = domain.check_element("L", "EI", [1, 2])
# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# L_E_I_comp_A = domain.check_element("J", "EI", element_a)
# - The variable is not defined as LAYER type.
# L_E_I_comp_A = domain.check_element("I", "EI", element_a)
# - The element is not defined in the LAYER variable
# L_E_I_comp_A = domain.check_element("L", "EF", element_a)

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

L_layer_a = domain.check_layer("L", layer_a)
L_layer_b = domain.check_layer("L", layer_b)
L_layer_c = domain.check_layer("L", layer_c)
L_layer_d = domain.check_layer("L", layer_d)
L_layer_e = domain.check_layer("L", layer_e)
L_layer_f = domain.check_layer("L", layer_f)
L_layer_g = domain.check_layer("L", layer_g)
print("Are these layers compatible with L ? ")
print(str(layer_a) + " => " + str(L_layer_a) + "\n" + str(layer_b) + " => " + str(L_layer_b) + "\n"
      + str(layer_c) + " => " + str(L_layer_c) + "\n" + str(layer_d) + " => " + str(L_layer_d) + "\n"
      + str(layer_e) + " => " + str(L_layer_e) + "\n" + str(layer_f) + " => " + str(L_layer_f) + "\n"
      + str(layer_g) + " => " + str(L_layer_g) + "\n")

# **** Argument type errors (static):
# - The variable and must be str. The value must be a map.
# L_layer_a = domain.check_layer(1, layer_a)
# L_layer_a = domain.check_layer("L", 1)
# **** Definition errors (raise DefinitionError):
# - The  variable is not defined.
# L_layer_a = domain.check_layer("J", layer_a)
# - The variable is not defined as LAYER type.
# L_layer_a = domain.check_layer("I", layer_a)
# - The layer is not complete.
# L_layer_a = domain.check_layer("L",  {"EI": 20, "ER": 1.8})

# ==================================================================================================================== #
# ======================== 4. Checking BASIC component values of a VECTOR variable =================================== #
# ==================================================================================================================== #

# Values to check
component_a = 5
component_b = 11
component_c = 0.0001
component_d = 0.2
component_e = "V1"
component_f = "Lb1"

# Value compatibility of the V_I components
V_I_comp_A = domain.check_vector_basic_value("VI", component_a)
V_I_comp_B = domain.check_vector_basic_value("VI", component_b)
V_I_comp_C = domain.check_vector_basic_value("VI", component_c)
V_I_comp_E = domain.check_vector_basic_value("VI", component_e)
print("Are these values compatible with the components definition of VI in this domain ? ")
print(str(component_a) + " => " + str(V_I_comp_A) + " , " + str(component_b) + " => " + str(V_I_comp_B) + " , "
      + str(component_c) + " => " + str(V_I_comp_C) + " , " + str(component_e) + " => " + str(V_I_comp_E) + "\n")

# Value compatibility of the V_R components
V_R_comp_C = domain.check_vector_basic_value("VR", component_c)
V_R_comp_D = domain.check_vector_basic_value("VR", component_d)
V_R_comp_A = domain.check_vector_basic_value("VR", component_a)
V_R_comp_E = domain.check_vector_basic_value("VR", component_e)
print("Are these values compatible with the components definition of VR in this domain ? ")
print(str(component_c) + " => " + str(V_R_comp_C) + " , " + str(component_d) + " => " + str(V_R_comp_D) + " , "
      + str(component_a) + " => " + str(V_R_comp_A) + " , " + str(component_e) + " => " + str(V_R_comp_E) + "\n")

# Value compatibility of the V_C components
V_C_comp_E = domain.check_vector_basic_value("VC", component_e)
V_C_comp_F = domain.check_vector_basic_value("VC", component_f)
V_C_comp_A = domain.check_vector_basic_value("VC", component_a)
V_C_comp_C = domain.check_vector_basic_value("VC", component_c)
print("Are these values compatible with the components definition of VC in this domain ? ")
print(str(component_e) + " => " + str(V_C_comp_E) + " , " + str(component_f) + " => " + str(V_C_comp_F) + " , "
      + str(component_a) + " => " + str(V_C_comp_A) + " , " + str(component_c) + " => " + str(V_C_comp_C) + "\n")

# **** Argument type errors (static):
# - The variable must be str. The value must be int, float or str.
# V_I_comp_A = domain.check_vector_basic_value(1, component_a)
# V_I_comp_A = domain.check_vector_basic_value("VC", [1, 2])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_comp_A = domain.check_vector_basic_value("J", component_a)
# - The variable is not defined as VECTOR type.
# V_I_comp_A = domain.check_vector_basic_value("I", component_a)
#  - The components of the VECTOR variable are not defined.
# V_I_comp_A = domain.check_vector_basic_value("VN", component_a)
#  - The components of the VECTOR variable are not defined as BASIC.
# V_I_comp_A = domain.check_vector_basic_value("VL", component_a)


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

# Value compatibility of the el1 element of VL
V_L_el_1_comp_A = domain.check_vector_layer_element_value("VL", "el1", component_element_a)
V_L_el_1_comp_B = domain.check_vector_layer_element_value("VL", "el1", component_element_b)
V_L_el_1_comp_C = domain.check_vector_layer_element_value("VL", "el1", component_element_c)
V_L_el_1_comp_G = domain.check_vector_layer_element_value("VL", "el1", component_element_g)
print("Are these values compatible with the el1 element definition of the components of VL ? ")
print(str(component_element_a) + " => " + str(V_L_el_1_comp_A) + " , "
      + str(component_element_b) + " => " + str(V_L_el_1_comp_B) + " , "
      + str(component_element_c) + " => " + str(V_L_el_1_comp_C) + " , "
      + str(component_element_g) + " => " + str(V_L_el_1_comp_G) + "\n")

# Value compatibility of the el2 element of VL
V_L_el_2_comp_C = domain.check_vector_layer_element_value("VL", "el2", component_element_c)
V_L_el_2_comp_D = domain.check_vector_layer_element_value("VL", "el2", component_element_d)
V_L_el_2_comp_A = domain.check_vector_layer_element_value("VL", "el2", component_element_a)
V_L_el_2_comp_G = domain.check_vector_layer_element_value("VL", "el2", component_element_g)
print("Are these values compatible with the el2 element definition of the components of VL ? ")
print(str(component_element_c) + " => " + str(V_L_el_2_comp_C) + " , "
      + str(component_element_d) + " => " + str(V_L_el_2_comp_D) + " , "
      + str(component_element_a) + " => " + str(V_L_el_2_comp_A) + " , "
      + str(component_element_g) + " => " + str(V_L_el_2_comp_G) + "\n")

# Value compatibility of the el3 element of VL
V_L_el_3_comp_E = domain.check_vector_layer_element_value("VL", "el3", component_element_e)
V_L_el_3_comp_F = domain.check_vector_layer_element_value("VL", "el3", component_element_f)
V_L_el_3_comp_C = domain.check_vector_layer_element_value("VL", "el3", component_element_c)
V_L_el_3_comp_G = domain.check_vector_layer_element_value("VL", "el3", component_element_g)
print("Are these values compatible with the el3 element definition of the components of VL ? ")
print(str(component_element_e) + " => " + str(V_L_el_3_comp_E) + " , "
      + str(component_element_f) + " => " + str(V_L_el_3_comp_F) + " , "
      + str(component_element_c) + " => " + str(V_L_el_3_comp_C) + " , "
      + str(component_element_g) + " => " + str(V_L_el_3_comp_G) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str. The value must be int, float or str.
# V_L_el_1_comp_A = domain.check_vector_layer_element_value(1, "el1", component_element_a)
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("VL", 1, component_element_a)
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("VL", "el1", [1, 2])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("J", "el1", component_element_a)
# - The variable is not defined as VECTOR type.
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("I", "el1", component_element_a)
# - The components of the VECTOR variable are not defined.
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("VN", "el1", component_element_a)
# - The components of the VECTOR variable are not defined as LAYER.
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("VI", "el1", component_element_a)
# - The element is not defined in the VECTOR LAYER variable
# V_L_el_1_comp_A = domain.check_vector_layer_element_value("VL", "el4", component_element_a)


# ==================================================================================================================== #
# ============================= 6. Checking the size of complete VECTOR values ======================================= #
# ==================================================================================================================== #

# Values to check
integer_values_a = [1, 2, 3, 4, 5]
integer_values_b = []
integer_values_c = [1, 2, 3, 4, 5, 6, 7, 8]
real_values_a = [0.001, 0.002, 0.003, 0.004, 0.005]
real_values_b = [0.001]
real_values_c = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010, 0.011]
categorical_values_a = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
categorical_values_b = ["V1", "V2", "V3"]
categorical_values_c = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1", "V1", "V2",
                        "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
layer_values_a = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1}]
layer_values_b = [{"el-1": 15, "el-2": 0.2, "el-3": 2}]
layer_values_c = [{"el-1": 15, "el-2": 0.2, "el-3": 2}, {"el-1": 12, "el-2": 0.3, "el-3": 1},
                  {"el-1": 17, "el-2": 0.5, "el-3": 2}, {"el-1": 14, "el-2": 0.15, "el-3": 3},
                  {"el-1": 11, "el-2": 0.12, "el-3": 3}]

V_I_size_i_a = domain.check_vector_values_size("VI", integer_values_a)
V_I_size_l_b = domain.check_vector_values_size("VI", layer_values_b)
print("Are these sizes compatible with VI definition ? ")
print(str(integer_values_a) + " => " + str(V_I_size_i_a) + "\n"
      + str(layer_values_b) + " => " + str(V_I_size_l_b) + "\n")

V_R_size_r_a = domain.check_vector_values_size("VR", real_values_a)
V_R_size_i_b = domain.check_vector_values_size("VR", integer_values_b)
print("Are these sizes compatible with VR definition ? ")
print(str(real_values_a) + " => " + str(V_R_size_r_a) + "\n"
      + str(integer_values_b) + " => " + str(V_R_size_i_b) + "\n")

V_C_size_c_a = domain.check_vector_values_size("VC", categorical_values_a)
V_C_size_l_c = domain.check_vector_values_size("VC", layer_values_c)
print("Are these sizes compatible with VC definition ? ")
print(str(categorical_values_a) + " => " + str(V_C_size_c_a) + "\n"
      + str(layer_values_c) + " => " + str(V_C_size_l_c) + "\n")

V_L_size_l_a = domain.check_vector_values_size("VL", layer_values_a)
V_L_size_i_c = domain.check_vector_values_size("VL", integer_values_c)
print("Are these sizes compatible with VL definition ? ")
print(str(layer_values_a) + " => " + str(V_L_size_l_a) + "\n"
      + str(integer_values_c) + " => " + str(V_L_size_i_c) + "\n")

# **** Argument type errors (static):
# - The variable must be str. The values must be a list.
# V_I_size_i_a = domain.check_vector_values_size(1, integer_values_a)
# V_I_size_i_a = domain.check_vector_values_size("VI", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_size_i_a = domain.check_vector_values_size("J", integer_values_a)
# - The variable is not defined as VECTOR type.
# V_I_size_i_a = domain.check_vector_values_size("I", integer_values_a)


# ==================================================================================================================== #
# ============================= 7. Checking complete values of BASIC VECTOR ========================================== #
# ==================================================================================================================== #

# Values to check
values_a = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
values_b = [1, 20, 3, 4, 5, 6, 7, 8, 9, 10]
values_c = [0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010]
values_d = [0.001, 0.002, 0.003, 0.004, 5]
values_e = ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"]
values_f = ["V1", "V2", 1, "V1", "V2", "V3", "V1", "V2", "V3", "V1"]

V_I_val_a = domain.check_vector_basic_values("VI", values_a)
V_I_val_b = domain.check_vector_basic_values("VI", values_b)
V_I_val_c = domain.check_vector_basic_values("VI", values_c)
print("Are these values compatible with VI definition ? ")
print(str(values_a) + " => " + str(V_I_val_a) + "\n" + str(values_b) + " => " + str(V_I_val_b) + "\n"
      + str(values_c) + " => " + str(V_I_val_c) + "\n")

V_R_val_c = domain.check_vector_basic_values("VR", values_c)
V_R_val_d = domain.check_vector_basic_values("VR", values_d)
V_R_val_a = domain.check_vector_basic_values("VR", values_a)
V_R_val_e = domain.check_vector_basic_values("VR", values_e)
print("Are these values compatible with VR definition ? ")
print(str(values_c) + " => " + str(V_R_val_c) + "\n" + str(values_d) + " => " + str(V_R_val_d) + "\n"
      + str(values_a) + " => " + str(V_R_val_a) + "\n" + str(values_e) + " => " + str(V_R_val_e) + "\n")

V_C_val_e = domain.check_vector_basic_values("VC", values_e)
V_C_val_f = domain.check_vector_basic_values("VC", values_f)
print("Are these values compatible with VC definition ? ")
print(str(values_e) + " => " + str(V_C_val_e) + "\n" + str(values_f) + " => " + str(V_C_val_f) + "\n")

# **** Argument type errors (static):
# - The variable name must be str. The values must be list.
# V_I_val_a = domain.check_vector_basic_values(1, values_a)
# V_I_val_a = domain.check_vector_basic_values("VI", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_val_a = domain.check_vector_basic_values("J", values_a)
# - The variable is not defined as VECTOR type.
# V_I_val_a = domain.check_vector_basic_values("I", values_a)
# - The components of the VECTOR variable are not defined.
# V_I_val_a = domain.check_vector_basic_values("VN", values_a)
# - The components of the VECTOR variable are not defined as BASIC.
# V_I_val_a = domain.check_vector_basic_values("VL", values_a)
# - The size of the values is not compatible with the vector definition.
# V_I_val_a = domain.check_vector_basic_values("VI", [1, 2])

# ==================================================================================================================== #
# ============================= 8. Checking layers for a LAYER VECTOR ================================================ #
# ==================================================================================================================== #

vector_layer_a = {"el1": 15, "el2": 0.2, "el3": 2}
vector_layer_b = {"el1": 8, "el2": 0.3, "el3": 1}
vector_layer_c = {"el1": 17, "el2": 0.05, "el3": 2}
vector_layer_d = {"el1": 14, "el2": 0.15, "el3": 4}

V_L_layer_a = domain.check_vector_layer_elements_values("VL", vector_layer_a)
V_L_layer_b = domain.check_vector_layer_elements_values("VL", vector_layer_b)
V_L_layer_c = domain.check_vector_layer_elements_values("VL", vector_layer_c)
V_L_layer_d = domain.check_vector_layer_elements_values("VL", vector_layer_d)
print("Are these layers compatible with VL definition ? ")
print(str(vector_layer_a) + " => " + str(V_L_layer_a) + "\n" + str(vector_layer_b) + " => " + str(V_L_layer_b) + "\n"
      + str(vector_layer_c) + " => " + str(V_L_layer_c) + "\n" + str(vector_layer_d) + " => " + str(V_L_layer_d) + "\n")

# **** Argument type errors (static):
# - The variable name must be str. The values must be dict.
# V_L_layer_a = domain.check_vector_layer_elements_values(1, vector_layer_a)
# V_L_layer_a = domain.check_vector_layer_elements_values("V_L", [1, 2])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_layer_a = domain.check_vector_layer_elements_values("J", vector_layer_a)
# - The variable is not defined as VECTOR type.
# V_L_layer_a = domain.check_vector_layer_elements_values("I", vector_layer_a)
# - The components of the VECTOR variable are not defined.
# V_L_layer_a = domain.check_vector_layer_elements_values("VN", vector_layer_a)
# - The components of the VECTOR variable are not defined as LAYER.
# V_L_layer_a = domain.check_vector_layer_elements_values("VI", vector_layer_a)
# - The element of the values is not defined in the VECTOR LAYER variable.
# V_L_layer_a = domain.check_vector_layer_elements_values("VL", {"el1": 15, "el2": 0.2, "el3": 2, "el4": 3})
# - The layer is not complete.
# V_L_layer_a = domain.check_vector_layer_elements_values("VL", {"el1": 14, "el2": 0.15})

# ==================================================================================================================== #
# ========================= 9. Checking complete layer values for a LAYER VECTOR ===================================== #
# ==================================================================================================================== #

vector_layer_values_a = [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]
vector_layer_values_b = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}]
vector_layer_values_c = [{"el1": 25, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": "V1"}]
vector_layer_values_d = [{"el1": 15, "el2": 0.2, "el3": 2}, {"el1": 12, "el2": 0.3, "el3": 1}
    , {"el1": 14, "el2": 0.15, "el3": 3}, {"el1": 17, "el2": 0.25, "el3": 2}]

V_L_vector_layer_a = domain.check_vector_layer_values("VL", vector_layer_values_a)
V_L_vector_layer_b = domain.check_vector_layer_values("VL", vector_layer_values_b)
V_L_vector_layer_c = domain.check_vector_layer_values("VL", vector_layer_values_c)
V_L_vector_layer_d = domain.check_vector_layer_values("VL", vector_layer_values_d)
print("Are these layer values compatible with VL definition ? ")
print(str(vector_layer_values_a) + " => " + str(V_L_vector_layer_a) + "\n"
      + str(vector_layer_values_b) + " => " + str(V_L_vector_layer_b) + "\n"
      + str(vector_layer_values_c) + " => " + str(V_L_vector_layer_c) + "\n"
      + str(vector_layer_values_d) + " => " + str(V_L_vector_layer_d) + "\n")

# **** Argument type errors (static):
# - The variable name must be str. The values must be list of dict.
# V_L_vector_layer_a = domain.check_vector_layer_values(1, vector_layer_values_a)
# V_L_vector_layer_a = domain.check_vector_layer_values("VL", [1, 2])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_vector_layer_a = domain.check_vector_layer_values("J", vector_layer_values_a)
# - The variable is not defined as VECTOR type.
# V_L_vector_layer_a = domain.check_vector_layer_values("I", vector_layer_values_a)
# - The components of the VECTOR variable are not defined.
# V_L_vector_layer_a = domain.check_vector_layer_values("VN", vector_layer_values_a)
# - The components of the VECTOR variable are not defined as LAYER.
# V_L_vector_layer_a = domain.check_vector_layer_values("VI", vector_layer_values_a)
# - The size of the values is not compatible with the vector definition.
# V_L_vector_layer_a = domain.check_vector_layer_values("VL", [{"el1": 15, "el2": 0.2, "el3": 2}])
# - The element a component of the values not defined in the VECTOR LAYER variable.
# V_L_vector_layer_a = domain.check_vector_layer_values("VL", [{"el1": 15, "el2": 0.2, "el3": 2},
#                                                              {"el1": 12, "el2": 0.3, "el5": 1}])
# - A layer of the components of the VECTOR LAYER variable is not complete.
# V_L_vector_layer_a = domain.check_vector_layer_values("VL", [{"el1": 15, "el2": 0.2, "el3": 2},
#                                                             {"el1": 12, "el2": 0.3}])
