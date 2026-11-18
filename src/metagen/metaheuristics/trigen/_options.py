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

from typing import Any, Optional, Sequence, Tuple

from metagen.metaheuristics.trigen.trigen_ga import require_integer, validate
from metagen.triclustering import Cube
from metagen.triclustering.cube import AXES

# What TriGen checks of its options, by group, in the order its constructor checks them: the
# constructor held some 70 lines of checks among the building of its shape and its fitness
# (OF-17 of the independent audit). The messages are the ones the tests check.


def check_search(cube: Cube, n_triclusters: int, population_size: int, generations: int, random_fraction: float,
                 selection_rate: float, mutation_probability: float, min_sizes: Sequence[int],
                 max_sizes: Optional[Sequence[int]]) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    """
    Check the number of triclusters, the parameters of a search and the sizes.

    :return: The smallest and the largest sizes, the largest those of the cube when not given.
    :raises ValueError: if one of them is not valid.
    """
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
    return smallest, largest


def check_layout(growth: Any, hierarchy: Any, ordered: Sequence[str], neighborhood: int) -> None:
    """
    Check the growth, the hierarchy, the dimensions with order and the neighborhood.

    :raises ValueError: if one of them is not valid.
    """
    if growth not in ("fitness", "quality", None):
        raise ValueError(f"growth is 'fitness', 'quality' or None, not {growth!r}.")
    if hierarchy not in ("coordinates", "cells"):
        raise ValueError(f"hierarchy is 'coordinates' or 'cells', not {hierarchy!r}.")
    if isinstance(ordered, str) or any(axis not in AXES for axis in ordered) or len(set(ordered)) != len(ordered):
        raise ValueError(f"ordered names dimensions of {list(AXES)}, each once, not {ordered!r}.")
    if neighborhood not in (4, 8):
        raise ValueError(f"neighborhood is 4 or 8, not {neighborhood!r}.")


def check_shape(shape: str, shuffle_genes: bool, pixels: Optional[Sequence[int]], smallest: Tuple[int, ...],
                largest: Tuple[int, ...]) -> Optional[Tuple[int, int]]:
    """
    Check the options of the shape: what only a prism takes, and its pixels.

    :return: The fewest and most pixels of a prism, from the sizes when not given; None for
        the other shapes.
    :raises ValueError: if one of them is not valid.
    """
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
        return int(pixels[0]), int(pixels[1])
    if pixels is not None:
        raise ValueError("pixels bound the surface of a prism, shape='prism'.")
    return None


def check_stop(shape: str, stop: Any, cover: Any, coverage: float, noise_rule: Any, scoring: Any, decline: float,
               patience: int, disjoint: Any) -> Any:
    """
    Check when a run ends and what it counts, and whether the triclusters are disjoint.

    :return: What the coverage counts, the pixels for a prism and the genes otherwise when
        not given.
    :raises ValueError: if one of them is not valid.
    """
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
    require_integer("patience", patience)
    if patience < 1:
        raise ValueError(f"patience is at least 1, not {patience}.")
    if not isinstance(disjoint, bool):
        raise ValueError(f"disjoint is True or False, not {disjoint!r}.")
    if disjoint and shape == "prism" and cover != "pixels":
        raise ValueError("With a prism, disjoint keeps the pixels of the prisms apart: cover='pixels'.")
    return cover
