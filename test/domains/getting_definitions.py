from utils import domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ===================================== 1. Is a variable defined ? =================================================== #
# ==================================================================================================================== #

is_V_I = domain.is_defined_variable("VL")
is_V_5 = domain.is_defined_variable("V5")
print("Is the VL variable defined in the example domain ? " + str(is_V_I))
print("Is the V5 variable defined in the example domain ? " + str(is_V_5) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# is_V_I = domain.is_defined_variable(1)

# ==================================================================================================================== #
# ============================ 2. Is an element of a LAYER variable defined ? ======================================== #
# ==================================================================================================================== #

is_L_E_I = domain.is_defined_element("L", "EI")
is_L_E_J = domain.is_defined_element("L", "EJ")
print("Is the EI element defined in the L LAYER variable in the example domain ? " + str(is_L_E_I))
print("Is the EJ element defined in the L LAYER variable in the example domain ? " + str(is_L_E_J) + "\n")

# **** Argument type errors (static):
# - The variable and the element name must be str.
# is_L_E_I = domain.is_defined_element(1, "EI")
# is_L_E_I = domain.is_defined_element("L", 1)
# **** Definition errors (raise DefinitionError):
# - The LAYER variable is not defined.
# is_L_E_I = domain.is_defined_element("J", "EI")
# - The variable is not defined as LAYER type.
# is_L_E_I = domain.is_defined_element("I", "EI")

# ==================================================================================================================== #
# ========================= 3. Are the components of a VECTOR variable defined ? ===================================== #
# ==================================================================================================================== #

are_V_I = domain.are_defined_components("VI")
are_V_N = domain.are_defined_components("VN")
print("Are the components of the VI vector variable already defined in the example domain ? " + str(are_V_I))
print("Are the components of the VN vector variable already defined in the example domain ? " + str(are_V_N) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# are_V_I = domain.are_defined_components(1)
# **** Definition errors (raise DefinitionError):
# - The VECTOR variable is not defined.
# are_V_I = domain.are_defined_components("J")
# - The variable is not defined as VECTOR type.
# are_V_I = domain.are_defined_components("L")

# ==================================================================================================================== #
# ======================================== 4. Getting the variable type  ============================================= #
# ==================================================================================================================== #

L_type = domain.get_variable_type("L")
print("The type of the L variable is " + L_type + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# L_type = domain.get_variable_type(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# L_type = domain.get_variable_type("J")


# ==================================================================================================================== #
# =============================== 5. Getting the element type of a LAYER variable  =================================== #
# ==================================================================================================================== #

E_C_L_type = domain.get_layer_element_type("L", "EC")
print("The type of the EC element of the LAYER variable L is " + E_C_L_type + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str.
# E_C_L_type = domain.get_layer_element_type(1, "E_C")
# E_C_L_type = domain.get_layer_element_type("L", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# E_C_L_type = domain.get_layer_element_type("J", "EC")
# - The variable is not defined as LAYER type.
# E_C_L_type = domain.get_layer_element_type("I", "EC")
# - The element is not defined in the LAYER variable.
# E_C_L_type = domain.get_layer_element_type("L", "E")


# ==================================================================================================================== #
# =========================== 6. Getting the components type of a VECTOR variable  =================================== #
# ==================================================================================================================== #

V_I_type = domain.get_vector_components_type("VI")
print("The component type of the VI VECTOR variable is " + V_I_type + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# V_I_type = domain.get_vector_components_type(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_type = domain.get_vector_components_type("J")
# - The variable is not defined as VECTOR type.
# V_I_type = domain.get_vector_components_type("L")
# - The components of the VECTOR variable are not defined.
# V_I_type = domain.get_vector_components_type("VN")


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

# **** Argument type errors (static):
# - The variable must be str.
# I_definition = domain.get_variable_definition(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# I_definition = domain.get_variable_definition("J")

# ==================================================================================================================== #
# =========================== 7. Getting the elements definitions of a LAYER variable ================================ #
# ==================================================================================================================== #

# To get a list of the defined elements in a LAYER variable, use the "get_element_list" method
element_list = domain.get_element_list("L")
for element in element_list:
    print("The element " + element + " is defined in the L LAYER variable in the domain")
print("")

# **** Argument type errors (static):
# - The variable must be str.
# element_list = domain.get_element_list(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# element_list = domain.get_element_list("J")
# - The variable is not defined as LAYER type.
# element_list = domain.get_element_list("I")

# To get the definition of an element of a LAYER variable, use the "get_element_list" method
E_C_definition = domain.get_element_definition("L", "EC")
print("E_C element definition in the L LAYER variable: " + str(E_C_definition) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str.
# E_C_definition = domain.get_element_definition(1, "EC")
# E_C_definition = domain.get_element_definition("L", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# E_C_definition = domain.get_element_definition("J", "EC")
# 2.2. The variable is not defined as LAYER type.
# E_C_definition = domain.get_element_definition("I", "EC")
# 2.3. The element is not defined in the LAYER variable
# E_C_definition = domain.get_element_definition("L", "E")


# ==================================================================================================================== #
# ======================== 8. Getting the components definition of a VECTOR variable ================================= #
# ==================================================================================================================== #

# To get the component definition of a VECTOR variable, use the "get_component_definition" method
V_I_component_definition = domain.get_vector_component_definition("VI")
print("Component definition of the VI VECTOR variable: " + str(V_I_component_definition) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# V_I_component_definition = domain.get_vector_component_definition(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_component_definition = domain.get_vector_component_definition("J")
# - The variable is not defined as VECTOR type.
# V_I_component_definition = domain.get_vector_component_definition("L")
# - The components of the VECTOR variable are not defined.
# V_I_component_definition = domain.get_vector_component_definition("VN")

# ==================================================================================================================== #
# ======================== 9. Getting the elements definition of a LAYER VECTOR variable ============================= #
# ==================================================================================================================== #

# To get a list of the defined elements of the LAYER components of a VECTOR variable, use the
# "get_component_element_list" method
V_L_element_list = domain.get_component_element_list("VL")
for element in V_L_element_list:
    print("The element " + element + " is defined in the LAYER component of the VL VECTOR variable in the domain")
print("")

# **** Argument type errors (static):
# - The variable must be str.
# V_L_element_list = domain.get_component_element_list(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_element_list = domain.get_component_element_list("J")
# - The variable is not defined as VECTOR type.
# V_L_element_list = domain.get_component_element_list("I")
# - The components of the VECTOR variable are not defined.
# V_L_element_list = domain.get_component_element_list("VN")
# - The components of the VECTOR variable are not defined as LAYER.
# V_L_element_list = domain.get_component_element_list("VI")


# To get an element definition of LAYER components of a VECTOR variable, use the "get_component_element_definition"
# method
V_L_el_1 = domain.get_component_element_definition("VL", "el1")
print("Element definition of the el1 element of the VI VECTOR variable: " + str(V_L_el_1) + "\n")


# **** Argument type errors (static):
# - The variable must be str.
# V_L_el_1 = domain.get_component_element_definition(1, "el1")
# V_L_el_1 = domain.get_component_element_definition("VL", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_el_1 = domain.get_component_element_definition("J", "el1")
# - The variable is not defined as VECTOR type.
# V_L_el_1 = domain.get_component_element_definition("I", "el1")
# - The components of the VECTOR variable are not defined.
# V_L_el_1 = domain.get_component_element_definition("VN", "el1")
# - The components of the VECTOR variable are not defined as LAYER.
# V_L_el_1 = domain.get_component_element_definition("VI", "el1")
# - The element is not defined in the LAYER VECTOR variable.
# V_L_el_1 = domain.get_component_element_definition("VL", "el")

# ==================================================================================================================== #
# ================ 10. Getting remaining available components of a VECTOR variable =================================== #
# ==================================================================================================================== #

# To get the remaining available components of a VECTOR variable, use the "get_remaining_available_components" method.

print("VI definition = " + str(domain.get_variable_definition("VI")))

# If the current size is lower than the minimum size of the vector definition, returns the number of remaining elements
# to satisfy the size definition multiplying by -1.
current_size = 5
r_components = domain.get_remaining_available_complete_components("VI", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

# If the current size is greater or equal than the minimum size and lower than the maximum size, returns
# the number of remaining available components to complete the vector and satisfy the size definition.
current_size = 10
r_components = domain.get_remaining_available_complete_components("VI", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

current_size = 25
r_components = domain.get_remaining_available_complete_components("VI", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components))

# Otherwise returns 0

current_size = 100
r_components = domain.get_remaining_available_complete_components("VI", current_size)
print("Available components with current size (" + str(current_size) + ") = " + str(r_components)+"\n")

# **** Argument type errors (static):
# - The variable must be str.
# r_components = domain.get_remaining_available_complete_components(1, 4)
# r_components = domain.get_remaining_available_complete_components("V_L", "current_size")
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# r_components = domain.get_remaining_available_complete_components("J", 4)
# - The variable is not defined as VECTOR type.
# r_components = domain.get_remaining_available_complete_components("I", 4)

# ==================================================================================================================== #
# ================= 11. Getting the attributes of a INTEGER/REAL (NUMERICAL) variable definition ===================== #
# ==================================================================================================================== #

I_attr = domain.get_numerical_variable_attributes("I")
R_attr = domain.get_numerical_variable_attributes("R")
print("Variable I: Minimum value = " + str(I_attr[0]) + ", Maximum value = " + str(I_attr[1])
      + " , Step = " + str(I_attr[2]))
print("Variable R: Minimum value = " + str(R_attr[0]) + ", Maximum value = " + str(R_attr[1])
      + " , Step = " + str(R_attr[2]) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# I_attr = domain.get_numerical_variable_attributes(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# I_attr = domain.get_numerical_variable_attributes("J")
# - The variable is not defined as NUMERICAL type.
# I_attr = domain.get_numerical_variable_attributes("C")

# ==================================================================================================================== #
# ======================= 12. Getting the attributes of a CATEGORICAL variable definition ============================ #
# ==================================================================================================================== #

C_attr = domain.get_categorical_variable_attributes("C")
print("Variable C: Available categories = " + str(C_attr) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# C_attr = domain.get_categorical_variable_attributes(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# C_attr = domain.get_categorical_variable_attributes("J")
# - The variable is not defined as CATEGORICAL type.
# C_attr = domain.get_categorical_variable_attributes("I")

# ==================================================================================================================== #
# ================= 13. Getting the attributes of a NUMERICAL element of a LAYER variable definition ================= #
# ==================================================================================================================== #

L_E_I_attr = domain.get_numerical_element_attributes("L", "EI")
L_E_R_attr = domain.get_numerical_element_attributes("L", "ER")
print("Variable L, element EI: Minimum value = " + str(L_E_I_attr[0]) + ", Maximum value = " + str(L_E_I_attr[1])
      + " , Step = " + str(L_E_I_attr[2]))
print("Variable L, element ER: Minimum value = " + str(L_E_R_attr[0]) + ", Maximum value = " + str(L_E_R_attr[1])
      + " , Step = " + str(L_E_R_attr[2]) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# L_E_I_attr = domain.get_numerical_element_attributes(1, "EI")
# L_E_I_attr = domain.get_numerical_element_attributes("L", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# L_E_I_attr = domain.get_numerical_element_attributes("J", "EI")
# - The variable is not defined as LAYER type.
# L_E_I_attr = domain.get_numerical_element_attributes("I", "EI")
# - The element is not defined.
# L_E_I_attr = domain.get_numerical_element_attributes("L", "EI_")
# - The element is not defined as NUMERICAL type.
# L_E_I_attr = domain.get_numerical_element_attributes("L", "EC")

# ==================================================================================================================== #
# ============== 14. Getting the attributes of a CATEGORICAL element of a LAYER variable definition ================== #
# ==================================================================================================================== #

L_E_C_attr = domain.get_categorical_element_attributes("L", "EC")
print("Variable L, element EC: Available categories = " + str(L_E_C_attr) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str.
# L_E_C_attr = domain.get_categorical_element_attributes(1, "EC")
# L_E_C_attr = domain.get_categorical_element_attributes("L", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# L_E_C_attr = domain.get_categorical_element_attributes("J", "EC")
# - The variable is not defined as LAYER type.
# L_E_C_attr = domain.get_categorical_element_attributes("I", "EC")
# - The element is not defined.
# L_E_C_attr = domain.get_categorical_element_attributes("L", "EC_")
# - The element is not defined as CATEGORICAL type.
# L_E_C_attr = domain.get_categorical_element_attributes("L", "EI")

# ==================================================================================================================== #
# =================== 15. Getting the attributes of a VECTOR variable definition ===================================== #
# ==================================================================================================================== #

V_I_attr = domain.get_vector_variable_attributes("VN")
print("Vector variable VI: Minimum size = " + str(V_I_attr[0]) + ", Maximum size = " + str(V_I_attr[1])
      + " , Step size = " + str(V_I_attr[2])+"\n")

# **** Argument type errors (static):
# - The variable must be str.
# V_I_attr = domain.get_vector_variable_attributes(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_attr = domain.get_vector_variable_attributes("J")
# - The variable is not defined as VECTOR type.
# V_I_attr = domain.get_vector_variable_attributes("C")

# ==================================================================================================================== #
# ============== 16. Getting the attributes of the NUMERICAL components of a VECTOR variable  ======================== #
# ==================================================================================================================== #

V_I_comp_attr = domain.get_numerical_components_attributes("VI")
V_R_comp_attr = domain.get_numerical_components_attributes("VR")
print("Vector variable VI components: Minimum value = " + str(V_I_comp_attr[0]) + ", Maximum value = "
      + str(V_I_comp_attr[1]) + " , Step = " + str(V_I_comp_attr[2]))
print("Vector variable VR components: Minimum value = " + str(V_R_comp_attr[0]) + ", Maximum value = "
      + str(V_R_comp_attr[1]) + " , Step = " + str(V_R_comp_attr[2]) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# V_I_comp_attr = domain.get_numerical_components_attributes(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_I_comp_attr = domain.get_numerical_components_attributes("J")
# - The variable is not defined as VECTOR type.
# V_I_comp_attr = domain.get_numerical_components_attributes("C")
# - The components are not defined as NUMERICAL type.
# V_I_comp_attr = domain.get_numerical_components_attributes("VC")

# ==================================================================================================================== #
# =================== 17. Getting the attributes of the CATEGORICAL components of a VECTOR variable ================== #
# ==================================================================================================================== #

V_C_comp_attr = domain.get_categorical_components_attributes("VC")
print("Vector variable VC components: Available categories = " + str(V_C_comp_attr) + "\n")

# **** Argument type errors (static):
# - The variable must be str.
# V_C_comp_attr = domain.get_categorical_components_attributes(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_C_comp_attr = domain.get_categorical_components_attributes("J")
# - The variable is not defined as VECTOR type.
# V_C_comp_attr = domain.get_categorical_components_attributes("C")
# - The components are not defined as CATEGORICAL type.
# V_C_comp_attr = domain.get_categorical_components_attributes("VI")

# ==================================================================================================================== #
# =================== 18. Getting the attributes of a NUMERICAL element of LAYER VECTOR variable ===================== #
# ==================================================================================================================== #

V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("VL", "el1")
V_L_e_2_attr = domain.get_layer_vector_numerical_element_attributes("VL", "el2")
print("Vector Layer Variable VL, element el1: Minimum value = " + str(V_L_e_1_attr[0]) + ", Maximum value = "
      + str(V_L_e_1_attr[1]) + " , Step = " + str(V_L_e_1_attr[2]))
print("Vector Layer Variable VL, element el2: Minimum value = " + str(V_L_e_2_attr[0]) + ", Maximum value = "
      + str(V_L_e_2_attr[1]) + " , Step = " + str(V_L_e_2_attr[2]) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes(1, "el1")
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("VL", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("J", "el1")
# - The variable is not defined as VECTOR type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("I", "el1")
# - The components are not defined as LAYER type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("VI", "el1")
# - The element is not defined.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("VL", "el4")
# - The element is not defined as NUMERICAL type.
# V_L_e_1_attr = domain.get_layer_vector_numerical_element_attributes("VL", "el3")

# ==================================================================================================================== #
# ================== 19. Getting the attributes of a CATEGORICAL element of a LAYER VECTOR variable ================== #
# ==================================================================================================================== #

V_L_e_3_attr = domain.get_layer_vector_categorical_attributes("VL", "el3")
print("Variable L, element EC: Available categories = " + str(V_L_e_3_attr) + "\n")

# **** Argument type errors (static):
# - The variable and the element must be str.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes(1, "el3")
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("VL", 1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("J", "el3")
# - The variable is not defined as VECTOR type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("I", "el3")
# - The components are not defined as LAYER type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("VI", "el3")
# - The element is not defined.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("VL", "el4")
# - The element is not defined as CATEGORICAL type.
# V_L_e_1_attr = domain.get_layer_vector_categorical_attributes("VL", "el1")
