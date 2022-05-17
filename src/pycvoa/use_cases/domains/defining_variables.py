from pycvoa.problem.domain import Domain

domain = Domain()

# ==================================================================================================================== #
# ===================================== 1. Defining BASIC variables: INTEGER ========================================= #
# ==================================================================================================================== #

# The BASIC types Domain-Solution framework are three: INTEGER, REAL and CATEGORICAL
# To define any variable, the user must provide a unique variable name.
# Depending on the variable type, additional elements must be provided to define a variable.

# A INTEGER variable represents an integer number that is located in an interval.
# To define an INTEGER variable, four parameters must be provided to the "define_integer" function:
#       - A variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define a INTEGER variable "I", in the interval [0, 100] and step 50 (that is, in a random selection, the available
# values will be {0, 50, 100}):
domain.define_integer(1, 0, 100, 20)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_integer("I", 0, 100)
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_integer(1, 0, 100, 20)
# domain.define_integer("I", "I", 100, 20)
# domain.define_integer("I", 0, 1.2, 20)
# domain.define_integer("I", 0, 100, 5.2)
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_integer("I", 100, 0, 3)
# domain.define_integer("I", 100, 100, 3)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_integer("I", 0, 100, 55)
# 3. Definition errors:
# 3.1. The variable is already used.
# domain.define_integer("I", 0, 100, 50)

# ==================================================================================================================== #
# ===================================== 2. Defining BASIC variables: REAL == ========================================= #
# ==================================================================================================================== #

# A REAL variable represents a real number that is located in an interval.
# To define a REAL variable, four parameters must be provided to the "define_real" function:
#       - A variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a REAL variable "R", in the interval [0.0, 1.0] and step 0.1 (that is, in a random selection, the available
# values will be {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}):
domain.define_real("R", 0.0, 1.0, 0.1)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_real("R", 0.0, 1.0)
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be float.
# domain.define_real(1, 0.0, 1.0, 0.1)
# domain.define_real("R", "R", 1.0, 0.1)
# domain.define_real("R", 0.0, 1, 0.1)
# domain.define_real("R", 0.0, 1.0, 1)
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_real("R", 1.0, 0.0, 0.1)
# domain.define_real("R", 1.0, 1.0, 0.1)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_real("R", 0.0, 1.0, 0.7)
# 3. Definition errors:
# 3.1. The variable is already used.
# domain.define_real("R", 0.0, 1.0, 0.1)

# ==================================================================================================================== #
# ===================================== 3. Defining BASIC variables: CATEGORICAL====================================== #
# ==================================================================================================================== #

# A CATEGORICAL variable represents a closed set of values of the same type, i.e., categories.
# To define a CATEGORICAL variable, two parameters must be provided to the "define_real" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
domain.define_categorical("C_A", ["C1", "C2", "C3", "C4"])
domain.define_categorical("C_B", [1, 2, 3, 4])
domain.define_categorical("C_C", [0.1, 0.2, 0.3, 0.4])
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The categories must be a list.
# domain.define_categorical(1, ["C1", "C2", "C3", "C4"])
# domain.define_categorical("C_D", 1)
# 1.2. The categories of the list must be the same type
# domain.define_categorical("C_D", [1, "C2", "C3", "C4"])
# 2. Argument value errors:
# 2.1. The categories list must be at least two elements.
# domain.define_categorical("C_D", ["C1"])
# 2.2. The categories list can not contain repeated values.
# domain.define_categorical("C_D", ["C1", "C2", "C4", "C4"])
# 3. Definition errors:
# 3.1. The variable element is already used.
# domain.define_categorical("C_A", ["C1", "C2", "C3", "C4"])

# ==================================================================================================================== #
# ======================================== 4. Defining LAYER variables =============================================== #
# ==================================================================================================================== #

# A LAYER is a special type of variable. It represents a set of closed related set of variables that are called elements
# defined as BASIC.
# The LAYER type is specially useful to optimize neural network hyper-parameters where each layer has its
# own set of variables.

# To define a LAYER variable, just a variable name must be provided to the "define_layer" function:
domain.define_layer("L")

# **** Possible errors
# 1. If the variable name is already used, raise a definition error
# domain.define_layer("L")

# Next, the element of the layer "L" must be also defined.

# ==================================================================================================================== #
# ============================= 5. Defining INTEGER elements of a LAYER variable ===================================== #
# ==================================================================================================================== #

# To define an INTEGER element of a layer, five parameters must be provided to the "define_integer_element" function:
#       - The layer variable name.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define an INTEGER element "E_I" for the "L" variable, in the interval [0, 100] and step 20:
domain.define_integer_element("L", "E_I", 0, 100, 20)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_integer_element("L", "E_I", 0, 100)
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_integer_element(1, "E_I", 0, 100, 20)
# domain.define_integer_element("L", 1, 0, 100, 20)
# domain.define_integer_element("L", "E_I", 0.1, 100, 20)
# domain.define_integer_element("L", "E_I", 0, 1.2, 20)
# domain.define_integer_element("L", "E_I", 0, 100, "20")
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_integer_element("L", "L_I", 100, 0, 5)
# domain.define_integer_element("L", "L_I", 100, 100, 5)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_integer_element("L", "L_I", 0, 100, 55)
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_integer_element("J", "L_I", 0, 100, 20)
# 3.2. The variable is not defined as LAYER.
# domain.define_integer_element("I", "L_I", 0, 100, 20)
# 3.3. The variable element is already used.
# domain.define_integer_element("L", "E_I", 0, 100, 20)


# ==================================================================================================================== #
# ============================= 6. Defining REAL elements of a LAYER variable ======================================== #
# ==================================================================================================================== #

# To define an REAL element of a layer, five parameters must be provided to the "define_real_element" function:
#       - The layer variable name.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a REAL element "E_R" for the "L" variable, in the interval [1.5, 3.0] and step 0.01:
domain.define_real_element("L", "E_R", 1.5, 3.0, 0.01)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_real_element("L", "E_R", 1.5, 3.0)
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be float.
# domain.define_real_element(1, "E_R", 1.5, 3.0, 0.01)
# domain.define_real_element("L", 1, 1.5, 3.0, 0.01)
# domain.define_real_element("L", "E_I_", 1, 3.0, 0.01)
# domain.define_real_element("L", "E_I_", 1.5, 3, 0.01)
# domain.define_real_element("L", "E_I_", 1.5, 3.0, "E")
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_real_element("L", "E_I_", 3.0, 1.5, 0.01)
# domain.define_real_element("L", "E_I_", 3.0, 3.0, 0.01)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_real_element("L", "E_I_", 1.5, 3.0, 1.7)
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_real_element("J", "E_R", 1.5, 3.0, 0.01)
# 3.2. The variable is not defined as LAYER.
# domain.define_real_element("I", "E_R", 1.5, 3.0, 0.01)
# 3.3. The variable element is already used.
# domain.define_real_element("L", "E_R", 1.5, 3.0, 0.01)


# ==================================================================================================================== #
# ============================ 7. Defining CATEGORICAL elements of a LAYER variable ================================== #
# ==================================================================================================================== #

# To define a CATEGORICAL element "E_C" for the "L" variable,, two parameters must be provided to the
# "define_categorical_element" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
domain.define_categorical_element("L", "E_C", ["Lb1", "Lb2", "Lb3"])
print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The categories must be a list.
# domain.define_categorical_element(1, "E_C_", ["C1", "C2", "C3", "C4"])
# domain.define_categorical_element("L", 1, ["C1", "C2", "C3", "C4"])
# domain.define_categorical_element("L", "E_C_", 1)
# 1.2. The categories of the list must be the same type.
# domain.define_categorical_element("L", "E_C", ["Lb1", "Lb2", 1])
# 2. Argument value errors:
# 2.1. The categories list must be at least two elements.
# domain.define_categorical_element("L", "E_C_", ["Lb1"])
# 2.2. The categories list can not contain repeated values.
# domain.define_categorical_element("L", "E_C_", ["Lb1", "Lb2", "Lb1"])
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_categorical_element("J", "E_C", ["Lb1", "Lb2", "Lb3"])
# 3.2. The variable is not defined as LAYER.
# domain.define_categorical_element("I", "E_C", ["Lb1", "Lb2", "Lb3"])
# 3.3. The variable element is already used.
# domain.define_categorical_element("L", "E_C", ["Lb1", "Lb2", "Lb3"])

# ==================================================================================================================== #
# ======================================= 8. Defining VECTOR variables =============================================== #
# ==================================================================================================================== #

# A VECTOR is a special type of variable. It represents a collection of indexed values with the same type
# (INTEGER, REAL, CATEGORICAL or LAYER); each value of a vector is called component.

# To define a VECTOR variable, four parameters must be provided to the "define_vector" function:
#       - A variable name.
#       - The minimum size of the vector.
#       - The maximum size of the vector.
#       - [Optional] The step: a number to divide the vector, in order to get random components. If it is not
#        provided, will be set to a default value ((maximum size - minimum size) / 2)

# To define a VECTOR variable "V_I", whose size is in the interval [2, 8], with step size 2:
domain.define_vector("V", 2, 8, 1)
print(str(domain))
# If the step size is not provided, it is set to the default value ((maximum size - minimum size) / 2)
# domain.define_vector("V_I", 2, 8)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_vector(1, 2, 8, 1)
# domain.define_vector("V", 2.1, 8, 1)
# domain.define_vector("V", 2, 8.1, 1)
# domain.define_vector("V", 2, 8, "W")
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_vector("V", 8, 2, 2)
# domain.define_vector("V", 8, 8, 2)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_vector("V", 2, 8, 5)
# 3. Definition errors:
# 3.1. The variable element is already used.
# domain.define_vector("V", 2, 8, 2)

# ==================================================================================================================== #
# ============================== 9. Defining VECTOR components as BASIC: INTEGER ===================================== #
# ==================================================================================================================== #
# After defining the vector variable, the component type must be defined as INTEGER, REAL, CATEGORICAL or LAYER.
# To illustrate the INTEGER definition of a VECTOR variable, first, define a VECTOR variable "V_I", whose size is in
# the interval [2, 8] and step 1:
domain.define_vector("V_I", 2, 8, 1)
print(str(domain))

# To set the components of the VECTOR variable "V_I" to INTEGER, four parameters must be provided to the
# "define_components_integer" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define the components of the vector "V_I" as INTEGER, in the interval [1, 10] and step 2:
domain.define_components_as_integer("V_I", 1, 10, 2)
print(str(domain))
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_components_as_integer("V_I", 1, 10)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_components_as_integer(1, 1, 10, 2)
# domain.define_components_as_integer("V_I", 1.2, 10, 2)
# domain.define_components_as_integer("V_I", 1, 10.2, 2)
# domain.define_components_as_integer("V_I", 1, 10, "2")
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_components_as_integer("V_I", 10, 1, 1)
# domain.define_components_as_integer("V_I", 10, 10, 1)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_components_as_integer("V_I", 1, 10, 8)
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_components_as_integer("J", 1, 10, 1)
# 3.2. The variable is not defined as VECTOR.
# domain.define_components_as_integer("I", 1, 10, 1)
# 3.3. The components are already defined.
# domain.define_components_as_integer("V_I", 1, 10, 1)

# ==================================================================================================================== #
# ============================== 10. Defining VECTOR components as BASIC: REAL ======================================= #
# ==================================================================================================================== #

# To illustrate the REAL definition of a VECTOR variable, first, define a VECTOR variable "V_R", whose size is in
# the interval [1, 10] and step 1:
domain.define_vector("V_R", 1, 10, 1)

# To set the components of the VECTOR variable "V_R" to REAL, four parameters must be provided to the
# "define_components_real" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define the components of the vector "V_R" as REAL, in the interval [0.0, 0.1] and step 0.0001:
domain.define_components_as_real("V_R", 0.0, 0.1, 0.0001)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_components_as_real("V_R", 0.0, 0.1)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_components_as_integer(1, 1, 10, 2)
# domain.define_components_as_integer("V_I", 1.2, 10, 2)
# domain.define_components_as_integer("V_I", 1, 10.2, 2)
# domain.define_components_as_integer("V_I", 1, 10, "2")
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain_A.define_components_integer("V_R", 0.1, 0.0, 1)
# domain_A.define_components_integer("V_R", 0.1, 0.1, 1)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain_A.define_components_integer("V_R", 0.0, 0.1, 1)
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_components_as_real("J", 0.0, 0.1, 0.0001)
# 3.2. The variable is not defined as VECTOR
# domain.define_components_as_real("I", 0.0, 0.1, 0.0001)
# 3.3. The components are already defined.
# domain.define_components_as_real("V_R", 0.0, 0.1, 0.0001)

# ==================================================================================================================== #
# ============================== 11. Defining VECTOR components as BASIC: CATEGORICAL ================================ #
# ==================================================================================================================== #

# To illustrate the CATEGORICAL definition of a VECTOR variable, first, define a VECTOR variable "V_C", whose size is in
# the interval [10, 20] and step 1:
domain.define_vector("V_C", 10, 20, 1)

# To set the components of the VECTOR variable "V_C" to CATEGORICAL, two parameters must be provided to the
# "define_components_categorical" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
domain.define_components_as_categorical("V_C", ["V1", "V2", "V3"])
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The categories must be a list.
# domain.define_components_as_categorical(1, ["V1", "V2", "V3"])
# domain.define_components_as_categorical("C_D", 1)
# 1.2. The categories of the list must be the same type
# domain.define_components_as_categorical("V_C", ["V1", 1, "V3"])
# 2. Argument value errors:
# 2.1. The categories list must be at least two elements.
# domain.define_categorical("V_C", ["V1"])
# 2.2. The categories list can not contain repeated values.
# domain.define_categorical("V_C", ["V1", "V2", "V2"])
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_components_as_categorical("J", ["V1", "V2", "V3"])
# 3.2. The variable is not defined as VECTOR
# domain.define_components_as_categorical("L", ["V1", "V2", "V3"])
# 3.3. The components are already defined.
# domain.define_components_as_categorical("V_C", ["V1", "V2", "V3"])

# ==================================================================================================================== #
# ============================== 12. Defining VECTOR components as LAYER ============================================= #
# ==================================================================================================================== #

# To illustrate the LAYER definition of a VECTOR variable, first, define a VECTOR variable "V_L", whose size is in
# the interval [10, 20] and step 1:
domain.define_vector("V_L", 10, 20, 1)

# Next, define its components type as LAYER with the "define_components_layer" method:
domain.define_components_as_layer("V_L")
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str.
# domain.define_components_as_layer(1)
# 3. Definition errors:
# 3.1. The variable is not defined.
# domain.define_components_as_layer("J")
# 3.2. The variable is not defined as VECTOR
# domain.define_components_as_layer("L")
# 3.3. The components are already defined.
# domain.define_components_as_layer("V_L")

# ==================================================================================================================== #
# ========================= 13. Defining elements of LAYER VECTOR components: INTEGER ================================ #
# ==================================================================================================================== #

# To define an INTEGER element of the LAYER components, five parameters must be provided to the
# "define_vector_integer_element" function:
#       - The VECTOR variable name whose components are defined as LAYER.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define an INTEGER element "el-1" for the "V_L" VECTOR variable, in the interval [10, 20] and step 1:
domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 1)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_layer_vector_integer_element(1, "el-1", 10, 20, 1)
# domain.define_layer_vector_integer_element("V_L", 1, 10, 20, 1)
# domain.define_layer_vector_integer_element("V_L", "el-1", "w", 20, 1)
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20.2, 1)
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 1.2)
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_layer_vector_integer_element("V_L", "el-1", 20, 10, 1)
# domain.define_layer_vector_integer_element("V_L", "el-1", 20, 20, 1)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 8)
# 3. Definition errors:
# 3.1. The vector variable is not defined.
# domain.define_layer_vector_integer_element("J", "el-1", 10, 20, 1)
# 3.2. The variable is not defined as VECTOR.
# domain.define_layer_vector_integer_element("I", "el-1", 10, 20, 1)
# 3.3. The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_integer_element("V_I", "el-1", 10, 20, 1)
# 3.3. The variable element is already used.
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 1)


# ==================================================================================================================== #
# =========================== 14. Defining elements of LAYER VECTOR components: REAL ================================= #
# ==================================================================================================================== #

# To define a REAL element of the LAYER components, five parameters must be provided to the
# "define_vector_integer_element" function:
#       - The VECTOR variable name whose components are defined as LAYER.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define a REAL element "el-2" for the "V_L" VECTOR variable, in the interval [0.1, 0.5] and step 0.1:
domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5, 0.1)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_layer_vector_real_element(1, "el-2", 0.1, 0.5, 0.1)
# domain.define_layer_vector_real_element("V_L", 1, 0.1, 0.5, 0.1)
# domain.define_layer_vector_real_element("V_L", "el-2", 1, 0.5, 0.1)
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, "e", 0.1)
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5, 1)
# 2. Argument value errors:
# 2.1. The minimum value is greater or equal than the maximum one.
# domain.define_layer_vector_real_element("V_L", "el-2", 0.5, 0.1, 0.1)
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.1, 0.1)
# 2.2. The step value is greater than (maximum value - minimum value) / 2.
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5, 2.0)
# 3. Definition errors:
# 3.1. The vector variable is not defined.
# domain.define_layer_vector_real_element("J", "el-2", 0.1, 0.5, 0.1)
# 3.2. The variable is not defined as VECTOR.
# domain.define_layer_vector_real_element("I", "el-2", 0.1, 0.5, 0.1)
# 3.3. The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_real_element("V_I", "el-2", 0.1, 0.5, 0.1)
# 3.3. The variable element is already used.
# domain.define_layer_vector_real_element("V_L", "el-2", 0.1, 0.5, 0.1)


# ==================================================================================================================== #
# ======================= 15. Defining elements of LAYER VECTOR components: CATEGORICAL ============================== #
# ==================================================================================================================== #

# To define a CATEGORICAL element of the LAYER components, two parameters must be provided to the
# "define_vector_categorical_element" function:
#       - A element name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
domain.define_layer_vector_categorical_element("V_L", "el-3", [1, 2, 3])
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name a and the element name must be str. The categories must be a list.
# domain.define_layer_vector_categorical_element(1, "el-3", [1, 2, 3])
# domain.define_layer_vector_categorical_element("V_L", 2, [1, 2, 3])
# domain.define_layer_vector_categorical_element("V_L", "el-3", 1)
# 1.2. The categories of the list must be the same type.
# domain.define_layer_vector_categorical_element("V_L", "el-3", [1, 2, 3.3])
# 2. Argument value errors:
# 2.1. The categories list must be at least two elements.
# domain.define_layer_vector_categorical_element("V_L", "el-3", [1])
# 2.2. The categories list can not contain repeated values.
# domain.define_layer_vector_categorical_element("V_L", "el-3", [1, 1, 1])
# 3. Definition errors:
# 3.1. The vector variable is not defined.
# domain.define_layer_vector_categorical_element("J", "el-3", [1, 2, 3])
# 3.2. The variable is not defined as VECTOR.
# domain.define_layer_vector_categorical_element("I", "el-3", [1, 2, 3])
# 3.3. The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_categorical_element("V_I", "el-3", [1, 2, 3])
# 3.3. The variable element is already used.
# domain.define_layer_vector_categorical_element("V_L", "el-3", [1, 2, 3])

print(str(domain))
