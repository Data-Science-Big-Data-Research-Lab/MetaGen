from pycvoa.use_cases.solutions.support_variables import example_solution as solution
from pycvoa.use_cases.domains.support_domain import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# =========================== 1. Setting the components of a BASIC VECTOR variable =================================== #
# ==================================================================================================================== #

solution.set_basic_vector("V_C", ["V1", "V2", "V3", "V1", "V2", "V3", "V1", "V2", "V3", "V1"], domain)

# print("\nSolution:\n" + str(solution))

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
# =========================== 2. Adding values to a BASIC VECTOR variable ============================================ #
# ==================================================================================================================== #

remain = solution.add_basic_component("V_I", 1, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.add_basic_component("V_I", 2, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.add_basic_component("V_I", 3, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.add_basic_component("V_I", 4, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.add_basic_component("V_I", 5, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.add_basic_component(1, 1, domain)
# 1.2. The values must be int, float or str.
# remain = solution.add_basic_component("V_I", [1, 2], domain)
# remain = solution.add_basic_component("V_I", {1: "t", 2: "e"}, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.add_basic_component("V_I", 1)
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.add_basic_component("J", 1, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.add_basic_component("I", 1, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.add_basic_component("V_N", 1, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# remain = solution.add_basic_component("V_I", "W", domain)
# remain = solution.add_basic_component("V_I", 200, domain)
# 5. Solution errors:
# 5.1. The addition is not permitted since the vector is completed
# remain = solution.add_basic_component("V_I", 1, domain)

# ==================================================================================================================== #
# =========================== 3. Inserting values to a BASIC VECTOR variable ========================================= #
# ==================================================================================================================== #

solution.set_basic_vector("V_R", [0.01, 0.02, 0.03, 0.04, 0.05], domain)

remain = solution.insert_basic_component("V_R", 1, 0.0001, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.insert_basic_component("V_R", 4, 0.0001, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.insert_basic_component("V_R", 0, 0.0001, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.insert_basic_component("V_R", 10, 0.0001, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

remain = solution.insert_basic_component("V_R", 20, 0.0001, domain)
print("Solution = " + str(solution) + " => [" + str(remain) + "]")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# remain = solution.insert_basic_component(1, 1, 0.0001, domain)
# 1.2. The index must be int.
# remain = solution.insert_basic_component("V_R", "1", 0.0001, domain)
# 1.2. The values must be int, float or str.
# remain = solution.insert_basic_component("V_R", 1, [1, 2], domain)
# remain = solution.insert_basic_component("V_R", 1, {1: "t", 2: "e"}, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.insert_basic_component("V_R", 1, 0.0001)
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.insert_basic_component("J", 1, 0.0001, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.insert_basic_component("I", 1, 0.0001, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.insert_basic_component("V_N", 1, 0.0001, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# remain = solution.insert_basic_component("V_R", 1, "w", domain)
# remain = solution.insert_basic_component("V_R", 1, 0.5, domain)
# 5. Solution errors:
# 5.1. The addition is not permitted since the vector is completed
# remain = solution.insert_basic_component("V_R", 1, 0.0001, domain)

# ==================================================================================================================== #
# =========================== 4. Setting a component of a BASIC VECTOR variable ====================================== #
# ==================================================================================================================== #

solution.set_basic_component("V_I", 3, 8, domain)

# print("\nSolution:\n" + str(solution))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_basic_component(1, 3, 8, domain)
# 1.2. The index must be int.
# solution.set_basic_component("V_I", "3", 8, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_basic_component("V_I", 3, 8)
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_basic_component("J", 3, 8, domain)
# 3.2. The variable is not defined as VECTOR.
# solution.set_basic_component("I", 3, 8, domain)
# 3.3. The components of the VECTOR variable are not defined.
# solution.set_basic_component("V_N", 3, 8, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# solution.set_basic_component("V_I", 3, 200, domain)
# solution.set_basic_component("V_I", 3, "w", domain)
# 5. Solution errors:
# 5.1. The component is not assigned.
# solution.set_basic_component("V_I", 7, 8, domain)
