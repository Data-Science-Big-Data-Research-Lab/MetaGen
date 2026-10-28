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

import numpy as np

from metagen.framework import Solution
from metagen.framework.rng import get_numpy_rng, set_seed
from metagen.logging.metagen_logger import metagen_logger
from metagen.metaheuristics.trigen.fitness import (NULL_SAMPLES, NULL_SIZES, Measure, Overlap, Scoring,
                                                   SizeReference, TriclusterFitness)
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes
from metagen.metaheuristics.trigen.results import TriGenResult, _plain
from metagen.metaheuristics.trigen.shape import Shape, grow, prism_parts, shape_named  # noqa: F401
from metagen.metaheuristics.trigen.trigen_ga import TriGenGA, require_integer, validate
from metagen.triclustering import Cube, Tricluster, null_cube
from metagen.triclustering.cube import AXES
from metagen.triclustering.measures import Views
from metagen.triclustering.quality import FlatProfiles

Growth = Optional[Literal["fitness", "quality"]]

#: When a run ends: after a number of searches, or when the triclusters hold enough.
Stop = Literal["count", "coverage"]

#: What a run by coverage counts.
Cover = Literal["genes", "pixels"]

#: When a tricluster found is no better than noise.
NoiseRule = Literal["null", "decline"]

#: The searches of the short run in the null cube that sets the threshold of noise_rule="null".
NOISE_PROBES = 3

#: What the searches after the first start from: the coordinates or the cells least held.
Hierarchy = Literal["coordinates", "cells"]


class TriGen:
    """
    TriGen: a genetic algorithm that finds ``n_triclusters`` triclusters in a cube, one
    after another. Each is the outcome of a search of its own, a
    :py:class:`~metagen.metaheuristics.trigen.trigen_ga.TriGenGA`, and what is found
    shapes the searches that follow in two ways: the fitness penalizes repeating the
    coordinates of the triclusters found (see :py:class:`TriclusterFitness`), and every
    search after the first starts mostly from what they have explored least (``hierarchy``).

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

    The order of the genes in the cube steers the search: the initial population draws
    genes from runs of neighboring positions, and MSL with the default views reads the
    slopes along the genes in their order. When that order means nothing, as in most
    expression data, ``shuffle_genes=True`` makes each run search the genes in an order of
    its own, drawn from the seeded generator, and gives back the triclusters with the
    positions of the cube; their fitness and terms are those of the order the run saw.

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
    :param generations: The generations of each search, defaults to 50.
    :type generations: int, optional
    :param population_size: The population of each search, at least 4, defaults to 200.
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
    :param shuffle_genes: Whether each run searches the genes in an order of its own,
        defaults to False.
    :type shuffle_genes: bool, optional
    :param overlap: What the overlap of the weighted fitness counts, ``"coordinates"`` or
        ``"cells"``, defaults to ``"coordinates"``; see :py:class:`TriclusterFitness`.
    :type overlap: str, optional
    :param hierarchy: What the searches after the first start from, ``"coordinates"``,
        the genes, conditions and times the triclusters found hold least, or ``"cells"``,
        the conditions and times they hold least and the genes with the fewest of their
        cells in them, defaults to ``"cells"``.
    :type hierarchy: str, optional
    :param shape: The shape of the triclusters, defaults to ``"cube"``, every combination
        of some genes, some conditions and some times. ``"prism"`` is a surface of the plane
        of the genes and the conditions, pixels that are one piece through their neighbors,
        held along a window of the times, as a field through a season in a series of
        images: it needs the three dimensions in ``ordered``, ``views="time"`` and the
        quality ``"msl"`` or ``"lsl"``, which measure its pixels as series along its window.
        ``max_sizes`` bound the extent of its surface in the genes and the conditions, and
        ``pixels`` its number of pixels.
    :type shape: str, optional
    :param ordered: The dimensions whose positions have an order, by name (``"genes"``,
        ``"conditions"``, ``"times"``), none by default. In a dimension with order a
        tricluster holds a window, consecutive positions: the searches draw, cross, mutate
        and grow windows there, and the model of chance of the significance draws windows.
    :type ordered: Sequence[str], optional
    :param neighborhood: The neighbors of a pixel of a prism, 4 (those that share a side)
        or 8 (a side or a corner), defaults to 4.
    :type neighborhood: int, optional
    :param pixels: The fewest and most pixels of the surface of a prism, defaults to the
        pixels of rectangles of the smallest and the largest sizes of the genes and the
        conditions. Each pixel is a step of what a search represents, so a bound well
        below the plane keeps the search light.
    :type pixels: Sequence[int], optional
    :param stop: When the run ends, ``"count"`` (the default), after ``n_triclusters``
        searches, or ``"coverage"``, when the triclusters found hold the ``coverage`` share of
        the genes or of the pixels, when a search finds nothing new, when the ``noise_rule``
        leaves out ``patience`` triclusters in a row as no better than noise, or after
        ``n_triclusters`` searches, which are then the most. What no tricluster holds is the
        residue, and :py:attr:`stop_reason` says why the run ended.
    :type stop: str, optional
    :param cover: What ``stop="coverage"`` counts: ``"genes"``, held by a tricluster in any
        conditions and times, or, with a prism, ``"pixels"``, held by its surface at any
        time; by default the genes, and the pixels with a prism.
    :type cover: str, optional
    :param coverage: The share to hold with ``stop="coverage"``, defaults to 1.0, all.
    :type coverage: float, optional
    :param noise_rule: With ``stop="coverage"`` and ``scoring="significance"``, when a
        tricluster found is no better than noise: None (the default), never; ``"null"``,
        when its significance not already found is no higher than the highest a short run
        finds in :py:func:`~metagen.triclustering.null_cube` of the data, run at the start;
        ``"decline"``, when it is below ``decline`` times that of the most significant
        tricluster found so far.
    :type noise_rule: str, optional
    :param decline: The share of the significance of the most significant tricluster found
        so far below which ``noise_rule="decline"`` leaves one out, defaults to 0.5.
    :type decline: float, optional
    :param patience: How many triclusters in a row the ``noise_rule`` leaves out before
        the run ends, defaults to 2. One left out still counts as found, so the next
        search looks elsewhere.
    :type patience: int, optional
    :raises ValueError: if a parameter is out of its range.
    """

    def __init__(self, cube: Cube, n_triclusters: int = 5, generations: int = 50, population_size: int = 200,
                 random_fraction: float = 0.2, selection_rate: float = 0.5, mutation_probability: float = 0.1,
                 min_sizes: Sequence[int] = (2, 2, 2), max_sizes: Optional[Sequence[int]] = None,
                 measure: Measure = "msl", views: Views = "distinct", flat_profiles: FlatProfiles = "exclude",
                 weights: Optional[Mapping[str, float]] = None, size_reference: SizeReference = "dataset",
                 seed: Optional[int] = None, history: Optional[str] = None,
                 growth: Growth = "fitness", scoring: Scoring = "weighted",
                 pruning: Optional[bool] = None, shuffle_genes: bool = False,
                 overlap: Overlap = "coordinates", hierarchy: Hierarchy = "cells", shape: str = "cube",
                 ordered: Sequence[str] = (), neighborhood: int = 4, pixels: Optional[Sequence[int]] = None,
                 stop: Stop = "count", cover: Optional[Cover] = None, coverage: float = 1.0,
                 noise_rule: Optional[NoiseRule] = None, decline: float = 0.5, patience: int = 2) -> None:
        # The defaults of the search were chosen by measurement (C7,
        # metagen-auditoria/trigen/c7/informe_c7.md): a grid of populations and generations,
        # then of selection and mutation rates, over planted cubes, 30 seeds each. A
        # population of 200 over 50 generations is the cheapest configuration as good as the
        # best on most problems, and the values of the published TriGen; the rates of 0.5 and
        # 0.1 are the most robust of their grid (as good as the best on 6 of 8 problems).
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
        if hierarchy not in ("coordinates", "cells"):
            raise ValueError(f"hierarchy is 'coordinates' or 'cells', not {hierarchy!r}.")
        if isinstance(ordered, str) or any(axis not in AXES for axis in ordered) or len(set(ordered)) != len(ordered):
            raise ValueError(f"ordered names dimensions of {list(AXES)}, each once, not {ordered!r}.")
        #: The dimensions with order, by name.
        self.ordered: Tuple[str, ...] = tuple(axis for axis in AXES if axis in ordered)
        if neighborhood not in (4, 8):
            raise ValueError(f"neighborhood is 4 or 8, not {neighborhood!r}.")
        self.neighborhood = int(neighborhood)
        #: The fewest and most pixels of a prism; None for the other shapes.
        self.pixels: Optional[Tuple[int, int]] = None
        options: Dict[str, Any] = {}
        if shape == "prism":
            if shuffle_genes:
                raise ValueError("A prism lies on the plane of the genes and the conditions in their order: "
                                 "shuffle_genes does not apply.")
            if pixels is None:
                pixels = (smallest[0] * smallest[1], largest[0] * largest[1])
            if isinstance(pixels, str) or len(pixels) != 2:
                raise ValueError(f"pixels is the fewest and the most pixels of a prism, not {pixels!r}.")
            for count in pixels:
                require_integer("pixels", count)
            self.pixels = (int(pixels[0]), int(pixels[1]))
            options = dict(neighborhood=self.neighborhood, pixels=self.pixels, box=(largest[0], largest[1]))
        elif pixels is not None:
            raise ValueError("pixels bound the surface of a prism, shape='prism'.")
        #: The shape of the triclusters it searches.
        self.form: Shape = shape_named(shape, [AXES.index(axis) for axis in self.ordered], **options)
        if stop not in ("count", "coverage"):
            raise ValueError(f"stop is 'count' or 'coverage', not {stop!r}.")
        cover = cover if cover is not None else ("pixels" if shape == "prism" else "genes")
        if cover not in ("genes", "pixels") or (cover == "pixels" and shape != "prism"):
            raise ValueError(f"cover is 'genes' or, with shape='prism', 'pixels', not {cover!r}.")
        if not 0.0 < coverage <= 1.0:
            raise ValueError(f"coverage is a share in (0, 1], not {coverage}.")
        if noise_rule not in (None, "null", "decline"):
            raise ValueError(f"noise_rule is None, 'null' or 'decline', not {noise_rule!r}.")
        if noise_rule is not None and (stop != "coverage" or scoring != "significance"):
            raise ValueError("noise_rule applies to stop='coverage' with scoring='significance'.")
        if not 0.0 < decline < 1.0:
            raise ValueError(f"decline is a share in (0, 1), not {decline}.")
        # A patience of 2 by default: measured in the Mac over 30 seeds (metagen-auditoria/trigen/
        # parada/etapa1/informe_parada_etapa1.md, 7), the null rule recovers 0.59 of ten planted
        # modules instead of 0.45 with 1, as much as the decline rule with half its noise, at the
        # price of 2.1 triclusters of noise in a cube with nothing instead of 0.8; with 3 the
        # relevance starts to fall.
        require_integer("patience", patience)
        if patience < 1:
            raise ValueError(f"patience is at least 1, not {patience}.")
        #: When a run ends and what it counts; see the parameters.
        self.stop: Stop = stop
        self.cover: Cover = cover
        self.coverage = float(coverage)
        self.noise_rule: Optional[NoiseRule] = noise_rule
        self.decline = float(decline)
        self.patience = patience
        self.cube = cube
        self.n_triclusters = n_triclusters
        self.generations = generations
        self.population_size = population_size
        self.random_fraction = random_fraction
        self.selection_rate = selection_rate
        self.mutation_probability = mutation_probability
        self.sizes: Sizes = ((smallest[0], largest[0]), (smallest[1], largest[1]), (smallest[2], largest[2]))
        self._fitness_options: Dict[str, Any] = dict(measure=measure, views=views, flat_profiles=flat_profiles,
                                                     weights=weights, size_reference=size_reference,
                                                     max_sizes=largest, scoring=scoring, overlap=overlap,
                                                     form=self.form)
        self.fitness = TriclusterFitness(cube, **self._fitness_options)
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
        # Measured in phase 5c (metagen-auditoria/trigen/fase5c/informe_5c.md, section 5):
        # on gse112660, whose genes are in alphabetical order, TriGen without growth finds
        # purity 0.226 in the given order and 0.018 with the genes shuffled; on yeast the
        # triclusters of runs with the same order share genes by position, not by biology.
        self.shuffle_genes = bool(shuffle_genes)
        #: What the searches after the first start from, ``"coordinates"`` or ``"cells"``.
        self.hierarchy_kind: Hierarchy = hierarchy
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
        #: Why the last run ended: ``"count"``, ``"coverage"``, ``"maximum"``, ``"exhausted"`` or
        #: ``"noise"``; None before any run.
        self.stop_reason: Optional[str] = None
        #: The share of the genes or pixels the triclusters of the last run hold.
        self.covered = 0.0
        #: The significance a tricluster has to exceed with ``noise_rule="null"``, from the last run.
        self.noise_threshold: Optional[float] = None

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
        # The searches work on the cube in the order of this run, and what they find goes
        # back to the positions of the cube before it is kept.
        cube, fitness, order = self.cube, self.fitness, None
        if self.shuffle_genes:
            order = [int(position) for position in get_numpy_rng().permutation(self.cube.shape[0])]
            cube = Cube(self.cube.values[order], genes=[self.cube.genes[position] for position in order],
                        conditions=self.cube.conditions, times=self.cube.times)
            fitness = TriclusterFitness(cube, **self._fitness_options)
        cells = self.hierarchy_kind == "cells"
        hierarchy = DataHierarchy(cube.shape, cells=cells)
        self.hierarchy = DataHierarchy(self.cube.shape, cells=cells)
        self.fitness.found = []
        fitness.found = []
        # Each run fits the model of chance anew from the seeded generator, here in the
        # driver and not lazily inside an evaluation: the same seed gives the same run.
        if fitness.scoring == "significance":
            fitness.fit_chance()
            if self.started is not None:
                self.started["chance_evaluations"] = NULL_SIZES * NULL_SAMPLES
        self.triclusters = []
        self.history = []
        self.stop_reason, self.covered, self.noise_threshold = None, 0.0, None
        if self.noise_rule == "null":
            self.noise_threshold = self._threshold_in_noise()
        held: Set[Any] = set()
        total = self.cube.shape[0] if self.cover == "genes" else self.cube.shape[0] * self.cube.shape[1]
        best_significance: Optional[float] = None
        left_out = 0
        found: List[Tricluster] = []
        for index in range(self.n_triclusters):
            search = TriGenGA(fitness, self.sizes, hierarchy, first=index == 0,
                              population_size=self.population_size, generations=self.generations,
                              random_fraction=self.random_fraction, selection_rate=self.selection_rate,
                              mutation_probability=self.mutation_probability, form=self.form)
            search.run()
            chosen = _choose(search, set(found))
            record: Dict[str, Any] = {"search": index, "evaluations": search._evaluations,
                                      "seconds": search._seconds,
                                      "best_fitnesses": list(search.best_solution_fitnesses),
                                      "growth_evaluations": 0}
            if chosen is not None and self.growth is not None:
                score = fitness.evaluate if self.growth == "fitness" else fitness.quality
                quality_only = self.growth == "quality"
                grown, record["growth_evaluations"] = self.form.grow(
                    chosen, score, self.sizes, cube.shape, pruning=self.pruning,
                    adding_genes=lambda base, genes: fitness.adding_genes(base, genes, quality_only=quality_only),
                    moving_pixels=lambda base, added, removed: fitness.moving_pixels(base, added, removed,
                                                                                     quality_only=quality_only))
                if grown not in found:
                    chosen = grown
            terms = fitness.terms(chosen) if chosen is not None else {}
            if chosen is not None and self.stop == "coverage" and self.noise_rule is not None:
                significance = -terms["fitness"]
                noise = (significance <= (self.noise_threshold or 0.0) if self.noise_rule == "null"
                         else best_significance is not None and significance < self.decline * best_significance)
                if noise:
                    record["tricluster"], record["left_out"] = None, {"significance": significance}
                    self._write(record)
                    left_out += 1
                    if left_out >= self.patience:
                        self.stop_reason = "noise"
                        break
                    # Stopping at the first one left out cut what came after it: in the bench
                    # of stage 1, every tricluster above the threshold of the null rule was a
                    # planted one, also after one below it
                    # (metagen-auditoria/trigen/parada/etapa1/informe_parada_etapa1.md, 2).
                    # The one left out still counts as found, or the next search goes back to it.
                    passed = _with_fitness(chosen, terms["fitness"])
                    found.append(passed)
                    fitness.found.append(passed)
                    hierarchy.update(passed)
                    continue
                left_out = 0
                best_significance = significance if best_significance is None else max(best_significance,
                                                                                       significance)
            if chosen is None:
                metagen_logger.warning(f"TriGen search {index} evaluated no tricluster that had not been found "
                                       f"already: the search space has run out of new ones.")
                record["tricluster"] = None
                if self.stop == "coverage":
                    self._write(record)
                    self.stop_reason = "exhausted"
                    break
            else:
                chosen = _with_fitness(chosen, terms["fitness"])
                found.append(chosen)
                fitness.found.append(chosen)
                hierarchy.update(chosen)
                if order is not None:
                    chosen = Tricluster([order[position] for position in chosen.genes], chosen.conditions,
                                        chosen.times, fitness=terms["fitness"])
                record["tricluster"] = {"genes": list(chosen.genes), "conditions": list(chosen.conditions),
                                        "times": list(chosen.times)}
                if not chosen.is_cube:
                    record["tricluster"]["cells"] = [column.tolist() for column in chosen.cells()]
                record["sizes"] = list(chosen.size)
                record["fitness"] = terms["fitness"]
                record["terms"] = terms
                self.triclusters.append(chosen)
                if fitness is not self.fitness:
                    self.fitness.found.append(chosen)
                self.hierarchy.update(chosen)
                held |= set(chosen.genes) if self.cover == "genes" else set(prism_parts(chosen)[0])
                self.covered = len(held) / total
                record["covered"] = self.covered
            self._write(record)
            if self.stop == "coverage" and self.covered >= self.coverage:
                self.stop_reason = "coverage"
                break
        if self.stop_reason is None:
            self.stop_reason = "count" if self.stop == "count" else "maximum"
        self.finished = True
        return list(self.triclusters)

    def _write(self, record: Dict[str, Any]) -> None:
        self.history.append(record)
        if self.history_file is not None:
            with open(self.history_file, "a") as handle:
                handle.write(json.dumps(record) + "\n")

    def _threshold_in_noise(self) -> float:
        """The highest significance not already found of the triclusters a short run finds in
        the null cube of the data, drawn from the seeded generator."""
        # Three searches with the configuration of the run: the search finds in noise
        # triclusters as significant as in real data (metagen-auditoria/trigen/fase5d/
        # informe_5d.md, 1), so the threshold is what a search finds there, not what a
        # random tricluster scores.
        null = null_cube(self.cube, seed=int(get_numpy_rng().integers(0, 2 ** 31)))
        options = {**self.configuration(), "n_triclusters": NOISE_PROBES, "seed": None, "stop": "count",
                   "noise_rule": None, "patience": 1}
        probe = TriGen(null, **options)
        return max((-tricluster.fitness for tricluster in probe.run() if tricluster.fitness is not None),
                   default=0.0)

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
                "scoring": self.fitness.scoring, "pruning": self.pruning,
                "shuffle_genes": self.shuffle_genes, "overlap": self.fitness.overlap,
                "hierarchy": self.hierarchy_kind, "shape": self.form.name, "ordered": list(self.ordered),
                "neighborhood": self.neighborhood, "pixels": None if self.pixels is None else list(self.pixels),
                "stop": self.stop, "cover": self.cover, "coverage": self.coverage, "noise_rule": self.noise_rule,
                "decline": self.decline, "patience": self.patience})

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


def _with_fitness(tricluster: Tricluster, fitness: float) -> Tricluster:
    """The same tricluster, with a fitness."""
    if tricluster.is_cube:
        return Tricluster(tricluster.genes, tricluster.conditions, tricluster.times, fitness=fitness)
    return Tricluster.from_cells(*tricluster.cells(), fitness=fitness)


def _choose(search: TriGenGA, found: Set[Tricluster]) -> Optional[Tricluster]:
    """The best of the last population that is new; else the best new one evaluated."""
    for individual in sorted(search.current_solutions, key=Solution.get_fitness):
        tricluster = search.form.from_solution(individual)
        if tricluster not in found:
            return tricluster
    new = {tricluster: value for tricluster, value in search.evaluated.items() if tricluster not in found}
    return min(new, key=new.__getitem__) if new else None
