from __future__ import annotations

import metagen.framework.solution as types
from metagen.framework import BaseConnector, Solution
from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                      IntegerDefinition, RealDefinition,
                                      StaticStructureDefinition, DynamicStructureDefinition)
from scipy.stats import norm
import numpy as np

def sample_from_values(tpe_type, best_values, worst_values):
    _, min_value, max_value, step = tpe_type.get_definition().get_attributes()
    step = step or 1

    mu_best, sigma_best = norm.fit(best_values)
    mu_worst, sigma_worst = norm.fit(worst_values)

    value = 0

    if sigma_best > 0 and sigma_worst > 0:

        p_best = norm.pdf(tpe_type.value, mu_best, sigma_best)
        p_worst = norm.pdf(tpe_type.value, mu_worst, sigma_worst)
    
        if p_best / (p_best + p_worst + 1e-16) > np.random.rand():
            value = np.clip(np.random.normal(mu_best, sigma_best), min_value, max_value).item()
        else:
            value = np.clip(np.random.normal(mu_worst, sigma_worst), min_value, max_value).item()
    else:
        value = np.random.uniform(min_value, max_value + 1)

    return value

class TPEInteger(types.Integer):
    """
    The Integer class inherits from the BaseType class and represents an integer variable.

    :param definition: An instance of `IntegerDefinition` class representing the definition of the categorical variable.
    :type definition: `IntegerDefinition`
    """

    def resample(self, best_values, worst_values):
        """
        Modify the value of this Integer instance to a rs category from its definition.
        """
        _, min_value, max_value, _ = self.get_definition().get_attributes()

        best_values = [val.value for val in best_values]
        worst_values = [val.value for val in worst_values]

        value = round(sample_from_values(self, best_values, worst_values))

        if np.isnan(value) or value is None:
            value = np.random.randint(min_value, max_value + 1)
        
        self.value = value

class TPEReal(types.Real):
    """

    """

    def resample(self, best_values, worst_values):
        """
        """
        best_values = [val.value for val in best_values]
        worst_values = [val.value for val in worst_values]


        _, min_value, max_value, _ = self.get_definition().get_attributes()
        value = sample_from_values(self, best_values, worst_values)
        if np.isnan(value) or value is None:
            value = np.random.uniform(min_value, max_value + 1)
        
        self.value = value

class TPECategorical(types.Categorical):
    """

    """

    def resample(self, best_values, worst_values):
        """
        """
        best_values = [val.value for val in best_values]
        _, categories = self.get_definition().get_attributes()
        unique, counts = np.unique(best_values, return_counts=True)
        probabilities = counts / counts.sum() if len(unique) > 1 else None

        self.value = np.random.choice(unique,p=probabilities) if probabilities is not None else np.random.choice(categories)

class TPEStructure(types.Structure):
    """
    Represents the custom Structure type for the Genetic Algorithm (GA).
    
    This class extends the base Structure type to add genetic algorithm specific operations
    like crossover.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def resample(self, best_values, worst_values):
        """
        """
        for i in range(len(self)):
            self.get(i).resample([val.get(i) for val in best_values], [val.get(i) for val in  worst_values])

class TPESolution(Solution):
    """
    Represents a Solution type for the Genetic Algorithm (GA).

    This class extends the base Solution type to add genetic algorithm specific operations
    like crossover between solutions.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def resample(self, best_solutions, worst_solutions):
        """
        Performs crossover operation with another GASolution instance.

        :param other: Another GASolution instance to perform crossover with
        :type other: GASolution
        :return: A tuple containing two new GASolution instances (children)
        :rtype: Tuple[GASolution, GASolution]
        :raises AssertionError: If the solutions have different variable keys
        """

        for variable_name, variable_value in self.get_variables().items():
            best_values = [sol.get(variable_name) for sol in best_solutions]
            worst_values = [sol.get(variable_name) for sol in worst_solutions]

            variable_value.resample(best_values, worst_values)


class TPEConnector(BaseConnector):
    """
    Represents the custom Connector for the Genetic Algorithm (GA).

    This connector links the following classes:
    * BaseDefinition - GASolution - dict
    * IntegerDefinition - types.Integer - int
    * RealDefinition - types.Real - float
    * CategoricalDefinition - types.Categorical - str
    * StaticStructureDefinition - GAStructure - list

    The Solution and Structure original classes have been replaced by custom GA classes.
    When instantiating a StaticStructureDefinition, the GAStructure will be employed.
    """

    def __init__(self) -> None:
        """
        Initialize the GAConnector with predefined type mappings for GA operations.
        """
        super().__init__()

        self.register(BaseDefinition, TPESolution, dict)
        self.register(IntegerDefinition, TPEInteger, int)
        self.register(RealDefinition, TPEReal, float)
        self.register(CategoricalDefinition, TPECategorical, str)
        self.register(StaticStructureDefinition, (TPEStructure, "static"), list)
        self.register(DynamicStructureDefinition, (TPEStructure, "dynamic"), list)