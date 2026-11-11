from __future__ import annotations

import math
from functools import lru_cache
from typing import Tuple

import metagen.framework.solution as types
from metagen.framework import BaseConnector, Solution
from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                      IntegerDefinition, PermutationDefinition, RealDefinition,
                                      StaticStructureDefinition, DynamicStructureDefinition,
                                      SubsetDefinition)
from scipy.stats import norm
import numpy as np
from metagen.framework.rng import get_numpy_rng
from metagen.metaheuristics.tpe.subset_model import SubsetModel

def _on_grid(value: float, low: float, high: float, step: float | None) -> float:
    """
    The point of the grid of a variable with a step nearest to a value, never past the last
    one inside the range; the value itself without a step.

    :param value: The value drawn from the model.
    :param low: The minimum of the variable, where its grid starts.
    :param high: The maximum of the variable.
    :param step: The step of the variable, or None.
    :return: The point of the grid, or the value.
    """
    # The model draws on a continuous line, and the step was left out: TPE evaluated and
    # returned points that were not in the domain (F-62). No draw is added, so a variable
    # without a step gets exactly what it got before.
    if step is None:
        return value
    last = math.floor((high - low) / step + 1e-9)
    return min(max(low + min(max(round((value - low) / step), 0), last) * step, low), high)


def sample_from_values(tpe_type, best_values, worst_values):
    _, min_value, max_value, step = tpe_type.get_definition().get_attributes()
    if tpe_type.get_definition().log:
        # On a logarithmic scale the model is fitted and sampled on the logarithms.
        drawn = np.exp(_sample(np.log(tpe_type.value), np.log(best_values), np.log(worst_values),
                               np.log(min_value), np.log(max_value)))
        return float(min(max(drawn, min_value), max_value))
    return _sample(tpe_type.value, best_values, worst_values, min_value, max_value)


#: The normalizing constant of the normal density, as scipy computes it.
_NORM_PDF_C = math.sqrt(2 * math.pi)


@lru_cache(maxsize=1024)
def _fit(values: Tuple[float, ...]) -> Tuple[float, float]:
    """The mean and the standard deviation of the values, as ``scipy.stats.norm.fit`` gives them."""
    # Every candidate of an iteration fitted the same values again, for every variable and
    # side: fitted once, the result is the same (E-02,
    # metagen-auditoria/auditoria-independiente-2026-11/eficiencia.md).
    return norm.fit(values)


def _pdf(x: float, loc: float, scale: float) -> float:
    """
    The normal density at ``x``, with the operations of ``scipy.stats.norm.pdf`` in its order,
    on an array of one element as scipy does: the same value, bit for bit.
    """
    # The generic machinery of scipy.stats took most of the time of an iteration for a
    # single number (E-02). Checked equal to norm.pdf on 200 000 values and on seeded runs.
    y = np.asarray([(np.asarray(x) - loc) / scale], dtype=np.float64)
    return float((np.exp(-y ** 2 / 2.0) / _NORM_PDF_C / scale)[0])


def _sample(current, best_values, worst_values, min_value, max_value):

    mu_best, sigma_best = _fit(tuple(best_values))
    mu_worst, sigma_worst = _fit(tuple(worst_values))

    value = 0

    if sigma_best > 0 and sigma_worst > 0:

        p_best = _pdf(current, mu_best, sigma_best)
        p_worst = _pdf(current, mu_worst, sigma_worst)
    
        if p_best / (p_best + p_worst + 1e-16) > get_numpy_rng().random():
            value = np.clip(get_numpy_rng().normal(mu_best, sigma_best), min_value, max_value).item()
        else:
            value = np.clip(get_numpy_rng().normal(mu_worst, sigma_worst), min_value, max_value).item()
    else:
        # max_value, not max_value + 1: that +1 belongs to numpy's integers(), whose
        # upper bound is exclusive. On a uniform draw it just reached past the domain
        # (F-22).
        value = get_numpy_rng().uniform(min_value, max_value)

    return float(value)

class TPEInteger(types.Integer):
    """
    The Integer class inherits from the BaseType class and represents an integer variable.

    :param definition: An instance of `IntegerDefinition` class representing the definition of the categorical variable.
    :type definition: `IntegerDefinition`
    """

    def resample(self, best_values, worst_values):
        """
        Modify the value of this Integer instance to a random category from its definition.
        """
        _, min_value, max_value, step = self.get_definition().get_attributes()

        best_values = [val.value for val in best_values]
        worst_values = [val.value for val in worst_values]

        value = sample_from_values(self, best_values, worst_values)

        # `value is None` first: np.isnan(None) raises TypeError, so the guard could
        # never have caught a None (F-22).
        if value is None or np.isnan(value):
            # +1 is right here: numpy's integers() excludes its upper bound.
            value = get_numpy_rng().integers(min_value, max_value + 1)

        # set(), not self.value: assigning straight to the attribute skipped check()
        # and let an out-of-domain value reach the user's fitness function (F-22).
        self.set(int(round(float(_on_grid(float(value), min_value, max_value, step)))))

class TPEReal(types.Real):
    """

    """

    def resample(self, best_values, worst_values):
        """
        """
        best_values = [val.value for val in best_values]
        worst_values = [val.value for val in worst_values]


        _, min_value, max_value, step = self.get_definition().get_attributes()
        value = sample_from_values(self, best_values, worst_values)
        if value is None or np.isnan(value):
            value = get_numpy_rng().uniform(min_value, max_value)

        self.set(float(_on_grid(float(value), min_value, max_value, step)))

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

        elegida = (get_numpy_rng().choice(unique, p=probabilities)
                   if probabilities is not None
                   else get_numpy_rng().choice(categories))

        # .item(), so the user gets a str and not a numpy.str_ (F-22).
        self.set(elegida.item() if hasattr(elegida, "item") else elegida)

class TPEPermutation(types.Permutation):
    """
    The permutation type TPE resamples. An ordering has no density to fit, so a new one
    is the ordering of one of the best reference solutions, drawn at random, moved by
    one swap.
    """

    def resample(self, best_values, worst_values):
        """
        Take the ordering of one of the best references and swap two of its positions.

        :param best_values: The permutations of the best reference solutions.
        :param worst_values: The permutations of the worst ones, not used.
        """
        chosen = best_values[int(get_numpy_rng().integers(len(best_values)))]
        self.set(list(chosen.get()))
        self.mutate(alteration_limit=1)



class TPESubset(types.Subset):
    """
    The subset type TPE resamples: every element in with the probability it has among
    the best reference solutions, together with a prior worth one of them.
    """

    def resample(self, best_values, worst_values):
        """
        Draw a selection from the inclusion probabilities of the best references.

        :param best_values: The subsets of the best reference solutions.
        :param worst_values: The subsets of the worst ones, not used.
        """
        model = SubsetModel(self.get_definition(), [value.get() for value in best_values], 1.0)
        self.set(model.draw())

class TPEStructure(types.Structure):
    """
    The Structure type TPE resamples position by position.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def resample(self, best_values, worst_values):
        """
        Resample every position from the reference structures that have it.

        With a dynamic structure the references come in different lengths, so each
        position is resampled from the references long enough to have it. A position
        no reference reaches keeps the value it was initialized with.

        The length itself is not resampled: a new structure keeps the length it was
        born with, drawn uniformly by initialize().

        :param best_values: The structures of the best reference solutions.
        :param worst_values: The structures of the worst reference solutions.
        """
        # F-35: this used to ask every reference for every one of its own positions, so
        # the first reference shorter than itself raised IndexError. Modeling the length
        # with TPE's own rule was measured on the variable-degree polynomial problem and
        # was not distinguishable from this -- 17 wins of 20 against 16 -- so the
        # sampling rule stays as it is.
        for i in range(len(self)):
            best = [val.get(i) for val in best_values if i < len(val)]
            worst = [val.get(i) for val in worst_values if i < len(val)]
            if best and worst:
                self.get(i).resample(best, worst)

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
            # A conditional variable is modeled only from the solutions in which it was
            # active; its values elsewhere meant nothing.
            best_values = [sol.get(variable_name) for sol in best_solutions if sol.is_active(variable_name)]
            worst_values = [sol.get(variable_name) for sol in worst_solutions if sol.is_active(variable_name)]
            if not best_values or not worst_values:
                continue

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
        self.register(PermutationDefinition, TPEPermutation, tuple)
        self.register(SubsetDefinition, TPESubset, frozenset)