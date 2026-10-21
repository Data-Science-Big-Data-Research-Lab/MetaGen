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

import math
from dataclasses import dataclass
from typing import Any, Collection, List, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class Stability:
    """
    How much a tricluster recurs in the other runs of a search on the same data.

    :param stability: The share of the pairs of its genes that share a tricluster in each
        of the other runs, on average, from 0 to 1.
    :param chance: The same share were the triclusters of the other runs genes drawn at
        random, of their same sizes.
    :param core: Its genes that, in at least a share of the other runs, are in the tricluster
        that shares most genes with it, in the order of its genes (sorted, when they come as
        a set).
    """

    stability: float
    chance: float
    core: Tuple[Any, ...]


def stability(runs: Sequence[Any], population: Optional[int] = None, share: float = 0.5) -> List[List[Stability]]:
    """
    How much each tricluster of several runs of a search on the same data recurs in the
    others, by the names of its genes: for each, the share of the pairs of its genes that
    share a tricluster in the other runs, what that share would be by chance, and its core,
    the genes that keep turning up together with it. The runs are compared by the names of
    the genes, so they may have searched the genes in different orders.

    .. code-block:: python

        from metagen.triclustering import stability

        runs = [[{"a", "b", "c", "d"}, {"x", "y", "z"}],
                [{"a", "b", "c", "e"}, {"p", "q", "r"}],
                [{"a", "b", "d", "f"}, {"x", "q", "s"}]]
        first = stability(runs, population=20)[0]
        print(first[0].stability, round(first[0].chance, 3), first[0].core)   # 0.5 0.047 ('a', 'b', 'c', 'd')
        print(first[1].stability, first[1].core)                              # 0.0 ('x',)

    :param runs: The runs, each its triclusters, a collection of the names of the genes of
        each; or the results of the runs, :py:class:`~metagen.metaheuristics.TriGenResult`,
        whose names it takes.
    :type runs: Sequence
    :param population: The number of genes of the data; by default, that of the shape of the
        first result. It sets what is expected by chance.
    :type population: int, optional
    :param share: The share of the other runs in which a gene of the core turns up, defaults
        to 0.5.
    :type share: float, optional
    :return: For each run, a :py:class:`Stability` per tricluster, in their order. A
        tricluster with fewer than two different genes has no pairs: its stability and its
        chance are not a number.
    :rtype: List[List[Stability]]
    :raises ValueError: if there are fewer than two runs, the population is missing or
        smaller than a tricluster, or the share is not in (0, 1].
    """
    sets, population = _runs(runs, population)
    if not 0 < share <= 1:
        raise ValueError(f"share is in (0, 1], not {share}.")
    pairs = population * (population - 1) / 2
    together_by_chance = [1.0 - math.prod(1.0 - len(found) * (len(found) - 1) / 2 / pairs for found in run)
                          for run in sets]
    result = []
    for index, run in enumerate(sets):
        others = [other for other in range(len(sets)) if other != index]
        measured = []
        for genes in run:
            ordered = list(genes)
            count = len(ordered)
            shares, chances = [], []
            turns = dict.fromkeys(ordered, 0)
            for other in others:
                if count >= 2:
                    member = np.array([[gene in found for found in sets[other]] for gene in ordered], dtype=float)
                    together = (member @ member.T) > 0
                    shares.append(float(np.triu(together, k=1).sum()) / (count * (count - 1) / 2))
                    chances.append(together_by_chance[other])
                best = max(sets[other], key=lambda found: len(genes & found)) if sets[other] else set()
                for gene in genes & best:
                    turns[gene] += 1
            core = tuple(gene for gene in ordered if turns[gene] >= share * len(others))
            measured.append(Stability(float(np.mean(shares)) if shares else math.nan,
                                      float(np.mean(chances)) if chances else math.nan, core))
        result.append(measured)
    return result


def _runs(runs: Sequence[Any], population: Optional[int]) -> Tuple[List[List[Any]], int]:
    """The runs as lists of ordered sets of gene names, and the population."""
    if len(runs) < 2:
        raise ValueError(f"Stability compares runs: give at least two, not {len(runs)}.")
    sets: List[List[Any]] = []
    for run in runs:
        if hasattr(run, "names") and hasattr(run, "data"):
            if population is None:
                population = int(run.data["shape"][0])
            for tricluster in getattr(run, "triclusters", ()):
                tricluster.require_cube("Stability")
            found = [names["genes"] for names in run.names]
        else:
            found = list(run)
        sets.append([_OrderedSet(genes) for genes in found])
    if population is None:
        raise ValueError("Give the population, the number of genes of the data.")
    largest = max((len(genes) for run in sets for genes in run), default=0)
    if population < max(2, largest):
        raise ValueError(f"The population, {population}, is smaller than a tricluster, of {largest} genes.")
    return sets, population


class _OrderedSet(set):
    """A set that remembers the order in which its elements were given, or sorts them when
    they come as a set, whose order would change from one run of Python to another."""

    def __init__(self, items: Collection[Any]) -> None:
        if isinstance(items, (set, frozenset)):
            try:
                items = sorted(items)
            except TypeError:
                items = sorted(items, key=repr)
        unique = list(dict.fromkeys(items))
        super().__init__(unique)
        self._order = unique

    def __iter__(self):  # type: ignore[no-untyped-def]
        return iter(self._order)
