from pycvoa.control import DefinitionError, DomainError, SolutionError
from pycvoa.problem.domain import Domain
from pycvoa.control.types import *


def get_valid_domain(external_domain: Union[Domain, None], internal_domain: Union[Domain, None]) -> Domain:
    current_domain = external_domain
    if current_domain is None:
        current_domain = internal_domain
    if current_domain is None:
        raise DomainError("A domain must be specified, via parameter or set_domain method.")
    return current_domain


@final
class SolValChk:
    @staticmethod
    def check_basic_value(bvar: str, bval: Basic, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_basic(bvar, bval):
            raise DomainError("The value " + str(bval) + " is not compatible with the "
                              + bvar + " variable definition.")

    @staticmethod
    def check_layer_value(lvar: str, lval: SolLayer, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        for element, value in lval.items():
            if not vdom.check_element(lvar, element, value):
                raise DomainError(
                    "The value " + str(value) + " is not compatible for the " + element + " element in the "
                    + lvar + " variable.")

    @staticmethod
    def check_layer_element_value(lval: str, ele: str, bval: Basic,
                                  edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_element(lval, ele, bval):
            raise DomainError(
                "The value " + str(bval) + " is not compatible for the " + ele + " element in the "
                + lval + " variable.")

    @staticmethod
    def check_basic_vector_values(bvvar: str, bvval: BasicVector, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_vector_basic_values(bvvar, bvval):
            raise DomainError(
                "The values are not compatible with the " + bvvar + " variable definition")

    @staticmethod
    def check_basic_vector_value(bvvar: str, bval: Basic,
                                 edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_vector_basic_value(bvvar, bval):
            raise DomainError(
                "The value " + str(bval) + " is not valid for the " + str(bvvar) + " variable.")
        return vdom

    @staticmethod
    def check_layer_vector_values(lvvar: str, lvval: SolLayerVector, edom: Union[Domain, None],
                                  idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_vector_values_size(lvvar, lvval):
            raise DomainError("The size of " + str(lvval) + " is not compatible with the " + lvvar
                              + " definition.")
        for layer in lvval:
            assert type(layer) is SolLayer
            for element, value in layer.items():
                if not vdom.check_vector_layer_element_value(lvvar, element, value):
                    raise DomainError(
                        "The " + element + " element of the " + str(lvval.index(layer))
                        + "-nh component is not compatible with its definition.")

    @staticmethod
    def check_layer_vector_component(lvvar: str, lval: SolLayer, edom: Union[Domain, None], idom: Union[Domain, None]):
        vodm = get_valid_domain(edom, idom)
        for element, value in lval.items():
            if not vodm.check_vector_layer_element_value(lvvar, element, value):
                raise DomainError(
                    "The " + element + " element of the is not compatible with its definition.")
        return vodm

    @staticmethod
    def check_layer_vector_element(lvvar: str, ele: str, value: Basic,
                                   edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = get_valid_domain(edom, idom)
        if not vdom.check_vector_layer_element_value(lvvar, ele, value):
            raise ValueError(
                "The value " + str(value) + " is not valid for the " + str(ele) + " element in the "
                + str(lvvar) + " variable.")
        return vdom


@final
class SolDefChk:
    @staticmethod
    def is_defined_variable(var: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = get_valid_domain(edom, idom)
        if vdom.is_defined_variable(var) is not True:
            raise DomainError(
                "The variable " + var + " is not defined in this solution's domain.")
        return vdom

    @staticmethod
    def var_defined_as(var: str, tpy: PYCVOA_TYPE, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = SolDefChk.is_defined_variable(var, edom, idom)
        if ArgChk.check_item_type(tpy, vdom.get_variable_type(var)) is False:
            raise DefinitionError("The variable " + var + " is not defined as "+str(tpy)+" in this solution's domain.")
        return vdom

    @staticmethod
    def is_defined_as_basic(var: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = SolDefChk.is_defined_variable(var, edom, idom)
        if ArgChk.check_item_type(BASIC, vdom.get_variable_type(var)) is False:
            raise DefinitionError("The variable " + var + " is not defined as BASIC in this solution's domain.")
        return vdom

    @staticmethod
    def is_defined_as_layer(var: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = SolDefChk.is_defined_variable(var, edom, idom)
        if ArgChk.check_item_type(LAYER, vdom.get_variable_type(var)) is False:
            raise DefinitionError("The variable " + var + " is not defined as LAYER.")
        return vdom

    @staticmethod
    def is_defined_as_vector_variable(var: str, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = SolDefChk.is_defined_variable(var, edom, idom)
        if vdom.get_variable_type(var) is not VECTOR:
            raise DomainError("The variable " + var + " is not defined as LAYER.")
        if not vdom.are_defined_components(var):
            raise DomainError("The components of the " + var + " VECTOR variable have not defined.")

    @staticmethod
    def is_defined_as_layer_vector_variable(var: str, edom: Union[Domain, None], idom: Union[Domain, None]):
        vdom = SolDefChk.is_defined_variable(var, edom, idom)
        if vdom.get_variable_type(var) is not VECTOR:
            raise DomainError("The variable " + var + " is not defined as LAYER.")
        if not vdom.get_vector_components_type(var) is not LAYER:
            raise DomainError("The components of the " + var + " VECTOR variable have not defined as LAYER.")

    @staticmethod
    def is_defined_as_layer_element(var: str, ele: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = get_valid_domain(edom, idom)
        if ArgChk.check_item_type(LAYER, vdom.get_variable_type(var)) is False:
            raise DefinitionError("The variable " + var + " is not defined as LAYER.")
        if vdom.is_defined_element(var, ele) is False:
            raise DefinitionError(
                "The element " + ele + " of the " + var +
                " LAYER variable is not defined in this domain.")
        return vdom

    @staticmethod
    def is_defined_as_basic_vector(var: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = get_valid_domain(edom, idom)
        SolDefChk.__check_component_type(var, BASIC, vdom)
        return vdom

    @staticmethod
    def is_defined_as_layer_vector(var: str, edom: Union[Domain, None], idom: Union[Domain, None]) -> Domain:
        vdom = get_valid_domain(edom, idom)
        SolDefChk.__check_component_type(var, LAYER, vdom)
        return vdom

    @staticmethod
    def __check_component_type(var: str, chk_typ: PYCVOA_TYPE, dom: Domain):
        """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
        py:class:`~pycvoa.problem.domain.WrongItemType`.

        :param var: The **VECTOR** variable.
        :param chk_typ: The component type.
        :param dom: The domain
        :type var: str
        :type chk_typ: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
        """
        cmp_typ = dom.get_vector_components_type(var)
        if chk_typ is BASIC:
            if cmp_typ not in BASICS:
                raise ValueError("The components of " + var + " are not defined as BASIC.")
        elif chk_typ is NUMERICAL:
            if cmp_typ not in NUMERICALS:
                raise ValueError("The components of " + var + " are not defined as NUMERICAL.")
        else:
            if cmp_typ is not chk_typ:
                raise ValueError("The components of " + var
                                 + " are not defined as " + str(chk_typ) + ".")



@final
class AsgChk:

    @staticmethod
    def is_assigned_variable(var: str, sol: SolStructure):
        if var not in sol.keys():
            raise SolutionError("The " + str(var) + " variable is not assigned in this solution.")

    @staticmethod
    def is_assigned_layer_element(lvar: str, ele: str, sol: SolStructure):
        AsgChk.is_assigned_variable(lvar, sol)
        layer: SolLayer = cast(SolLayer, sol.get(lvar))
        if ele not in layer.keys():
            raise SolutionError(
                "The element " + str(ele) + " is not assigned in the " + str(lvar) + "variable of this "
                                                                                     "solution.")

    @staticmethod
    def is_assigned_element(lvar: str, ele: str, sol: SolStructure):
        layer: SolLayer = cast(SolLayer, sol.get(lvar))
        if ele not in layer.keys():
            raise SolutionError(
                "The element " + str(ele) + " is not assigned in the " + str(lvar) + "variable of this "
                                                                                     "solution.")

    @staticmethod
    def is_assigned_component(vvar: str, index: int, vval_size: int):
        if index < 0 or index >= vval_size:
            raise SolutionError(
                "The " + str(
                    index) + "-nh component of " + vvar + " VECTOR variable is not assigned in this solution.")

    @staticmethod
    def is_assigned_component_element(lvvar: str, index: int, ele: str, lvval: SolLayerVector):
        if ele not in lvval[index].keys():
            raise SolutionError("The element " + str(ele) + " in not assigned in the " + str(index)
                                + "-nh component of the " + str(lvvar) + " variable in this solution.")



@final
class ModChk:
    @staticmethod
    def vector_insertion_available(vvar: str, dom: Domain, vval: SolVector):
        if dom.get_remaining_available_complete_components(vvar, len(vval)) == 0:
            raise SolutionError("The " + str(vvar) + " is complete.")

    @staticmethod
    def vector_adding_available(vvar: str, rem: int):
        if rem == 0:
            raise SolutionError("The " + str(vvar) + " is complete.")

    @staticmethod
    def vector_element_adding_available(lvvar: str, lvval: SolLayerVector, dom: Domain):
        key_sizes = len(lvval[-1].keys()
                        & dom.get_layer_components_attributes(lvvar).keys())
        if key_sizes == 0:
            v_size = len(lvval)
        else:
            v_size = len(lvval) - 1
        if dom.get_remaining_available_complete_components(lvvar, v_size) == 0:
            raise SolutionError("The " + str(lvvar) + " is complete.")

    @staticmethod
    def assigned_vector_removal_available(vvar:str, vval_size: int, dom: Domain):
        r = dom.get_remaining_available_complete_components(vvar, vval_size - 1)
        if r < 0:
            raise SolutionError("The " + str(vvar) + " can not deleting.")
        return vval_size - r


@final
class SetMet:
    @staticmethod
    def set_basic_pycvoatype(value: Any, element: str | None, index: int | None):
        if isinstance(value, (int, float, str)):
            if element is None and index is not None:
                raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR.")
            elif element is not None and index is None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
        else:
            raise ValueError("The value must a BASIC value (int, float or str).")

    @staticmethod
    def set_layer_pycvoatype(value: Any, element: str | None, index: int | None) -> str:
        if isinstance(value, (int, float, str)):
            if element is None and index is None:
                raise ValueError("You are trying to set an element's value without specifying the element name.")
            if element is None and index is not None:
                raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
            else:
                res = "a"
        elif Primitives.is_layer_value(value):
            if element is None and index is not None:
                raise ValueError("You are trying to set a value of a component of a variable that is not LAYER VECTOR")
            elif element is not None and index is None:
                raise ValueError("You are trying to set an element's value with a value different from int, float, "
                                 "or str.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a component of a variable that is not "
                                 "LAYER VECTOR.")
            else:
                res = "b"
        else:
            raise ValueError("The value must be a BASIC value (int, float, or str) or a well-formed LAYER value.")
        return res

    @staticmethod
    def set_basic_vector_pycvoatype(value: Any, element: str | None, index: int | None) -> str:
        if isinstance(value, (int, float, str)):
            if element is None and index is None:
                raise ValueError("You are trying to set a component's value without specifying the target index.")
            if element is not None and index is None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER VECTOR.")
            else:
                res = "a"
        elif Primitives.is_basic_vector_value(value):
            if element is None and index is not None:
                raise ValueError(
                    "You are trying to set a value of a component of a BASIC VECTOR variable with a complete "
                    "BASIC VECTOR value.")
            elif element is not None and index is None:
                raise ValueError("You are trying to set an element's value with a value different from int, float, "
                                 "or str of a variable that is not LAYER.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a component of a variable that is not "
                                 "LAYER VECTOR.")
            else:
                res = "b"
        else:
            raise ValueError(
                "The value must be a BASIC value (int, float, or str) or a well-formed BASIC VECTOR value.")
        return res

    @staticmethod
    def set_layer_vector_pycvoatype(value: Any, element: str | None, index: int | None) -> str:
        if isinstance(value, (int, float, str)):
            if element is None and index is None:
                raise ValueError("You are trying to set a LAYER VECTOR variable with a BASIC value.")
            elif element is None and index is not None:
                raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
            elif element is not None and index is None:
                raise ValueError("You are trying to set a value of an element of a variable that is not LAYER.")
            else:
                res = "a"
        elif Primitives.is_layer_value(value):
            if element is None and index is None:
                raise ValueError("You are trying to set a LAYER VECTOR variable with a LAYER value without specifying "
                                 "the component index.")
            elif element is not None and index is None:
                raise ValueError("You are trying to set an element's value with a value different from int, float, "
                                 "or str and without specifying the component index.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a component with a value that is not "
                                 "BASIC.")
            else:
                res = "b"
        elif Primitives.is_layer_vector_value(value):
            if element is None and index is not None:
                raise ValueError("You are trying to set a value of a component of a variable that is not BASIC VECTOR")
            elif element is not None and index is None:
                raise ValueError("You are trying to set an element's value with a value different from int, float, "
                                 "or str and without specifying the component index.")
            elif element is not None and index is not None:
                raise ValueError("You are trying to set a value of an element of a component with a value that is not "
                                 "BASIC.")
            else:
                res = "c"
        else:
            raise ValueError("The value must be a BASIC value (int, float, or str) a well-formed LAYER value or a "
                             "well-formed LAYER VECTOR value.")
        return res


@final
class GetMet:
    @staticmethod
    def get_basic_pycvoatype(element: str | None, index: int | None):
        if element is None and index is not None:
            raise ValueError("You are trying to get a value of a component of a variable that is not BASIC VECTOR.")
        elif element is not None and index is None:
            raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
        elif element is not None and index is not None:
            raise ValueError("You are trying to get a value of an element of a variable that is not LAYER VECTOR.")

    @staticmethod
    def get_layer_pycvoatype(element: str | None, index: int | None) -> str:
        if element is None and index is None:
            r = "a"
        elif element is None and index is not None:
            raise ValueError("You are trying to get a value of a component of a variable that is not BASIC VECTOR")
        elif element is not None and index is None:
            r = "b"
        else:
            raise ValueError(
                "You are trying to get an element value of a component of a variable that is not LAYER VECTOR.")
        return r

    @staticmethod
    def get_basic_vector_pycvoatype(element: str | None, index: int | None) -> str:
        if element is None and index is None:
            r = "a"
        elif element is None and index is not None:
            r = "b"
        elif element is not None and index is None:
            raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
        else:
            raise ValueError(
                "You are trying to get an element value of a component of a variable that is not LAYER VECTOR.")
        return r

    @staticmethod
    def get_layer_vector_pycvoatype(element: str | None, index: int | None) -> str:
        if element is None and index is None:
            r = "a"
        elif element is None and index is not None:
            r = "b"
        elif element is not None and index is None:
            raise ValueError("You are trying to get a value of an element of a variable that is not LAYER.")
        else:
            r = "c"
        return r
