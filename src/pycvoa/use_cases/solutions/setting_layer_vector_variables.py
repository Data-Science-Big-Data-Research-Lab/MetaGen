from pycvoa.use_cases.solutions.support_variables import example_solution as solution
from pycvoa.use_cases.domains.support_domain import example_domain as domain

# print("The example domain:\n")
# print(str(domain) + "\n\n")

# ==================================================================================================================== #
# ================================ 1. Setting a LAYER VECTOR variable ================================================ #
# ==================================================================================================================== #

values = [{"el-1": 11, "el-2": 0.1, "el-3": 1}, {"el-1": 12, "el-2": 0.4, "el-3": 3}]

# solution.set_layer_vector("V_L", values, domain)
# print("\nSolution:\n" + str(solution)+"\n")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_layer_vector(1, values, domain)
# 1.2. The values must be a list.
# solution.set_layer_vector("V_L", 1, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_layer_vector("V_L", values)
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_layer_vector("J", values, domain)
# 3.2. The variable is not defined as VECTOR.
# solution.set_layer_vector("I", values, domain)
# 3.3. The components of the VECTOR variable are not defined.
# solution.set_layer_vector("V_N", values, domain)
# 3.4. The VECTOR components are not defined a LAYER
# solution.set_layer_vector("V_I", values, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# solution.set_layer_vector("V_L", [1, {"el-1": 11, "el-2": 0.1, "el-3": 1}], domain)
# solution.set_layer_vector("V_L", [{"el-1": 12, "el-2": 0.2, "el-3": 2}, {"el-1": 200, "el-2": 0.1, "el-3": 1}]
#                           , domain)
# solution.set_layer_vector("V_L", [{"el-1": 12, "el-2": 0.2, "el-3": 2}, {"el-1": 11, "el-2": 0.1, "el-3": "1"}],
#                           domain)

# ==================================================================================================================== #
# =========================== 2. Adding values to a LAYER VECTOR variable ============================================ #
# ==================================================================================================================== #

# solution.set_layer_vector("V_L", values, domain)

# remain = solution.add_layer_component("V_L", {"el-1": 14, "el-2": 0.1, "el-3": 1}, domain)
# print("Solution = " + str(solution) + " => [" + str(remain) + "]")

# remain = solution.add_layer_component("V_L", {"el-1": 12, "el-2": 0.2, "el-3": 2}, domain)
# print("Solution = " + str(solution) + " => [" + str(remain) + "]\n")


# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# remain = solution.add_layer_component(1, {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 1.2. The value must be dict.
# remain = solution.add_layer_component("V_L", 1, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.add_layer_component("V_L", {"el-1": 10, "el-2": 0.1, "el-3": 1})
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.add_layer_component("J", {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.add_layer_component("V_I", {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.add_layer_component("V_N", {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 3.4. The VECTOR components are not defined a LAYER
# remain = solution.add_layer_component("V_I", {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 3.5. The size of the values is not compatible.
# remain = solution.add_layer_component("V_L", {"el-1": 10, "el-2": 0.1, "el-3": 1}, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# remain = solution.add_layer_component("V_L", {"el-1": "w", "el-2": 0.1, "el-3": 1}, domain)
# remain = solution.add_layer_component("V_L", {"el-1": 10, "el-2": 1.5, "el-3": 1}, domain)

# ==================================================================================================================== #
# =========================== 3. Inserting values to a LAYER VECTOR variable ========================================= #
# ==================================================================================================================== #

# solution.set_layer_vector("V_L", values, domain)
#
# remain = solution.insert_layer_component("V_L", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# # print("Solution = " + str(solution) + " => [" + str(remain) + "]")
#
# remain = solution.insert_layer_component("V_L", 3, {"el-1": 17, "el-2": 0.12, "el-3": 3}, domain)
# print("Solution = " + str(solution) + " => [" + str(remain) + "]")

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# remain = solution.insert_layer_component(1, 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 1.2. The index must be int.
# remain = solution.insert_layer_component("V_L", "e", {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 1.3. The layer values must be dict.
# remain = solution.insert_layer_component("V_L", 1, 1, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.insert_layer_component("V_L", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3})
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.insert_layer_component("J", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.insert_layer_component("I", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.insert_layer_component("V_N", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 3.4. The VECTOR components are not defined a LAYER
# remain = solution.insert_layer_component("V_I", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 3.5. The size of the values is not compatible.
# remain = solution.insert_layer_component("V_L", 1, {"el-1": 15, "el-2": 0.12, "el-3": 3}, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# remain = solution.insert_layer_component("V_L", 1, {"el-1": "w", "el-2": 0.12, "el-3": 3}, domain)
# remain = solution.insert_layer_component("V_L", 1, {"el-1": 15, "el-2": 0.5, "el-3": 4}, domain)

# ==================================================================================================================== #
# =========================== 4. Setting a component of a LAYER VECTOR variable ====================================== #
# ==================================================================================================================== #

# solution.set_layer_component("V_L", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)

# print("\nSolution:\n" + str(solution))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_layer_component(1, 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 1.2. The index must be int.
# solution.set_layer_component("V_L", "3",  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 1.3. The layer values must be dict.
# solution.set_layer_component("V_L", 3,  1, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_layer_component("V_L", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3})
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_layer_component("J", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 3.2. The variable is not defined as VECTOR.
# solution.set_layer_component("I", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 3.3. The components of the VECTOR variable are not defined.
# solution.set_layer_component("V_N", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 3.4. The VECTOR components are not defined a LAYER
# solution.set_layer_component("V_I", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# solution.set_layer_component("V_L", 3,  {"el-1": 200, "el-2": 0.123456789, "el-3": 3}, domain)
# solution.set_layer_component("V_L", 3,  {"el-1": 17, "el-2": 0.123456789, "el-3": "w"}, domain)
# 5. Solution errors:
# 5.1. The component is not assigned.
# solution.set_layer_component("V_L", 8,  {"el-1": 17, "el-2": 0.123456789, "el-3": 3}, domain)

# ==================================================================================================================== #
# =========================== 5. Adding element values to a LAYER VECTOR variable ==================================== #
# ==================================================================================================================== #

# solution.set_layer_vector("V_L", values, domain)
#
# remain = solution.add_element_to_layer_component("V_L", "el-1", 14, domain)
# print("Solution = " + str(solution) + " => " + str(remain))
#
# remain = solution.add_element_to_layer_component("V_L", "el-2", 0.14, domain)
# print("Solution = " + str(solution) + " => " + str(remain))
#
# remain = solution.add_element_to_layer_component("V_L", "el-3", 1, domain)
# print("Solution = " + str(solution) + " => " + str(remain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# remain = solution.add_element_to_layer_component(1, "el-1", 14, domain)
# 1.3. The element must be str.
# remain = solution.add_element_to_layer_component("V_L", 1, 14, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.add_element_to_layer_component("V_L", "el-1", 14)
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.add_element_to_layer_component("J", "el-1", 14, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.add_element_to_layer_component("V_I", "el-1", 14, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.add_element_to_layer_component("V_N", "el-1", 14, domain)
# 3.4. The VECTOR components are not defined a LAYER
# remain = solution.add_element_to_layer_component("V_I", "el-1", 14, domain)
# 3.4. The element is not defined in the LAYER VECTOR variable
# remain = solution.add_element_to_layer_component("V_L", "el-4", 14, domain)
# 4. Domain errors:
# 4.1. The element value is not compatible with de variable definition
# remain = solution.add_element_to_layer_component("V_L", "el-1", 14.5, domain)
# remain = solution.add_element_to_layer_component("V_L", "el-1", -5, domain)

# ==================================================================================================================== #
# =========================== 6. Inserting element values to a LAYER VECTOR variable ================================= #
# ==================================================================================================================== #

# solution.set_layer_vector("V_L", values, domain)
#
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-1", 14, domain)
# print("Solution: " + str(solution) + " => " + str(remain))
#
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-2", 0.14, domain)
# print("Solution: " + str(solution) + " => " + str(remain))
#
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-3", 1, domain)
# print("Solution: " + str(solution) + " => " + str(remain))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# remain = solution.insert_element_to_layer_component(1, 1, "el-1", 14, domain)
# 1.2. The index must be int.
# remain = solution.insert_element_to_layer_component("V_L", "1", "el-1", 14, domain)
# 1.3. The element must be str.
# remain = solution.insert_element_to_layer_component("V_L", 1, 1, 14, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-1", 14)
# 3. Definition errors:
# 3.1. The variable is not defined.
# remain = solution.insert_element_to_layer_component("J", 1, "el-1", 14, domain)
# 3.2. The variable is not defined as VECTOR.
# remain = solution.insert_element_to_layer_component("I", 1, "el-1", 14, domain)
# 3.3. The components of the VECTOR variable are not defined.
# remain = solution.insert_element_to_layer_component("V_N", 1, "el-1", 14, domain)
# 3.4. The VECTOR components are not defined a LAYER
# remain = solution.insert_element_to_layer_component("V_I", 1, "el-1", 14, domain)
# 3.4. The element is not defined in the LAYER VECTOR variable
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-4", 14, domain)
# 4. Domain errors:
# 4.1. The element value is not compatible with de variable definition
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-1", "w", domain)
# remain = solution.insert_element_to_layer_component("V_L", 1, "el-1", 100, domain)


# ==================================================================================================================== #
# =========================== 7. Setting an element value a LAYER VECTOR variable ==================================== #
# ==================================================================================================================== #

solution.set_layer_vector("V_L", values, domain)

solution.set_element_of_layer_component("V_L", 0, "el-2", 0.45, domain)
solution.set_element_of_layer_component("V_L", 1, "el-1", 15, domain)

print("\nSolution:\n" + str(solution))

# ************ Possible errors
# 1. Argument type errors:
# 1.1. The variable name must be str.
# solution.set_element_of_layer_component(1, 0, "el-2", 0.45, domain)
# 1.2. The index must be int.
# solution.set_element_of_layer_component("V_L", "0", "el-2", 0.45, domain)
# 1.3. The element must be str.
# solution.set_element_of_layer_component("V_L", 0, 1, 0.45, domain)
# 2. Argument value errors:
# 2.1. The domain is not available.
# solution.set_element_of_layer_component("V_L", 0, "el-2", 0.45)
# 3. Definition errors:
# 3.1. The variable is not defined.
# solution.set_element_of_layer_component("J", 0, "el-2", 0.45, domain)
# 3.2. The variable is not defined as VECTOR.
# solution.set_element_of_layer_component("I", 0, "el-2", 0.45, domain)
# 3.3. The components of the VECTOR variable are not defined.
# solution.set_element_of_layer_component("V_N", 0, "el-2", 0.45, domain)
# 3.4. The VECTOR components are not defined a LAYER
# solution.set_element_of_layer_component("V_I", 0, "el-2", 0.45, domain)
# 3.4. The element is not defined in the LAYER VECTOR variable
# solution.set_element_of_layer_component("V_L", 0, "el-4", 0.45, domain)
# 4. Domain errors:
# 4.1. The values are not compatible with de variable definition
# solution.set_element_of_layer_component("V_L", 0, "el-2", 45, domain)
# solution.set_element_of_layer_component("V_L", 0, "el-2", 10.45, domain)
# 5. Solution errors:
# 5.1. The component is not assigned.
# solution.set_element_of_layer_component("V_L", 3, "el-2", 0.45, domain)
