from pycvoa.problem.domain import Domain

domain = Domain()

# ==================================================================================================================== #
# ===================================== 1. Defining INTEGER variables ================================================ #
# ==================================================================================================================== #

# The BASIC types in the Domain-Solution framework are three: INTEGER, REAL and CATEGORICAL
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
domain.define_integer("I", 0, 100, 20)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)
# domain.define_integer("I", 0, 100)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_integer(1, 0, 100, 20)
# domain.define_integer("I", "I", 100, 20)
# domain.define_integer("I", 0, 1.2, 20)
# domain.define_integer("I", 0, 100, 5.2)
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_integer("I", 100, 0, 3)
# domain.define_integer("I", 100, 100, 3)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_integer("I", 0, 100, 55)
# **** Definition errors (raise DefinitionError):
# - The variable is already used.
# domain.define_integer("I", 0, 100, 50)

# ==================================================================================================================== #
# ===================================== 2. Defining REAL variables =================================================== #
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

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be float.
# domain.define_real(1, 0.0, 1.0, 0.1)
# domain.define_real("R", "R", 1.0, 0.1)
# domain.define_real("R", 0.0, "min", 0.1)
# domain.define_real("R", 0.0, 1.0, "max")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_real("R", 1.0, 0.0, 0.1)
# domain.define_real("R", 1.0, 1.0, 0.1)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_real("R", 0.0, 1.0, 0.7)
# **** Definition errors (raise DefinitionError):
# - The variable is already used.
# domain.define_real("R", 0.0, 1.0, 0.1)

# ==================================================================================================================== #
# ===================================== 3. Defining CATEGORICAL variables ============================================ #
# ==================================================================================================================== #

# A CATEGORICAL variable represents a closed set of values of the same type, i.e., categories.
# To define a CATEGORICAL variable, two parameters must be provided to the "define_categorical" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.

domain.define_categorical("CA", ["C1", "C2", "C3", "C4"])
domain.define_categorical("CB", [1, 2, 3, 4])
domain.define_categorical("CC", [0.1, 0.2, 0.3, 0.4])

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The categories must be a list.
# domain.define_categorical(1, ["C1", "C2", "C3", "C4"])
# domain.define_categorical("CD", 1)
# **** Argument type errors (raise TypeError):
# - The categories of the list must be the same type
# domain.define_categorical("CD", [1, "C2", "C3", "C4"])
# **** Argument value errors (raise ValueError):
# - The categories list must be at least two elements.
# domain.define_categorical("CD", ["C1"])
# - The categories list can not contain repeated values.
# domain.define_categorical("CD", ["C1", "C2", "C4", "C4"])
# **** Definition errors (raise DefinitionError):
# - The variable is already used.
# domain.define_categorical("CA", ["C1", "C2", "C3", "C4"])

# ==================================================================================================================== #
# ======================================== 4. Defining LAYER variables =============================================== #
# ==================================================================================================================== #

# A LAYER is a special type of variable. It represents a set of closed related set of variables that are called elements
# defined as BASICS (INTEGER, REAL or CATEGORICAL).
# The LAYER type is specially useful to optimize neural network hyperparameters where each layer has its
# own set of variables.

# To define a LAYER variable, just a variable name must be provided to the "define_layer" function:
domain.define_layer("L")

# **** Argument type errors (static):
# - The variable name a and the element name must be str.
# domain.define_layer(1)
# **** Definition errors (raise DefinitionError):
# - The variable is already used.
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

domain.define_integer_element("L", "EI", 0, 100, 20)

# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

# domain.define_integer_element("L", "EI", 0, 100)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_integer_element(1, "EI", 0, 100, 20)
# domain.define_integer_element("L", 1, 0, 100, 20)
# domain.define_integer_element("L", "EI", 0.1, 100, 20)
# domain.define_integer_element("L", "EI", 0, 1.2, 20)
# domain.define_integer_element("L", "EI", 0, 100, "20")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_integer_element("L", "LI", 100, 0, 5)
# domain.define_integer_element("L", "LI", 100, 100, 5)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_integer_element("L", "LI", 0, 100, 55)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_integer_element("J", "LI", 0, 100, 20)
# - The variable is not defined as LAYER.
# domain.define_integer_element("I", "LI", 0, 100, 20)
# - The variable element is already used.
# domain.define_integer_element("L", "EI", 0, 100, 20)


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
# domain.define_real_element("L", "ER", 1.5, 3.0, 0.01)
# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

domain.define_real_element("L", "ER", 1.5, 3.0)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be float.
# domain.define_real_element(1, "ER", 1.5, 3.0, 0.01)
# domain.define_real_element("L", 1, 1.5, 3.0, 0.01)
# domain.define_real_element("L", "ER", "1", 3.0, 0.01)
# domain.define_real_element("L", "ER", 1.5, "2", 0.01)
# domain.define_real_element("L", "ER", 1.5, 3.0, "3")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_real_element("L", "ER", 3.0, 1.5, 0.01)
# domain.define_real_element("L", "ER", 3.0, 3.0, 0.01)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_real_element("L", "ER", 1.5, 3.0, 1.7)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_real_element("J", "ER", 1.5, 3.0, 0.01)
# - The variable is not defined as LAYER.
# domain.define_real_element("I", "ER", 1.5, 3.0, 0.01)
# - The variable element is already used.
# domain.define_real_element("L", "ER", 1.5, 3.0, 0.01)


# ==================================================================================================================== #
# ============================ 7. Defining CATEGORICAL elements of a LAYER variable ================================== #
# ==================================================================================================================== #

# To define a CATEGORICAL element "EC" for the "L" variable, two parameters must be provided to the
# "define_categorical_element" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.

domain.define_categorical_element("L", "EC", ["Lb1", "Lb2", "Lb3"])

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The categories must be a list.
# domain.define_categorical_element(1, "EC", ["C1", "C2", "C3", "C4"])
# domain.define_categorical_element("L", 1, ["C1", "C2", "C3", "C4"])
# domain.define_categorical_element("L", "EC", 1)
# **** Argument type errors (raise TypeError):
# - The categories of the list must be the same type.
# domain.define_categorical_element("L", "EC", ["Lb1", "Lb2", 1])
# **** Argument value errors (raise ValueError):
# - The categories list must be at least two elements.
# domain.define_categorical_element("L", "EC", ["Lb1"])
# - The categories list can not contain repeated values.
# domain.define_categorical_element("L", "EC", ["Lb1", "Lb2", "Lb1"])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_categorical_element("J", "EC", ["Lb1", "Lb2", "Lb3"])
# - The variable is not defined as LAYER.
# domain.define_categorical_element("I", "EC", ["Lb1", "Lb2", "Lb3"])
# - The variable element is already used.
# domain.define_categorical_element("L", "EC", ["Lb1", "Lb2", "Lb3"])

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

# To define a VECTOR variable "V", whose size is in the interval [2, 8], with step size 2:

# domain.define_vector("V", 2, 8, 1)

# If the step size is not provided, it is set to the default value ((maximum size - minimum size) / 2)

domain.define_vector("V", 2, 8)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_vector(1, 2, 8, 1)
# domain.define_vector("V", 2.1, 8, 1)
# domain.define_vector("V", 2, 8.1, 1)
# domain.define_vector("V", 2, 8, "W")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_vector("V", 8, 2, 2)
# domain.define_vector("V", 8, 8, 2)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_vector("V", 2, 8, 5)
# **** Definition errors (raise DefinitionError):
# - The variable element is already used.
# domain.define_vector("V", 2, 8, 2)

# ==================================================================================================================== #
# ============================== 9. Defining VECTOR components as INTEGER ============================================ #
# ==================================================================================================================== #
# After defining the vector variable, the component type must be defined as INTEGER, REAL, CATEGORICAL or LAYER.
# To illustrate the INTEGER definition of a VECTOR variable, first, define a VECTOR variable "VI", whose size is in
# the interval [2, 8] and step 1:

domain.define_vector("VI", 2, 8, 1)

# To set the components of the VECTOR variable "VI" to INTEGER, four parameters must be provided to the
# "define_components_integer" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define the components of the vector "VI" as INTEGER, in the interval [1, 10] and step 2:

# domain.define_components_as_integer("VI", 1, 10, 2)

# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

domain.define_components_as_integer("VI", 1, 10)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_components_as_integer(1, 1, 10, 2)
# domain.define_components_as_integer("VI", 1.2, 10, 2)
# domain.define_components_as_integer("VI", 1, 10.2, 2)
# domain.define_components_as_integer("VI", 1, 10, "2")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_components_as_integer("VI", 10, 1, 1)
# domain.define_components_as_integer("VI", 10, 10, 1)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_components_as_integer("VI", 1, 10, 8)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_components_as_integer("J", 1, 10, 1)
# - The variable is not defined as VECTOR.
# domain.define_components_as_integer("I", 1, 10, 1)
# - The components are already defined.
# domain.define_components_as_integer("VI", 1, 10, 1)

# ==================================================================================================================== #
# ============================== 10. Defining VECTOR components as REAL ============================================== #
# ==================================================================================================================== #

# To illustrate the REAL definition of a VECTOR variable, first, define a VECTOR variable "VR", whose size is in
# the interval [1, 10] and step 1:

domain.define_vector("VR", 1, 10, 1)

# To set the components of the VECTOR variable "VR" to REAL, four parameters must be provided to the
# "define_components_real" function:
#       - The vector variable name.
#       - The minimum value of the interval.
#       - The maximum value of the interval.
#       - [Optional] The step: a number to divide the interval, in order to generate random values. If it is not
#         provided, will be set to a default value ((maximum value - minimum value) / 2)

# To define the components of the vector "V_R" as REAL, in the interval [0.0, 0.1] and step 0.0001:

domain.define_components_as_real("VR", 0.0, 0.1, 0.0001)

# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

# domain.define_components_as_real("V_R", 0.0, 0.1)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be a float.
# domain.define_components_as_real(1, 0.0, 0.1, 0.0001)
# domain.define_components_as_real("VR", "min", 0.1, 0.0001)
# domain.define_components_as_real("VR", 0.0, "max", 0.0001)
# domain.define_components_as_real("VR", 0.0, 0.1, "step")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_components_as_real("VR", 0.1, 0.0, 0.0001)
# domain.define_components_as_real("VR", 0.1, 0.1, 0.0001)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_components_as_real("VR", 0.0, 0.1, 0.1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_components_as_real("J", 0.0, 0.1, 0.0001)
# - The variable is not defined as VECTOR
# domain.define_components_as_real("I", 0.0, 0.1, 0.0001)
# - The components are already defined.
# domain.define_components_as_real("VR", 0.0, 0.1, 0.0001)

# ==================================================================================================================== #
# ============================== 11. Defining VECTOR components as CATEGORICAL ======================================= #
# ==================================================================================================================== #

# To illustrate the CATEGORICAL definition of a VECTOR variable, first, define a VECTOR variable "VC", whose size is in
# the interval [10, 20] and step 1:

domain.define_vector("VC", 10, 20, 1)

# To set the components of the VECTOR variable "V_C" to CATEGORICAL, two parameters must be provided to the
# "define_components_categorical" function:
#       - A variable name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.

domain.define_components_as_categorical("VC", ["V1", "V2", "V3"])

# ************ Possible errors
# **** Argument type errors (static):
# - The variable name a and the element name must be str. The categories must be a list.
# domain.define_components_as_categorical(1, ["V1", "V2", "V3"])
# domain.define_components_as_categorical("VC", 1)
# **** Argument type errors (raise TypeError):
# - The categories of the list must be the same type
# domain.define_components_as_categorical("VC", ["V1", 1, "V3"])
# **** Argument value errors (raise ValueError):
# - The categories list must be at least two elements.
# domain.define_categorical("VC", ["V1"])
# - The categories list can not contain repeated values.
# domain.define_categorical("VC", ["V1", "V2", "V1"])
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_components_as_categorical("J", ["V1", "V2", "V3"])
# - The variable is not defined as VECTOR
# domain.define_components_as_categorical("L", ["V1", "V2", "V3"])
# - The components are already defined.
# domain.define_components_as_categorical("VC", ["V1", "V2", "V3"])

# ==================================================================================================================== #
# ============================== 12. Defining VECTOR components as LAYER ============================================= #
# ==================================================================================================================== #

# To illustrate the LAYER definition of a VECTOR variable, first, define a VECTOR variable "V_L", whose size is in
# the interval [10, 20] and step 1:

domain.define_vector("VL", 10, 20, 1)

# Next, define its components type as LAYER with the "define_components_layer" method:

domain.define_components_as_layer("VL")

# **** Argument type errors (static):
# - The variable name a and the element name must be str.
# domain.define_components_as_layer(1)
# **** Definition errors (raise DefinitionError):
# - The variable is not defined.
# domain.define_components_as_layer("J")
# - The variable is not defined as VECTOR
# domain.define_components_as_layer("L")
# - The components are already defined.
# domain.define_components_as_layer("VL")

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

# To define an INTEGER element "el1" for the "VL" VECTOR variable, in the interval [10, 20] and step 1:

domain.define_layer_vector_integer_element("VL", "el1", 10, 20, 1)

# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

# domain.define_layer_vector_integer_element("VL", "el1", 10, 20)


# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_layer_vector_integer_element(1, "el1", 10, 20, 1)
# domain.define_layer_vector_integer_element("VL", 1, 10, 20, 1)
# domain.define_layer_vector_integer_element("VL", "el1", "w", 20, 1)
# domain.define_layer_vector_integer_element("VL", "el1", 10, 20.2, 1)
# domain.define_layer_vector_integer_element("VL", "el1", 10, 20, 1.2)
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_layer_vector_integer_element("VL", "el1", 20, 10, 1)
# domain.define_layer_vector_integer_element("VL", "el1", 20, 20, 1)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_layer_vector_integer_element("VL", "el1", 10, 20, 8)
# **** Definition errors (raise DefinitionError):
# - The vector variable is not defined.
# domain.define_layer_vector_integer_element("J", "el1", 10, 20, 1)
# - The variable is not defined as VECTOR.
# domain.define_layer_vector_integer_element("I", "el1", 10, 20, 1)
# - The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_integer_element("VI", "el1", 10, 20, 1)
# - The variable element is already used.
# domain.define_layer_vector_integer_element("VL", "el1", 10, 20, 1)


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

# To define a REAL element "el2" for the "VL" VECTOR variable, in the interval [0.1, 0.5] and step 0.1:

domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.5, 0.1)

# If the step is not provided, it is set to the default value ((maximum value - minimum value) / 2)

# domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.5)

# **** Argument type errors (static):
# - The variable name a and the element name must be str. The minimum, maximum and step values must be int.
# domain.define_layer_vector_real_element(1, "el2", 0.1, 0.5, 0.1)
# domain.define_layer_vector_real_element("VL", 1, 0.1, 0.5, 0.1)
# domain.define_layer_vector_real_element("VL", "el2", "a", 0.5, 0.1)
# domain.define_layer_vector_real_element("VL", "el2", 0.1, "b", 0.1)
# domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.5, "c")
# **** Argument value errors (raise ValueError):
# - The minimum value is greater or equal than the maximum one.
# domain.define_layer_vector_real_element("VL", "el2", 0.5, 0.1, 0.1)
# domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.1, 0.1)
# - The step value is greater than (maximum value - minimum value) / 2.
# domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.5, 2.0)
# **** Definition errors (raise DefinitionError):
# - The vector variable is not defined.
# domain.define_layer_vector_real_element("J", "el2", 0.1, 0.5, 0.1)
# - The variable is not defined as VECTOR.
# domain.define_layer_vector_real_element("I", "el2", 0.1, 0.5, 0.1)
# - The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_real_element("VI", "el2", 0.1, 0.5, 0.1)
# - The variable element is already used.
# domain.define_layer_vector_real_element("VL", "el2", 0.1, 0.5, 0.1)


# ==================================================================================================================== #
# ======================= 15. Defining elements of LAYER VECTOR components: CATEGORICAL ============================== #
# ==================================================================================================================== #

# To define a CATEGORICAL element of the LAYER components, two parameters must be provided to the
# "define_vector_categorical_element" function:
#       - A element name.
#       - A list with the categories; these values must have the same Python type, i.e., int, float or str.

domain.define_layer_vector_categorical_element("VL", "el3", [1, 2, 3])


# **** Argument type errors (static):
# - The variable name a and the element name must be str. The categories must be a list.
# domain.define_layer_vector_categorical_element(1, "el3", [1, 2, 3])
# domain.define_layer_vector_categorical_element("VL", 2, [1, 2, 3])
# domain.define_layer_vector_categorical_element("VL", "el3", 1)
# **** Argument type errors (raise TypeError):
# - The categories of the list must be the same type.
# domain.define_layer_vector_categorical_element("VL", "el3", [1, 2, 3.3])
# **** Argument value errors (raise ValueError):
# - The categories list must be at least two elements.
# domain.define_layer_vector_categorical_element("VL", "el3", [1])
# - The categories list can not contain repeated values.
# domain.define_layer_vector_categorical_element("VL", "el3", [1, 1, 1])
# **** Definition errors (raise DefinitionError):
# - The vector variable is not defined.
# domain.define_layer_vector_categorical_element("J", "el3", [1, 2, 3])
# - The variable is not defined as VECTOR.
# domain.define_layer_vector_categorical_element("I", "el3", [1, 2, 3])
# - The vector variable components are is not defined as LAYER.
# domain.define_layer_vector_categorical_element("VI", "el3", [1, 2, 3])
# - The variable element is already used.
# domain.define_layer_vector_categorical_element("VL", "el3", [1, 2, 3])

print("Domain:\n")
print(str(domain))
