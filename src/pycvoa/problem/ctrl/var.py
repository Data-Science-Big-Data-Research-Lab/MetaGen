from pycvoa.problem.domain import Domain
from pycvoa.problem.types import *
import pycvoa.problem.ctrl as ctrl


def valid_domain(external_domain:Domain, internal_domain:Domain) -> Domain:
    ctrl.par.is_domain_class(external_domain)
    current_domain = external_domain
    if current_domain is None:
        current_domain = internal_domain
    if current_domain is None:
        raise ValueError("A domain must be specified, via parameter or set_domain method.")
    return current_domain


def variable_type(variable, check_type, domain):
    var_type = domain.get_variable_type(variable)
    if check_type is BASIC:
        if var_type not in BASIC:
            raise ValueError("The " + variable + " variable is not defined as BASIC.")
    else:
        if var_type is not check_type:
            raise ValueError("The " + variable + " variable is not defined as " + check_type + ".")


def component_type(vector_variable, check_type, domain):
    """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
    py:class:`~pycvoa.problem.domain.WrongItemType`.

    :param vector_variable: The **VECTOR** variable.
    :param check_type: The component type.
    :param domain: The domain
    :type vector_variable: str
    :type check_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
    """
    comp_type = domain.get_vector_components_type(vector_variable)
    if check_type is BASIC:
        if comp_type not in BASIC:
            raise ValueError("The components of " + vector_variable + " are not defined as BASIC.")
    else:
        if comp_type is not check_type:
            raise ValueError("The components of " + vector_variable + " are not defined as " + check_type + ".")


def domain_variable_type(variable, check_type, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    variable_type(variable, check_type, current_domain)
    return current_domain


def domain_basic(vector_variable, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    variable_type(vector_variable, BASIC, current_domain)
    return current_domain


def domain_layer(vector_variable, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    variable_type(vector_variable, LAYER, current_domain)
    return current_domain


def domain_vector(vector_variable, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    variable_type(vector_variable, VECTOR, current_domain)
    return current_domain


def domain_basic_vector(vector_variable, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    component_type(vector_variable, BASIC, current_domain)


def domain_layer_vector(vector_variable, external_domain, internal_domain):
    current_domain = valid_domain(external_domain, internal_domain)
    component_type(vector_variable, LAYER, current_domain)
