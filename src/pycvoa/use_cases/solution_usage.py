# ======================================== 0. Importing artifacts ======================================================
# The class Solution is in the pycvoa.problem.solution module:
from pycvoa.problem.solution import Solution
# The Domain class is also necessary to boost the Solution functionalities
from pycvoa.problem.domain import Domain

# ======================================== 1. Building a domain =======================================================

# A Solution is an instantiation of the variables defined by a Domain, therefore, firstly, a Domain must be defined
# Instantiating the Domain class
domain = Domain()
# Defining an INTEGER variable I
domain.define_integer("I", 0, 100, 50)
# Defining a REAL variable R
domain.define_real("R", 0.0, 1.0, 0.1)
# Defining a CATEGORICAL variable C
domain.define_categorical("C", ["C1", "C2", "C3", "C4"])
# Defining a LAYER variable L
domain.define_layer("L")
# Defining a INTEGER element, LI, in L (defined as LAYER)
domain.define_integer_element("L", "LI", 0, 100, 20)
# Defining a REAL element, LR, in L (defined as LAYER)
domain.define_real_element("L", "LR", 1.5, 3.0, 0.01)
# Defining a CATEGORICAL element, LC, in L (defined as LAYER)
domain.define_categorical_element("L", "LC", ["Lb1", "Lb2", "Lb3"])
# Defining a VECTOR variable, VI
domain.define_vector("VI", 2, 8, 2)
# Defining the components of VI as INTEGER
domain.define_components_integer("VI", 1, 10, 1)
# Defining a VECTOR variable, VR
domain.define_vector("VR", 1, 10, 1)
# Defining the components of VR as REAL
domain.define_components_real("VR", 0.0, 0.1, 0.0001)
# Defining a VECTOR variable, VC
domain.define_vector("VC", 10, 20, 1)
# Defining the components of VC as CATEGORICAL
domain.define_components_categorical("VC", ["V1", "V2", "V3"])
# Defining a VECTOR variable, VL
domain.define_vector("VL", 10, 20, 1)
# Defining the components of VL as LAYER
domain.define_components_layer("VL")
# Defining a INTEGER element, el-1, in the VL components (defined as LAYER)
domain.define_vector_integer_element("VL", "el-1", 10, 20, 1)
# Defining a REAL element, el-2, in the VL components (defined as LAYER)
domain.define_vector_real_element("VL", "el-2", 0.1, 0.5, 0.1)
# Defining a CATEGORICAL element, el-3, in the VL components (defined as LAYER)
domain.define_vector_categorical_element("VL", "el-3", [1, 2, 3])

print("\nCurrent domain definitions:\n" + str(domain) + "\n")

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
internal_best = Solution(True, domain)
# To build an internal worst solution, instantiate the Solution class with best=False (by default) and domain=domain
internal_worst = Solution(domain=domain)
# To build an external best solution, instantiate the Solution class with best=True
external_best = Solution(True)
# To build an external worst solution, instantiate the Solution class with best=False (by default)
external_worst = Solution()

# The Solution objects can be printed with str() method
print("Internal best: " + str(internal_best) + "\nInternal worst: " + str(internal_worst) + "\nExternal best: "
      + str(external_best) + "\nInternal worst: " + str(external_worst)+"\n")

# The Solution objects have two accessible member variables: the fitness function value and the discovery iteration.
# PyCVOA users can use these attributes to develop their algorithms.
fitness = internal_worst.fitness
iteration = internal_worst.discovery_iteration
print("Solution current fitness value: "+str(fitness))
print("Solution current discovery iteration: "+str(iteration)+"\n")






























