# from pycvoa.use_cases.solutions.support_variables import example_solution as solution
# from pycvoa.use_cases.domains.support_domain import example_domain as domain
#
# # print("The example domain:\n")
# # print(str(domain) + "\n\n")
#
# # ==================================================================================================================== #
# # ==================================== 1. Setting a LAYER variable =================================================== #
# # ==================================================================================================================== #
#
# solution.set_layer("L", {"E_I": 3, "E_R": 1.55, "E_C": "Lb1"}, domain)
#
# # print("Solution:\n" + str(solution))
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable name must be str.
# # solution.set_layer(1, {"E_I": 3, "E_R": 1.55, "E_C": "Lb1"}, domain)
# # 1.2. The layer value name must be dict.
# # solution.set_layer("L", 1, domain)
# # 1.3. The keys of the layer value must be str.
# # solution.set_layer("L", {1: 3, "E_R": 1.55, "E_C": "Lb1"}, domain)
# # 2. Argument value errors:
# # 2.1. The domain is not available.
# # solution.set_layer("L", {"E_I": 3, "E_R": 1.55, "E_C": "Lb1"})
# # 3. Definition errors:
# # 3.1. The variable is not defined.
# # solution.set_layer("J", {"E_I": 3, "E_R": 1.55, "E_C": "Lb1"}, domain)
# # 3.2. The variable is not defined as LAYER.
# # solution.set_layer("I", {"E_I": 3, "E_R": 1.55, "E_C": "Lb1"}, domain)
# # 4. Domain errors:
# # 4.1. The layer value is not compatible with de variable definition
# # solution.set_layer("L", {"E_I": 3.2, "E_R": 1.55, "E_C": "Lb1"}, domain)
# # solution.set_layer("L", {"E_I": 3, "E_R": 100.2, "E_C": "Lb1"}, domain)
#
#
# # ==================================================================================================================== #
# # ==================================== 2. Setting the elements of a LAYER variable =================================== #
# # ==================================================================================================================== #
#
# solution.set_element("L", "E_I", 5, domain)
# solution.set_element("L", "E_R", 1.55, domain)
# solution.set_element("L", "E_C", "Lb1", domain)
#
# # print("Solution:\n" + str(solution))
#
# # ************ Possible errors
# # 1. Argument type errors:
# # 1.1. The variable name must be str.
# # solution.set_element(1, "E_I", 3, domain)
# # 1.2. The element name must be str.
# # solution.set_element("L", 1, 3, domain)
# # 2. Argument value errors:
# # 2.1. The domain is not available.
# # solution.set_element("L", "E_I", 3)
# # 3. Definition errors:
# # 3.1. The variable is not defined.
# # solution.set_element("J", "E_I", 3, domain)
# # 3.2. The variable is not defined as LAYER.
# # solution.set_element("I", "E_I", 3, domain)
# # 3.3. The element is not defined in the LAYER variable.
# # solution.set_element("L", "E_I-1", 3, domain)
# # 4. Domain errors:
# # 4.1. The value is not compatible with de variable definition
# # solution.set_element("L", "E_I", "Value", domain)
