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

# Reading a cube from text files: a long table, or a matrix per time.

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import AXES, Cube


#: What a text file may write for a missing value, by default.
MISSING: Tuple[str, ...] = ("", "NA", "N/A", "NaN", "nan", "null", "NULL")


def read_long(path: str, gene: str = "gene", condition: str = "condition", time: str = "time",
              value: str = "value", sep: Optional[str] = None, missing: Sequence[str] = MISSING,
              genes: Optional[Sequence[Any]] = None, conditions: Optional[Sequence[Any]] = None,
              times: Optional[Sequence[Any]] = None, drop_missing: Optional[str] = None) -> Cube:
    """
    Read a cube from a long table: a text file with a header and a row per value, with a
    column for the gene, one for the condition, one for the time and one for the value,
    in any order and among any other columns. It is the simplest format to exchange data
    in, the one a spreadsheet or a data frame in R or pandas writes.

    The genes, the conditions and the times come in the order in which they first appear,
    or in the order given. A name made only of integers, or only of numbers, is read as
    one. A cell with no row, or with a value that the file writes as missing, is missing.

    .. code-block:: python

        from metagen.triclustering.data import read_long

        rows = ["gene,condition,time,value"] + [f"g{g},c{c},{t},{g + c * t}"
                                                for g in range(4) for c in range(2) for t in (0, 6, 12)]
        open("long.csv", "w").write("\\n".join(rows) + "\\n")
        cube = read_long("long.csv")
        print(cube.shape, cube.times)                          # (4, 2, 3) (0, 6, 12)
        print(cube.values[3, 1].tolist())                      # [3.0, 9.0, 15.0]

    :param path: The file.
    :type path: str
    :param gene: The header of the column of the genes, defaults to ``"gene"``.
    :type gene: str, optional
    :param condition: The header of the column of the conditions, defaults to ``"condition"``.
    :type condition: str, optional
    :param time: The header of the column of the times, defaults to ``"time"``.
    :type time: str, optional
    :param value: The header of the column of the values, defaults to ``"value"``.
    :type value: str, optional
    :param sep: The separator of the columns; by default, a tab for ``.tsv`` and ``.tab``
        files and otherwise the one of ``,``, ``;`` and tab that the header uses.
    :type sep: str, optional
    :param missing: What the file writes for a missing value, defaults to the empty cell,
        ``NA``, ``N/A``, ``NaN`` and ``null``.
    :type missing: Sequence[str], optional
    :param genes: The genes, in the order wanted; by default, all, as they first appear.
    :type genes: Sequence, optional
    :param conditions: The conditions, in the order wanted.
    :type conditions: Sequence, optional
    :param times: The times, in the order wanted.
    :type times: Sequence, optional
    :param drop_missing: With missing cells, the axis along which to drop every position
        that holds one, as :py:meth:`Cube.without_missing` does; None, the default, makes
        them an error.
    :type drop_missing: str, optional
    :return: The cube.
    :rtype: Cube
    :raises ValueError: if a column is not in the header, a value is not a number, a cell
        appears twice, or cells are missing and ``drop_missing`` is None.
    """
    rows = _rows(path, sep)
    header, body = rows[0], rows[1:]
    columns = []
    for name in (gene, condition, time, value):
        if name not in header:
            raise ValueError(f"{path} has no column {name!r}; its columns are {header}.")
        columns.append(header.index(name))
    gaps = set(missing)
    cells: Dict[Tuple[str, str, str], float] = {}
    for line, row in enumerate(body, start=2):
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))
        key = (row[columns[0]], row[columns[1]], row[columns[2]])
        if key in cells:
            raise ValueError(f"Line {line} of {path} repeats the cell of gene {key[0]!r}, condition {key[1]!r} "
                             f"and time {key[2]!r}.")
        cells[key] = parsed_number(row[columns[3]], gaps, path, line)
    labels = [_ordered([key[axis] for key in cells], given)
              for axis, given in enumerate((genes, conditions, times))]
    index = [{text: position for position, (text, _) in enumerate(axis)} for axis in labels]
    values = np.full(tuple(len(axis) for axis in labels), np.nan)
    for (g, c, t), number in cells.items():
        if g in index[0] and c in index[1] and t in index[2]:
            values[index[0][g], index[1][c], index[2][t]] = number
    return cube_from(values, [[name for _, name in axis] for axis in labels], path, drop_missing)


def read_slices(paths: Any, sep: Optional[str] = None, header: bool = True, gene_column: bool = True,
                genes: Optional[Sequence[Any]] = None, conditions: Optional[Sequence[Any]] = None,
                missing: Sequence[str] = MISSING, drop_missing: Optional[str] = None) -> Cube:
    """
    Read a cube from a matrix per time: a text file for each time, with a row per gene and
    a column per condition, the form in which series are often exported. Every file holds
    the same genes and conditions, in the same order.

    .. code-block:: python

        from metagen.triclustering.data import read_slices

        for hour in (0, 6, 12):
            rows = ["gene,wild,mutant"] + [f"g{g},{g + hour},{g - hour}" for g in range(5)]
            open(f"hour{hour}.csv", "w").write("\\n".join(rows) + "\\n")
        cube = read_slices({0: "hour0.csv", 6: "hour6.csv", 12: "hour12.csv"})
        print(cube.shape, cube.conditions, cube.times)         # (5, 2, 3) ('wild', 'mutant') (0, 6, 12)
        print(cube.values[4, 1].tolist())                      # [4.0, -2.0, -8.0]

    :param paths: The files, by time: a mapping from each time to its file, or a sequence of
        files, whose times are then their positions.
    :type paths: Mapping or Sequence
    :param sep: The separator of the columns; by default, a tab for ``.tsv`` and ``.tab``
        files and otherwise the one of ``,``, ``;`` and tab that the first line uses.
    :type sep: str, optional
    :param header: Whether the first row names the conditions, defaults to True.
    :type header: bool, optional
    :param gene_column: Whether the first column names the genes, defaults to True.
    :type gene_column: bool, optional
    :param genes: The names of the genes, when the files do not hold them.
    :type genes: Sequence, optional
    :param conditions: The names of the conditions, when the files do not hold them.
    :type conditions: Sequence, optional
    :param missing: What the files write for a missing value, defaults to the empty cell,
        ``NA``, ``N/A``, ``NaN`` and ``null``.
    :type missing: Sequence[str], optional
    :param drop_missing: With missing cells, the axis along which to drop every position
        that holds one; None, the default, makes them an error.
    :type drop_missing: str, optional
    :return: The cube.
    :rtype: Cube
    :raises ValueError: if the files disagree on their genes or conditions, a value is not
        a number, or cells are missing and ``drop_missing`` is None.
    """
    if isinstance(paths, Mapping):
        times, files = list(paths.keys()), list(paths.values())
    elif isinstance(paths, (list, tuple)):
        times, files = list(range(len(paths))), list(paths)
    else:
        raise ValueError("paths is a mapping from each time to its file, or a sequence of files.")
    if len(files) < 2:
        raise ValueError("A cube needs at least two times: give a file for each.")
    gaps = set(missing)
    slices: List[np.ndarray] = []
    gene_names: Optional[List[str]] = None
    condition_names: Optional[List[str]] = None
    for file in files:
        rows = _rows(file, sep)
        body = rows[1:] if header else rows
        if not body:
            raise ValueError(f"{file} holds no rows of values.")
        own_genes = [row[0] for row in body] if gene_column else None
        first = 1 if gene_column else 0
        width = max(len(row) for row in body) - first
        # The header may or may not have a cell over the column of the genes.
        own_conditions = (rows[0][-width:] if len(rows[0]) >= width else None) if header else None
        if header and own_conditions is None:
            raise ValueError(f"The header of {file} names {len(rows[0])} conditions for {width} columns of values.")
        matrix = np.array([[parsed_number(cell, gaps, file, line) for cell in (row[first:] + [""] * width)[:width]]
                           for line, row in enumerate(body, start=2 if header else 1)])
        for what, own, kept in (("genes", own_genes, gene_names), ("conditions", own_conditions, condition_names)):
            if own is not None and kept is not None and own != kept:
                raise ValueError(f"{file} does not hold the same {what}, in the same order, as {files[0]}.")
        if slices and matrix.shape != slices[0].shape:
            raise ValueError(f"{file} has {matrix.shape[0]} genes and {matrix.shape[1]} conditions, and "
                             f"{files[0]} {slices[0].shape[0]} and {slices[0].shape[1]}.")
        gene_names = own_genes if own_genes is not None else gene_names
        condition_names = own_conditions if own_conditions is not None else condition_names
        slices.append(matrix)
    values = np.stack(slices, axis=2)
    names = [genes if genes is not None else converted(gene_names),
             conditions if conditions is not None else converted(condition_names), times]
    return cube_from(values, names, str(files[0]), drop_missing)


def _rows(path: str, sep: Optional[str]) -> List[List[str]]:
    """The rows of a text file, whatever its line endings, with no empty lines."""
    import csv
    with open(path, encoding="utf-8-sig", newline="") as handle:
        text = handle.read()
    lines = [line for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]
    if not lines:
        raise ValueError(f"{path} is empty.")
    if sep is None:
        if str(path).lower().endswith((".tsv", ".tab")):
            sep = "\t"
        else:
            counts = {candidate: lines[0].count(candidate) for candidate in (",", ";", "\t")}
            sep = max(counts, key=lambda candidate: counts[candidate]) if any(counts.values()) else ","
    return [[cell.strip() for cell in row] for row in csv.reader(lines, delimiter=sep)]


def parsed_number(text: str, missing: set, path: str, line: int) -> float:
    if text in missing:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Line {line} of {path} holds {text!r}, which is not a number.") from None


def converted(texts: Optional[Sequence[str]]) -> Optional[List[Any]]:
    """Names as integers when they all are, as numbers when they all are, and as text otherwise."""
    if texts is None:
        return None
    for kind in (int, float):
        try:
            return [kind(text) for text in texts]
        except ValueError:
            continue
    return list(texts)


def _ordered(seen: Sequence[str], given: Optional[Sequence[Any]]) -> List[Tuple[str, Any]]:
    """The labels of an axis, as (text in the file, name), in the order given or of appearance.
    A name given matches the text of the file that it is, or the number that text reads as."""
    texts = list(dict.fromkeys(seen))
    labels = list(zip(texts, converted(texts) or []))
    if given is None:
        return labels
    chosen = []
    for name in given:
        match = next((label for label in labels if label[0] == name or label[1] == name or label[0] == str(name)), None)
        if match is None:
            raise ValueError(f"{name!r} is not in the file.")
        chosen.append((match[0], name))
    return chosen


def cube_from(values: np.ndarray, names: Sequence[Optional[Sequence[Any]]], path: str, drop_missing: Optional[str]) -> Cube:
    if drop_missing is not None and drop_missing not in AXES:
        raise ValueError(f"drop_missing is one of {list(AXES)} or None, not {drop_missing!r}.")
    genes, conditions, times = (list(axis) if axis is not None else list(range(size))
                                for axis, size in zip(names, values.shape))
    if np.isnan(values).any():
        if drop_missing is None:
            raise ValueError(f"{path} leaves {int(np.isnan(values).sum())} cells missing: drop the positions that "
                             f"hold them with drop_missing='genes' (or 'conditions', 'times'), or fill them in first.")
        cube, _ = Cube.without_missing(values, genes, conditions, times, axis=drop_missing)
        return cube
    return Cube(values, genes, conditions, times)
