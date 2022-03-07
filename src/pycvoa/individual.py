import sys

from pycvoa.support import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, variable_definition_to_string


class ProblemDefinition:

    def __init__(self):
        self.__definitions = {}

    # Registration methods for simple variables
    def register_integer_variable(self, name, min_value, max_value, step):
        self.__definitions[name] = [INTEGER, min_value, max_value, step]

    def register_real_variable(self, name, min_value, max_value, step):
        self.__definitions[name] = [REAL, min_value, max_value, step]

    def register_categorical_variable(self, name, categories):
        self.__definitions[name] = [CATEGORICAL, categories]

    # Registration method for layer variables
    def register_layer_variable(self, name):
        self.__definitions[name] = [LAYER, {}]

    def insert_layer_integer(self, layer_name, element_name, min_value, max_value, step):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [INTEGER, min_value, max_value, step]

    def insert_layer_real(self, layer_name, element_name, min_value, max_value, step):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def insert_layer_categorical(self, layer_name, element_name, categories):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    # Registration method for vector variables
    def register_vector_variable(self, name, min_size, max_size, step_size):
        self.__definitions[name] = [VECTOR, min_size, max_size, step_size, {}]

    def set_vector_component_to_integer(self, vector_variable_name, min_value, max_value, step):
        self.__definitions[vector_variable_name][4] = [INTEGER, min_value, max_value, step]

    def set_vector_component_to_real(self, vector_variable_name, min_value, max_value, step):
        self.__definitions[vector_variable_name][4] = [REAL, min_value, max_value, step]

    def set_vector_component_to_categorical(self, vector_variable_name, categories):
        self.__definitions[vector_variable_name][4] = [CATEGORICAL, categories]

    def set_vector_component_to_layer(self, vector_variable_name):
        self.__definitions[vector_variable_name][4] = [LAYER, {}]

    def insert_integer_in_vector_layer_component(self, vector_variable_name, element_name, min_value, max_value, step):
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [INTEGER, min_value, max_value, step]

    def insert_real_in_vector_layer_component(self, vector_variable_name, element_name, min_value, max_value, step):
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [REAL, min_value, max_value, step]

    def insert_categorical_in_vector_layer_component(self, vector_variable_name, element_name, categories):
        layer_definition = self.__definitions[vector_variable_name][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    def get_definition(self):
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
