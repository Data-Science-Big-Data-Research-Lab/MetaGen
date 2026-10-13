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

import datetime
import json
import os
import time
from typing import Any, Callable, Dict, List, Literal, Mapping, Optional, Sequence, Set, Tuple

from metagen.framework import Solution
from metagen.framework.rng import set_seed
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.trigen.fitness import (NULL_SAMPLES, NULL_SIZES, Measure, Scoring, SizeReference,
                                                   TriclusterFitness)
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes
from metagen.metaheuristics.trigen.results import TriGenResult, _plain
from metagen.metaheuristics.trigen.trigen_ga import TriGenGA, require_integer, validate
from metagen.triclustering import Cube, Tricluster
from metagen.triclustering.cube import AXES
from metagen.triclustering.measures import Views
from metagen.triclustering.quality import FlatProfiles

Growth = Optional[Literal["fitness", "quality"]]


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

    The tricluster a search returns then grows: TriGen adds to it, one at a time, the
    gene, condition or time that leaves its fitness lowest, while that fitness is no
    higher than the current one and the dimension is below its largest size. With
    ``growth="quality"`` the same steps follow the quality term instead of the whole
    fitness, and with ``growth=None`` the tricluster is kept as the search returned it.
    With ``pruning``, each step may also remove a gene, condition or time, down to the
    smallest sizes, and takes whichever addition or removal lowers the score most, until
    none lowers it.

    The smallest and largest sizes bound every tricluster TriGen builds, whatever the
    fitness. With ``scoring="significance"`` (see :py:class:`TriclusterFitness`) the
    fitness has no size term, and the largest sizes can be left at the size of the cube.
    A tricluster that grows into one already found is kept as the search returned it.

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
        size of the cube. The fitness rewards size, so without them a tricluster may take in
        most of the cube.
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
        its sizes, fitness and terms, the best fitness after each generation, the
        evaluations and seconds it took, and the evaluations its growth took. None, the
        default, writes nothing.
    :type history: str or None, optional
    :param growth: What the tricluster a search returns grows by, ``"fitness"``,
        ``"quality"`` or None not to grow it, defaults to ``"fitness"``.
    :type growth: str or None, optional
    :param scoring: How the fitness scores a tricluster, ``"weighted"`` or
        ``"significance"``, defaults to ``"weighted"``.
    :type scoring: str, optional
    :param pruning: Whether growing may also remove coordinates; None, the default, prunes
        with ``scoring="significance"`` and ``growth="fitness"``, and not otherwise.
    :type pruning: bool or None, optional
    :raises ValueError: if a parameter is out of its range.
    """

    def __init__(self, cube: Cube, n_triclusters: int = 5, generations: int = 20, population_size: int = 10,
                 random_fraction: float = 0.2, selection_rate: float = 0.5, mutation_probability: float = 0.1,
                 min_sizes: Sequence[int] = (2, 2, 2), max_sizes: Optional[Sequence[int]] = None,
                 measure: Measure = "msl", views: Views = "distinct", flat_profiles: FlatProfiles = "exclude",
                 weights: Optional[Mapping[str, float]] = None, size_reference: SizeReference = "dataset",
                 seed: Optional[int] = None, history: Optional[str] = None,
                 growth: Growth = "fitness", scoring: Scoring = "weighted",
                 pruning: Optional[bool] = None) -> None:
        require_integer("n_triclusters", n_triclusters)
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
        if growth not in ("fitness", "quality", None):
            raise ValueError(f"growth is 'fitness', 'quality' or None, not {growth!r}.")
        self.cube = cube
        self.n_triclusters = n_triclusters
        self.generations = generations
        self.population_size = population_size
        self.random_fraction = random_fraction
        self.selection_rate = selection_rate
        self.mutation_probability = mutation_probability
        self.sizes: Sizes = ((smallest[0], largest[0]), (smallest[1], largest[1]), (smallest[2], largest[2]))
        self.fitness = TriclusterFitness(cube, measure=measure, views=views, flat_profiles=flat_profiles,
                                         weights=weights, size_reference=size_reference, max_sizes=largest,
                                         scoring=scoring)
        # Growing is not part of the Java TriGen; it is the node addition of Cheng and
        # Church taken to three dimensions. Measured in the bench of phase 4b, 30 seeds
        # (metagen-auditoria/trigen/banco/bloque4_tablas.md and bloque5_informe.md):
        # growing by the fitness doubles the recovery of planted triclusters (Jaccard
        # 0.25 -> 0.52, 0.21 -> 0.34, 0.09 -> 0.22, p < 0.01) and the baseline does not
        # reach it with more generations for the same evaluations: it converges to small,
        # very coherent pieces near the smallest size, with more precision on P4 and more
        # TRIQ on yeast than growing. A trade of size for coherence, decided for size,
        # pending BIOQ. Growing costs evaluations, little on small cubes and up to 25
        # times the search on yeast (a thousand genes tried per step). Growing against
        # the starting score instead of the current one drifted to the largest sizes.
        self.growth = growth
        # Pruning while growing pays off with the significance and not with the weighted
        # fitness. Bench block 6 (metagen-auditoria/trigen/banco/bloque6_informe.md, 30
        # seeds): with the significance, without max_sizes, recovery 0.51 -> 0.80 on P1
        # and 0.17 -> 0.47 on P4 when pruning; with the weighted fitness, pruning shrinks
        # the triclusters (P4: 45 -> 12 genes) and recovery drops 0.22 -> 0.10.
        # With growth="quality" the quality alone improves as the tricluster shrinks, so
        # pruning by it ends every tricluster at the smallest sizes.
        self.pruning = (scoring == "significance" and growth == "fitness") if pruning is None else bool(pruning)
        self.size_reference = size_reference
        self.seed = seed
        self.history_file = history
        #: The seconds the last run took.
        self.seconds = 0.0
        #: Whether the last run reached its end.
        self.finished = False
        #: The configuration and the date the last run started with; None before any run.
        self.started: Optional[Dict[str, Any]] = None
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
        clock = time.perf_counter()
        self.seconds, self.finished = 0.0, False
        self.started = {"configuration": self.configuration(), "chance_evaluations": 0,
                        "date": datetime.datetime.now().astimezone().isoformat(timespec="seconds")}
        try:
            return self._run()
        finally:
            self.seconds = time.perf_counter() - clock

    def _run(self) -> List[Tricluster]:
        if self.seed is not None:
            set_seed(self.seed)
        if self.history_file is not None and os.path.exists(self.history_file):
            os.remove(self.history_file)
        hierarchy = self.hierarchy = DataHierarchy(self.cube.shape)
        self.fitness.found = []
        # Each run fits the model of chance anew from the seeded generator, here in the
        # driver and not lazily inside an evaluation: the same seed gives the same run.
        if self.fitness.scoring == "significance":
            self.fitness.fit_chance()
            if self.started is not None:
                self.started["chance_evaluations"] = NULL_SIZES * NULL_SAMPLES
        self.triclusters = []
        self.history = []
        for index in range(self.n_triclusters):
            search = TriGenGA(self.fitness, self.sizes, hierarchy, first=index == 0,
                              population_size=self.population_size, generations=self.generations,
                              random_fraction=self.random_fraction, selection_rate=self.selection_rate,
                              mutation_probability=self.mutation_probability)
            search.run()
            found = set(self.triclusters)
            chosen = _choose(search, found)
            record: Dict[str, Any] = {"search": index, "evaluations": search._evaluations,
                                      "seconds": search._seconds,
                                      "best_fitnesses": list(search.best_solution_fitnesses),
                                      "growth_evaluations": 0}
            if chosen is not None and self.growth is not None:
                score = self.fitness.evaluate if self.growth == "fitness" else self.fitness.quality
                grown, record["growth_evaluations"] = grow(chosen, score, self.sizes, self.cube.shape,
                                                           pruning=self.pruning)
                if grown not in found:
                    chosen = grown
            if chosen is None:
                metagen_logger.warning(f"TriGen search {index} evaluated no tricluster that had not been found "
                                       f"already: the search space has run out of new ones.")
                record["tricluster"] = None
            else:
                terms = self.fitness.terms(chosen)
                chosen = Tricluster(chosen.genes, chosen.conditions, chosen.times, fitness=terms["fitness"])
                record["tricluster"] = {"genes": list(chosen.genes), "conditions": list(chosen.conditions),
                                        "times": list(chosen.times)}
                record["sizes"] = list(chosen.size)
                record["fitness"] = terms["fitness"]
                record["terms"] = terms
                self.triclusters.append(chosen)
                self.fitness.found.append(chosen)
                hierarchy.update(chosen)
            self.history.append(record)
            if self.history_file is not None:
                with open(self.history_file, "a") as handle:
                    handle.write(json.dumps(record) + "\n")
        self.finished = True
        return list(self.triclusters)

    def configuration(self) -> Dict[str, Any]:
        """
        The arguments this TriGen was built with, all but the cube and the history file,
        by name and as plain values: a TriGen built with them on the same cube is this one.

        :return: The configuration.
        :rtype: Dict[str, Any]
        """
        return _plain({"n_triclusters": self.n_triclusters, "generations": self.generations,
                "population_size": self.population_size, "random_fraction": self.random_fraction,
                "selection_rate": self.selection_rate, "mutation_probability": self.mutation_probability,
                "min_sizes": [low for low, _ in self.sizes], "max_sizes": [high for _, high in self.sizes],
                "measure": self.fitness.measure, "views": self.fitness.views,
                "flat_profiles": self.fitness.flat_profiles,
                "weights": None if self.fitness.scoring == "significance" else dict(self.fitness.weights),
                "size_reference": self.size_reference, "seed": self.seed, "growth": self.growth,
                "scoring": self.fitness.scoring, "pruning": self.pruning})

    def result(self, label: Optional[str] = None) -> TriGenResult:
        """
        The result of the last run, with all it takes to keep it and to run it again. Of a
        run cut short, it is what its searches had found, and says it is not complete.

        :param label: A free label for the data, such as the name of the dataset.
        :type label: str, optional
        :return: The result.
        :rtype: TriGenResult
        :raises ValueError: if this TriGen has not run.
        """
        return TriGenResult.from_run(self, label)

    def save(self, path: str, label: Optional[str] = None) -> None:
        """
        Save the result of the last run to a JSON file; :py:meth:`TriGenResult.load` reads
        it back.

        :param path: The file.
        :type path: str
        :param label: A free label for the data, such as the name of the dataset.
        :type label: str, optional
        :raises ValueError: if this TriGen has not run.
        """
        self.result(label).save(path)


def _tricluster(solution: Solution) -> Tricluster:
    return Tricluster(solution["genes"], solution["conditions"], solution["times"])


def grow(tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
         shape: Tuple[int, int, int], pruning: bool = False) -> Tuple[Tricluster, int]:
    """
    Grow a tricluster one coordinate at a time: at each step, the gene, condition or time,
    of a dimension below its largest size, that leaves the score lowest, as long as that
    score is no higher than the current one. Ties go to the first dimension, then to the
    first position.

    With ``pruning``, each step also weighs removing a gene, condition or time from a
    dimension above its smallest size, takes the addition or removal that leaves the score
    lowest, and stops when none leaves it lower than the current one.

    :param tricluster: The tricluster to grow.
    :type tricluster: Tricluster
    :param score: What to keep low, the lower the better.
    :type score: Callable[[Tricluster], float]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :param shape: The shape of the cube.
    :type shape: Tuple[int, int, int]
    :param pruning: Whether a step may remove a coordinate, defaults to False.
    :type pruning: bool, optional
    :return: The grown tricluster, and how many triclusters were scored.
    :rtype: Tuple[Tricluster, int]
    """
    parts = [list(tricluster.genes), list(tricluster.conditions), list(tricluster.times)]
    current = score(tricluster)
    evaluations = 1
    while True:
        best: Optional[Tuple[float, int, List[int]]] = None
        for dimension in range(3):
            low, high = sizes[dimension]
            moves: List[List[int]] = []
            if len(parts[dimension]) < high:
                held = set(parts[dimension])
                moves += [parts[dimension] + [position] for position in range(shape[dimension]) if position not in held]
            if pruning and len(parts[dimension]) > low:
                moves += [[kept for kept in parts[dimension] if kept != removed] for removed in parts[dimension]]
            for move in moves:
                trial = list(parts)
                trial[dimension] = move
                value = score(Tricluster(trial[0], trial[1], trial[2]))
                evaluations += 1
                # Without pruning, a step that leaves the score equal is taken: it only adds.
                # With pruning, only a step that lowers it, so that no step can undo another.
                better = value < current if pruning else value <= current
                if better and (best is None or value < best[0]):
                    best = (value, dimension, move)
        if best is None:
            return Tricluster(parts[0], parts[1], parts[2]), evaluations
        current = best[0]
        parts[best[1]] = best[2]


def _choose(search: TriGenGA, found: Set[Tricluster]) -> Optional[Tricluster]:
    """The best of the last population that is new; else the best new one evaluated."""
    for individual in sorted(search.current_solutions, key=Solution.get_fitness):
        tricluster = _tricluster(individual)
        if tricluster not in found:
            return tricluster
    new = {tricluster: value for tricluster, value in search.evaluated.items() if tricluster not in found}
    return min(new, key=new.__getitem__) if new else None
