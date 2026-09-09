"""
    Copyright (C) 2023 David Gutierrez Avilés and Manuel Jesús Jiménez Navarro

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from copy import deepcopy
from typing import Any, Protocol, Tuple, List, cast

import metagen.framework.solution as types
from metagen.framework import BaseConnector, Solution, Domain
from metagen.framework.domain import (BaseDefinition, CategoricalDefinition,
                                      DynamicStructureDefinition,
                                      IntegerDefinition, RealDefinition,
                                      StaticStructureDefinition)
from metagen.framework.rng import get_rng

class Crossable(Protocol):
    """
    What GASolution.crossover asks of a variable: that it knows how to cross over.

    It is a capability and not a class on purpose -- the connector is the extension
    point, and a user's own type with its own operator qualifies (A-07) -- so the
    check is hasattr and this is what passing it means to the type checker.
    """

    def crossover(self, other: Any) -> Tuple[Any, Any]: ...


#: Width of the BLX interval, as a share of the distance between the two parents,
#: added at each end. Eshelman and Schaffer's own recommendation; measured over the
#: nine benchmark functions and 30 seeds, anything from 0.25 to 0.75 performs the
#: same, so the value from the literature is the one that needs no defending.
BLX_ALPHA = 0.5


def blend_interval(first: float, second: float, min_value: float, max_value: float,
                   alpha: float = BLX_ALPHA) -> Tuple[float, float]:
    """
    The interval a BLX-alpha child is drawn from, clipped to the domain.

    Uniform crossover hands a whole variable to one child or the other, so on a
    numerical variable the offspring can only ever hold values the population
    already had; every value the search has not seen has to come from a mutation
    (F-33). BLX draws instead from the interval the two parents span, widened by
    ``alpha`` of its width at each end, which is what lets a crossover produce a
    value neither parent held.

    It is symmetric in its two arguments, so which parent is which does not matter
    -- that is why a blended variable is not also exchanged.

    :param first: One parent's value.
    :type first: float
    :param second: The other parent's value.
    :type second: float
    :param min_value: Lower bound of the variable's definition.
    :type min_value: float
    :param max_value: Upper bound of the variable's definition.
    :type max_value: float
    :param alpha: Share of the parents' distance added at each end.
    :type alpha: float
    :return: The interval to draw the child's value from.
    :rtype: Tuple[float, float]
    """
    spread = abs(first - second) * alpha
    return (max(min_value, min(first, second) - spread),
            min(max_value, max(first, second) + spread))


class GAReal(types.Real):
    """
    A real variable that knows how to cross over, by BLX-alpha.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GAReal) -> Tuple[GAReal, GAReal]:
        """
        Draw two children from the BLX-alpha interval this variable spans with another.

        :param other: The other parent's value for this variable.
        :type other: GAReal
        :return: Two new values, each drawn independently.
        :rtype: Tuple[GAReal, GAReal]
        """
        # Cast because BaseType.get_definition() is declared as the whole union of
        # definitions, so mypy sees a five-element unpack among the possibilities. A
        # GAReal always holds a RealDefinition; the declared type is what is too wide
        # (P-11). types.Real has the same three errors and no cast, for now.
        definition = cast(RealDefinition, self.get_definition())
        _, min_value, max_value, step = definition.get_attributes()
        left, right = blend_interval(self.get(), other.get(), min_value, max_value)

        children = []
        for _ in range(2):
            child = GAReal(definition, connector=self.connector)
            # Through _generate_numerical so the value lands on the domain's own grid
            # when the definition has a step, anchored at its minimum (F-01).
            child.set(self._generate_numerical(left, right, step, origin=min_value))
            children.append(child)
        return children[0], children[1]


class GAInteger(types.Integer):
    """
    An integer variable that knows how to cross over, by BLX-alpha.

    Integers have the same problem as reals -- a uniform swap never produces a value
    the population did not hold -- and it matters most in the case the package is
    sold on, hyperparameter optimization, whose domains are full of them.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GAInteger) -> Tuple[GAInteger, GAInteger]:
        """
        Draw two children from the BLX-alpha interval, rounded to the definition's grid.

        :param other: The other parent's value for this variable.
        :type other: GAInteger
        :return: Two new values, each drawn independently.
        :rtype: Tuple[GAInteger, GAInteger]
        """
        definition = cast(IntegerDefinition, self.get_definition())
        _, min_value, max_value, step = definition.get_attributes()
        left, right = blend_interval(self.get(), other.get(), min_value, max_value)

        children = []
        for _ in range(2):
            child = GAInteger(definition, connector=self.connector)
            child.set(int(round(self._generate_numerical(
                left, right, step or 1, origin=min_value))))
            children.append(child)
        return children[0], children[1]


class GAStructure(types.Structure):
    """
    Represents the custom Structure type for the Genetic Algorithm (GA).
    
    This class extends the base Structure type to add genetic algorithm specific operations
    like crossover.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GAStructure) -> Tuple[GAStructure, GAStructure]:
        """
        Performs crossover operation with another GAStructure instance.

        A static structure recombines position by position. A dynamic one has to
        decide what happens where the parents' lengths differ, and that is cut and
        splice (F-31); the positions both parents share recombine by the same rule
        either way.

        :param other: Another GAStructure instance to perform crossover with
        :type other: GAStructure
        :return: A tuple containing two new GAStructure instances (children)
        :rtype: Tuple[GAStructure, GAStructure]
        """
        definition = self.get_definition()
        common = min(len(self), len(other))

        if isinstance(definition, DynamicStructureDefinition):
            elements1, elements2 = cut_and_splice(self, other, definition)
        else:
            elements1, elements2 = self._recombine_prefix(other, common)

        # Built whole, from the elements: a child initializes at a random length,
        # so writing into it position by position would run off its end.
        child1 = GAStructure(definition, connector=self.connector)
        child2 = GAStructure(definition, connector=self.connector)
        child1.set(elements1)
        child2.set(elements2)
        return child1, child2

    def _recombine_prefix(self, other: GAStructure, size: int) -> Tuple[list, list]:
        """
        Recombine the first ``size`` positions of this structure with another's.

        An element that knows how to cross over does its own recombining, the same
        rule GASolution follows one level up: a structure of reals blends component
        by component, which is how BLX is defined for a vector, instead of only
        shuffling values between positions (F-33). Elements that do not, categoricals
        among them, swap positions, some of them chosen at random.

        :param other: The other parent.
        :type other: GAStructure
        :param size: How many leading positions to recombine, at most the shorter length.
        :type size: int
        :return: The recombined leading elements of each child.
        :rtype: Tuple[list, list]
        """
        head1: list = []
        head2: list = []
        if size == 0:
            return head1, head2

        number_of_changes = get_rng().randint(1, size)
        indexes_to_change = get_rng().sample(list(range(size)), number_of_changes)

        for i in range(size):
            if hasattr(self.get(i), "crossover"):
                first, second = self.get(i).crossover(other.get(i))
            elif i in indexes_to_change:
                first, second = deepcopy(other.get(i)), deepcopy(self.get(i))
            else:
                first, second = deepcopy(self.get(i)), deepcopy(other.get(i))
            head1.append(first)
            head2.append(second)
        return head1, head2


def _valid_length(definition: DynamicStructureDefinition, length: int) -> bool:
    """Whether ``length`` is one the definition allows, step included."""
    _, min_length, max_length, step, _ = definition.get_attributes()
    return min_length <= length <= max_length and (length - min_length) % (step or 1) == 0


def prefix_and_tails(first: GAStructure, second: GAStructure,
                     definition: DynamicStructureDefinition) -> Tuple[list, list]:
    """
    Crossover for variable lengths that keeps the parents' lengths.

    The positions both parents have recombine by the usual rule, and each child gets
    one parent's tail, drawn at random, so one child is as long as one parent and the
    other as long as the other. Lengths are valid by construction, which is why this
    is what cut_and_splice falls back on when no cut gives two valid lengths.

    It is the fallback and not the operator because it never produces a length the
    population did not already hold, and that showed: measured over 30 seeds on the
    polynomial problem, whose right length is four, GA settled at a mean length of
    2.5 with this and 3.6 with cut and splice, and won 19 seeds against 24 (F-31).
    It is F-33's lesson again, for lengths instead of values.

    :return: The elements of each child.
    :rtype: Tuple[list, list]
    """
    common = min(len(first), len(second))
    head1, head2 = first._recombine_prefix(second, common)
    tail1 = [deepcopy(first.get(i)) for i in range(common, len(first))]
    tail2 = [deepcopy(second.get(i)) for i in range(common, len(second))]
    if get_rng().random() < 0.5:
        tail1, tail2 = tail2, tail1
    return head1 + tail1, head2 + tail2


def cut_and_splice(first: GAStructure, second: GAStructure,
                   definition: DynamicStructureDefinition) -> Tuple[list, list]:
    """
    Crossover for variable lengths that recombines the lengths too.

    Goldberg's cut and splice: each parent is cut at a point of its own and the
    halves are crossed, so a child's length is the head of one parent plus the tail
    of the other -- a length neither parent need have had. The cut points are drawn
    among the pairs that give both children a length the definition allows, step
    included; when no such pair exists the parents' own lengths are kept instead.
    The positions both heads share recombine by the usual rule (F-31).

    Chosen over keeping the parents' lengths by measurement: see prefix_and_tails.

    :return: The elements of each child.
    :rtype: Tuple[list, list]
    """
    length1, length2 = len(first), len(second)
    pairs = [(cut1, cut2)
             for cut1 in range(length1 + 1) for cut2 in range(length2 + 1)
             if _valid_length(definition, cut1 + length2 - cut2)
             and _valid_length(definition, cut2 + length1 - cut1)]
    if not pairs:
        return prefix_and_tails(first, second, definition)

    cut1, cut2 = pairs[get_rng().randrange(len(pairs))]
    shared = min(cut1, cut2)
    head1, head2 = first._recombine_prefix(second, shared)
    own1 = [deepcopy(first.get(i)) for i in range(shared, cut1)]
    own2 = [deepcopy(second.get(i)) for i in range(shared, cut2)]
    tail1 = [deepcopy(second.get(i)) for i in range(cut2, length2)]
    tail2 = [deepcopy(first.get(i)) for i in range(cut1, length1)]
    return head1 + own1 + tail1, head2 + own2 + tail2



class GASolution(Solution):
    """
    Represents a Solution type for the Genetic Algorithm (GA).

    This class extends the base Solution type to add genetic algorithm specific operations
    like crossover between solutions.

    :ivar connector: The connector used to link different types
    :vartype connector: BaseConnector
    """

    def crossover(self, other: GASolution) -> Tuple[GASolution, GASolution]:
        """
        Performs crossover operation with another GASolution instance.

        :param other: Another GASolution instance to perform crossover with
        :type other: GASolution
        :return: A tuple containing two new GASolution instances (children)
        :rtype: Tuple[GASolution, GASolution]
        :raises AssertionError: If the solutions have different variable keys
        """
        assert self.get_variables().keys() == other.get_variables().keys()

        # The question is what a variable can do, not what builtin it maps to. Asking
        # for the builtin put reals and integers in with the categoricals, so the only
        # thing that ever happened to a number was being handed whole to one child or
        # the other: the offspring could not hold a value the population did not
        # already have (F-33). Since GAReal and GAInteger cross over themselves, what
        # is left here are the variables that cannot be blended, categoricals.
        swappable = [variable_name
                     for variable_name, variable_value in self.get_variables().items()
                     if not hasattr(variable_value, "crossover")]

        if swappable:
            # Exchanging every one of them would hand the parents straight back when
            # there is nothing else being recombined, which is why the count used to
            # stop one short. It only does so when nothing blends.
            most = len(swappable) - 1 if len(swappable) == len(self.get_variables()) \
                else len(swappable)
            variables_to_exchange = get_rng().sample(
                swappable, get_rng().randint(1, most)) if most >= 1 else []
        else:
            variables_to_exchange = []

        child1 = GASolution(self.get_definition(), connector=self.connector)
        child2 = GASolution(self.get_definition(), connector=self.connector)

        for variable_name, variable_value in self.get_variables().items():  # Iterate over all variables

            if variable_name not in swappable:
                variable_child1, variable_child2 = cast(Crossable, variable_value).crossover(
                    other.get(variable_name))
                child1.set(variable_name, deepcopy(variable_child1))
                child2.set(variable_name, deepcopy(variable_child2))
            elif variable_name in variables_to_exchange:
                child1.set(variable_name, deepcopy(other.get(variable_name)))
                child2.set(variable_name, deepcopy(self.get(variable_name)))
            else:
                child1.set(variable_name, deepcopy(self.get(variable_name)))
                child2.set(variable_name, deepcopy(other.get(variable_name)))

        return child1, child2


def require_crossover(domain: Domain, algorithm: str) -> None:
    """
    Check that the domain's connector yields solutions that know how to cross over.

    GA, SSGA and the memetic algorithm all cross solutions, an operator that only
    GASolution and GAStructure provide. With a plain Domain() they used to die on the
    first iteration with `AttributeError: 'Solution' object has no attribute
    'crossover'`, which says nothing about what to do (A-07).

    The check asks for the capability rather than for GAConnector itself, so that a
    user bringing their own connector with their own crossover operator still works:
    the connector is the framework's extension point.

    :param domain: The domain the algorithm was given.
    :type domain: Domain
    :param algorithm: The algorithm's name, for the error message.
    :type algorithm: str
    :raises ValueError: If the domain's solutions have no crossover operator.
    """
    solution_type: type = domain.get_connector().get_type(domain.get_core())
    if not hasattr(solution_type, "crossover"):
        raise ValueError(
            f"{algorithm} crosses solutions over, and this domain's connector maps it "
            f"to {solution_type.__name__}, which has no crossover operator. Build the "
            f"domain with the GA connector:\n\n"
            f"    from metagen.metaheuristics import GAConnector\n"
            f"    domain = Domain(connector=GAConnector())\n"
        )


class GAConnector(BaseConnector):
    """
    Represents the custom Connector for the Genetic Algorithm (GA).

    This connector links the following classes:
    * BaseDefinition - GASolution - dict
    * IntegerDefinition - GAInteger - int
    * RealDefinition - GAReal - float
    * CategoricalDefinition - types.Categorical - str
    * StaticStructureDefinition - GAStructure - list
    * DynamicStructureDefinition - GAStructure - list

    Every type but the categorical is replaced by a GA one, and what they add is a
    crossover operator: a categorical has no meaningful blend between two values, so
    it keeps the uniform swap. Bringing another operator -- SBX instead of BLX, say --
    is a matter of registering another class here, which is what the connector is for.
    """

    def __init__(self) -> None:
        """
        Initialize the GAConnector with predefined type mappings for GA operations.
        """
        super().__init__()

        self.register(BaseDefinition, GASolution, dict)
        self.register(IntegerDefinition, GAInteger, int)
        self.register(RealDefinition, GAReal, float)
        self.register(CategoricalDefinition, types.Categorical, str)
        self.register(StaticStructureDefinition, (GAStructure, "static"), list)
        self.register(DynamicStructureDefinition, (GAStructure, "dynamic"), list)


def tournament_selection(solutions: Sequence[Solution], tournament_size: int = 2) -> Solution:
    """
    Pick a parent by tournament: draw a few individuals at random and keep the best.

    This is the selection operator GA, SSGA and the memetic algorithm share. They
    used to take the two best of the population instead, which is truncation
    selection at its most extreme: the population converged on that pair within a
    couple of generations and the crossover stopped recombining anything (A-01).

    ``tournament_size`` is the selection pressure. Two is the mildest tournament and
    the usual default; raising it makes the search greedier and converge sooner. A
    size larger than the population is clamped to it, which turns the tournament into
    picking the best individual outright.

    :param solutions: The population to choose from.
    :type solutions: Sequence[:py:class:`~metagen.framework.Solution`]
    :param tournament_size: How many individuals compete, at least 1, defaults to 2.
    :type tournament_size: int
    :return: The best of the drawn individuals.
    :rtype: :py:class:`~metagen.framework.Solution`
    """
    contenders = get_rng().sample(solutions, min(tournament_size, len(solutions)))
    return min(contenders, key=lambda solution: solution.get_fitness())


def yield_two_children(parents: Tuple[GASolution, GASolution], mutation_rate: float,
                      fitness_function: Callable[[Solution], float]) -> Tuple[GASolution, GASolution]:
    """
    Generate two children solutions through crossover and mutation operations.

    :param parents: A tuple containing two parent solutions
    :type parents: Tuple[GASolution, GASolution]
    :param mutation_rate: The probability of mutation occurring in each child
    :type mutation_rate: float
    :param fitness_function: Function to evaluate the fitness of solutions
    :type fitness_function: Callable[[Solution], float]
    :return: A tuple containing two new solutions (children)
    :rtype: Tuple[GASolution, GASolution]
    """

    child1, child2 = parents[0].crossover(parents[1])

    if get_rng().uniform(0, 1) <= mutation_rate:
        child1.mutate()
    if get_rng().uniform(0, 1) <= mutation_rate:
        child2.mutate()

    child1.evaluate(fitness_function)
    child2.evaluate(fitness_function)

    return child1, child2
