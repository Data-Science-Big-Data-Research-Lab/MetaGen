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

from typing import Dict, List, Optional, Sequence, Tuple, cast

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_rng
from metagen.metaheuristics.base import Metaheuristic
from metagen.metaheuristics.genetic.genetic_tools import GAConnector, GASolution
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.trigen.fitness import TriclusterFitness
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes, exact_floor, initial_population
from metagen.triclustering import Tricluster
from metagen.triclustering.cube import AXES


def tricluster_domain(shape: Sequence[int], sizes: Sizes) -> Domain:
    """
    The search space of a tricluster: three subsets, of the genes, the conditions and the
    times of a cube, each between its smallest and largest size.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :return: The domain, with the connector of the genetic algorithms.
    :rtype: Domain
    """
    domain = Domain(GAConnector())
    for axis, length, (smallest, largest) in zip(AXES, shape, sizes):
        domain.define_subset(axis, list(range(length)), smallest, largest)
    return domain


def select_by_groups(population: Sequence[Solution], count: int) -> List[Solution]:
    """
    TriGen's selection: every individual falls at random into one of three groups (two if
    the population has two or fewer), the best of each group is selected, and then, until
    there are ``count``, the best left in a group drawn at random among those that still
    have someone. So the best of the population is always selected, and at least one per
    group, which can make more than ``count``.

    :param population: The population, evaluated.
    :type population: Sequence[Solution]
    :param count: How many to select.
    :type count: int
    :return: The individuals selected, the best of each group first.
    :rtype: List[Solution]
    """
    group_count = 2 if len(population) <= 2 else 3
    groups: List[List[Solution]] = [[] for _ in range(group_count)]
    for individual in population:
        groups[get_rng().randrange(group_count)].append(individual)
    remaining = [sorted(group, key=Solution.get_fitness) for group in groups if group]
    selected = [group.pop(0) for group in remaining]
    while len(selected) < count:
        group = get_rng().choice([group for group in remaining if group])
        selected.append(group.pop(0))
    return selected


class TriGenGA(Metaheuristic):
    """
    One search of TriGen: a genetic algorithm that finds one tricluster of a cube.
    :py:class:`~metagen.metaheuristics.TriGen` runs one per tricluster.

    - **The initial population** comes from :py:func:`initial_population`: scattered
      triclusters and blocks of consecutive positions, and, after the first search,
      triclusters drawn from the least explored coordinates of the data hierarchy.
    - **Each generation** selects ``floor(selection_rate · population_size)`` individuals
      by groups (:py:func:`select_by_groups`), which pass on untouched and are the only
      parents; breeds the rest of the population from pairs of distinct parents, crossing
      the genes, the conditions and the times each at one point; mutates each child, with
      probability ``mutation_probability``, by one step in one of its three dimensions
      (adding, removing or changing one coordinate); and evaluates the children.
    - **It stops** after ``generations`` generations.

    Every tricluster it evaluates is kept in :py:attr:`evaluated`, with its fitness, so
    that TriGen can take the best one that does not repeat a tricluster already found.

    :param fitness: The fitness, with the cube and the triclusters already found.
    :type fitness: TriclusterFitness
    :param sizes: The smallest and largest number of genes, conditions and times.
    :type sizes: Sizes
    :param hierarchy: The data hierarchy of the triclusters already found.
    :type hierarchy: DataHierarchy
    :param first: Whether this is the first search.
    :type first: bool
    :param population_size: The size of the population, at least 4, defaults to 10.
    :type population_size: int, optional
    :param generations: The number of generations, defaults to 20.
    :type generations: int, optional
    :param random_fraction: The share of the initial population drawn without the hierarchy
        after the first search, defaults to 0.2.
    :type random_fraction: float, optional
    :param selection_rate: The share of the population selected each generation, defaults
        to 0.5; it has to select at least 2 and leave at least 1 to breed.
    :type selection_rate: float, optional
    :param mutation_probability: The probability that a child mutates, defaults to 0.1.
    :type mutation_probability: float, optional
    :param seed: Seed for MetaGen's generators, defaults to None.
    :type seed: int or None, optional
    :param checkpoint: File the run saves its state to; see
        :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type checkpoint: str or None, optional
    :param checkpoint_every: Iterations between two saves, defaults to 1.
    :type checkpoint_every: int, optional
    :param history: File the run writes its history to; see
        :py:class:`~metagen.metaheuristics.base.Metaheuristic`.
    :type history: str or None, optional
    :raises ValueError: if a parameter is out of its range.
    """

    def __init__(self, fitness: TriclusterFitness, sizes: Sizes, hierarchy: DataHierarchy, first: bool,
                 population_size: int = 10, generations: int = 20, random_fraction: float = 0.2,
                 selection_rate: float = 0.5, mutation_probability: float = 0.1, seed: Optional[int] = None,
                 checkpoint: Optional[str] = None, checkpoint_every: int = 1, history: Optional[str] = None) -> None:
        validate(population_size, generations, random_fraction, selection_rate, mutation_probability)
        super().__init__(tricluster_domain(fitness.cube.shape, sizes), fitness, population_size=population_size,
                         seed=seed, checkpoint=checkpoint, checkpoint_every=checkpoint_every, history=history)
        self.tricluster_fitness = fitness
        self.sizes = sizes
        self.hierarchy = hierarchy
        self.first = first
        self.generations = generations
        self.random_fraction = random_fraction
        self.selection_count = exact_floor(selection_rate, population_size)
        self.mutation_probability = mutation_probability
        #: Every tricluster evaluated, with its fitness. Filled on the driver, from the
        #: population after each step, which holds every individual just evaluated.
        self.evaluated: Dict[Tricluster, float] = {}

    def _solution(self, tricluster: Tricluster) -> Solution:
        solution = solution_class(self.domain)(self.domain, connector=self.domain.get_connector())
        solution.set("genes", list(tricluster.genes))
        solution.set("conditions", list(tricluster.conditions))
        solution.set("times", list(tricluster.times))
        return solution

    def initialize(self, num_solutions: int = 10) -> Tuple[List[Solution], Solution]:
        """
        The initial population, evaluated.

        :param num_solutions: Its size.
        :type num_solutions: int
        :return: The population and its best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        population = [self._solution(tricluster) for tricluster in
                      initial_population(self.tricluster_fitness.cube.shape, self.sizes, self.hierarchy, self.first,
                                         num_solutions, self.random_fraction)]
        for individual in population:
            individual.evaluate(self.fitness_function)
        return population, min(population, key=Solution.get_fitness)

    def iterate(self, solutions: List[Solution]) -> Tuple[List[Solution], Solution]:
        """
        One generation: selection by groups, crossover of the selected, mutation and
        evaluation of the children.

        :param solutions: The current population, evaluated.
        :type solutions: List[Solution]
        :return: The next population and its best individual.
        :rtype: Tuple[List[Solution], Solution]
        """
        selected = select_by_groups(solutions, self.selection_count)
        wanted = len(solutions) - len(selected)
        children: List[Solution] = []
        while len(children) < wanted:
            father, mother = get_rng().sample(selected, 2)
            # With an odd number to breed, the last pair gives one child.
            for child in cast(GASolution, father).crossover(cast(GASolution, mother))[:wanted - len(children)]:
                if get_rng().random() < self.mutation_probability:
                    child.mutate(alterations_number=1, alteration_limit=1)
                child.evaluate(self.fitness_function)
                children.append(child)
        population = selected + children
        return population, min(population, key=Solution.get_fitness)

    def _initialize(self) -> Tuple[List[Solution], Solution]:
        result = super()._initialize()
        self._record(self.current_solutions)
        return result

    def post_iteration(self) -> None:
        """Record the children of the generation, then do what every metaheuristic does."""
        self._record(self.current_solutions)
        super().post_iteration()

    def _record(self, population: Sequence[Solution]) -> None:
        for individual in population:
            tricluster = Tricluster(individual["genes"], individual["conditions"], individual["times"])
            self.evaluated.setdefault(tricluster, individual.get_fitness())

    def stopping_criterion(self) -> bool:
        return self.current_iteration >= self.generations


def validate(population_size: int, generations: int, random_fraction: float, selection_rate: float,
             mutation_probability: float) -> None:
    """
    Check the parameters of a search: a population of at least 4, at least one
    generation, the three rates in ``[0, 1]``, and a selection of at least 2 that leaves at
    least 1 to breed. With 3 groups the selection takes at least 3, so a population of 3
    would have no children.

    :raises ValueError: if a parameter is out of its range.
    """
    if population_size < 4:
        raise ValueError(f"TriGen needs a population of at least 4, not {population_size}.")
    if generations < 1:
        raise ValueError(f"TriGen needs at least one generation, not {generations}.")
    for name, rate in (("random_fraction", random_fraction), ("selection_rate", selection_rate),
                       ("mutation_probability", mutation_probability)):
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], not {rate}.")
    selected = exact_floor(selection_rate, population_size)
    if not 2 <= selected <= population_size - 1:
        raise ValueError(f"selection_rate {selection_rate} selects {selected} of {population_size}: it has to "
                         f"select at least 2 and leave at least 1 to breed.")
