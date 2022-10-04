from solutions.support_variables import example_solution as solution
from domains.support_domain import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ========================== 1. Removing the last component of a VECTOR variable ===================================== #
# ==================================================================================================================== #

# solution.set_basic_vector("V_I", [1, 2, 3], domain)
# print("\nSolution:\n" + str(solution)+"\n")

# remain = solution.remove_component("V_I", domain)
# print("Solution: " + str(solution) + " => " + str(remain))

# ************ Possible errors
# 1. Argument value errors:
# 1.1. The domain is not available.
# remain = solution.remove_component("V_I")
# 2. Solution errors:
# 2.1. The variable is not assigned.
# solution.remove_component(1, domain)
# solution.remove_component("V_C", domain)
# 2.2. The variable has assigned the minimum number of components
# solution.remove_component("V_I", domain)

# ==================================================================================================================== #
# ========================= 2. Deleting an specific component of a VECTOR variable =================================== #
# ==================================================================================================================== #

solution.set_basic_vector("V_I", [1, 2, 3], domain)
# print("\nSolution:\n" + str(solution)+"\n")

remain = solution.delete_component("V_I", 1, domain)
print("Solution: " + str(solution) + " => " + str(remain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The index must be int.
# remain = solution.delete_component("V_I", "1", domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.delete_component("V_I", 1)
# 3. Solution errors:
# 3.1. The variable is not assigned.
# remain = solution.delete_component(1, 1, domain)
# remain = solution.delete_component("V_C", 1, domain)
# 3.2. The component is not assigned.
# remain = solution.delete_component("V_I", 5, domain)
# 3.3. The variable has assigned the minimum number of components
# remain = solution.delete_component("V_I", 1, domain)
