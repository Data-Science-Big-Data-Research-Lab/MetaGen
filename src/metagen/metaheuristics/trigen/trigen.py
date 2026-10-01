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

import json
import os
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from metagen.framework import Solution
from metagen.framework.rng import set_seed
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.trigen.fitness import Measure, SizeReference, TriclusterFitness
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes
from metagen.metaheuristics.trigen.trigen_ga import TriGenGA, validate
from metagen.triclustering import Cube, Tricluster
from metagen.triclustering.cube import AXES
from metagen.triclustering.measures import Views
from metagen.triclustering.quality import FlatProfiles


class TriGen:
    """
    TriGen: a genetic algorithm that finds ``n_triclusters`` triclusters in a cube, one
    after another. Each is the outcome of a search of its own, a
    :py:class:`~metagen.metaheuristics.trigen.trigen_ga.TriGenGA`, and what is found
    shapes the searches that follow in two ways: the fitness penalizes repeating the
    coordinates of the triclusters found (see :py:class:`TriclusterFitness`), and every
    search after the first starts mostly from the least explored coordinates.

    Each search returns the best tricluster of its last population that is not one
    already found. When the whole population repeats triclusters already found, it
    returns the best of the rest of those it evaluated, and when it evaluated nothing new,
    it returns nothing, and TriGen says so: fewer triclusters than asked for mean the
    search space ran out of new ones.

    .. code-block:: python

        from metagen.metaheuristics import TriGen
        from metagen.triclustering import plant

        cube, planted = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
        trigen = TriGen(cube, n_triclusters=2, generations=10, population_size=20,
                        min_sizes=(4, 2, 3), max_sizes=(15, 4, 6), seed=0)
        triclusters = trigen.run()
        print(len(triclusters), triclusters[0] != triclusters[1])   # 2 True

    :param cube: The data.
    :type cube: Cube
    :param n_triclusters: How many triclusters to find, defaults to 5.
    :type n_triclusters: int, optional
    :param generations: The generations of each search, defaults to 20.
    :type generations: int, optional
    :param population_size: The population of each search, at least 4, defaults to 10.
    :type population_size: int, optional
    :param random_fraction: The share of the initial population drawn without the data
        hierarchy after the first search, defaults to 0.2.
    :type random_fraction: float, optional
    :param selection_rate: The share of the population selected each generation, defaults
        to 0.5.
    :type selection_rate: float, optional
    :param mutation_probability: The probability that a child mutates, defaults to 0.1.
    :type mutation_probability: float, optional
    :param min_sizes: The fewest genes, conditions and times of a tricluster, at least 2
        each, defaults to (2, 2, 2).
    :type min_sizes: Sequence[int], optional
    :param max_sizes: The most genes, conditions and times of a tricluster, defaults to the
        size of the cube.
    :type max_sizes: Sequence[int], optional
    :param measure: The quality term of the fitness, defaults to ``"msl"``.
    :type measure: str, optional
    :param views: The views of MSL, LSL and TRIQ, defaults to ``"distinct"``.
    :type views: str, optional
    :param flat_profiles: How TRIQ's correlations treat flat profiles, defaults to ``"exclude"``.
    :type flat_profiles: str, optional
    :param weights: The weights of the fitness; see :py:class:`TriclusterFitness`.
    :type weights: Mapping[str, float], optional
    :param size_reference: What the size term measures against, ``"dataset"`` or ``"max"``,
        defaults to ``"dataset"``.
    :type size_reference: str, optional
    :param seed: Seed for MetaGen's generators, set once for the whole run, defaults to None.
    :type seed: int or None, optional
    :param history: File the run writes a JSON line to per search: the tricluster found,
        its fitness and terms, and the evaluations and seconds it took. None, the default,
        writes nothing.
    :type history: str or None, optional
    :raises ValueError: if a parameter is out of its range.
    """

    def __init__(self, cube: Cube, n_triclusters: int = 5, generations: int = 20, population_size: int = 10,
                 random_fraction: float = 0.2, selection_rate: float = 0.5, mutation_probability: float = 0.1,
                 min_sizes: Sequence[int] = (2, 2, 2), max_sizes: Optional[Sequence[int]] = None,
                 measure: Measure = "msl", views: Views = "distinct", flat_profiles: FlatProfiles = "exclude",
                 weights: Optional[Mapping[str, float]] = None, size_reference: SizeReference = "dataset",
                 seed: Optional[int] = None, history: Optional[str] = None) -> None:
        if n_triclusters < 1:
            raise ValueError(f"TriGen finds at least one tricluster, not {n_triclusters}.")
        validate(population_size, generations, random_fraction, selection_rate, mutation_probability)
        largest = tuple(cube.shape if max_sizes is None else max_sizes)
        smallest = tuple(min_sizes)
        if len(smallest) != 3 or len(largest) != 3:
            raise ValueError(f"Give one size per dimension ({', '.join(AXES)}).")
        for axis, low, high, size in zip(AXES, smallest, largest, cube.shape):
            if not 2 <= low <= high <= size:
                raise ValueError(f"The sizes of the {axis} must satisfy 2 <= minimum ({low}) <= maximum ({high}) "
                                 f"<= the {size} {axis} of the cube.")
        self.cube = cube
        self.n_triclusters = n_triclusters
        self.generations = generations
        self.population_size = population_size
        self.random_fraction = random_fraction
        self.selection_rate = selection_rate
        self.mutation_probability = mutation_probability
        self.sizes: Sizes = ((smallest[0], largest[0]), (smallest[1], largest[1]), (smallest[2], largest[2]))
        self.fitness = TriclusterFitness(cube, measure=measure, views=views, flat_profiles=flat_profiles,
                                         weights=weights, size_reference=size_reference, max_sizes=largest)
        self.seed = seed
        self.history_file = history
        #: The triclusters found by the last run, in the order they were found.
        self.triclusters: List[Tricluster] = []
        #: A record per search of the last run, as written to the history file.
        self.history: List[Dict[str, Any]] = []
        #: How many of the triclusters found by the last run hold each gene, condition and time.
        self.hierarchy = DataHierarchy(cube.shape)

    def run(self) -> List[Tricluster]:
        """
        Find the triclusters.

        :return: The triclusters found, in order, each with its fitness: the fitness it had
            when it was found, against the triclusters found before it.
        :rtype: List[Tricluster]
        """
        if self.seed is not None:
            set_seed(self.seed)
        if self.history_file is not None and os.path.exists(self.history_file):
            os.remove(self.history_file)
        hierarchy = self.hierarchy = DataHierarchy(self.cube.shape)
        self.fitness.found = []
        self.triclusters = []
        self.history = []
        for index in range(self.n_triclusters):
            search = TriGenGA(self.fitness, self.sizes, hierarchy, first=index == 0,
                              population_size=self.population_size, generations=self.generations,
                              random_fraction=self.random_fraction, selection_rate=self.selection_rate,
                              mutation_probability=self.mutation_probability)
            search.run()
            chosen = _choose(search, set(self.triclusters))
            record: Dict[str, Any] = {"search": index, "evaluations": search._evaluations,
                                      "seconds": search._seconds}
            if chosen is None:
                metagen_logger.warning(f"TriGen search {index} evaluated no tricluster that had not been found "
                                       f"already: the search space has run out of new ones.")
                record["tricluster"] = None
            else:
                terms = self.fitness.terms(chosen)
                chosen = Tricluster(chosen.genes, chosen.conditions, chosen.times, fitness=terms["fitness"])
                record["tricluster"] = {"genes": list(chosen.genes), "conditions": list(chosen.conditions),
                                        "times": list(chosen.times)}
                record["fitness"] = terms["fitness"]
                record["terms"] = terms
                self.triclusters.append(chosen)
                self.fitness.found.append(chosen)
                hierarchy.update(chosen)
            self.history.append(record)
            if self.history_file is not None:
                with open(self.history_file, "a") as handle:
                    handle.write(json.dumps(record) + "\n")
        return list(self.triclusters)


def _tricluster(solution: Solution) -> Tricluster:
    return Tricluster(solution["genes"], solution["conditions"], solution["times"])


def _choose(search: TriGenGA, found: Set[Tricluster]) -> Optional[Tricluster]:
    """The best of the last population that is new; else the best new one evaluated."""
    for individual in sorted(search.current_solutions, key=Solution.get_fitness):
        tricluster = _tricluster(individual)
        if tricluster not in found:
            return tricluster
    new = {tricluster: value for tricluster, value in search.evaluated.items() if tricluster not in found}
    return min(new, key=new.__getitem__) if new else None
