# ======================================== 0. Importing artifacts ======================================================
# The class Solution is in the pycvoa.problem.solution module:
from pycvoa.problem.solution import Solution
# The Domain class is also necessary to boost the Solution functionalities
from pycvoa.problem.domain import Domain

# ======================================== 1. Building a domain =======================================================

# A Solution is an instantiation of the variables defined by a Domain, therefore, firstly, a Domain must be defined
# Instantiating the Domain class
domain_A = Domain()
# Defining an INTEGER variable I
domain_A.define_integer("I", 0, 100, 50)
# Defining a REAL variable R
domain_A.define_real("R", 0.0, 1.0, 0.1)
# Defining a CATEGORICAL variable C
domain_A.define_categorical("C", ["C1", "C2", "C3", "C4"])
# Defining a LAYER variable L
domain_A.define_layer("L")
# Defining a INTEGER element, LI, in L (defined as LAYER)
domain_A.define_integer_element("L", "LI", 0, 100, 20)
# Defining a REAL element, LR, in L (defined as LAYER)
domain_A.define_real_element("L", "LR", 1.5, 3.0, 0.01)
# Defining a CATEGORICAL element, LC, in L (defined as LAYER)
domain_A.define_categorical_element("L", "LC", ["Lb1", "Lb2", "Lb3"])
# Defining a VECTOR variable, VI
domain_A.define_vector("VI", 2, 8, 2)
# Defining the components of VI as INTEGER
domain_A.define_components_as_integer("VI", 1, 10, 1)
# Defining a VECTOR variable, VR
domain_A.define_vector("VR", 1, 10, 1)
# Defining the components of VR as REAL
domain_A.define_components_as_real("VR", 0.0, 0.1, 0.0001)
# Defining a VECTOR variable, VC
domain_A.define_vector("VC", 10, 20, 1)
# Defining the components of VC as CATEGORICAL
domain_A.define_components_as_categorical("VC", ["V1", "V2", "V3"])
# Defining a VECTOR variable, VL
domain_A.define_vector("VL", 10, 20, 1)
# Defining the components of VL as LAYER
domain_A.define_components_as_layer("VL")
# Defining a INTEGER element, el-1, in the VL components (defined as LAYER)
domain_A.define_layer_vector_integer_element("VL", "el-1", 10, 20, 1)
# Defining a REAL element, el-2, in the VL components (defined as LAYER)
domain_A.define_layer_vector_real_element("VL", "el-2", 0.1, 0.5, 0.1)
# Defining a CATEGORICAL element, el-3, in the VL components (defined as LAYER)
domain_A.define_layer_vector_categorical_element("VL", "el-3", [1, 2, 3])

# print("\nCurrent domain definitions:\n" + str(domain_A) + "\n")

# ======================================== 2. Building a solution =====================================================

# Two aspects should be taken into account when building a solution:
# 1. The initial fitness function value: the best (0.0) or the worst (sys.float_info.max, 1.7976931348623157e+308)
#    This decision depends on the meta-heuristic implementation.
# 2. The domain management: internal or external.
#    In the internal management scenario, the domain is passed as parameter in the constructor method, and, all members
#    of the Solution class will use it to perform their operations.
#    In the external management scenario, the domain must be provided as parameter of each Solution member to perform
#    its task.
#    Both of them are valid mechanisms, the decision depends on third-party developer preference.

# To build an internal best solution, instantiate the Solution class with best=True and domain=domain
internal_best = Solution(True, domain_A)
# To build an internal worst solution, instantiate the Solution class with best=False (by default) and domain=domain
internal_worst = Solution(domain=domain_A)
# To build an external best solution, instantiate the Solution class with best=True
external_best = Solution(True)
# To build an external worst solution, instantiate the Solution class with best=False (by default)
external_worst = Solution()

# The Solution objects can be printed with str() method
# print("Internal best: " + str(internal_best) + "\nInternal worst: " + str(internal_worst) + "\nExternal best: "
#      + str(external_best) + "\nInternal worst: " + str(external_worst)+"\n")

# The Solution objects have two accessible member variables: the fitness function value and the discovery iteration.
# PyCVOA users can use these attributes to develop their algorithms.
fitness = internal_worst.fitness
iteration = internal_worst.discovery_iteration
# print("Solution current fitness value: "+str(fitness)+"\nSolution current discovery iteration: "+str(iteration)+"\n")

# A solution without internal domain is built to illustrate the remaining examples
solution = Solution()

# ======================================== 3. Domain management ========================================================

# If the Domain was not specified in the Solution constructor, the domain must be to passed as parameter
# in the member operations. If not the NotAvailableItem exception will be raised.
# Incorrect:
# external_worst.set_basic("I", 3)
# Correct:
external_worst.set_basic("I", 3, domain_A)

# The domain can be set globally with the set_domain method. Then it is not necessary to specify the domain
# as parameter in the member operations.
external_worst.set_domain(domain_A)
external_worst.set_basic("I", 4)

# If the Domain was specified in the constructor of the object, it is not necessary to specify the domain
# as parameter in the member operations.
internal_worst.set_basic("I", 3)

# print("External Worst:\n"+str(external_worst)+"\nInternal Worst:\n"+str(internal_worst)+"\n")


# ======================================== 4. Setting variables ========================================================
# A variable will be set by means of "set_*" methods. If the variable already exist in the solution, its value will be
# set.

#                              %%%%%%%%%% 4.1 Setting BASIC variables %%%%%%%%%%
# Set a BASIC variable with the set_basic method
solution.set_basic("I", 3, domain_A)
solution.set_basic("R", 0.001, domain_A)
solution.set_basic("C", "C1", domain_A)

# **** Possible errors
# 1. The domain is not available in the solution, then raise NotAvailableItem.
# solution.set_basic("I", 3)
# solution.set_basic("R", 0.001)
# solution.set_basic("C", "C1")
# 2. [Domain-derived error] The variable name is not <str> type, then raise WrongParameters
# solution.set_basic(1, 3, domain_A)
# solution.set_basic(2, 0.001, domain_A)
# solution.set_basic(3, "C1", domain_A)
# 3. The variable type is not BASIC, then raise WrongItemType.
# solution.set_basic("L", 3, domain_A)
# solution.set_basic("L", 0.001, domain_A)
# solution.set_basic("L", "C1", domain_A)
# 4. [Domain-derived error] The variable is not defines in the domain, then raise NotAvailableItem
# solution.set_basic("W", 3, domain_A)
# solution.set_basic("W", 0.001, domain_A)
# solution.set_basic("W", "C1", domain_A)
# 5. [Domain-derived error] The Python type of the new value is not correct, then raise WrongParameters
# solution.set_basic("I", 3.5, domain_A)
# solution.set_basic("R", "C1", domain_A)
# 6. [Domain-derived error, only for CATEGORICAL variables] The Python type of the new value must be the same as the
# categories, then raise WrongParameters
# solution.set_basic("C", 1, domain_A)
# 7. The new value is not compatible with the variable definition, then raise WrongItemValue
# solution.set_basic("I", -1, domain_A)
# solution.set_basic("R", 1.2, domain_A)
# solution.set_basic("C", "label", domain_A)

# print("External Worst:\n"+str(external_worst))

#                             %%%%%%%%%% 4.2 Setting the elements of a LAYER variable %%%%%%%%%%
# Set an element of a LAYER variable with the set_element method.
solution.set_element("L", "LI", 3, domain_A)
solution.set_element("L", "LR", 1.55, domain_A)
solution.set_element("L", "LC", "Lb1", domain_A)

# **** Possible errors
# 1. The domain is not available in the solution, then raise NotAvailableItem.
# solution.set_element("L", "LI", 3)
# solution.set_element("L", "LR", 1.55)
# solution.set_element("L", "LC", "Lb1")
# 2. [Domain-derived error] The variable name is not <str> type, then raise WrongParameters
# solution.set_element(1, "LI", 3, domain_A)
# solution.set_element(1, "LR", 1.55, domain_A)
# solution.set_element(1, "LC", "Lb1", domain_A)
# 3. [Domain-derived error] The element name is not <str> type, then raise WrongParameters
# solution.set_element("L", 1, 3, domain_A)
# solution.set_element("L", 2, 1.55, domain_A)
# solution.set_element("L", 3, "Lb1", domain_A)
# 4. The variable type is not LAYER, then raise WrongItemType.
# solution.set_element("I", "LI", 3, domain_A)
# solution.set_element("I", "LR", 1.55, domain_A)
# solution.set_element("I", "LC", "Lb1", domain_A)
# 5. [Domain-derived error] The variable is not defines in the domain, then raise NotAvailableItem
# solution.set_element("W", "LI", 3, domain_A)
# solution.set_element("W", "LR", 1.55, domain_A)
# solution.set_element("W", "LC", "Lb1", domain_A)
# 6. [Domain-derived error] The element is not defined in the LAYER variable, then raise NotAvailableItem
# solution.set_element("L", "LI-1", 3, domain_A)
# solution.set_element("L", "LR-1", 1.55, domain_A)
# solution.set_element("L", "LC-1", "Lb1", domain_A)
# 7. [Domain-derived error] The Python type of the new value is not correct, then raise WrongParameters
# solution.set_element("L", "LI", "A", domain_A)
# solution.set_element("L", "LR", 1, domain_A)
# 8. [Domain-derived error, only for CATEGORICAL variables] The Python type of the new value must be the same as the
# categories, then raise WrongParameters
# solution.set_element("L", "LC", 1.2, domain_A)
# 9. The new value is not compatible with the variable definition, then raise WrongItemValue
# solution.set_element("L", "LI", 300, domain_A)
# solution.set_element("L", "LR", 0.5, domain_A)
# solution.set_element("L", "LC", "Lb1_1", domain_A)


#                             %%%%%%%%%% 4.3. Setting the components of a VECTOR variable %%%%%%%%%%

# To simplify the example code, the domain_A is internally set for the solution object
solution.set_domain(domain_A)

# Setting the values from a Python list

solution.set_basic_vector("VI", [1, 2, 3])
# solution.set_basic_vector("VI",[1, 2])
# solution.set_basic_vector("VI",[1.2, 2])

solution.set_basic_vector("VR",[1.3, 2.1, 3.2])
# solution.set_basic_vector("VI",[1, 2])
# solution.set_basic_vector("VI",[1.2, 2])


# Firstly, add new basic components.
# solution.add_basic_component("VI", 1)
# solution.add_basic_component("VI", 2)
# solution.add_basic_component("VI", 3)
# solution.add_basic_component("VR", 0.001)
# solution.add_basic_component("VR", 0.002)
# solution.add_basic_component("VR", 0.003)
print("Solution:\n"+str(solution))




# Set a component of a VECTOR variable with the set_component method.
# solution.set_component("VI", 0, 1)
# solution.set_component("VI", 1, 2)
# solution.set_component("VR", 0, 0.001)
# solution.set_component("VR", 1, 0.002)
# solution.set_component("VC", 0, "V1")
# solution.set_component("VC", 1, "V2")





























