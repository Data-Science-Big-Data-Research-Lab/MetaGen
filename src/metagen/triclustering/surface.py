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

import bisect
import heapq
from functools import lru_cache
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Sequence, Set, Tuple

#: A pixel of the plane: its gene and its condition, the first two dimensions of a cube.
Pixel = Tuple[int, int]

#: The largest extent a surface may span in each of the two dimensions of the plane.
Box = Tuple[int, int]

_FOUR = ((-1, 0), (0, -1), (0, 1), (1, 0))
_EIGHT = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))


def neighbors(pixel: Pixel, extent: Tuple[int, int], neighborhood: int) -> List[Pixel]:
    """
    The pixels next to a pixel in a plane of an extent: the 4 that share a side with it,
    or with ``neighborhood=8`` the 8 that share a side or a corner, those inside the plane.

    :param pixel: The pixel.
    :type pixel: Pixel
    :param extent: The size of the plane in its two dimensions.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :return: Its neighbors, in raster order.
    :rtype: List[Pixel]
    """
    x, y = pixel
    rows, columns = extent
    return [(x + dx, y + dy) for dx, dy in (_FOUR if neighborhood == 4 else _EIGHT)
            if 0 <= x + dx < rows and 0 <= y + dy < columns]


def connected(surface: Iterable[Pixel], neighborhood: int) -> bool:
    """
    Whether a set of pixels is one piece: every pixel reaches every other through
    neighbors in the set.

    :param surface: The pixels.
    :type surface: Iterable[Pixel]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :return: Whether it is connected; an empty set is not.
    :rtype: bool
    """
    held = set(surface)
    if not held:
        return False
    start = next(iter(held))
    reached, stack = {start}, [start]
    steps = _FOUR if neighborhood == 4 else _EIGHT
    while stack:
        x, y = stack.pop()
        for dx, dy in steps:
            other = (x + dx, y + dy)
            if other in held and other not in reached:
                reached.add(other)
                stack.append(other)
    return len(reached) == len(held)


class _Growing:
    """A surface as it grows from a seed: its pixels, its extent so far, and, if
    ``ordered``, its frontier, the free neighbors of its pixels, kept in raster order."""

    def __init__(self, seed: Pixel, extent: Tuple[int, int], neighborhood: int, box: Optional[Box],
                 ordered: bool = True) -> None:
        self.extent, self.neighborhood, self.box, self.ordered = extent, neighborhood, box, ordered
        self.held: Set[Pixel] = set()
        self.frontier: List[int] = []          # the pixels as x · columns + y, sorted
        self.on_frontier: Set[int] = set()
        self.low, self.high = list(seed), list(seed)
        self.add(seed)

    def key(self, pixel: Pixel) -> int:
        return pixel[0] * self.extent[1] + pixel[1]

    def pixel(self, key: int) -> Pixel:
        x, y = divmod(key, self.extent[1])
        return x, y

    def fits(self, pixel: Pixel) -> bool:
        """Whether the surface with the pixel still fits in the box."""
        if self.box is None:
            return True
        return all(max(self.high[axis], pixel[axis]) - min(self.low[axis], pixel[axis]) < self.box[axis]
                   for axis in (0, 1))

    def add(self, pixel: Pixel) -> None:
        self.held.add(pixel)
        for axis in (0, 1):
            self.low[axis], self.high[axis] = min(self.low[axis], pixel[axis]), max(self.high[axis], pixel[axis])
        if not self.ordered:
            return
        key = self.key(pixel)
        if key in self.on_frontier:
            self.on_frontier.remove(key)
            del self.frontier[bisect.bisect_left(self.frontier, key)]
        for other in neighbors(pixel, self.extent, self.neighborhood):
            other_key = self.key(other)
            if other not in self.held and other_key not in self.on_frontier:
                self.on_frontier.add(other_key)
                bisect.insort(self.frontier, other_key)


def decode(extent: Tuple[int, int], neighborhood: int, box: Optional[Box], seed: Pixel,
           steps: Sequence[int]) -> Tuple[Pixel, ...]:
    """
    The surface a seed and some steps stand for. It starts at the seed, and each step
    ``k`` adds the free neighbor number ``k mod F`` of the ``F`` around the surface, in
    raster order; if that one would take the surface out of the box, the next one in that
    order that does not. It stops early only when no free neighbor fits.

    :param extent: The size of the plane.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :param box: The largest extent of the surface in each dimension, or None.
    :type box: Box, optional
    :param seed: The pixel it starts at.
    :type seed: Pixel
    :param steps: The steps.
    :type steps: Sequence[int]
    :return: Its pixels, in raster order: one more than the steps, but if it stopped early.
    :rtype: Tuple[Pixel, ...]
    """
    return _decode(tuple(extent), neighborhood, None if box is None else tuple(box), tuple(seed),
                   tuple(int(step) for step in steps))


# A search decodes every individual it evaluates and again every individual it records,
# and most of them are the same as one decoded before.
@lru_cache(maxsize=8192)
def _decode(extent: Tuple[int, int], neighborhood: int, box: Optional[Box], seed: Pixel,
            steps: Tuple[int, ...]) -> Tuple[Pixel, ...]:
    growing = _Growing(seed, extent, neighborhood, box)
    for step in steps:
        count = len(growing.frontier)
        chosen = None
        for offset in range(count):
            candidate = growing.pixel(growing.frontier[(step + offset) % count])
            if growing.fits(candidate):
                chosen = candidate
                break
        if chosen is None:
            break
        growing.add(chosen)
    return tuple(sorted(growing.held))


def encode(extent: Tuple[int, int], neighborhood: int, box: Optional[Box],
           surface: Iterable[Pixel]) -> Tuple[Pixel, List[int]]:
    """
    A seed and the steps that :py:func:`decode` takes to a surface: the seed is its first
    pixel in raster order, and each step adds its first pixel on the frontier.

    :param extent: The size of the plane.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :param box: The largest extent of a surface in each dimension, or None.
    :type box: Box, optional
    :param surface: The pixels, connected, and within the box.
    :type surface: Iterable[Pixel]
    :return: The seed and the steps.
    :rtype: Tuple[Pixel, List[int]]
    :raises ValueError: if the surface is not connected.
    """
    target = sorted(set(surface))
    if not connected(target, neighborhood):
        raise ValueError(f"A surface is one piece of neighboring pixels, {neighborhood} around each; this one is not.")
    wanted = set(target)
    growing = _Growing(target[0], extent, neighborhood, box)
    steps: List[int] = []
    while len(growing.held) < len(wanted):
        index = next(position for position, key in enumerate(growing.frontier) if growing.pixel(key) in wanted)
        steps.append(index)
        growing.add(growing.pixel(growing.frontier[index]))
    return target[0], steps


def grow_by(seed: Pixel, size: int, extent: Tuple[int, int], neighborhood: int, box: Optional[Box],
            priority: Callable[[Pixel], float], blocked: FrozenSet[Pixel] = frozenset()) -> Tuple[Pixel, ...]:
    """
    A surface of ``size`` pixels grown from a seed, taking each time the free neighbor of
    lowest priority that fits in the box and is not blocked. With random priorities, a
    random surface; with the occupation of each pixel, the least occupied one.

    :param seed: The pixel it starts at.
    :type seed: Pixel
    :param size: How many pixels.
    :type size: int
    :param extent: The size of the plane.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :param box: The largest extent of the surface in each dimension, or None.
    :type box: Box, optional
    :param priority: The priority of a pixel, drawn once, when it reaches the frontier.
    :type priority: Callable[[Pixel], float]
    :param blocked: Pixels it may not take, defaults to none.
    :type blocked: FrozenSet[Pixel], optional
    :return: Its pixels, in raster order; fewer than ``size`` if no more fit.
    :rtype: Tuple[Pixel, ...]
    """
    # It keeps its own frontier by priority: the one in raster order is what decoding needs,
    # and keeping it took nearly half of drawing a surface.
    growing = _Growing(seed, extent, neighborhood, box, ordered=False)
    queue: List[Tuple[float, int]] = []
    seen: Dict[int, None] = {}

    def push(pixel: Pixel) -> None:
        for other in neighbors(pixel, extent, neighborhood):
            key = growing.key(other)
            if other not in growing.held and other not in blocked and key not in seen:
                seen[key] = None
                heapq.heappush(queue, (priority(other), key))

    push(seed)
    while len(growing.held) < size and queue:
        _, key = heapq.heappop(queue)
        pixel = growing.pixel(key)
        if growing.fits(pixel):
            growing.add(pixel)
            push(pixel)
        else:
            # It may fit later only if it did not fit for being far; the box only grows
            # tighter around the surface, so it never will.
            continue
    return tuple(sorted(growing.held))


def frontier(surface: Iterable[Pixel], extent: Tuple[int, int], neighborhood: int) -> List[Pixel]:
    """
    The free neighbors of a surface, in raster order.

    :param surface: The pixels.
    :type surface: Iterable[Pixel]
    :param extent: The size of the plane.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :return: The pixels next to the surface and not in it.
    :rtype: List[Pixel]
    """
    held = set(surface)
    around = {other for pixel in held for other in neighbors(pixel, extent, neighborhood)}
    return sorted(around - held)


def removable(surface: Sequence[Pixel], extent: Tuple[int, int], neighborhood: int) -> List[Pixel]:
    """
    The pixels of a surface whose removal leaves it one piece: those on its border, with a
    free neighbor or on the edge of the plane, that do not join two parts of it.

    :param surface: The pixels, connected.
    :type surface: Sequence[Pixel]
    :param extent: The size of the plane.
    :type extent: Tuple[int, int]
    :param neighborhood: 4 or 8.
    :type neighborhood: int
    :return: The pixels that can go, in raster order.
    :rtype: List[Pixel]
    """
    held = set(surface)
    if len(held) < 2:
        return []
    steps = _FOUR if neighborhood == 4 else _EIGHT
    border = [pixel for pixel in sorted(held)
              if any((pixel[0] + dx, pixel[1] + dy) not in held for dx, dy in steps)]
    return [pixel for pixel in border if connected(held - {pixel}, neighborhood)]
