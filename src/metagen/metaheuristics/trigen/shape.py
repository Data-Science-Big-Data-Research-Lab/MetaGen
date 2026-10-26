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
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, cast

import numpy as np

from metagen.framework import Domain, Solution
from metagen.framework.rng import get_numpy_rng, get_rng
from metagen.metaheuristics.genetic.genetic_tools import GAConnector
from metagen.metaheuristics.tools import solution_class
from metagen.triclustering import surface as plane
from metagen.metaheuristics.trigen.population import DataHierarchy, Sizes, block, hierarchical, scattered
from metagen.triclustering import Cube, Tricluster
from metagen.triclustering.cube import AXES


class Shape(ABC):
    """
    What a kind of tricluster is to TriGen: how a search represents it, crosses and
    mutates it (the domain of its genetic algorithm), how it draws the triclusters a search
    starts from, how a tricluster found grows, and how the model of chance of the
    significance draws random ones. The rest of TriGen, the memory of what was found, the
    overlap and the hierarchy, works on the cells of a tricluster, whatever its shape.
    """

    #: The name of the shape, as ``TriGen(shape=...)`` takes it.
    name: str

    @abstractmethod
    def domain(self, shape: Sequence[int], sizes: Sizes) -> Domain:
        """The search space of a tricluster of a cube of a shape, between the sizes."""

    @abstractmethod
    def to_solution(self, tricluster: Tricluster, domain: Domain) -> Solution:
        """The solution of the domain that stands for a tricluster."""

    @abstractmethod
    def from_solution(self, solution: Solution) -> Tricluster:
        """The tricluster a solution of the domain stands for."""

    @abstractmethod
    def scattered(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        """A tricluster drawn at random over the whole cube."""

    @abstractmethod
    def block(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        """A tricluster of neighboring positions, drawn at random."""

    @abstractmethod
    def hierarchical(self, hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
        """A tricluster drawn from what the triclusters found have explored least."""

    @abstractmethod
    def grow(self, tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
             shape: Tuple[int, int, int], pruning: bool = False,
             adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None
             ) -> Tuple[Tricluster, int]:
        """The tricluster grown, and how many triclusters were scored; see :py:func:`grow`."""

    @abstractmethod
    def chance(self, shape: Sequence[int], size: Sequence[int]) -> Tricluster:
        """A random tricluster of a size, for the model of chance, drawn with MetaGen's NumPy
        generator."""

    def measured_size(self, tricluster: Tricluster) -> Tuple[int, ...]:
        """The size the model of chance reads a tricluster by: for a cube, its genes,
        conditions and times."""
        return tricluster.size

    def chance_extents(self, shape: Sequence[int]) -> Tuple[int, ...]:
        """The largest of each part of :py:meth:`measured_size` in a cube of a shape."""
        return tuple(shape)

    def size_shares(self, tricluster: Tricluster, references: Sequence[int]) -> Tuple[float, float, float]:
        """The size of a tricluster in each dimension as a share of its reference, for the
        size terms of the weighted fitness: for a cube, its genes, conditions and times."""
        genes, conditions, times = (len(positions) / reference for positions, reference in
                                    zip((tricluster.genes, tricluster.conditions, tricluster.times), references))
        return genes, conditions, times

    def values(self, cube: Cube, tricluster: Tricluster) -> Optional[np.ndarray]:
        """The values the quality of a tricluster is measured on, as (series, 1, times),
        when they are not the subcube of its genes, conditions and times; None for a cube."""
        return None

    def check_measure(self, measure: str, views: str) -> None:
        """Check that a quality term can measure this shape.

        :raises ValueError: if it cannot."""

    def shared(self, tricluster: Tricluster, other: Tricluster) -> Optional[Tricluster]:
        """The tricluster of what two triclusters share, for the significance against the
        triclusters found, or None if it is too small to measure: for cubes, the genes,
        conditions and times both hold, at least two of each."""
        for one in (tricluster, other):
            one.require_cube("The significance against the triclusters found")
        genes, conditions, times = (sorted(set(mine) & set(theirs)) for mine, theirs in
                                    zip((tricluster.genes, tricluster.conditions, tricluster.times),
                                        (other.genes, other.conditions, other.times)))
        if min(len(genes), len(conditions), len(times)) < 2:
            return None
        return Tricluster(genes, conditions, times)

    def __eq__(self, other: object) -> bool:
        return type(self) is type(other) and vars(self) == vars(other)

    def __hash__(self) -> int:
        return hash(type(self))

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class CubeShape(Shape):
    """
    The cube: every combination of some genes, some conditions and some times. In a
    dimension without order they are any subset of its positions; in one with order, a
    window, consecutive positions, which a search represents by its start and its length.

    :param ordered: The dimensions with order, 0 for the genes, 1 for the conditions and 2
        for the times; none by default.
    :type ordered: Sequence[int], optional
    """
    # A window is its start and its length, two integers that the genetic algorithm crosses
    # by BLX and mutates by a step. The start is cut to n - length, so that the window
    # fits; that gives the last start a little more weight than the others, which the
    # initial population, drawn with every start as likely, does not have
    # (metagen-auditoria/trigen/SPEC-C5-etapa2-ventanas.md, 2.2).

    name = "cube"

    def __init__(self, ordered: Sequence[int] = ()) -> None:
        self.ordered: Tuple[int, ...] = tuple(sorted(set(int(dimension) for dimension in ordered)))

    def domain(self, shape: Sequence[int], sizes: Sizes) -> Domain:
        return tricluster_domain(shape, sizes, self.ordered)

    def to_solution(self, tricluster: Tricluster, domain: Domain) -> Solution:
        solution = solution_class(domain)(domain, connector=domain.get_connector())
        for dimension, (axis, positions) in enumerate(zip(AXES, (tricluster.genes, tricluster.conditions,
                                                                  tricluster.times))):
            if dimension in self.ordered:
                solution.set(f"{axis}_start", positions[0])
                solution.set(f"{axis}_length", len(positions))
            else:
                solution.set(axis, list(positions))
        return solution

    def from_solution(self, solution: Solution) -> Tricluster:
        parts: List[Sequence[int]] = []
        for dimension, axis in enumerate(AXES):
            if dimension in self.ordered:
                # The start goes from 0 to n minus the smallest length, so n is its largest
                # value plus that length; a longer window starts at most at n - length.
                length = int(solution[f"{axis}_length"])
                extent = _bounds(solution, f"{axis}_start")[1] + _bounds(solution, f"{axis}_length")[0]
                start = min(int(solution[f"{axis}_start"]), extent - length)
                parts.append(range(start, start + length))
            else:
                parts.append(solution[axis])
        return Tricluster(parts[0], parts[1], parts[2])

    def scattered(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        return scattered(shape, sizes, self.ordered)

    def block(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        return block(shape, sizes)

    def hierarchical(self, hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
        return hierarchical(hierarchy, sizes, self.ordered)

    def grow(self, tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
             shape: Tuple[int, int, int], pruning: bool = False,
             adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None
             ) -> Tuple[Tricluster, int]:
        return grow(tricluster, score, sizes, shape, pruning=pruning, adding_genes=adding_genes,
                    ordered=self.ordered)

    def chance(self, shape: Sequence[int], size: Sequence[int]) -> Tricluster:
        rng = get_numpy_rng()
        parts: List[Any] = []
        for dimension, (extent, count) in enumerate(zip(shape, size)):
            if dimension in self.ordered:
                start = int(rng.integers(0, extent - count + 1))
                parts.append(range(start, start + count))
            else:
                parts.append(rng.choice(extent, count, replace=False))
        return Tricluster(parts[0], parts[1], parts[2])

    def __repr__(self) -> str:
        return f"CubeShape(ordered={self.ordered!r})"


class PrismShape(Shape):
    """
    The prism: a surface of the plane of the first two dimensions, pixels that are one
    piece through their neighbors, held along a window of the times, as a field through a
    season. Its cells are every pixel of the surface at every time of the window; a
    rectangle over a window is a cube. All three dimensions have an order.

    A search represents a prism by a seed pixel, steps of growth and a window. The surface
    starts at the seed, and each step ``k`` adds the free neighbor number ``k mod F`` of
    the ``F`` around it, in raster order, so that every combination of a seed and steps is
    a connected surface, and every connected surface has one; the genetic algorithm
    crosses and mutates the steps as a structure of integers of variable length.

    The quality of a prism is that of its pixels as series along the window: the cube of
    its pixels, one condition and its times, read with the times on the X axis.

    :param ordered: The dimensions with order, all three.
    :type ordered: Sequence[int], optional
    :param neighborhood: The neighbors of a pixel, 4 (those that share a side) or 8 (a
        side or a corner), defaults to 4.
    :type neighborhood: int, optional
    :param pixels: The fewest and most pixels of a surface, defaults to (4, 64).
    :type pixels: Sequence[int], optional
    :param box: The largest extent of a surface in each dimension of the plane, or None,
        the default, for no bound but the plane.
    :type box: Sequence[int], optional
    :raises ValueError: if a dimension is left without order, the neighborhood is not 4 or
        8, or the pixels are not at least 2 and at most what the box holds.
    """
    # The representation and its alternative, a mask over the box repaired to its largest
    # piece, are weighed in metagen-auditoria/trigen/SPEC-C5-etapa3-prisma.md, 2.2: with
    # the seed and the steps every child is a prism and MetaGen's crossover and mutation of
    # a structure of integers serve as they are. A step means another pixel when the
    # surface before it changes, which makes the crossover more disruptive than in a cube.

    name = "prism"

    def __init__(self, ordered: Sequence[int] = (0, 1, 2), neighborhood: int = 4,
                 pixels: Sequence[int] = (4, 64), box: Optional[Sequence[int]] = None) -> None:
        if sorted(set(int(dimension) for dimension in ordered)) != [0, 1, 2]:
            raise ValueError(f"A prism holds a surface of the plane of the {AXES[0]} and the {AXES[1]} over a "
                             f"window of the {AXES[2]}: all three dimensions have an order, ordered={list(AXES)}.")
        if neighborhood not in (4, 8):
            raise ValueError(f"neighborhood is 4 or 8, not {neighborhood!r}.")
        low, high = (int(count) for count in pixels)
        bound = None if box is None else (int(box[0]), int(box[1]))
        if not 2 <= low <= high or (bound is not None and high > bound[0] * bound[1]):
            raise ValueError(f"The pixels of a prism must satisfy 2 <= fewest ({low}) <= most ({high})"
                             + ("" if bound is None else f" <= the {bound[0] * bound[1]} pixels of a box of {bound}")
                             + ".")
        self.ordered: Tuple[int, ...] = (0, 1, 2)
        self.neighborhood = int(neighborhood)
        self.pixels: Tuple[int, int] = (low, high)
        self.box: Optional[plane.Box] = bound

    def domain(self, shape: Sequence[int], sizes: Sizes) -> Domain:
        rows, columns, times = shape
        low, high = self.pixels
        domain = Domain(GAConnector())
        _fixed_or_integer(domain, "seed_x", 0, rows - 1)
        _fixed_or_integer(domain, "seed_y", 0, columns - 1)
        domain.define_dynamic_structure("steps", low - 1, high - 1)
        # The frontier of a surface of n pixels has fewer than n · neighborhood pixels, so
        # every step of every surface is below this.
        domain.set_structure_to_integer("steps", 0, self.neighborhood * high - 1)
        smallest, largest = sizes[2]
        _fixed_or_integer(domain, "times_start", 0, times - smallest)
        _fixed_or_integer(domain, "times_length", smallest, largest)
        return domain

    def to_solution(self, tricluster: Tricluster, domain: Domain) -> Solution:
        solution = solution_class(domain)(domain, connector=domain.get_connector())
        pixels, times = prism_parts(tricluster)
        seed, steps = plane.encode(self._extent(solution), self.neighborhood, self.box, pixels)
        solution.set("seed_x", seed[0])
        solution.set("seed_y", seed[1])
        solution.set("steps", steps)
        solution.set("times_start", times[0])
        solution.set("times_length", len(times))
        return solution

    def from_solution(self, solution: Solution) -> Tricluster:
        length = int(solution["times_length"])
        extent = _bounds(solution, "times_start")[1] + _bounds(solution, "times_length")[0]
        start = min(int(solution["times_start"]), extent - length)
        pixels = plane.decode(self._extent(solution), self.neighborhood, self.box,
                              (int(solution["seed_x"]), int(solution["seed_y"])), solution["steps"])
        return prism(pixels, range(start, start + length))

    def _extent(self, solution: Solution) -> Tuple[int, int]:
        return _bounds(solution, "seed_x")[1] + 1, _bounds(solution, "seed_y")[1] + 1

    def scattered(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        rows, columns, times = shape
        rng = get_rng()
        seed = (rng.randrange(rows), rng.randrange(columns))
        pixels = plane.grow_by(seed, rng.randint(*self.pixels), (rows, columns), self.neighborhood, self.box,
                               lambda pixel: rng.random())
        return prism(pixels, _window(times, rng.randint(*sizes[2])))

    def block(self, shape: Sequence[int], sizes: Sizes) -> Tricluster:
        rows, columns, times = shape
        rectangles = _rectangles(self.pixels, self.box or (rows, columns), (rows, columns))
        if not rectangles:
            return self.scattered(shape, sizes)
        rng = get_rng()
        height, width = rng.choice(rectangles)
        top, left = rng.randint(0, rows - height), rng.randint(0, columns - width)
        pixels = [(x, y) for x in range(top, top + height) for y in range(left, left + width)]
        return prism(pixels, _window(times, rng.randint(*sizes[2])))

    def hierarchical(self, hierarchy: DataHierarchy, sizes: Sizes) -> Tricluster:
        rows, columns, times = (len(levels) for levels in hierarchy.levels)
        rng = get_rng()
        window = hierarchy.draw(2, rng.randint(*sizes[2]), window=True)
        if hierarchy.cells is not None:
            held = hierarchy.cells[:, :, window].sum(axis=2)
        else:
            held = np.add.outer(np.asarray(hierarchy.levels[0]), np.asarray(hierarchy.levels[1]))
        lowest = [(int(x), int(y)) for x, y in np.argwhere(held == held.min())]
        seed = lowest[0] if len(lowest) == 1 else rng.choice(lowest)
        # The least held neighbor first, ties drawn at random.
        pixels = plane.grow_by(seed, rng.randint(*self.pixels), (rows, columns), self.neighborhood, self.box,
                               lambda pixel: float(held[pixel]) + 0.5 * rng.random())
        return prism(pixels, window)

    def grow(self, tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
             shape: Tuple[int, int, int], pruning: bool = False,
             adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None
             ) -> Tuple[Tricluster, int]:
        """
        Grow a prism one step at a time, as :py:func:`grow` grows a cube: at each step, the
        pixel of the frontier or the time before or after the window that leaves the score
        lowest, while it is no higher than the current one and within the sizes, the
        pixels and the box. With ``pruning``, each step also weighs removing a pixel of the
        border that leaves the surface one piece, or the first or the last time, and stops
        when no step lowers the score. ``adding_genes`` is not used.
        """
        extent = (shape[0], shape[1])
        low, high = self.pixels
        smallest, largest = sizes[2]
        pixels, times = prism_parts(tricluster)
        surface, start, end = set(pixels), times[0], times[-1]
        current = score(tricluster)
        evaluations = 1
        while True:
            moves: List[Tuple[Set[plane.Pixel], int, int]] = []
            if len(surface) < high:
                fits = _fits_in_box(surface, self.box)
                moves += [(surface | {pixel}, start, end) for pixel in plane.frontier(surface, extent, self.neighborhood)
                          if fits(pixel)]
            if pruning and len(surface) > low:
                moves += [(surface - {pixel}, start, end)
                          for pixel in plane.removable(sorted(surface), extent, self.neighborhood)]
            if end - start + 1 < largest:
                moves += [(surface, first, last) for first, last in ((start - 1, end), (start, end + 1))
                          if 0 <= first and last < shape[2]]
            if pruning and end - start + 1 > smallest:
                moves += [(surface, start + 1, end), (surface, start, end - 1)]
            best: Optional[Tuple[float, Tuple[Set[plane.Pixel], int, int]]] = None
            for move in moves:
                value = score(prism(sorted(move[0]), range(move[1], move[2] + 1)))
                evaluations += 1
                better = value < current if pruning else value <= current
                if better and (best is None or value < best[0]):
                    best = (value, move)
            if best is None:
                return prism(sorted(surface), range(start, end + 1)), evaluations
            current = best[0]
            surface, start, end = best[1]

    def chance(self, shape: Sequence[int], size: Sequence[int]) -> Tricluster:
        rows, columns, times = shape
        count, length = int(size[0]), int(size[1])
        rng = get_numpy_rng()
        seed = (int(rng.integers(0, rows)), int(rng.integers(0, columns)))
        # Every pixel added puts at most one draw per neighbor on the frontier.
        draws = iter(rng.random(self.neighborhood * (count + 1)).tolist())
        pixels = plane.grow_by(seed, count, (rows, columns), self.neighborhood, None, lambda pixel: next(draws))
        start = int(rng.integers(0, times - length + 1))
        return prism(pixels, range(start, start + length))

    def measured_size(self, tricluster: Tricluster) -> Tuple[int, ...]:
        """The pixels and the times of a prism."""
        return tricluster.n_cells // len(tricluster.times), len(tricluster.times)

    def chance_extents(self, shape: Sequence[int]) -> Tuple[int, ...]:
        return shape[0] * shape[1], shape[2]

    def size_shares(self, tricluster: Tricluster, references: Sequence[int]) -> Tuple[float, float, float]:
        """The genes and the conditions both take the side of a square of the area of the
        surface, the square root of its share of the pixels of the plane of reference, as
        a square takes its rows and its columns; the times take the share of the window."""
        # By the rows and the columns it spans, as for a cube, the weighted fitness rewarded
        # small surfaces strewn over a wide extent: 13 pixels over 6 x 6 where 150 were
        # planted, and 0.574 of a rectangle the cube recovers at 0.875; by the share of the
        # pixels itself, the reward is so small that the surfaces shrink to the fewest
        # pixels (metagen-auditoria/trigen/c5/informe_c5_etapa3.md, 3).
        pixels, times = self.measured_size(tricluster)
        side = math.sqrt(pixels / (references[0] * references[1]))
        return side, side, times / references[2]

    def values(self, cube: Cube, tricluster: Tricluster) -> Optional[np.ndarray]:
        pixels, times = prism_parts(tricluster)
        rows = np.fromiter((pixel[0] for pixel in pixels), dtype=np.int64, count=len(pixels))
        columns = np.fromiter((pixel[1] for pixel in pixels), dtype=np.int64, count=len(pixels))
        return cube.values[rows[:, None], columns[:, None], np.asarray(times)[None, :]][:, None, :]

    def check_measure(self, measure: str, views: str) -> None:
        if measure not in ("msl", "lsl") or views != "time":
            raise ValueError(f"A prism is measured by its pixels as series along its window, with measure 'msl' "
                             f"or 'lsl' and views='time', not measure={measure!r} and views={views!r}: the order "
                             f"of the pixels of a surface is not an order of the data.")

    def shared(self, tricluster: Tricluster, other: Tricluster) -> Optional[Tricluster]:
        """The pixels and the times two prisms share, at least two of each."""
        mine, my_times = prism_parts(tricluster)
        theirs, their_times = prism_parts(other)
        pixels = sorted(set(mine) & set(theirs))
        times = sorted(set(my_times) & set(their_times))
        if len(pixels) < 2 or len(times) < 2:
            return None
        return prism(pixels, times)

    def __repr__(self) -> str:
        return f"PrismShape(neighborhood={self.neighborhood!r}, pixels={self.pixels!r}, box={self.box!r})"


def prism(pixels: Sequence[plane.Pixel], times: Sequence[int], fitness: Optional[float] = None) -> Tricluster:
    """
    The tricluster of a surface over some times: every pixel at every time.

    :param pixels: The pixels, a gene and a condition each.
    :type pixels: Sequence[Pixel]
    :param times: The times.
    :type times: Sequence[int]
    :param fitness: Its fitness, if any.
    :type fitness: float, optional
    :return: The tricluster, a cube if the surface is a rectangle of at least 2 × 2.
    :rtype: Tricluster
    """
    held = np.asarray(sorted(pixels), dtype=np.int64).reshape(-1, 2)
    span = np.asarray(list(times), dtype=np.int64)
    g, c, t = np.repeat(held[:, 0], span.size), np.repeat(held[:, 1], span.size), np.tile(span, len(held))
    # Growing a prism builds one for every move it weighs, hundreds of thousands in a run
    # over a satellite tile, and checking and sorting the cells of each took more than
    # scoring it: distinct pixels in raster order over increasing times are cells already
    # sorted and distinct (metagen-auditoria/trigen/c5/informe_c5_etapa3_pastis.md, 2).
    if (len(g) >= 2 and held.min() >= 0 and span.min() >= 0 and bool(np.all(np.diff(span) > 0))
            and not bool(np.any(np.all(np.diff(held, axis=0) == 0, axis=1)))):
        return Tricluster._from_sorted_cells(g, c, t, fitness)
    return Tricluster.from_cells(g, c, t, fitness=fitness)


def prism_parts(tricluster: Tricluster) -> Tuple[List[plane.Pixel], Tuple[int, ...]]:
    """
    The pixels and the times of a prism.

    :param tricluster: The prism.
    :type tricluster: Tricluster
    :return: Its pixels, in raster order, and its times.
    :rtype: Tuple[List[Pixel], Tuple[int, ...]]
    :raises ValueError: if it is not a surface held at the same times at every pixel.
    """
    times = tricluster.times
    if tricluster.is_cube:
        return [(gene, condition) for gene in tricluster.genes for condition in tricluster.conditions], times
    genes, conditions, held = tricluster.cells()
    count = len(genes) // len(times)
    if count * len(times) != len(genes) or not np.array_equal(held.reshape(count, len(times)),
                                                              np.tile(np.asarray(times), (count, 1))):
        raise ValueError("A prism holds the same times at each of its pixels; this tricluster does not.")
    step = len(times)
    return list(zip(genes[::step].tolist(), conditions[::step].tolist())), times


def _fits_in_box(surface: Set[plane.Pixel], box: Optional[plane.Box]) -> Callable[[plane.Pixel], bool]:
    """Whether a pixel added to a surface keeps it within the box, with the extent of the
    surface found once for all the pixels of its frontier."""
    if box is None:
        return lambda pixel: True
    low = [min(held[axis] for held in surface) for axis in (0, 1)]
    high = [max(held[axis] for held in surface) for axis in (0, 1)]
    return lambda pixel: all(max(high[axis], pixel[axis]) - min(low[axis], pixel[axis]) < box[axis]
                             for axis in (0, 1))


@lru_cache(maxsize=64)
def _rectangles(pixels: Tuple[int, int], box: Tuple[int, int], extent: Tuple[int, int]) -> List[Tuple[int, int]]:
    """The heights and widths of the rectangles that fit in the box and the plane with a
    number of pixels within the bounds."""
    low, high = pixels
    return [(height, width) for height in range(1, min(box[0], extent[0]) + 1)
            for width in range(1, min(box[1], extent[1]) + 1) if low <= height * width <= high]


def _window(length: int, size: int) -> range:
    start = get_rng().randint(0, length - size)
    return range(start, start + size)


#: The shapes TriGen knows, by name.
SHAPES: Dict[str, Any] = {CubeShape.name: CubeShape, PrismShape.name: PrismShape}


def shape_named(name: str, ordered: Sequence[int] = (), **options: Any) -> Shape:
    """
    The shape of a name.

    :param name: Its name, ``"cube"`` or ``"prism"``.
    :type name: str
    :param ordered: The dimensions with order, none by default.
    :type ordered: Sequence[int], optional
    :param options: The options of the shape, such as the ``neighborhood`` of a prism.
    :return: The shape.
    :rtype: Shape
    :raises ValueError: if no shape has that name.
    """
    if name not in SHAPES:
        raise ValueError(f"shape is one of {sorted(SHAPES)}, not {name!r}.")
    return SHAPES[name](ordered, **options)


def _bounds(solution: Solution, name: str) -> Tuple[int, int]:
    """The smallest and largest value of a variable of a window: an integer, or a
    categorical of one value when it can only take that one."""
    attributes = cast(Any, solution.get(name)).get_definition().get_attributes()
    if attributes[0] == "CATEGORICAL":
        return int(attributes[1][0]), int(attributes[1][0])
    return int(attributes[1]), int(attributes[2])


def _fixed_or_integer(domain: Domain, name: str, low: int, high: int) -> None:
    """An integer between two values, or, when they are the same, a categorical of that one,
    since an integer needs its minimum below its maximum."""
    if low == high:
        domain.define_categorical(name, [low])
    else:
        domain.define_integer(name, low, high)


def tricluster_domain(shape: Sequence[int], sizes: Sizes, ordered: Sequence[int] = ()) -> Domain:
    """
    The search space of a tricluster: three subsets, of the genes, the conditions and the
    times of a cube, each between its smallest and largest size. A dimension with order is
    a window instead, two variables, ``<axis>_start`` and ``<axis>_length``.

    :param shape: The number of genes, conditions and times of the cube.
    :type shape: Sequence[int]
    :param sizes: The smallest and largest size of each dimension.
    :type sizes: Sizes
    :param ordered: The dimensions with order, none by default.
    :type ordered: Sequence[int], optional
    :return: The domain, with the connector of the genetic algorithms.
    :rtype: Domain
    """
    domain = Domain(GAConnector())
    for dimension, (axis, length, (smallest, largest)) in enumerate(zip(AXES, shape, sizes)):
        if dimension in ordered:
            _fixed_or_integer(domain, f"{axis}_start", 0, length - smallest)
            _fixed_or_integer(domain, f"{axis}_length", smallest, largest)
        else:
            domain.define_subset(axis, list(range(length)), smallest, largest)
    return domain


def grow(tricluster: Tricluster, score: Callable[[Tricluster], float], sizes: Sizes,
         shape: Tuple[int, int, int], pruning: bool = False,
         adding_genes: Optional[Callable[[Tricluster, List[int]], Optional[Any]]] = None,
         ordered: Sequence[int] = ()) -> Tuple[Tricluster, int]:
    """
    Grow a tricluster one coordinate at a time: at each step, the gene, condition or time,
    of a dimension below its largest size, that leaves the score lowest, as long as that
    score is no higher than the current one. Ties go to the first dimension, then to the
    first position.

    With ``pruning``, each step also weighs removing a gene, condition or time from a
    dimension above its smallest size, takes the addition or removal that leaves the score
    lowest, and stops when none leaves it lower than the current one.

    In a dimension with order, where the tricluster holds a window, a step only adds the
    position before it or the one after it and, with ``pruning``, only removes its first or
    its last, so that it stays a window.

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
    :param adding_genes: What scores the tricluster with each of many genes added at once,
        the same, but for rounding, as ``score`` on each, such as
        :py:meth:`TriclusterFitness.adding_genes`; when it gives None, or without it, each
        is scored with ``score``.
    :type adding_genes: Callable, optional
    :param ordered: The dimensions with order, none by default.
    :type ordered: Sequence[int], optional
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
                if dimension in ordered:
                    ends = (min(held) - 1, max(held) + 1)
                    additions = [position for position in ends if 0 <= position < shape[dimension]]
                else:
                    additions = [position for position in range(shape[dimension]) if position not in held]
                values = (adding_genes(Tricluster(parts[0], parts[1], parts[2]), additions)
                          if dimension == 0 and adding_genes is not None and additions else None)
                if values is None:
                    moves += [parts[dimension] + [position] for position in additions]
                else:
                    # The same choice as scoring them one by one: the first lowest that qualifies.
                    evaluations += len(additions)
                    qualifies = values < current if pruning else values <= current
                    if qualifies.any():
                        index = int(np.flatnonzero(qualifies)[np.argmin(values[qualifies])])
                        if best is None or values[index] < best[0]:
                            best = (float(values[index]), dimension, parts[dimension] + [additions[index]])
            if pruning and len(parts[dimension]) > low:
                removable = ((min(parts[dimension]), max(parts[dimension])) if dimension in ordered
                             else parts[dimension])
                moves += [[kept for kept in parts[dimension] if kept != removed] for removed in removable]
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
