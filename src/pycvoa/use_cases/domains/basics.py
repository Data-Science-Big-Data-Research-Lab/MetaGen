# =====================================================================================================================#
# ======================================== 1. Importing artifacts =====================================================#
# =====================================================================================================================#

# The class Domain is in the pycvoa.problem.domain module:
from pycvoa.problem.domain import Domain

# =====================================================================================================================#
# ======================================== 2. Variable types ==========================================================#
# =====================================================================================================================#

# The Domain-Solution framework provides four variable type definitions: INTEGER, REAL, CATEGORICAL, LAYER and VECTOR.
# The INTEGER, REAL and CATEGORICAL types are BASIC types that represent a single value.
# The LAYER variable is composed by a set of several variables (called elements) of BASIC type.
# The VECTOR variable is a collection of indexed values with the same type (INTEGER, REAL, CATEGORICAL or LAYER); each
# value of a vector is called component.
# These four types have a literal representation in pycvoa, and can be imported the pycvoa.problem using the
# following instruction (the BASIC type, that contains the  INTEGER, REAL, CATEGORICAL types, is also available):
# from pycvoa.problem import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, BASIC

# =====================================================================================================================#
# ======================================== 3. Building a new domain ===================================================#
# =====================================================================================================================#

# To build a new domain, the default an unique constructor of the Domain class must be used
domain = Domain()