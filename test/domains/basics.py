# ==================================================================================================================== #
# ======================================== 1. Importing artifacts ==================================================== #
# ==================================================================================================================== #

# The Domain class is in the pycvoa.problem.domain module:
from pycvoa.problem.domain import Domain

# ==================================================================================================================== #
# ======================================== 2. Variable types ========================================================= #
# ==================================================================================================================== #

# The Domain-Solution framework provides four variable type definitions: INTEGER, REAL, CATEGORICAL, LAYER and VECTOR.
# The INTEGER, REAL and CATEGORICAL types are called BASICS types and represent a single value.
# As an alias, the INTEGER and REAL types are also called NUMERICALS.
# The LAYER variable is composed by a set of several variables (called elements) of BASIC type.
# The VECTOR variable is a collection of indexed values with the same type (INTEGER, REAL, CATEGORICAL or LAYER); each
# value of a vector is called component.
# These four types have a literal representation in pycvoa, and can be imported the pycvoa.types using the
# following instruction (the BASICS and NUMERICALS alias are also available):
# from pycvoa.types import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, BASICS, NUMERICALS

# ==================================================================================================================== #
# ======================================== 3. Building a new domain ================================================== #
# ==================================================================================================================== #

# To build a new domain, the default a unique constructor of the Domain class must be used
domain = Domain()
