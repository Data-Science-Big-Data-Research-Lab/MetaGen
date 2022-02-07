import sys

from cvoa.support import INTEGER, REAL, CATEGORICAL, LAYER, VECTOR, variable_definition_to_string


class ProblemDefinition:

    def __init__(self):
        self.__definitions = {}

    # Registration methods for simple variables
    def register_integer_variable(self, name, minValue, maxValue, step):
        self.__definitions[name] = [INTEGER, minValue, maxValue, step]

    def register_real_variable(self, name, minValue, maxValue, step):
        self.__definitions[name] = [REAL, minValue, maxValue, step]

    def register_categorical_variable(self, name, categories):
        self.__definitions[name] = [CATEGORICAL, categories]

    # Registration method for layer variables
    def register_layer_variable(self, name):
        self.__definitions[name] = [LAYER, {}]

    def insert_layer_integer(self, layer_name, element_name, minValue, maxValue, step):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [INTEGER, minValue, maxValue, step]

    def insert_layer_real(self, layer_name, element_name, minValue, maxValue, step):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [REAL, minValue, maxValue, step]

    def insert_layer_categorical(self, layer_name, element_name, categories):
        layer_elements = self.__definitions[layer_name][1]
        layer_elements[element_name] = [CATEGORICAL, categories]

    # Registration method for vector variables
    def register_vector_variable(self, name, minSize, maxSize, stepSize):
        self.__definitions[name] = [VECTOR, minSize, maxSize, stepSize, {}]

    def set_vector_component_to_integer(self, vectorVariableName, minValue, maxValue, step):
        self.__definitions[vectorVariableName][4] = [INTEGER, minValue, maxValue, step]

    def set_vector_component_to_real(self, vectorVariableName, minValue, maxValue, step):
        self.__definitions[vectorVariableName][4] = [REAL, minValue, maxValue, step]

    def set_vector_component_to_categorical(self, vectorVariableName, categories):
        self.__definitions[vectorVariableName][4] = [CATEGORICAL, categories]

    def set_vector_component_to_layer(self, vectorVariableName):
        self.__definitions[vectorVariableName][4] = [LAYER, {}]

    def insert_integer_in_vector_layer_component(self, vectorVariableName, element_name, minValue, maxValue, step):
        layer_definition = self.__definitions[vectorVariableName][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [INTEGER, minValue, maxValue, step]

    def insert_real_in_vector_layer_component(self, vectorVariableName, element_name, minValue, maxValue, step):
        layer_definition = self.__definitions[vectorVariableName][4]
        layer_elements = layer_definition[1]
        layer_elements[element_name] = [REAL, minValue, maxValue, step]

    def insert_categorical_in_vector_layer_component(self, vectorVariableName, element_name, categories):
        layer_definition = self.__definitions[vectorVariableName][4]
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
    def get_variable_value(self, variableName):
        if variableName in self.__variables:
            return self.__variables.get(variableName)
        else:
            raise NotDefinedVariableError("The variable " + variableName + " is not defined")

    def get_layer_element_value(self, layerName, elementName):
        if layerName in self.__variables:
            layer = self.__variables.get(layerName)
            if type(layer) is dict:
                if elementName in layer.keys():
                    return layer[elementName]
                else:
                    raise NotDefinedLayerElementError("The element " + elementName + " of the layer " +
                                                      layerName + " is not defined")
            else:
                raise NotLayerError("The variable " + layerName + " is not a layer")
        else:
            raise NotDefinedLayerElementError("The variable " + layerName + " is not defined")

    def get_vector_size(self, vectorName):
        if vectorName in self.__variables:
            vector = self.__variables.get(vectorName)
            if type(vector) is list:
                return len(self.__variables.get(vectorName))
            else:
                raise NotVectorError("The variable " + vectorName + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vectorName + " is not defined")

    def get_vector_component_value(self, vectorName, index):
        if vectorName in self.__variables:
            vector = self.__variables.get(vectorName)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    return vector[index]
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector "
                                                         + vectorName + " is not defined")
            else:
                raise NotVectorError("The variable " + vectorName + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vectorName + " is not defined")

    def get_vector_layer_component_value(self, vectorName, index, layerElement):
        if vectorName in self.__variables:
            vector = self.__variables.get(vectorName)
            if type(vector) is list:
                if 0 <= index < len(vector):
                    layer = vector[index]
                    if type(layer) is dict:
                        if layerElement in vector[index].keys():
                            return vector[index][layerElement]
                        else:
                            raise NotDefinedLayerElementError("The layer element " + layerElement +
                                                              " is not defined for the vector " + vectorName)
                    else:
                        raise NotLayerError(
                            "The element " + str(index) + " of the vector " + vectorName + " is not a layer")
                else:
                    raise NotDefinedVectorComponentError("The component " + str(index) + " of the vector " +
                                                         vectorName + " is not defined")
            else:
                raise NotVectorError("The variable " + vectorName + " is not a vector")
        else:
            raise NotDefinedVariableError("The variable " + vectorName + " is not defined")

    # Setters
    def set_variable_value(self, variableName, value):
        self.__variables[variableName] = value

    def set_layer_element_value(self, layerName, elementName, value):
        if layerName not in self.__variables:
            self.__variables[layerName] = {elementName: value}
        else:
            self.__variables[layerName][elementName] = value

    def set_vector_element_by_index(self, vectorName, index, value):
        if vectorName not in self.__variables:
            self.__variables[vectorName] = [value]
        else:
            self.__variables[vectorName][index] = value

    def set_vector_layer_element_by_index(self, vectorName, index, layer_element, value):
        if vectorName in self.__variables:
            self.__variables[vectorName][index][layer_element] = value

    def add_vector_element(self, vectorName, value):
        if vectorName not in self.__variables:
            self.__variables[vectorName] = [value]
        else:
            self.__variables[vectorName].append(value)

    def add_vector_element_by_index(self, vectorName, index, value):
        if vectorName not in self.__variables:
            self.__variables[vectorName] = [value]
        else:
            self.__variables[vectorName].insert(index, value)

    def remove_vector_element(self, vectorName):
        self.__variables[vectorName].pop()

    def remove_vector_element_by_index(self, vectorName, index):
        del self.__variables[vectorName][index]

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
