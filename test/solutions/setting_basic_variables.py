from solutions.support_variables import example_solution as solution
from domains.support_domain import example_domain as domain

print("The example domain:\n")
print(str(domain) + "\n\n")

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





























print("\nThe solution:\n")
print(str(solution) + "\n\n")
