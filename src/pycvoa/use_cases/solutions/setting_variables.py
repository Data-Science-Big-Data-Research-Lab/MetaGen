from pycvoa.use_cases.solutions.support_variables import example_solution as solution
from pycvoa.use_cases.domains.support_variables import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ======================================= 1. Setting BASIC variables ================================================= #
# ==================================================================================================================== #

solution.set_basic("I", 3, domain)
solution.set_basic("R", 0.001, domain)
solution.set_basic("C", "C1", domain)

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_basic(1, 3, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_basic("I", 3)
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_basic("J", 3, domain)
# 4. Domain errors:
# 4.1. The value is not compatible with de variable definition
# solution.set_basic("I", 3.2, domain)


# ==================================================================================================================== #
# ==================================== 2. Setting the elements of a LAYER variable =================================== #
# ==================================================================================================================== #

solution.set_element("L", "E_I", 3, domain)
solution.set_element("L", "E_R", 1.55, domain)
solution.set_element("L", "E_C", "Lb1", domain)

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_element(1, "E_I", 3, domain)
# 1.2. The element name must be str.
# solution.set_element("L", 1, 3, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_element("L", "E_I", 3)
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_element("J", "E_I", 3, domain)
# 3.2. The variable is not defined as LAYER.
# solution.set_element("I", "E_I", 3, domain)
# 3.3. The element is not defined in the LAYER variable.
# solution.set_element("L", "E_I-1", 3, domain)
# 4. Domain errors:
# 4.1. The value is not compatible with de variable definition
# solution.set_element("L", "E_I", "Value", domain)

# ==================================================================================================================== #
# =========================== 3. Setting the components of a BASIC VECTOR variable =================================== #
# ==================================================================================================================== #

solution.set_basic_vector("V_I", [1, 2, 3], domain)
solution.set_basic_vector("V_R", [0.01, 0.02, 0.03, 0.04, 0.05], domain)
solution.set_basic_vector("V_C", ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"], domain)

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_basic_vector(1, [1, 2, 3], domain)
# 1.2. The values must be list.
# solution.set_basic_vector("V_I", 1, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_basic_vector(1, [1, 2, 3])
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_basic_vector("J", [1, 2, 3], domain)
# 3.2. The variable is not defined as VECTOR.
# solution.set_basic_vector("I", [1, 2, 3], domain)
# 3.3. The components of the VECTOR variable are not defined.
# solution.set_basic_vector("V_N", [1, 2, 3], domain)
# 3.4. The size of the values is not compatible.
# solution.set_basic_vector("V_I", [1], domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# solution.set_basic_vector("V_I", [1, "w", 3], domain)
# solution.set_basic_vector("V_I", [1, 2, 3, 100], domain)

# ==================================================================================================================== #
# =========================== 4. Adding values to a BASIC VECTOR variable ============================================ #
# ==================================================================================================================== #

solution.add_basic_component("V_I", 1, domain)


print("The solution:\n")
print(str(solution) + "\n\n")
