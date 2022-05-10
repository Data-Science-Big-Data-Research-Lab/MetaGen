from pycvoa.use_cases.domains.support_domain import example_domain as domain

print("The example domain:\n")
print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ===================================== 1. Is a variable defined ? =================================================== #
# ==================================================================================================================== #

is_V_I = domain.is_defined_variable("V_L")
is_V_5 = domain.is_defined_variable("V_5")
print("Is the V_L variable defined in the example domain ? " + str(is_V_I))
print("Is the V_5 variable defined in the example domain ? " + str(is_V_5) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# is_V_I = domain.is_defined_variable(1)

# ==================================================================================================================== #
# ============================ 2. Is an element of a LAYER variable defined ? ======================================== #
# ==================================================================================================================== #

is_L_E_I = domain.is_defined_element("L", "E_I")
is_L_E_J = domain.is_defined_element("L", "E_J")
print("Is the E_I element defined in the L LAYER variable in the example domain ? " + str(is_L_E_I))
print("Is the E_J element defined in the L LAYER variable in the example domain ? " + str(is_L_E_J) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element name must be str.
# is_L_E_I = domain.is_defined_element(1, "E_I")
# is_L_E_I = domain.is_defined_element("L", 1)
# 2. Definition errors:
# 2.1. The LAYER variable is not defined.
# is_L_E_I = domain.is_defined_element("J", "E_I")
# 2.2. The variable is not defined as LAYER type.
# is_L_E_I = domain.is_defined_element("I", "E_I")

# ==================================================================================================================== #
# ========================= 3. Are the components of a VECTOR variable defined ? ===================================== #
# ==================================================================================================================== #

are_V_I = domain.are_defined_components("V_I")
are_V_N = domain.are_defined_components("V_N")
print("Are the components of the V_I vector variable already defined in the example domain ? " + str(are_V_I))
print("Are the components of the V_I_ vector variable already defined in the example domain ? " + str(are_V_N) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# are_V_I = domain.are_defined_components(1)
# 2. Definition errors:
# 2.1. The VECTOR variable is not defined.
# are_V_I = domain.are_defined_components("J")
# 2.2. The variable is not defined as VECTOR type.
# are_V_I = domain.are_defined_components("L")

# ==================================================================================================================== #
# ======================================== 4. Getting the variable type  ============================================= #
# ==================================================================================================================== #

L_type = domain.get_variable_type("L")
print("The type of the L variable is " + L_type + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# L_type = domain.get_variable_type(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# L_type = domain.get_variable_type("J")


# ==================================================================================================================== #
# =============================== 5. Getting the element type of a LAYER variable  =================================== #
# ==================================================================================================================== #

E_C_L_type = domain.get_layer_element_type("L", "E_C")
print("The type of the E_C element of the LAYER variable L is " + E_C_L_type + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# E_C_L_type = domain.get_layer_element_type(1, "E_C")
# E_C_L_type = domain.get_layer_element_type("L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# E_C_L_type = domain.get_layer_element_type("J", "E_C")
# 2.2. The variable is not defined as LAYER type.
# E_C_L_type = domain.get_layer_element_type("I", "E_C")
# 2.3. The element is not defined in the LAYER variable.
# E_C_L_type = domain.get_layer_element_type("L", "E")


# ==================================================================================================================== #
# =========================== 6. Getting the components type of a VECTOR variable  =================================== #
# ==================================================================================================================== #

V_I_type = domain.get_vector_components_type("V_I")
print("The component type of the V_I VECTOR variable is " + V_I_type + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_I_type = domain.get_vector_components_type(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_I_type = domain.get_vector_components_type("J")
# 2.2. The variable is not defined as VECTOR type.
# V_I_type = domain.get_vector_components_type("L")
# 2.3. The components of the VECTOR variable are not defined.
# V_I_type = domain.get_vector_components_type("V_N")


# ==================================================================================================================== #
# =============================== 7. Getting the domain definition =================================================== #
# ==================================================================================================================== #

# The internal definition structure is accessible via "get_definitions" method:
internal_structure = domain.get_definitions()
print(str(internal_structure) + "\n")

# A list of (key, value) pairs can be retained via "get_definition_list"
# It is useful to iterate over the elements of a definition in a for loop
definition_list = domain.get_definition_list()
for variable, definition in definition_list:
    print("The variable " + variable + " has this definition: " + str(definition))

# A list of defined variables can be retained via "get_variable_list"
print("")
variable_list = domain.get_variable_list()
for variable in variable_list:
    print("The variable " + variable + " is defined in the domain")
print("")

# ==================================================================================================================== #
# =============================== 8. Getting the definition of a variable ============================================ #
# ==================================================================================================================== #

I_definition = domain.get_variable_definition("I")
print("I variable definition : " + str(I_definition) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# I_definition = domain.get_variable_definition(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# I_definition = domain.get_variable_definition("J")

# ==================================================================================================================== #
# =========================== 7. Getting the elements definitions of a LAYER variable ================================ #
# ==================================================================================================================== #

# To get a list of the defined elements in a LAYER variable, use the "get_element_list" method
element_list = domain.get_element_list("L")
for element in element_list:
    print("The element " + element + " is defined in the L LAYER variable in the domain")
print("")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# element_list = domain.get_element_list(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# element_list = domain.get_element_list("J")
# 2.2. The variable is not defined as LAYER type.
# element_list = domain.get_element_list("I")

# To get the definition of an element of a LAYER variable, use the "get_element_list" method
E_C_definition = domain.get_element_definition("L", "E_C")
print("E_C element definition in the L LAYER variable: " + str(E_C_definition) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# E_C_definition = domain.get_element_definition(1, "E_C")
# E_C_definition = domain.get_element_definition("L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# E_C_definition = domain.get_element_definition("J", "E_C")
# 2.2. The variable is not defined as LAYER type.
# E_C_definition = domain.get_element_definition("I", "E_C")
# 2.3. The element is not defined in the LAYER variable
# E_C_definition = domain.get_element_definition("L", "E")


# ==================================================================================================================== #
# ======================== 8. Getting the components definition of a VECTOR variable ================================= #
# ==================================================================================================================== #

# To get the component definition of a VECTOR variable, use the "get_component_definition" method
V_I_component_definition = domain.get_vector_component_definition("V_I")
print("Component definition of the V_I VECTOR variable: " + str(V_I_component_definition) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_I_component_definition = domain.get_vector_component_definition(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_I_component_definition = domain.get_vector_component_definition("J")
# 2.2. The variable is not defined as VECTOR type.
# V_I_component_definition = domain.get_vector_component_definition("L")
# 2.3. The components of the VECTOR variable are not defined.
# V_I_component_definition = domain.get_vector_component_definition("V_N")

# ==================================================================================================================== #
# ======================== 9. Getting the elements definition of a LAYER VECTOR variable ============================= #
# ==================================================================================================================== #

# To get a list of the defined elements of the LAYER components of a VECTOR variable, use the
# "get_component_element_list" method
V_L_element_list = domain.get_component_element_list("V_L")
for element in V_L_element_list:
    print("The element " + element + " is defined in the LAYER component of the V_L VECTOR variable in the domain")
print("")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_L_element_list = domain.get_component_element_list(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_L_element_list = domain.get_component_element_list("J")
# 2.2. The variable is not defined as VECTOR type.
# V_L_element_list = domain.get_component_element_list("I")
# 2.3. The components of the VECTOR variable are not defined.
# V_L_element_list = domain.get_component_element_list("V_N")
# 2.4. The components of the VECTOR variable are not defined as LAYER.
# V_L_element_list = domain.get_component_element_list("V_I")


# To get an element definition of LAYER components of a VECTOR variable, use the "get_component_element_definition"
# method
V_L_el_1 = domain.get_component_element_definition("V_L", "el-1")
print("Element definition of the el-1 element of the V_I VECTOR variable: " + str(V_L_el_1) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_L_el_1 = domain.get_component_element_definition(1, "el-1")
# V_L_el_1 = domain.get_component_element_definition("V_L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_L_el_1 = domain.get_component_element_definition("J", "el-1")
# 2.2. The variable is not defined as VECTOR type.
# V_L_el_1 = domain.get_component_element_definition("I", "el-1")
# 2.3. The components of the VECTOR variable are not defined.
# V_L_el_1 = domain.get_component_element_definition("V_N", "el-1")
# 2.4. The components of the VECTOR variable are not defined as LAYER.
# V_L_el_1 = domain.get_component_element_definition("V_I", "el-1")
# 2.5. The element is not defined in the LAYER VECTOR variable.
# V_L_el_1 = domain.get_component_element_definition("V_L", "el")

# ==================================================================================================================== #
# ================ 10. Getting remaining available components of a VECTOR variable =================================== #
# ==================================================================================================================== #

# To get the remaining available components of a VECTOR variable, use the "get_remaining_available_components" method.

print("V_L definition = " + str(domain.get_variable_definition("V_I")))

# If the current size is lower than the minimum size of the vector definition, returns the number of remaining elements
# to satisfy the size definition multiplying by -1.
current_size = 10
r_components = domain.get_remaining_available_complete_components("V_I", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

# If the current size is greater or equal than the minimum size and lower than the maximum size, returns
# the number of remaining available components to complete the vector and satisfy the size definition.
current_size = 25
r_components = domain.get_remaining_available_complete_components("V_I", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

# Otherwise returns 0

current_size = 100
r_components = domain.get_remaining_available_complete_components("V_I", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

current_size = 120
r_components = domain.get_remaining_available_complete_components("V_I", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components)+"\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str. The current size must be int.
# r_components = domain.get_remaining_available_components(1, 4)
# r_components = domain.get_remaining_available_components("V_L", "current_size")
# 2. Definition errors:
# 2.1. The variable is not defined.
# r_components = domain.get_remaining_available_components("J", 4)
# 2.2. The variable is not defined as VECTOR type.
# r_components = domain.get_remaining_available_components("I", 4)

# ==================================================================================================================== #
# ======================= 11. Getting the attributes of a NUMERICAL variable definition ============================== #
# ==================================================================================================================== #

I_attr = domain.get_numerical_variable_attributes("I")
R_attr = domain.get_numerical_variable_attributes("R")
print("Variable I: Minimum value = " + str(I_attr[0]) + ", Maximum value = " + str(I_attr[1])
      + " , Step = " + str(I_attr[2]))
print("Variable R: Minimum value = " + str(R_attr[0]) + ", Maximum value = " + str(R_attr[1])
      + " , Step = " + str(R_attr[2]) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# I_attr = domain.get_numerical_variable_attributes(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# I_attr = domain.get_numerical_variable_attributes("J")
# 2.2. The variable is not defined as NUMERICAL type.
# I_attr = domain.get_numerical_variable_attributes("C")

# ==================================================================================================================== #
# ======================= 12. Getting the attributes of a CATEGORICAL variable definition ============================ #
# ==================================================================================================================== #

C_attr = domain.get_categorical_variable_attributes("C")
print("Variable C: Available categories = " + str(C_attr) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# C_attr = domain.get_categorical_variable_attributes(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# C_attr = domain.get_categorical_variable_attributes("J")
# 2.2. The variable is not defined as CATEGORICAL type.
# C_attr = domain.get_categorical_variable_attributes("I")

# ==================================================================================================================== #
# ================= 13. Getting the attributes of a NUMERICAL element of a LAYER variable definition ================= #
# ==================================================================================================================== #

L_E_I_attr = domain.get_numerical_element_attributes("L", "E_I")
L_E_R_attr = domain.get_numerical_element_attributes("L", "E_R")
print("Variable L, element E_I: Minimum value = " + str(L_E_I_attr[0]) + ", Maximum value = " + str(L_E_I_attr[1])
      + " , Step = " + str(L_E_I_attr[2]))
print("Variable L, element E_R: Minimum value = " + str(L_E_R_attr[0]) + ", Maximum value = " + str(L_E_R_attr[1])
      + " , Step = " + str(L_E_R_attr[2]) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# L_E_I_attr = domain.get_numerical_element_attributes(1, "E_I")
# L_E_I_attr = domain.get_numerical_element_attributes("L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# L_E_I_attr = domain.get_numerical_element_attributes("J", "E_I")
# 2.2. The variable is not defined as LAYER type.
# L_E_I_attr = domain.get_numerical_element_attributes("I", "E_I")
# 2.3. The element is not defined.
# L_E_I_attr = domain.get_numerical_element_attributes("L", "E_I_")
# 2.3. The element is not defined as NUMERICAL type.
# L_E_I_attr = domain.get_numerical_element_attributes("L", "E_C")

# ==================================================================================================================== #
# ============== 14. Getting the attributes of a CATEGORICAL element of a LAYER variable definition ================== #
# ==================================================================================================================== #

L_E_C_attr = domain.get_categorical_element_attributes("L", "E_C")
print("Variable L, element E_C: Available categories = " + str(L_E_C_attr) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# L_E_C_attr = domain.get_categorical_element_attributes(1, "E_C")
# L_E_C_attr = domain.get_categorical_element_attributes("L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# L_E_C_attr = domain.get_categorical_element_attributes("J", "E_C")
# 2.2. The variable is not defined as LAYER type.
# L_E_C_attr = domain.get_categorical_element_attributes("I", "E_C")
# 2.3. The element is not defined.
# L_E_C_attr = domain.get_categorical_element_attributes("L", "E_C_")
# 2.3. The element is not defined as CATEGORICAL type.
# L_E_C_attr = domain.get_categorical_element_attributes("L", "E_I")

# ==================================================================================================================== #
# =================== 15. Getting the attributes of a VECTOR variable definition ===================================== #
# ==================================================================================================================== #

V_I_attr = domain.get_vector_variable_attributes("V_I")
print("Vector variable V_I: Minimum size = " + str(V_I_attr[0]) + ", Maximum size = " + str(V_I_attr[1])
      + " , Step size = " + str(V_I_attr[2])+"\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_I_attr = domain.get_vector_variable_attributes(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_I_attr = domain.get_vector_variable_attributes("J")
# 2.2. The variable is not defined as VECTOR type.
# V_I_attr = domain.get_vector_variable_attributes("C")

# ==================================================================================================================== #
# ============== 16. Getting the attributes of the NUMERICAL components of a VECTOR variable  ======================== #
# ==================================================================================================================== #

V_I_comp_attr = domain.get_numerical_components_attributes("V_I")
V_R_comp_attr = domain.get_numerical_components_attributes("V_R")
print("Vector variable V_I components: Minimum value = " + str(V_I_comp_attr[0]) + ", Maximum value = "
      + str(V_I_comp_attr[1]) + " , Step = " + str(V_I_comp_attr[2]))
print("Vector variable V_R components: Minimum value = " + str(V_R_comp_attr[0]) + ", Maximum value = "
      + str(V_R_comp_attr[1]) + " , Step = " + str(V_R_comp_attr[2]) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_I_comp_attr = domain.get_numerical_components_attributes(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_I_comp_attr = domain.get_numerical_components_attributes("J")
# 2.2. The variable is not defined as VECTOR type.
# V_I_comp_attr = domain.get_numerical_components_attributes("C")
# 2.3. The components are not defined as NUMERICAL type.
# V_I_comp_attr = domain.get_numerical_components_attributes("V_C")

# ==================================================================================================================== #
# =================== 17. Getting the attributes of the CATEGORICAL components of a VECTOR variable ================== #
# ==================================================================================================================== #

V_C_comp_attr = domain.get_categorical_components_attributes("V_C")
print("Vector variable V_C components: Available categories = " + str(V_C_comp_attr) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable must be str.
# V_C_comp_attr = domain.get_categorical_components_attributes(1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_C_comp_attr = domain.get_categorical_components_attributes("J")
# 2.2. The variable is not defined as VECTOR type.
# V_C_comp_attr = domain.get_categorical_components_attributes("C")
# 2.3. The components are not defined as CATEGORICAL type.
# V_C_comp_attr = domain.get_categorical_components_attributes("V_I")

# ==================================================================================================================== #
# =================== 18. Getting the attributes of a NUMERICAL element of LAYER VECTOR variable ===================== #
# ==================================================================================================================== #

V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("V_L", "el-1")
V_L_e_2_attr = domain.get_layer_vector_numerical_element_attributes("V_L", "el-2")
print("Vector Layer Variable V_L, element el-1: Minimum value = " + str(V_L_e_1_attr[0]) + ", Maximum value = "
      + str(V_L_e_1_attr[1]) + " , Step = " + str(V_L_e_1_attr[2]))
print("Vector Layer Variable V_L, element el-2: Minimum value = " + str(V_L_e_2_attr[0]) + ", Maximum value = "
      + str(V_L_e_2_attr[1]) + " , Step = " + str(V_L_e_2_attr[2]) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes(1, "el-1")
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("V_L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("J", "el-1")
# 2.2. The variable is not defined as VECTOR type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("I", "el-1")
# 2.3. The components are not defined as LAYER type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("V_I", "el-1")
# 2.4. The element is not defined.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("V_L", "el-4")
# 2.4. The element is not defined as NUMERICAL type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("V_L", "el-3")

# ==================================================================================================================== #
# ================== 19. Getting the attributes of a CATEGORICAL element of a LAYER VECTOR variable ================== #
# ==================================================================================================================== #

V_L_e_3_attr = domain.get_layer_vector_categorical_attributes("V_L", "el-3")
print("Variable L, element E_C: Available categories = " + str(V_L_e_3_attr) + "\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable and the element must be str.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes(1, "el-3")
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("V_L", 1)
# 2. Definition errors:
# 2.1. The variable is not defined.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("J", "el-3")
# 2.2. The variable is not defined as VECTOR type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("I", "el-3")
# 2.3. The components are not defined as LAYER type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("V_I", "el-3")
# 2.4. The element is not defined.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("V_L", "el-4")
# 2.4. The element is not defined as CATEGORICAL type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("V_L", "el-1")
