from pycvoa.types import PYCVOA_TYPE, BASIC, BASICS, NUMERICAL, NUMERICALS


# def check_variable_type(variable: str, check_type: PYCVOA_TYPE, actual_type: PYCVOA_TYPE) -> bool:
#     r = True
#     if check_type is BASIC:
#         if actual_type not in BASICS:
#             raise ValueError("The " + variable + " variable is not defined as BASIC.")
#     elif check_type is NUMERICAL:
#         if actual_type not in NUMERICALS:
#             raise ValueError("The " + variable + " variable is not defined as NUMERICAL.")
#     else:
#         if actual_type is not check_type:
#             raise ValueError("The " + variable + " variable is not defined as " + str(check_type) + ".")
#     return r

def check_item_type(check_type: PYCVOA_TYPE, actual_type: PYCVOA_TYPE) -> bool:
    r = True
    if check_type is BASIC:
        if actual_type not in BASICS:
            r = False
    elif check_type is NUMERICAL:
        if actual_type not in NUMERICALS:
            r = False
    else:
        if actual_type is not check_type:
            r = False
    return r
