# ======================================== 0. Importing artifacts ======================================================

# The class Domain is in the pycvoa.problem.domain module:
from pycvoa.problem.domain import Domain

# ======================================== 1. Variable types ==========================================================

# The Domain-Solution framework provides four variable type definitions: INTEGER, REAL, CATEGORICAL, LAYER and VECTOR.
# The INTEGER, REAL and CATEGORICAL types are BASIC types that represent a single value.
# The LAYER variable is composed by a set of several variables (called elements) of BASIC type.
# The VECTOR variable is a collection of indexed values with the same type (INTEGER, REAL, CATEGORICAL or LAYER); each
# value of a vector is called component.
# These four types have a literal representation in pycvoa, and can be imported the pycvoa.problem using the
# following instruction (the BASIC type, that contains the  INTEGER, REAL, CATEGORICAL types, is also available):
# from pycvoa.problem import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, BASIC

# ======================================== 2. Building a new domain ===================================================

# To build a new domain, the default an unique constructor of the Domain class must be used
domain = Domain()

# ======================================== 3. Defining BASIC variables ================================================

# The BASIC types Domain-Solution framework are three: INTEGER, REAL and CATEGORICAL
# To define any variable, the user must provide a unique variable name.
# Depending on the variable type, additional elements must be provided to define a variable.

#                              %%%%%%%%%% 3.1 Defining INTEGER variables %%%%%%%%%%

# A INTEGER variable represents an integer number that is located in an interval.
# To define an INTEGER variable, four parameters must be provided to the "define_integer" function:
#       - A variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a INTEGER variable "I", in the interval [0, 100] and step 50 (that is, in a random selection, the available
# values will be {0, 50, 100}):
domain.define_integer("I", 0, 100, 50)
# print(str(domain))

# ************ Possible errors
# 1. Argument type errors:
# - The variable name must be str;  the minimum, maximum and step values must be int.
# domain.define_integer(1, 0, 100, 50)
# domain.define_integer("I", "I", 100, 50)
# domain.define_integer("I", 0, 1.2, 50)
# domain.define_integer("I", 0, 100, 5.2)
# 2. Argument value errors:
# - If the minimum value is greater or equal than the maximum one, raise a definition error
# domain.define_integer("I", 100, 0, 3)
# domain.define_integer("I", 100, 100, 3)
# - If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain.define_integer("I",0,100,55)
# 3. Definition errors:
# - If the variable name is already used, raise a definition error
# domain.define_integer("I", 0, 100, 50)

#                               %%%%%%%%%% 3.2 Defining REAL variables %%%%%%%%%%

# A REAL variable represents a real number that is located in an interval.
# To define a REAL variable, four parameters must be provided to the "define_real" function:
#       - A variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a REAL variable "R", in the interval [0.0, 1.0] and step 0.1 (that is, in a random selection, the available
# values will be {0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0}):
# domain.define_real("R", 0.0, 1.0, 0.1)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_real("R",1.0,0.0,3)
# domain_A.define_real("R",1.0,1.0,3)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_real("R",0.0,1.0,0.7)
# 3. If the variable name is already used, raise a definition error
# domain_A.define_real("R", 0.0, 1.0, 0.1)

#                           %%%%%%%%%% 3.3. Defining CATEGORICAL variables %%%%%%%%%%

# A CATEGORICAL variable represents a closed set of values of the same type, i.e., categories.
# To define a CATEGORICAL variable, two parameters must be provided to the "define_real" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
# domain.define_categorical("C_A", ["C1", "C2", "C3", "C4"])
# domain.define_categorical("C_B", [1, 2, 3, 4])
# domain.define_categorical("C_C", [0.1, 0.2, 0.3, 0.4])
# print(str(domain_A))

# **** Possible errors
# 1. If the variable name is already used, raise a definition error
# domain_A.define_categorical("C_A", ["C1", "C2", "C3", "C4"])

# ======================================== 4. Defining LAYER variables ================================================

# A LAYER is a special type of variable. It represents a set of closed related set of variables that are called elements
# with BASIC types. These type is specially useful to optimize neural network hyper-parameters where each layer has its
# own set of variables.

# To define a LAYER variable, only a parameter must be provided to the "define_layer" function:
#       - A variable name.
# domain.define_layer("L")

# **** Possible errors
# 1. If the variable name is already used, raise a definition error
# domain_A.define_layer("L")

# Next, the element of the layer "L" must be also defined.

#                               %%%%%%%%%% 4.1. Defining INTEGER elements %%%%%%%%%%

# To define an INTEGER element of a layer, five parameters must be provided to the "define_integer_element" function:
#       - The layer variable name.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define an INTEGER element "E_I" for the "L" variable, in the interval [0, 100] and step 20:
# domain.define_integer_element("L", "E_I", 0, 100, 20)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_integer_element("L","L_I",100,0,5)
# domain_A.define_integer_element("L","L_I",100,100,5)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_integer_element("L","L_I",0,100,55)
# 3. If the element name is already used, raise a definition error
# domain_A.define_integer_element("L", "E_I", 0, 100, 20)

#                               %%%%%%%%%% 4.2. Defining REAL elements %%%%%%%%%%

# To define an REAL element of a layer, five parameters must be provided to the "define_real_element" function:
#       - The layer variable name.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a REAL element "E_R" for the "L" variable, in the interval [1.5, 3.0] and step 0.01:
# domain.define_real_element("L", "E_R", 1.5, 3.0, 0.01)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_real_element("L","L_R",3.0,1.5,0.01)
# domain_A.define_real_element("L","L_R",3.0,3.0,0.01)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_real_element("L","L_R", 1.5, 3.0, 1.7)
# 3. If the element name is already used, raise a definition error
# domain_A.define_real_element("L", "E_R", 1.5, 3.0, 0.01)

#                               %%%%%%%%%% 4.3. Defining CATEGORICAL elements %%%%%%%%%%

# To define a CATEGORICAL element "E_C" for the "L" variable,, two parameters must be provided to the
# "define_categorical_element" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
# domain.define_categorical_element("L", "E_C", ["Lb1", "Lb2", "Lb3"])
# print(str(domain_A))

# **** Possible errors
# 1. If the element name is already used, raise a definition error
# domain_A.define_categorical_element("L","L_C", ["Lb1", "Lb2", "Lb3"])

# ======================================== 5. Defining VECTOR variables ================================================

# A VECTOR is a special type of variable. It represents a collection of indexed values with the same type
# (INTEGER, REAL, CATEGORICAL or LAYER); each value of a vector is called component.

# To define a VECTOR variable, four parameters must be provided to the "define_vector" function:
#       - A variable name.
#       - The minimum size of the vector.
#       - The maximum size of the vector.
#       - The step: a number to divide the interval size.

# To define a VECTOR variable "V_I", whose size is in the interval [2, 8] and step 2:
# domain.define_vector("V_I", 2, 8, 2)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum size is greater or equal than the maximum one, raise a definition error
# domain_A.define_vector("V_I", 8, 2, 2)
# domain_A.define_vector("V_I", 8, 8, 2)
# 2. If the step size is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_vector("V_I", 2, 8, 5)
# 3. If the variable name is already used, raise a definition error
# domain_A.define_vector("V_I", 2, 8, 2)

# After the definition of the vector, the type of the components must be set.

#                            %%%%%%%%%% 5.1. Defining the VECTOR components as INTEGER %%%%%%%%%%

# To set the components of the VECTOR variable "V_I" to INTEGER, four parameters must be provided to the
# "define_components_integer" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define the components of the vector "V_I" as INTEGER, in the interval [1, 10] and step 1:
# domain.define_components_as_integer("V_I", 1, 10, 1)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_components_integer("V_I", 10, 1, 1)
# domain_A.define_components_integer("V_I", 10, 10, 1)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_components_integer("V_I", 1, 10, 8)
# 3. If the components of the vector variable have already been defined, raise a definition error
# domain_A.define_components_integer("V_I", 1, 10, 1)

#                            %%%%%%%%%% 5.2. Defining the VECTOR components as REAL %%%%%%%%%%

# To illustrate the REAL definition of a VECTOR variable, first, define a VECTOR variable "V_R", whose size is in
# the interval [1, 10] and step 1:
# domain.define_vector("V_R", 1, 10, 1)

# To set the components of the VECTOR variable "V_R" to REAL, four parameters must be provided to the
# "define_components_real" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define the components of the vector "V_R" as REAL, in the interval [0.0, 0.1] and step 0.0001:
# domain.define_components_as_real("V_R", 0.0, 0.1, 0.0001)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_components_integer("V_R", 0.1, 0.0, 1)
# domain_A.define_components_integer("V_R", 0.1, 0.1, 1)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_components_integer("V_R", 0.0, 0.1, 1)
# 3. If the components of the vector variable have already been defined, raise a definition error
# domain_A.define_components_real("V_R", 0.0, 0.1, 0.0001)

#                          %%%%%%%%%% 5.3. Defining the VECTOR components as CATEGORICAL %%%%%%%%%%

# To illustrate the CATEGORICAL definition of a VECTOR variable, first, define a VECTOR variable "V_C", whose size is in
# the interval [10, 20] and step 1:
# domain.define_vector("V_C", 10, 20, 1)

# To set the components of the VECTOR variable "V_C" to CATEGORICAL, two parameters must be provided to the
# "define_components_categorical" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
# domain.define_components_as_categorical("V_C", ["V1", "V2", "V3"])
# print(str(domain_A))

# **** Possible errors
# 1. If the components of the vector variable have already been defined, raise a definition error
# domain_A.define_components_categorical("V_C",["V1","V2","V3"])


#                          %%%%%%%%%% 5.4. Defining the VECTOR components as LAYER %%%%%%%%%%

# To illustrate the LAYER definition of a VECTOR variable, first, define a VECTOR variable "V_L", whose size is in
# the interval [10, 20] and step 1:
# domain.define_vector("V_L", 10, 20, 1)

# Next, define its components type as LAYER with the "define_components_layer" method:
# domain.define_components_as_layer("V_L")

# **** Possible errors
# 1. If the components of the vector variable have already been defined, raise a definition error
# domain_A.define_components_layer("V_L")

# Finally, define the elements of the LAYER components.

# To define an INTEGER element of the LAYER components, five parameters must be provided to the
# "define_vector_integer_element" function:
#       - The VECTOR variable name whose components are defined as LAYER.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define an INTEGER element "el-1" for the "V_L" VECTOR variable, in the interval [10, 20] and step 1:
# domain.define_layer_vector_integer_element("V_L", "el-1", 10, 20, 1)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_vector_integer_element("V_L","el-1",20,10,1)
# domain_A.define_vector_integer_element("V_L","el-1",20,20,1)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_vector_integer_element("V_L","el-1",10,20,8)
# 3. If the element name is already used, raise a definition error
# domain_A.define_vector_integer_element("V_L","el-1",10,20,1)

# To define a REAL element of the LAYER components, five parameters must be provided to the
# "define_vector_integer_element" function:
#       - The VECTOR variable name whose components are defined as LAYER.
#       - The new element name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - The step: a number to divide the interval, in order to generate random values

# To define a REAL element "el-2" for the "V_L" VECTOR variable, in the interval [0.1, 0.5] and step 0.1:
# domain.define_vector_real_element("V_L", "el-2", 0.1, 0.5, 0.1)
# print(str(domain_A))

# **** Possible errors
# 1. If the minimum value is greater or equal than the maximum one, raise a definition error
# domain_A.define_vector_real_element("V_L","el-2",0.5,0.1,0.1)
# domain_A.define_vector_real_element("V_L","el-2",0.1,0.1,0.1)
# 2. If the step value is greater than (maximum value - minimum value) / 2, raise a definition error
# domain_A.define_vector_real_element("V_L","el-2",0.1,0.5,2.0)
# 3. If the element name is already used, raise a definition error
# domain_A.define_vector_real_element("V_L","el-2",0.1,0.5,0.1)

# To define a CATEGORICAL element of the LAYER components, two parameters must be provided to the
# "define_vector_categorical_element" function:
#       - A element name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.
# domain.define_vector_categorical_element("V_L", "el-3", [1, 2, 3])
# print(str(domain_A))

# **** Possible errors
# 1. If the element name is already used, raise a definition error
# domain_A.define_vector_categorical_element("V_L","el-3",[1,2,3])

# ======================================== 6. Is a variable/element/component defined ? ================================

# Is a variable defined in the domain ?
# is_V_I = domain.is_defined_variable("V_L")
# is_V_5 = domain.is_defined_variable("V_5")
# print("Is the V_L variable defined in the domain_A ? " + str(is_V_I))
# print("Is the V_5 variable defined in the domain_A ? " + str(is_V_5))

# Is an element of a LAYER variable defined in the domain ?
# is_L_E_I = domain.is_defined_element("L", "E_I")
# is_L_E_J = domain.is_defined_element("L", "E_J")
# print("Is the E_I element defined in the L LAYER variable in the domain_A ? " + str(is_L_E_I))
# print("Is the E_J element defined in the L LAYER variable in the domain_A ? " + str(is_L_E_J))

# **** Possible errors
# 1. The LAYER variable is not defined
# is_Y_E_I = domain_A.is_defined_element("Y","E_I")
# 2. The LAYER variable is not a LAYER variable
# is_I_E_I = domain_A.is_defined_element("I","E_I")

# Is the components of a VECTOR variable already defined in the domain ?
# is_V_I = domain.is_defined_components("V_I")
# domain.define_vector("V_I_", 1, 4, 1)
# is_V_I_ = domain.is_defined_components("V_I_")
# print("Is the components of the V_I vector variable already defined ? " + str(is_V_I))
# print("Is the components of the V_I_ vector variable already defined ? " + str(is_V_I_))

# **** Possible errors
# 1. The VECTOR variable is not defined
# is_V_J = domain_A.is_defined_components("V_J")
# 2. The VECTOR variable is not a VECTOR variable
# is_R = domain_A.is_defined_components("R")

# =========================================== 7. Getting the variable types ============================================

# Get a variable type via get_variable_type
# L_type = domain.get_variable_type("L")
# print("The type of the L variable is " + L_type)

# **** Possible errors
# 1. The variable is not defined
# J_type = domain_A.get_variable_type("J")

# Get a element type of a LAYER variable via get_element_type
# E_C_L_type = domain.get_layer_element_type("L", "E_C")
# print("The type of the E_C element of the LAYER variable L is " + E_C_L_type)

# **** Possible errors
# 1. The LAYER variable is not defined
# E_C_Y_type = domain_A.get_element_type("Y","E_C")
# 2. The LAYER variable is not defined as a LAYER variable
# E_C_I_type = domain_A.get_element_type("I","E_C")
# 3. The element is not defined in the LAYER variable
# E_Y_I_type = domain_A.get_element_type("L","E_Y")

# Get the component type of a VECTOR variable via get_component_type
# V_I_type = domain.get_vector_components_type("V_I")
# print("The component type of the V_I VECTOR variable is " + V_I_type)

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_I_type = domain_A.get_component_type("Y")
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_I_type = domain_A.get_component_type("I")
# 3. The components of the VECTOR variable are not defined
# V_I_type = domain_A.get_component_type("V_I_")

# ============================ 8. Getting the variable definitions ====================================================

# The internal definition structure is accessible via "get_definitions" method:
# internal_structure = domain.get_definitions()
# print(str(internal_structure))

# A list of (key, value) pairs can be retained via "get_definition_list"
# It is useful to iterate over the elements of a definition in a for loop
# definition_list = domain.get_definition_list()
# for variable, definition in definition_list:
#     print("The variable " + variable + " has this definition: " + str(definition))

# A list of defined variables can be retained via "get_variable_list"
# variable_list = domain.get_variable_list()
# for variable in variable_list:
#     print("The variable " + variable + " is defined in the domain")

# To get the definition of a variable, use the "get_variable_definition" method
# I_definition = domain.get_variable_definition("I")
# print("I variable definition : " + str(I_definition))

# **** Possible errors
# 1. The variable is not defined
# J_definition = domain_A.get_variable_definition("J")

# ============================ 9. Getting the element definitions =====================================================

# To get a list of the defined elements in a LAYER variable, use the "get_element_list" method
# element_list = domain.get_element_list("L")
# for element in element_list:
#     print("The element " + element + " is defined in the L LAYER variable in the domain")

# **** Possible errors
# 1. The LAYER variable is not defined
# element_list = domain_A.get_element_list("Y")
# 2. The LAYER variable is not defined as a LAYER variable
# element_list = domain_A.get_element_list("C_A")

# To get the definition of an element of a LAYER variable, use the "get_element_list" method
# E_C_definition = domain.get_element_definition("L", "E_C")
# print("E_C element definition in the L LAYER variable: " + str(E_C_definition))

# **** Possible errors
# 1. The LAYER variable is not defined
# E_C_definition = domain_A.get_element_definition("Y","E_C")
# 2. The LAYER variable is not defined as a LAYER variable
# E_C_definition = domain_A.get_element_definition("C_A","E_C")
# 3. The element is not defined in the LAYER variable
# E_C_definition = domain_A.get_element_definition("L","E_C_")

# ============================ 10. Getting the component definitions ===================================================

# To get the component definition of a VECTOR variable, use the "get_component_definition" method
# V_I_component_definition = domain.get_vector_component_definition("V_I")
# print("Component definition of the V_I VECTOR variable: " + str(V_I_component_definition))

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_I_component_definition = domain_A.get_component_definition("Y")
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_I_component_definition = domain_A.get_component_definition("I")
# 3. The components of the VECTOR variable are not defined
# V_I_component_definition = domain_A.get_component_definition("V_I_")

# To get a list of the defined elements of the LAYER components of a VECTOR variable, use the
# "get_component_element_list" method
# V_L_element_list = domain.get_component_element_list("V_L")
# for element in V_L_element_list:
#     print("The element " + element + " is defined in the LAYER component of the V_L VECTOR variable in the domain")

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_L_element_list = domain_A.get_component_element_list("Y")
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_L_element_list = domain_A.get_component_element_list("I")
# 3. The components of the VECTOR variable are not defined
# V_L_element_list = domain_A.get_component_element_list("V_I_")
# 4. The components of the VECTOR variable are not defined as LAYER
# V_L_element_list = domain_A.get_component_element_list("V_I")

# To get an element definition of LAYER components of a VECTOR variable, use the "get_component_element_definition"
# method
# V_L_el_1 = domain.get_component_element_definition("V_L", "el-1")
# print("Element definition of the el-1 element of the V_I VECTOR variable: " + str(V_L_el_1))

# **** Possible errors
# 1. The VECTOR variable is not defined
# V_L_el_1 = domain_A.get_component_element_definition("Y","el-1")
# 2. The VECTOR variable is not defined as a VECTOR variable
# V_L_el_1 = domain_A.get_component_element_definition("I","el-1")
# 3. The components of the VECTOR variable are not defined
# V_L_el_1 = domain_A.get_component_element_definition("V_I_","el-1")
# 4. The components of the VECTOR variable are not defined as LAYER
# V_L_el_1 = domain_A.get_component_element_definition("V_I", "el-1")
# 5. The element is not defined in the LAYER components
# V_L_el_1 = domain_A.get_component_element_definition("V_L", "el-5")

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
