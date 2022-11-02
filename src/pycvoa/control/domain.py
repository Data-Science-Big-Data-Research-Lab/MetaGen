import math
from typing import final, cast, Union, Any

from pycvoa.control import DefinitionError
from pycvoa.control.types import LayerDef, DefStructure, LAYER, PYCVOA_TYPE, ArgChk, LayerAttributes, VectorDef, \
    VectorValue, VectorInput, VECTOR, Primitives


@final
class RngChk:
    @staticmethod
    def check_integer_range_step(min_value: int, max_value: int, step: int | None, case: str):
        RngChk.__check_range(min_value, max_value, case)
        return RngChk.__check_int_step(min_value, max_value, step, case)

    @staticmethod
    def check_real_range_step(min_value: float, max_value: float, step: float | None, case: str):
        RngChk.__check_range(min_value, max_value, case)
        return RngChk.__check_float_step(min_value, max_value, step, case)

    @staticmethod
    def __check_range(min_value, max_value, case: str):
        """ It checks if min_value < max_value, if not, raise :py:class:`~pycvoa.problem.domain.DefinitionError`.
        If the first condition is fulfilled, it checks if step < (max_value-min_value) / 2, if not, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param min_value: The minimum value.
        :param max_value: The maximum value.
        :param case: The step.
        :type min_value: int, float
        :type max_value: int, float
        :type case: int, float
        """
        if min_value >= max_value:
            msg = ""
            if case == "a":
                msg = "The minimum value of the variable (" + str(min_value) \
                      + ") must be less than the maximum one (" + str(max_value) + ")."
            elif case == "b":
                msg = "The minimum value of the element (" + str(min_value) \
                      + ") must be less than the maximum one (" + str(max_value) + ")."
            elif case == "c":
                msg = "The minimum size of the VECTOR variable (" + str(min_value) \
                      + ") must be less than the maximum one (" + str(max_value) + ")."
            raise ValueError(msg)

    @staticmethod
    def __check_int_step(min_value: int, max_value: int, step: int | None, case: str) -> int:
        average = math.floor((max_value - min_value) / 2)
        if step is not None:
            if step > average:
                msg = ""
                if case == "a":
                    msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                           "(maximum value - minimum value) / 2 (" + str(average) + ")."
                elif case == "b":
                    msg = "The step value (" + str(step) + ") of the element must be less or equal than" \
                                                           "(maximum value - minimum value) / 2 (" + str(average) + ")."
                elif case == "c":
                    msg = "The step size (" + str(step) + ") of the VECTOR variable must be less or equal than " \
                                                          "(maximum size - minimum size) / 2 ( " + str(average) + ")."

                raise ValueError(msg)
            else:
                r = step
        else:
            r = average
        return r

    @staticmethod
    def __check_float_step(min_value: float, max_value: float, step: float | None, case: str) -> float:
        average = (max_value - min_value) / 2
        if step is not None:
            if step > average:
                msg = ""
                if case == "a":
                    msg = "The step value (" + str(step) + ") of the variable must be less or equal than " \
                                                           "(maximum value - minimum value) / 2 (" + str(average) + ")."
                elif case == "b":
                    msg = "The step value (" + str(step) + ") of the element must be less or equal than " \
                                                           "(maximum value - minimum value) / 2 (" + str(average) + ")."
                raise ValueError(msg)
            else:
                r = step
        else:
            r = average
        return r


@final
class VarDef:
    @staticmethod
    def is_defined_variable(variable: str, definitions: DefStructure):
        """ It checks if a variable is defined in the domain, if not, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param variable: The variable.
        :param definitions: The definitions.
        :type variable: str
        """
        if variable not in definitions.keys():
            raise DefinitionError("The variable " + variable + " is not defined in this domain.")

    @staticmethod
    def not_defined_variable(variable_name: str, definitions: DefStructure):
        """ It checks if a variable name is already used in the domain, if yes, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param variable_name: The variable name.
        :param definitions: The definitions.
        :type variable_name: str
        """
        if variable_name in definitions.keys():
            raise DefinitionError(
                "The " + variable_name + " variable is already defined, please, select another variable "
                                         "name.")

    @staticmethod
    def is_defined_variable_as_type(variable: str, definitions: DefStructure, variable_type: PYCVOA_TYPE):
        """ It checks if a variable is defined in the domain, if not, raise
            py:class:`~pycvoa.problem.domain.DefinitionError`.

            If the first condition is fulfilled, it checks if a variable is defined as a variable type, if not, raise
            py:class:`~pycvoa.problem.domain.WrongItemType`.

            :param variable: The variable.
            :param variable_type: The variable type.
            :param definitions: The definitions.
            :type variable: str
            :type variable_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
            """
        VarDef.is_defined_variable(variable, definitions)
        if ArgChk.check_item_type(variable_type, definitions[variable][0]) is False:
            raise DefinitionError("The " + variable + " variable is not defined as " + str(variable_type) + ".")


@final
class LayDef:
    @staticmethod
    def is_defined_element(layer_variable: str, element: str | None, layer_definition: LayerDef):
        """ It checks if an element is defined in a **LAYER** variable, if not, raise
        py:class:`~pycvoa.problem.domain.NotDefinedItem`.

        :param layer_variable: The variable.
        :param element: The element.
        :param layer_definition: The definitions.
        :type layer_variable: str
        :type element: str
        """
        if element not in layer_definition[1].keys():
            raise DefinitionError(
                "The element " + str(element) + " is not defined in the LAYER variable " + layer_variable + ".")

    @staticmethod
    def is_defined_layer_without_element(layer_variable: str, element: str, definitions: DefStructure):
        VarDef.is_defined_variable_as_type(layer_variable, definitions, LAYER)
        if element in cast(LayerDef, definitions[layer_variable])[1].keys():
            raise DefinitionError(
                "The " + element + " element is already defined in the LAYER variable " + layer_variable
                + ". Please, select another element name.")

    @staticmethod
    def is_defined_layer_with_element(layer_variable: str, element: str, definitions: DefStructure):
        VarDef.is_defined_variable_as_type(layer_variable, definitions, LAYER)
        LayDef.is_defined_element(layer_variable, element, cast(LayerDef, definitions[layer_variable]))

    @staticmethod
    def is_defined_layer_and_element_as_type(layer_variable: str, element: str, definitions: DefStructure,
                                             check_type: PYCVOA_TYPE):
        VarDef.is_defined_variable_as_type(layer_variable, definitions, LAYER)
        LayDef.is_defined_element(layer_variable, element, cast(LayerDef, definitions[layer_variable]))
        if ArgChk.check_item_type(check_type,
                                  cast(LayerAttributes, cast(LayerDef, definitions[layer_variable])[1])[element][
                                      0]) is False:
            raise DefinitionError("The element " + element + " is not defined as "
                                  + str(check_type) + " type in " + layer_variable + ".")


@final
class VecDef:
    @staticmethod
    def are_defined_components(vector_variable: str, vector_definition: VectorDef):
        """ It checks if the type of a **VECTOR** variable is already defined, if yes, raise
        py:class:`~pycvoa.problem.domain.DefinitionError`.

        :param vector_variable: The variable.
        :param vector_definition: The definitions.
        :type vector_variable: str
        """
        if vector_definition[4] is None:
            raise DefinitionError(
                "The components of " + vector_variable + " are not defined.")

    @staticmethod
    def check_vector_values_size(vector_variable: str, vector_definition: VectorDef,
                                 values: Union[VectorValue, VectorInput]):
        if len(values) < vector_definition[1] or len(values) > vector_definition[2]:
            raise DefinitionError(
                "The size of the values (" + str(len(values)) + ") is not compatible with the " + str(
                    vector_variable) + " definition [" + str(vector_definition[1])
                + "," + str(vector_definition[2]) + "].")

    @staticmethod
    def check_component_type(vector_variable: str, vector_definition: VectorDef, check_type: PYCVOA_TYPE):
        """ It checks if the components of a **VECTOR** variable are defined as a concrete type, if not, raise
        py:class:`~pycvoa.problem.domain.WrongItemType`.

        :param vector_variable: The **VECTOR** variable.
        :param check_type: The component type.
        :param vector_definition: The definitions.
        :type vector_variable: str
        :type check_type: **INTEGER**, **REAL**, **CATEGORICAL**, **BASIC**, **LAYER**, **VECTOR**
        """
        assert vector_definition[4] is not None
        if ArgChk.check_item_type(check_type, vector_definition[4][0]) is False:
            raise DefinitionError(
                "The components of the VECTOR variable " + vector_variable + " are not defined as " + str(check_type)
                + " type.")

    @staticmethod
    def is_defined_vector_without_components(vector_variable: str, definitions: DefStructure):
        VarDef.is_defined_variable_as_type(vector_variable, definitions, VECTOR)
        vdef: VectorDef = cast(VectorDef, definitions[vector_variable])
        if vdef[4] is not None:
            raise DefinitionError(
                "The " + vector_variable + " components are already defined as " + vdef[4][0] + ".")

    @staticmethod
    def is_defined_vector_with_components(vector_variable: str, definitions: DefStructure):
        VarDef.is_defined_variable_as_type(vector_variable, definitions, VECTOR)
        VecDef.are_defined_components(vector_variable, cast(VectorDef, definitions[vector_variable]))

    @staticmethod
    def is_defined_vector_and_components_as_type(vector_variable: str, definitions: DefStructure,
                                                 check_type: PYCVOA_TYPE):
        VarDef.is_defined_variable_as_type(vector_variable, definitions, VECTOR)
        vdef: VectorDef = cast(VectorDef, definitions[vector_variable])
        VecDef.are_defined_components(vector_variable, vdef)
        VecDef.check_component_type(vector_variable, vdef, check_type)

    @staticmethod
    def is_defined_component_element(layer_vector_variable: str, element: str, layer_vector_definition: VectorDef):
        """ It checks if an element is defined in the **LAYER** components of a **VECTOR** variable, if not, raise
        py:class:`~pycvoa.problem.domain.NotDefinedItem`.

        :param layer_vector_variable: The variable.
        :param element: The element.
        :param layer_vector_definition: The definitions.
        :type layer_vector_variable: str
        :type element: str
        """
        if element not in cast(LayerDef, layer_vector_definition[4])[1].keys():
            raise DefinitionError(
                "The element " + str(element) + " is not defined in the LAYER components of the "
                + str(layer_vector_variable) + " VECTOR variable.")

    @staticmethod
    def is_defined_layer_vector_without_element(layer_vector_variable: str, element: str, definitions: DefStructure):
        VecDef.is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
        if element in cast(LayerDef, cast(VectorDef, definitions[layer_vector_variable])[4])[1].keys():
            raise DefinitionError(
                "The " + element + " element is already defined in the LAYER components of the "
                + layer_vector_variable + " VECTOR variable, please, select another element name.")

    @staticmethod
    def is_defined_layer_vector_with_element(layer_vector_variable: str, element: str, definitions: DefStructure):
        VecDef.is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
        VecDef.is_defined_component_element(layer_vector_variable, element,
                                            cast(VectorDef, definitions[layer_vector_variable]))

    @staticmethod
    def is_defined_layer_vector_and_component_element(layer_vector_variable: str, element: str,
                                                      definitions: DefStructure):
        VecDef.is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
        VecDef.is_defined_component_element(layer_vector_variable, element,
                                            cast(VectorDef, definitions[layer_vector_variable]))

    @staticmethod
    def is_defined_layer_vector_and_component_element_as_type(layer_vector_variable: str, element: str,
                                                              definitions: DefStructure, check_type: PYCVOA_TYPE):
        VecDef.is_defined_vector_and_components_as_type(layer_vector_variable, definitions, LAYER)
        lvdef: VectorDef = cast(VectorDef, definitions[layer_vector_variable])
        VecDef.is_defined_component_element(layer_vector_variable, element,
                                            cast(VectorDef, definitions[layer_vector_variable]))
        if ArgChk.check_item_type(check_type, cast(LayerDef, lvdef[4])[1][element][0]) is False:
            raise DefinitionError(
                "The element " + element + " of the LAYER VECTOR variable " + layer_vector_variable
                + " are not defined as " + check_type + " type.")


@final
class ChkMet:
    @staticmethod
    def check_basic_pycvoatype(element: str | None):
        if element is not None:
            raise ValueError("You are trying to check a value of an element of a variable that is not LAYER or LAYER.")

    @staticmethod
    def check_layer_pycvoatype(value: Any, element: str | None) -> str:
        res = "f"
        if isinstance(value, (int, float, str)):
            if element is None:
                raise ValueError("You are trying to check an element's value without specifying the element name.")
            else:
                res = "a"
        elif Primitives.is_layer_value(value):
            if element is not None:
                raise ValueError(
                    "You are trying to check an element's value with a value different from int, float, or str.")
            else:
                res = "b"
        return res

    @staticmethod
    def check_basic_vector_pycvoatype(value: Any, element: str | None) -> str:
        res = "f"
        if isinstance(value, (int, float, str)):
            if element is not None:
                raise ValueError(
                    "You are trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.")
            else:
                res = "a"
        elif Primitives.is_basic_vector_value(value):
            if element is not None:
                raise ValueError(
                    "You are trying to check a value of an element of a variable that is not LAYER or LAYER VECTOR.")
            else:
                res = "b"
        return res

    @staticmethod
    def check_layer_vector_pycvoatype(value: Any, element: str | None) -> str:
        res = "f"
        if isinstance(value, (int, float, str)):
            if element is None:
                raise ValueError("You are trying to check an element's value without specifying the element name.")
            else:
                res = "a"
        elif Primitives.is_layer_value(value):
            if element is not None:
                raise ValueError("You are trying to check an element's value with a value different from int, float, "
                                 "or str.")
            else:
                res = "b"
        elif Primitives.is_layer_vector_value(value):
            if element is not None:
                raise ValueError("You are trying to check an element's value with a value different from int, float, "
                                 "or str.")
            else:
                res = "c"
        return res
