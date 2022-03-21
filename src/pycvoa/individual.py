import sys

from pycvoa.support import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, variable_definition_to_string


class ProblemDefinition:
    """ This class provides the required functionality to define a problem. The user must instantiate the class into a
    variable and, next, define the problem variables using the member methods of the class.
    """

    def __init__(self):
        self.__definitions = {}

    def register_integer_variable(self, name, min_value, max_value, step):
        """ It defines an integer variable receiving the variable name, the minimum and maximum values that it will be able
        to have, and the step size to traverse the interval.

        :param name: Variable name.
        :param min_value: Minimum value
        :param max_value: Maximum value
        :param step: Step size
        :type name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        self.__definitions[name] = [INTEGER, min_value, max_value, step]

    def register_real_variable(self, name, min_value, max_value, step):
        """ It defines a real variable receiving the variable name, the minimum and maximum values that it will be able to
        have, and the step size to traverse the interval.

        :param name: Variable name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        self.__definitions[name] = [REAL, min_value, max_value, step]

    def register_categorical_variable(self, name, categories):
        """ It defines a categorical variable receiving the variable name, and a list with the labels that it will be
        able to have.

        :param name: Variable name.
        :param categories: List of labels.
        :type name: str
        :type categories: list
        """
        self.__definitions[name] = [CATEGORICAL, categories]

    def register_layer_variable(self, name):
        """ It defines a layer variable receiving the variable name. Next, the layer elements have to be defined using the
        methods:

        - :py:meth:`~individual.ProblemDefinition.insert_layer_integer`
        - :py:meth:`~individual.ProblemDefinition.insert_layer_real`
        - :py:meth:`~individual.ProblemDefinition.insert_layer_categorical`

        :param name: Variable name.
        :type name: str
        """
        self.__definitions[name] = [LAYER, {}]

    def insert_layer_integer(self, layer_name, element_name, min_value, max_value, step):
        """ It inserts an integer element into the layer_name variable by receiving the element name, the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param layer_name: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type layer_name: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [INTEGER, min_value, max_value, step]

    def insert_layer_real(self, layer_name, element_name, min_value, max_value, step):
        """ It inserts a real element into the layer_name variable by receiving the element name, the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param layer_name: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type layer_name: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def insert_layer_categorical(self, layer_name, element_name, categories):
        """ It inserts a categorical element into the layer_name variable by receiving the element name, and a list with
        the labels that it will be able to have.

        :param layer_name: Layer variable where the new element will be inserted.
        :param element_name: Element name.
        :param categories: List of labels.
        :type layer_name: str
        :type element_name: str
        :type categories: list
        """
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    def register_vector_variable(self, name, min_size, max_size, step_size):
        """ It defines a vector variable receiving the variable name, the minimum and maximum size that it will be able
        to have, and the step size to select the size from the :math:`[min\_size, max\_size]`. Afterwards, the vector
        type must be set using the following methods:

        - :py:meth:`~individual.ProblemDefinition.set_vector_component_to_integer`
        - :py:meth:`~individual.ProblemDefinition.set_vector_component_to_real`
        - :py:meth:`~individual.ProblemDefinition.set_vector_component_to_categorical`
        - :py:meth:`~individual.ProblemDefinition.set_vector_component_to_layer`

        :param name: Variable name.
        :param min_size: Minimum size.
        :param max_size: Maximum size.
        :param step_size: Step size.
        :type name: str
        :type min_size: int
        :type max_size: int
        :type step_size: int
        """
        self.__definitions[name] = [VECTOR, min_size, max_size, step_size, {}]

    def set_vector_component_to_integer(self, vector_variable_name, min_value, max_value, step):
        """ It set the component type of the vector variable to integer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval

        :param vector_variable_name: Vector variable name previously defined.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        self.__definitions[vector_variable_name][4] = [INTEGER, min_value, max_value, step]

    def set_vector_component_to_real(self, vector_variable_name, min_value, max_value, step):
        """ It set the component type of the vector variable to real by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval

        :param vector_variable_name: Vector variable name previously defined.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        self.__definitions[vector_variable_name][4] = [REAL, min_value, max_value, step]

    def set_vector_component_to_categorical(self, vector_variable_name, categories):
        """ It set the component type of the vector variable to categorical by receiving a list with
        the labels that it will be able to have.

        :param vector_variable_name: Vector variable name previously defined.
        :param categories: List of label.
        :type vector_variable_name: str
        :type categories: list
        """
        self.__definitions[vector_variable_name][4] = [CATEGORICAL, categories]

    def set_vector_component_to_layer(self, vector_variable_name):
        """ It set the component type of the vector variable to layer. Afterwards, the components of
        the layer must be set using the methods:

        - :py:meth:`~individual.ProblemDefinition.insert_integer_in_vector_layer_component`
        - :py:meth:`~individual.ProblemDefinition.insert_real_in_vector_layer_component`
        - :py:meth:`~individual.ProblemDefinition.insert_categorical_in_vector_layer_component`

        :param vector_variable_name: Vector variable name previously defined.
        :type vector_variable_name: str
        """
        self.__definitions[vector_variable_name][4] = [LAYER, {}]

    def insert_integer_in_vector_layer_component(self, vector_variable_name, element_name, min_value, max_value, step):
        """ It defines an integer element of a vector variable set as a layer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type element_name: str
        :type min_value: int
        :type max_value: int
        :type step: int
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [INTEGER, min_value, max_value, step]

    def insert_real_in_vector_layer_component(self, vector_variable_name, element_name, min_value, max_value, step):
        """ It defines a real element of a vector variable set as a layer by receiving the minimum and
        maximum values that it will be able to have, and the step size to traverse the interval.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param min_value: Minimum value.
        :param max_value: Maximum value.
        :param step: Step size.
        :type vector_variable_name: str
        :type element_name: str
        :type min_value: float
        :type max_value: float
        :type step: float
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def insert_categorical_in_vector_layer_component(self, vector_variable_name, element_name, categories):
        """ It defines a categorical element of a vector variable set as a layer by receiving a list with
        the labels that it will be able to have.

        :param vector_variable_name: Vector variable name previously defined.
        :param element_name: Element name.
        :param categories: List of labels.
        :type vector_variable_name: str
        :type element_name: str
        :type categories: list
        """
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    def get_definition(self):
        """ Get the internal data structure for the :py:meth:`~individual.ProblemDefinition`

        :returns: Internal structure of the Problem Definition.
        :rtype: list
        :meta private:
        """
        return self.__definitions

    def __str__(self):
        res = ""
        count = 1
        for k, v in self.__definitions.items():
            res += variable_definition_to_string(k, v)
            if count != len(self.__definitions.items()):
                res += "\n"
            count += 1

        return res


class Individual:

    def __init__(self, best=True):
        self.__variables = {}
        self.discovering_iteration_time = 0
        if best:
            self.fitness = 0.0
        else:
            self.fitness = sys.float_info.max

    # Getters
    def get_variable_value(self, variable_name):
        if variable_name in self.__variables:
            return self.__variables.get(variable_name)
        else:
            raise NotDefinedVariableError("The variable " + variable_name + " is not defined")

    def get_layer_element_value(self, layer_name, element_name):
        if layer_name in self.__variables:
            layer = self.__variables.get(layer_name)
            if type(layer) is dict:
                if element_name in layer.keys():
                    return layer[element_name]
                else:
                    raise NotDefinedLayerElementError("The element " + element_name + " of the layer " +
                                                      layer_name + " is not defined")
            else:
                raise NotLayerError("The variable " + layer_name + " is not a layer")
        else:
            raise NotDefinedLayerElementError("The variable " + layer_name + " is not defined")

    def get_vector_size(self, vector_name):
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                return len(self.__variables.get(vector_name))
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    def get_vector_component_value(self, vector_name, index):
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    return vector[index]
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                         + vector_name + " is not defined")
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    def get_vector_layer_component_value(self, vector_name, index, layer_element):
        if vector_name in self.__variables:
            vector = self.__variables.get(vector_name)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    layer = vector[index]
                    if type(layer) is dict:
                        if layer_element in vector[index].keys():
                            return vector[index][layer_element]
                        else:
                            raise NotDefinedLayerElementError("The layer element " + layer_element +
                                                              " is not defined for the vector " + vector_name)
                    else:
                        raise NotLayerError(
                            "The element " + str(index) + " of the vector " + vector_name + " is not a layer")
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector " +
                                                         vector_name + " is not defined")
            else:
                raise NotVectorError("The variable " + vector_name + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vector_name + " is not defined")

    # Setters
    def set_variable_value(self, variable_name, value):
        self.__variables[variable_name] = value

    def set_layer_element_value(self, layer_name, element_name, value):
        if layer_name not in self.__variables:
            self.__variables[layer_name] = {element_name: value}
        else:
            self.__variables[layer_name][element_name] = value

    def set_vector_element_by_index(self, vector_name, index, value):
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name][index] = value

    def set_vector_layer_element_by_index(self, vector_name, index, layer_element, value):
        if vector_name in self.__variables:
            self.__variables[vector_name][index][layer_element] = value

    def add_vector_element(self, vector_name, value):
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name].append(value)

    def add_vector_element_by_index(self, vector_name, index, value):
        if vector_name not in self.__variables:
            self.__variables[vector_name] = [value]
        else:
            self.__variables[vector_name].insert(index, value)

    def remove_vector_element(self, vector_name):
        self.__variables[vector_name].pop()

    def remove_vector_element_by_index(self, vector_name, index):
        del self.__variables[vector_name][index]

    def __str__(self):
        res = "F = " + str(self.fitness) + "\t{"
        count = 1
        for variable in sorted(self.__variables):
            res += str(variable) + " = " + str(self.__variables[variable])
            if count < len(self.__variables):
                res += " , "
            count += 1
        res += "}"
        return res

    def __eq__(self, other):
        res = True

        if not isinstance(other, Individual):
            res = False
        else:
            i = 0
            keys = list(self.__variables.keys())
            while i < len(keys) & res:
                vf = self.get_variable_value(keys[i])
                vo = other.get_variable_value(keys[i])
                if vf != vo:
                    res = False
                i += 1

        return res

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.__variables.__hash__, self.fitness))

    def __lt__(self, other):
        return self.fitness < other.fitness

    def __le__(self, other):
        return self.fitness <= other.fitness

    def __gt__(self, other):
        return self.fitness > other.fitness

    def __ge__(self, other):
        return self.fitness >= other.fitness


class IndividualError(Exception):
    pass


class NotDefinedVariableError(IndividualError):
    def __init__(self, message):
        self.message = message


class NotDefinedLayerElementError(IndividualError):
    def __init__(self, message):
        self.message = message


class NotLayerError(IndividualError):
    def __init__(self, message):
        self.message = message


class NotVectorError(IndividualError):
    def __init__(self, message):
        self.message = message


class NotDefinedVectorComponentError(IndividualError):
    def __init__(self, message):
        self.message = message
