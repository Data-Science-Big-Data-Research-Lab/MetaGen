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

import numbers
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np

if TYPE_CHECKING:
    from metagen.triclustering.cube import Cube

#: The names of the dimensions of a cube in a NetCDF file, in the order of its axes.
NETCDF_DIMENSIONS: Tuple[str, str, str] = ("gene", "condition", "time")

#: The formats a cube can be written in: classic NetCDF, which needs nothing beyond SciPy,
#: and NetCDF-4, which needs the ``netcdf`` extra.
NetCDFFormat = Literal["NETCDF3_64BIT", "NETCDF4"]

_HDF5 = b"\x89HDF\r\n\x1a\n"
_INSTALL = "pip install pymetagen-datalabupo[netcdf]"


def write_netcdf(cube: Cube, path: str, attributes: Optional[Mapping[str, Any]] = None,
                 format: NetCDFFormat = "NETCDF3_64BIT") -> None:
    """
    Write a cube to a NetCDF file: the values in a variable ``values`` with the dimensions
    ``gene``, ``condition`` and ``time``, and the names of each dimension in a coordinate
    variable of its own, as numbers when they all are and as text otherwise. Any program
    that reads NetCDF reads it, from Python (xarray, netCDF4), R, Julia or MATLAB to the
    command line (``ncdump``). :py:meth:`Cube.to_netcdf` calls it.

    :param cube: The cube.
    :type cube: Cube
    :param path: The file.
    :type path: str
    :param attributes: Global attributes to describe the data, such as a description, its
        source or its units, each a text or a number.
    :type attributes: Mapping[str, Any], optional
    :param format: ``"NETCDF3_64BIT"``, the default, classic NetCDF, or ``"NETCDF4"``,
        which needs the ``netcdf`` extra.
    :type format: str, optional
    :raises ValueError: if the format is not one of the two, or an attribute is neither a
        text nor a number.
    :raises ImportError: for NetCDF-4 without the ``netcdf`` extra.
    """
    given = dict(attributes or {})
    for key, value in given.items():
        if not isinstance(key, str) or isinstance(value, bool) or not isinstance(value, (str, numbers.Real)):
            raise ValueError(f"An attribute is a text or a number with a name, not {key!r}: {value!r}.")
    globals_ = {"Conventions": "CF-1.8", **given}
    if format == "NETCDF3_64BIT":
        _write_classic(cube, path, globals_)
    elif format == "NETCDF4":
        _write_netcdf4(cube, path, globals_)
    else:
        raise ValueError(f"format is 'NETCDF3_64BIT' or 'NETCDF4', not {format!r}.")


def read_netcdf(path: str, variable: str = "values", dimensions: Sequence[str] = NETCDF_DIMENSIONS,
                drop_missing: Optional[str] = None) -> Cube:
    """
    Read a cube from a NetCDF file, classic or NetCDF-4 (the latter with the ``netcdf``
    extra). The variable may have its three dimensions in any order and under any names:
    ``dimensions`` says which are the genes, the conditions and the times. The names of each
    dimension come from its coordinate variable, the variable with the name of the
    dimension, and are its positions when there is none. Cells equal to the variable's
    ``_FillValue`` or ``missing_value``, or not a number, are missing.
    :py:meth:`Cube.from_netcdf` calls it.

    :param path: The file.
    :type path: str
    :param variable: The variable that holds the values, defaults to ``"values"``.
    :type variable: str, optional
    :param dimensions: The names in the file of the dimensions of the genes, the conditions
        and the times, defaults to ``("gene", "condition", "time")``.
    :type dimensions: Sequence[str], optional
    :param drop_missing: With missing cells, the axis, ``"genes"``, ``"conditions"`` or
        ``"times"``, along which to drop every position that holds one, as
        :py:meth:`Cube.without_missing` does; None, the default, makes them an error.
    :type drop_missing: str, optional
    :return: The cube.
    :rtype: Cube
    :raises ValueError: if the file has no such variable or dimensions, or holds missing
        cells and ``drop_missing`` is None.
    :raises ImportError: for a NetCDF-4 file without the ``netcdf`` extra.
    """
    from metagen.triclustering.cube import AXES, Cube
    wanted = tuple(dimensions)
    if len(wanted) != 3 or len(set(wanted)) != 3:
        raise ValueError(f"Give three different dimensions, of the genes, the conditions and the times, not {wanted}.")
    if drop_missing is not None and drop_missing not in AXES:
        raise ValueError(f"drop_missing is one of {list(AXES)} or None, not {drop_missing!r}.")
    values, own_dimensions, names, missing = (_read_netcdf4 if _is_hdf5(path) else _read_classic)(path, variable)
    if sorted(own_dimensions) != sorted(wanted):
        raise ValueError(f"The variable {variable!r} of {path} has the dimensions {list(own_dimensions)}, not "
                         f"{list(wanted)}: say which are the genes, the conditions and the times with dimensions=.")
    order = [own_dimensions.index(dimension) for dimension in wanted]
    values = np.transpose(np.asarray(values, dtype=np.float64), order)
    gaps = ~np.isfinite(values)
    for marker in missing:
        gaps |= values == marker
    values = np.where(gaps, np.nan, values)
    # Without a coordinate variable, the names are the positions in the file, kept when some are dropped.
    genes, conditions, times = (names.get(dimension, list(range(size))) for dimension, size in zip(wanted, values.shape))
    if gaps.any():
        if drop_missing is None:
            raise ValueError(f"{path} holds {int(gaps.sum())} missing cells: drop the positions that hold them "
                             f"with drop_missing='genes' (or 'conditions', 'times'), or fill them in first.")
        cube, _ = Cube.without_missing(values, genes, conditions, times, axis=drop_missing)
        return cube
    return Cube(values, genes, conditions, times)


def netcdf_attributes(path: str) -> Dict[str, Any]:
    """
    The global attributes of a NetCDF file, such as the description of its data.

    :param path: The file.
    :type path: str
    :return: The attributes, by name.
    :rtype: Dict[str, Any]
    """
    if _is_hdf5(path):
        xarray = _xarray()
        with xarray.open_dataset(path) as dataset:
            return dict(dataset.attrs)
    from scipy.io import netcdf_file
    with netcdf_file(path, "r", mmap=False) as handle:
        return {key: _plain_attribute(value) for key, value in handle._attributes.items()}


def _write_classic(cube: Cube, path: str, attributes: Mapping[str, Any]) -> None:
    from scipy.io import netcdf_file
    with netcdf_file(path, "w", version=2) as handle:
        for key, value in attributes.items():
            setattr(handle, key, value)
        for dimension, size in zip(NETCDF_DIMENSIONS, cube.shape):
            handle.createDimension(dimension, size)
        for dimension, names in zip(NETCDF_DIMENSIONS, (cube.genes, cube.conditions, cube.times)):
            kind, data = _coordinate(names)
            if kind == "c":
                width = max(1, data.shape[1])
                handle.createDimension(f"{dimension}_strlen", width)
                coordinate = handle.createVariable(dimension, "c", (dimension, f"{dimension}_strlen"))
                coordinate._Encoding = "utf-8"
            else:
                coordinate = handle.createVariable(dimension, kind, (dimension,))
            coordinate[:] = data
        values = handle.createVariable("values", "d", NETCDF_DIMENSIONS)
        values[:] = cube.values


def _coordinate(names: Sequence[Any]) -> Tuple[str, np.ndarray]:
    """The type and the data of a coordinate variable: integers, reals or text."""
    if all(isinstance(name, numbers.Integral) and not isinstance(name, bool) for name in names):
        integers = [int(name) for name in names]
        if all(-2 ** 31 <= name < 2 ** 31 for name in integers):
            return "i", np.array(integers, dtype=">i4")
    if all(isinstance(name, numbers.Real) and not isinstance(name, bool) for name in names):
        return "d", np.array([float(name) for name in names], dtype=">f8")
    encoded = [str(name).encode("utf-8") for name in names]
    width = max([len(text) for text in encoded] + [1])
    characters = np.zeros((len(encoded), width), dtype="S1")
    for row, text in enumerate(encoded):
        characters[row, :len(text)] = [text[position:position + 1] for position in range(len(text))]
    return "c", characters


def _read_classic(path: str, variable: str) -> Tuple[np.ndarray, Tuple[str, ...], Dict[str, List[Any]], List[float]]:
    from scipy.io import netcdf_file
    try:
        handle = netcdf_file(path, "r", mmap=False)
    except (TypeError, ValueError, OSError) as error:
        raise ValueError(f"{path} is not a NetCDF file: {error}") from None
    with handle:
        if variable not in handle.variables:
            raise ValueError(f"{path} has no variable {variable!r}; it has {sorted(handle.variables)}.")
        data = handle.variables[variable]
        dimensions = tuple(data.dimensions)
        values = np.array(data[:], dtype=np.float64)
        missing = [float(data._attributes[key]) for key in ("_FillValue", "missing_value") if key in data._attributes]
        names: Dict[str, List[Any]] = {}
        for dimension in dimensions:
            if dimension in handle.variables and handle.variables[dimension].dimensions[:1] == (dimension,):
                names[dimension] = _names_of(handle.variables[dimension][:])
    return values, dimensions, names, missing


def _names_of(data: np.ndarray) -> List[Any]:
    if data.dtype.kind in "SU" and data.ndim == 2:
        return [b"".join(row.tolist()).rstrip(b"\x00").decode("utf-8") for row in data]
    if data.dtype.kind in "iu":
        return [int(value) for value in data]
    if data.dtype.kind == "f":
        return [float(value) for value in data]
    return [value.decode("utf-8") if isinstance(value, bytes) else value for value in data.tolist()]


def _plain_attribute(value: Any) -> Any:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, np.ndarray):
        return value.item() if value.size == 1 else value.tolist()
    return value


def _is_hdf5(path: str) -> bool:
    with open(path, "rb") as handle:
        return handle.read(8) == _HDF5


def _xarray() -> Any:
    try:
        import xarray
    except ImportError:
        raise ImportError(f"NetCDF-4 needs xarray and netCDF4: {_INSTALL}.") from None
    return xarray


def _write_netcdf4(cube: Cube, path: str, attributes: Mapping[str, Any]) -> None:
    xarray = _xarray()
    coordinates = {}
    for dimension, names in zip(NETCDF_DIMENSIONS, (cube.genes, cube.conditions, cube.times)):
        text = _coordinate(names)[0] == "c"
        coordinates[dimension] = [str(name) for name in names] if text else list(names)
    dataset = xarray.Dataset({"values": (NETCDF_DIMENSIONS, np.array(cube.values))}, coords=coordinates,
                             attrs=dict(attributes))
    dataset.to_netcdf(path, format="NETCDF4")


def _read_netcdf4(path: str, variable: str) -> Tuple[np.ndarray, Tuple[str, ...], Dict[str, List[Any]], List[float]]:
    xarray = _xarray()
    with xarray.open_dataset(path, mask_and_scale=True, decode_times=False, decode_timedelta=False) as dataset:
        if variable not in dataset.variables:
            raise ValueError(f"{path} has no variable {variable!r}; it has {sorted(dataset.variables)}.")
        data = dataset[variable]
        dimensions = tuple(str(dimension) for dimension in data.dims)
        names = {dimension: _names_of(np.asarray(dataset[dimension].values)) for dimension in dimensions
                 if dimension in dataset.coords}
        return np.array(data.values, dtype=np.float64), dimensions, names, []


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
        cells[key] = _number(row[columns[3]], gaps, path, line)
    labels = [_ordered([key[axis] for key in cells], given)
              for axis, given in enumerate((genes, conditions, times))]
    index = [{text: position for position, (text, _) in enumerate(axis)} for axis in labels]
    values = np.full(tuple(len(axis) for axis in labels), np.nan)
    for (g, c, t), number in cells.items():
        if g in index[0] and c in index[1] and t in index[2]:
            values[index[0][g], index[1][c], index[2][t]] = number
    return _cube(values, [[name for _, name in axis] for axis in labels], path, drop_missing)


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
        matrix = np.array([[_number(cell, gaps, file, line) for cell in (row[first:] + [""] * width)[:width]]
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
    names = [genes if genes is not None else _converted(gene_names),
             conditions if conditions is not None else _converted(condition_names), times]
    return _cube(values, names, str(files[0]), drop_missing)


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


def _number(text: str, missing: set, path: str, line: int) -> float:
    if text in missing:
        return float("nan")
    try:
        return float(text)
    except ValueError:
        raise ValueError(f"Line {line} of {path} holds {text!r}, which is not a number.") from None


def _converted(texts: Optional[Sequence[str]]) -> Optional[List[Any]]:
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
    labels = list(zip(texts, _converted(texts) or []))
    if given is None:
        return labels
    chosen = []
    for name in given:
        match = next((label for label in labels if label[0] == name or label[1] == name or label[0] == str(name)), None)
        if match is None:
            raise ValueError(f"{name!r} is not in the file.")
        chosen.append((match[0], name))
    return chosen


def _cube(values: np.ndarray, names: Sequence[Optional[Sequence[Any]]], path: str, drop_missing: Optional[str]) -> Cube:
    from metagen.triclustering.cube import AXES, Cube
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


# --- preparing --------------------------------------------------------------------------

def drop_genes(cube: Cube, names: Optional[Sequence[Any]] = None, pattern: Optional[str] = None) -> Cube:
    """
    The cube without some of its genes: those named, and those whose name matches a
    regular expression, such as the control spots of a microarray, which are not genes.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube
        from metagen.triclustering.data import drop_genes

        values = np.random.default_rng(0).normal(size=(5, 3, 4))
        cube = Cube(values, genes=["YAL001C", "EMPTY", "YAL002W", "GENOMIC 50NG/UL", "YAL003W"])
        print(drop_genes(cube, names=["EMPTY"], pattern=r"^GENOMIC").genes)   # ('YAL001C', 'YAL002W', 'YAL003W')

    :param cube: The cube.
    :type cube: Cube
    :param names: The names of the genes to drop.
    :type names: Sequence, optional
    :param pattern: A regular expression; the genes whose name, as text, it matches
        anywhere are dropped.
    :type pattern: str, optional
    :return: The cube with the other genes, in their order.
    :rtype: Cube
    :raises ValueError: if fewer than two genes are left.
    """
    import re
    from metagen.triclustering.cube import Cube
    dropped = set(names or ())
    expression = re.compile(pattern) if pattern is not None else None
    kept = [position for position, name in enumerate(cube.genes)
            if name not in dropped and not (expression is not None and expression.search(str(name)))]
    return Cube(cube.values[kept], [cube.genes[position] for position in kept], cube.conditions, cube.times)


def collapse_genes(cube: Cube, how: str = "mean") -> Cube:
    """
    The cube with one row per gene name, for data with several rows per gene, such as
    the probes of a microarray: ``"mean"`` averages the rows of each name, and
    ``"variance"`` keeps the one whose values vary most, the usual choice before looking
    for genes that vary together. The genes come in the order in which their names first
    appear.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube
        from metagen.triclustering.data import collapse_genes

        values = np.arange(4 * 2 * 3, dtype=float).reshape(4, 2, 3)
        cube = Cube(values, genes=["A", "B", "A", "C"])
        collapsed = collapse_genes(cube)
        print(collapsed.genes, collapsed.values[0, 0].tolist())   # ('A', 'B', 'C') [6.0, 7.0, 8.0]

    :param cube: The cube.
    :type cube: Cube
    :param how: ``"mean"``, the default, or ``"variance"``.
    :type how: str, optional
    :return: The cube with one row per name.
    :rtype: Cube
    :raises ValueError: if ``how`` is not one of the two, or fewer than two genes are left.
    """
    from metagen.triclustering.cube import Cube
    if how not in ("mean", "variance"):
        raise ValueError(f"how is 'mean' or 'variance', not {how!r}.")
    rows: Dict[Any, List[int]] = {}
    for position, name in enumerate(cube.genes):
        rows.setdefault(name, []).append(position)
    values = cube.values
    if how == "mean":
        collapsed = [values[positions].mean(axis=0) for positions in rows.values()]
    else:
        collapsed = [values[max(positions, key=lambda position: float(np.var(values[position])))]
                     for positions in rows.values()]
    return Cube(np.stack(collapsed), list(rows), cube.conditions, cube.times)


def rename_genes(cube: Cube, mapping: Mapping[Any, Any], drop_unmapped: bool = False) -> Tuple[Cube, List[Any]]:
    """
    The cube with its genes renamed through a table, such as the annotation of a
    microarray platform from a probe to the symbol of its gene, and the names the table
    does not hold. Those keep their name, or are dropped with ``drop_unmapped``. Several
    rows may end up with the same name; :py:func:`collapse_genes` then makes one of them.

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube
        from metagen.triclustering.data import rename_genes

        cube = Cube(np.zeros((3, 2, 2)), genes=["1007_s_at", "1053_at", "117_at"])
        renamed, unmapped = rename_genes(cube, {"1007_s_at": "DDR1", "1053_at": "RFC2"})
        print(renamed.genes, unmapped)                  # ('DDR1', 'RFC2', '117_at') ['117_at']

    :param cube: The cube.
    :type cube: Cube
    :param mapping: The new name of each gene, by its current name.
    :type mapping: Mapping
    :param drop_unmapped: Whether to drop the genes the table does not hold, defaults to False.
    :type drop_unmapped: bool, optional
    :return: The renamed cube, and the names the table does not hold, in their order.
    :rtype: Tuple[Cube, List]
    :raises ValueError: if fewer than two genes are left.
    """
    from metagen.triclustering.cube import Cube
    unmapped = [name for name in cube.genes if name not in mapping]
    kept = [position for position, name in enumerate(cube.genes) if not (drop_unmapped and name not in mapping)]
    genes = [mapping.get(cube.genes[position], cube.genes[position]) for position in kept]
    return Cube(cube.values[kept], genes, cube.conditions, cube.times), unmapped


# --- checking ----------------------------------------------------------------------------

# Months as a spreadsheet writes them when it turns a gene name such as MARCH1 or SEPT2
# into a date: 1-Mar, Mar-01, 2001-03-01, March 1.
_MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec|january|february|march|april|june|july|" \
          "august|september|october|november|december"
_DATE = (rf"^(\d{{1,2}}[-/ ]({_MONTHS})([-/ ]\d{{2,4}})?|({_MONTHS})[-/ ]\d{{1,4}}|\d{{4}}-\d{{2}}-\d{{2}}"
         rf"(\s+00:00:00)?)$")
# Names that microarrays give to spots that are not genes.
# Only names that no gene has: CTRL, for one, is a human gene (chymotrypsin like).
_CONTROL = r"^(empty|blank|norf|3xssc|lambda|pbr322|poly ?a|salmon sperm)$|^genomic\b|^affx[-_]|^-+control|" \
           r"labell?ed dna|plasmid"
# Names of probes and of sequences rather than of genes: Affymetrix probe sets (1552563_a_at)
# and GenBank accessions (AF086181), which a platform annotation leaves where it knows no gene.
_IDENTIFIER = r"_at$|^[A-Z]{1,2}\d{5,6}(\.\d+)?$"


def check(cube: Cube) -> List[str]:
    """
    What may be wrong with a cube before searching it, without changing it: a warning per
    problem found, and none for data that look sound. It looks for

    - values in a scale where the slopes between consecutive times are almost all
      vertical, or almost all flat, so that MSL can tell little apart: expression data
      usually need a log2 transform;
    - conditions in which every gene changes over time almost the same, or the reverse:
      technical columns of a single measurement, such as the intensity and the background
      of a spot, rather than experimental conditions;
    - several rows with the same name, such as the probes of a gene;
    - names that look like dates, which a spreadsheet makes of gene names such as MARCH1;
    - names of probes or of sequences rather than of genes, which an enrichment analysis
      does not know;
    - names that look like the control spots of a microarray, which are not genes;
    - rows whose values never change, and many values that are exactly zero, which may
      stand for missing ones;
    - genes in alphabetical order, or nearly, an order the search reads (see
      ``shuffle_genes`` in :py:class:`~metagen.metaheuristics.TriGen`).

    .. code-block:: python

        import numpy as np
        from metagen.triclustering import Cube
        from metagen.triclustering.data import check

        rng = np.random.default_rng(0)
        values = rng.lognormal(mean=7, sigma=1.5, size=(50, 3, 6))      # raw intensities
        names = [f"g{index}" for index in rng.permutation(25)] * 2        # two probes per gene
        warnings = check(Cube(values, genes=names))
        print(len(warnings), warnings[0].split(":")[0])     # 2 The values may need a transform, such as log2
        print(warnings[1].split(":")[0])     # 25 names repeat, in 50 rows, such as 'g16', 'g18', 'g12'
        print(check(Cube(np.log2(values[:25]), genes=names[:25])))       # []

    :param cube: The cube.
    :type cube: Cube
    :return: The warnings, each a sentence that says what was found and what to do about it.
    :rtype: List[str]
    """
    import re
    warnings: List[str] = []
    values = cube.values
    steps = np.abs(np.diff(values, axis=2)).ravel()
    steep, flat = float(np.mean(steps > np.tan(np.radians(80)))), float(np.mean(steps < np.tan(np.radians(1))))
    if steep > 0.5:
        warnings.append(f"The values may need a transform, such as log2: {steep:.0%} of the steps between consecutive "
                        f"times are steeper than 80 degrees, and MSL then reads little more than whether a series "
                        f"rises or falls.")
    elif flat > 0.95:
        warnings.append(f"The values may need scaling: {flat:.0%} of the steps between consecutive times are flatter "
                        f"than 1 degree, and MSL then finds every series alike.")
    # The conditions are compared by how each gene changes over time in them: otherwise the
    # differences between genes, which every condition shares, make any two conditions of
    # expression data look alike.
    centered = values - values.mean(axis=2, keepdims=True)
    columns = centered.transpose(1, 0, 2).reshape(values.shape[1], -1)
    if values.shape[1] > 1 and np.all(np.std(columns, axis=1) > 0):
        correlation: np.ndarray = np.asarray(np.corrcoef(columns))
        pairs = [(cube.conditions[a], cube.conditions[b], correlation[a, b])
                 for a in range(len(columns)) for b in range(a + 1, len(columns)) if abs(correlation[a, b]) >= 0.98]
        if pairs:
            shown = ", ".join(f"{a!r} and {b!r} ({r:+.3f})" for a, b, r in pairs[:3])
            warnings.append(f"{len(pairs)} pairs of conditions are almost the same column or one the reverse of the "
                            f"other, such as {shown}: are they replicates, or technical columns of a single "
                            f"measurement? A condition should be an experimental one.")
    counts: Dict[Any, int] = {}
    for name in cube.genes:
        counts[name] = counts.get(name, 0) + 1
    repeated = [name for name, count in counts.items() if count > 1]
    if repeated:
        warnings.append(f"{len(repeated)} names repeat, in {sum(counts[name] for name in repeated)} rows, such as "
                        f"{', '.join(repr(name) for name in repeated[:3])}: several probes per gene? "
                        f"collapse_genes makes one row per name.")
    texts = [str(name) for name in cube.genes]
    dates = [text for text in texts if re.match(_DATE, text.strip(), re.IGNORECASE)]
    if dates:
        warnings.append(f"{len(dates)} names look like dates, such as {', '.join(repr(t) for t in dates[:3])}: a "
                        f"spreadsheet may have turned gene names such as MARCH1 or SEPT2 into dates.")
    identifiers = [text for text in texts if re.search(_IDENTIFIER, text.strip())]
    if identifiers:
        warnings.append(f"{len(identifiers)} names look like probe or sequence identifiers rather than gene symbols, "
                        f"such as {', '.join(repr(t) for t in identifiers[:3])}: an enrichment analysis does not know "
                        f"them; rename_genes translates them with the annotation of the platform, or drop_genes "
                        f"removes them.")
    controls = [text for text in texts if re.search(_CONTROL, text.strip(), re.IGNORECASE)]
    if controls:
        warnings.append(f"{len(controls)} rows look like control spots, such as "
                        f"{', '.join(repr(t) for t in list(dict.fromkeys(controls))[:3])}: they are not genes; "
                        f"drop_genes removes them.")
    constant = int(np.sum(np.ptp(values.reshape(values.shape[0], -1), axis=1) == 0))
    if constant:
        warnings.append(f"{constant} rows never change: they match any flat pattern and say nothing.")
    zeros = float(np.mean(values == 0))
    if zeros > 0.01 and not np.all(values == np.round(values)):
        warnings.append(f"{zeros:.1%} of the values are exactly zero in data that are not integers: zeros often "
                        f"stand for missing values, and a block of them looks like a perfect tricluster.")
    if all(isinstance(name, str) for name in cube.genes) and len(set(texts)) > 2:
        lowered = [text.lower() for text in texts]
        ordered = float(np.mean([first <= second for first, second in zip(lowered, lowered[1:])]))
        if ordered >= 0.95:
            warnings.append("The genes are in alphabetical order, or nearly, an order the search reads: with "
                            "shuffle_genes=True each run of TriGen searches them in an order of its own.")
    return warnings


# --- GEO ---------------------------------------------------------------------------------

def read_gds(path: str, time: str, conditions: Optional[Sequence[str]] = None, genes: str = "IDENTIFIER",
             replicates: str = "split", drop_missing: Optional[str] = None) -> Cube:
    """
    Read a cube from a GEO DataSet, a GDS of the Gene Expression Omnibus, in its SOFT file
    (``GDS4510_full.soft.gz`` or ``GDS4510.soft``, as GEO serves it, zipped or not). A GDS
    groups its samples by factors, such as the genotype, the age or the time: one of them
    gives the times, and the others make the conditions. The samples that share a condition
    and a time are replicates, kept as conditions of their own or averaged.

    .. code-block:: python

        from metagen.triclustering.data import read_gds

        # A GDS in miniature: two genotypes, two ages, two replicates of each.
        samples = [f"GSM{index}" for index in range(8)]
        lines = ["^DATASET = GDS0", "^SUBSET = GDS0_1", "!subset_description = wild type",
                 "!subset_sample_id = " + ",".join(samples[:4]), "!subset_type = genotype/variation",
                 "^SUBSET = GDS0_2", "!subset_description = mutant",
                 "!subset_sample_id = " + ",".join(samples[4:]), "!subset_type = genotype/variation",
                 "^SUBSET = GDS0_3", "!subset_description = day 2",
                 "!subset_sample_id = GSM0,GSM1,GSM4,GSM5", "!subset_type = age",
                 "^SUBSET = GDS0_4", "!subset_description = day 8",
                 "!subset_sample_id = GSM2,GSM3,GSM6,GSM7", "!subset_type = age",
                 "!dataset_table_begin", "\\t".join(["ID_REF", "IDENTIFIER"] + samples)]
        lines += ["\\t".join([f"probe{g}", f"GENE{g}"] + [str(g + s) for s in range(8)]) for g in range(3)]
        open("GDS0.soft", "w").write("\\n".join(lines + ["!dataset_table_end"]) + "\\n")

        cube = read_gds("GDS0.soft", time="age")
        print(cube.shape, cube.conditions[:3])     # (3, 4, 2) ('wild type #1', 'wild type #2', 'mutant #1')
        print(cube.times, cube.values[0, 0].tolist())               # ('day 2', 'day 8') [0.0, 2.0]
        print(read_gds("GDS0.soft", time="age", replicates="mean").conditions)   # ('wild type', 'mutant')

    :param path: The SOFT file.
    :type path: str
    :param time: The factor whose levels are the times, such as ``"time"`` or ``"age"``.
        The times are ordered by the first number in the name of each level.
    :type time: str
    :param conditions: The factors whose levels make the conditions, in the order in which
        their levels are joined in the names; by default, every factor but the time.
    :type conditions: Sequence[str], optional
    :param genes: The column that names the genes: ``"IDENTIFIER"``, the default, the
        gene symbol where GEO knows it, or ``"ID_REF"``, the probe.
    :type genes: str, optional
    :param replicates: ``"split"``, the default, keeps each replicate as a condition of its
        own, numbered after the name of its condition; ``"mean"`` averages them.
    :type replicates: str, optional
    :param drop_missing: The axis along which to drop the positions that hold missing values;
        None, the default, makes them an error.
    :type drop_missing: str, optional
    :return: The cube.
    :rtype: Cube
    :raises ValueError: if the file is not a GDS, a factor is not in it, a sample lacks a
        level of a factor, the replicates of the conditions are not as many at every time,
        or values are missing and ``drop_missing`` is None.
    """
    import gzip
    import re
    if replicates not in ("split", "mean"):
        raise ValueError(f"replicates is 'split' or 'mean', not {replicates!r}.")
    with open(path, "rb") as handle:
        zipped = handle.read(2) == b"\x1f\x8b"
    opener = gzip.open if zipped else open
    subsets: List[Dict[str, Any]] = []
    header: Optional[List[str]] = None
    table: List[List[str]] = []
    with opener(path, "rt", encoding="utf-8", errors="replace") as text:   # type: ignore[operator]
        inside = False
        for line in text:
            line = line.rstrip("\r\n")
            if line.startswith("^SUBSET"):
                subsets.append({})
            elif line.startswith("!subset_") and subsets:
                key, _, value = line[len("!subset_"):].partition(" = ")
                subsets[-1][key] = value.split(",") if key == "sample_id" else value
            elif line.startswith("!dataset_table_begin"):
                inside = True
            elif line.startswith("!dataset_table_end"):
                break
            elif inside:
                cells = line.split("\t")
                if header is None:
                    header = cells
                else:
                    table.append(cells)
    if header is None or not subsets:
        raise ValueError(f"{path} is not the SOFT file of a GEO DataSet: it has no subsets or no table.")
    factors: Dict[str, Dict[str, str]] = {}            # factor -> sample -> level
    levels: Dict[str, List[str]] = {}                  # factor -> levels, in order
    for subset in subsets:
        kind, level = subset.get("type", ""), subset.get("description", "")
        levels.setdefault(kind, []).append(level)
        for sample in subset.get("sample_id", []):
            factors.setdefault(kind, {})[sample.strip()] = level
    chosen = [factor for factor in factors if factor != time] if conditions is None else list(conditions)
    for factor in [time, *chosen]:
        if factor not in factors:
            raise ValueError(f"{path} has no factor {factor!r}; its factors are {list(factors)}.")
    if genes not in header[:2]:
        raise ValueError(f"genes is 'IDENTIFIER' or 'ID_REF', not {genes!r}.")
    samples = [column for column in header[2:] if column.startswith("GSM")]
    for sample in samples:
        for factor in [time, *chosen]:
            if sample not in factors[factor]:
                raise ValueError(f"The sample {sample} has no level of the factor {factor!r}.")

    def first_number(level: str) -> float:
        found = re.search(r"-?\d+(\.\d+)?", level)
        return float(found.group()) if found else float("inf")

    times = sorted(levels[time], key=lambda level: (first_number(level), levels[time].index(level)))
    labels = list(dict.fromkeys(" / ".join(factors[factor][sample] for factor in chosen) for sample in samples))
    groups: Dict[Tuple[str, str], List[int]] = {}
    for column, sample in enumerate(samples):
        key = (" / ".join(factors[factor][sample] for factor in chosen), factors[time][sample])
        groups.setdefault(key, []).append(column)
    counts = {len(groups.get((label, level), [])) for label in labels for level in times}
    if len(counts) != 1 or 0 in counts:
        raise ValueError(f"The conditions of {path} do not have as many replicates at every time ({sorted(counts)}): "
                         f"choose the factors of the conditions with conditions=.")
    copies = counts.pop()
    position = {column: index for index, column in enumerate(header)}
    columns = [position[sample] for sample in samples]
    raw = np.array([[_number(row[column] if column < len(row) else "", {"null", "", "NA"}, path, line)
                     for column in columns] for line, row in enumerate(table, start=1)])
    names = [row[header.index(genes)] for row in table]
    blocks = []
    for label in labels:
        per_time = [raw[:, groups[(label, level)]] for level in times]      # genes x replicates, per time
        stacked = np.stack(per_time, axis=2)                                   # genes x replicates x times
        blocks.append(stacked.mean(axis=1, keepdims=True) if replicates == "mean" else stacked)
    values = np.concatenate(blocks, axis=1)
    condition_names = labels if replicates == "mean" or copies == 1 else \
        [f"{label} #{copy + 1}" for label in labels for copy in range(copies)]
    return _cube(values, [names, condition_names, times], path, drop_missing)


_GEO = "https://ftp.ncbi.nlm.nih.gov/geo/datasets"


def fetch_gds(accession: str, folder: str = ".", full: bool = True, timeout: float = 300.0) -> str:
    """
    Download the SOFT file of a GEO DataSet into a folder, and return its path; a file
    already there is not downloaded again. :py:func:`read_gds` reads it. GEO updates the
    annotation of its platforms over time, so keeping the file keeps an analysis repeatable.

    .. code-block:: python

        from metagen.triclustering.data import fetch_gds, read_gds

        path = fetch_gds("GDS4510", folder="geo")
        print(path)                                           # geo/GDS4510_full.soft.gz
        cube = read_gds(path, time="age")
        print(cube.conditions[:2], cube.times[0])             # ('wild type #1', 'wild type #2') postnatal day 2

    :param accession: The accession of the DataSet, such as ``"GDS4510"``.
    :type accession: str
    :param folder: The folder to download it into, created if need be; the current one by
        default.
    :type folder: str, optional
    :param full: Whether to download the full file, with the annotation of each probe,
        defaults to True; otherwise, the file with the values alone.
    :type full: bool, optional
    :param timeout: Seconds to wait for GEO, defaults to 300.
    :type timeout: float, optional
    :return: The path of the file.
    :rtype: str
    :raises ValueError: if the accession is not that of a DataSet, or GEO has none with it.
    :raises RuntimeError: if GEO cannot be reached.
    """
    import os
    import re
    import tempfile
    import urllib.error
    if not isinstance(accession, str) or not re.fullmatch(r"GDS\d+", accession):
        raise ValueError(f"The accession of a GEO DataSet is GDS followed by digits, such as 'GDS4510', not {accession!r}.")
    name = f"{accession}_full.soft.gz" if full else f"{accession}.soft.gz"
    path = os.path.join(folder, name)
    if os.path.exists(path):
        return path
    os.makedirs(folder or ".", exist_ok=True)
    digits = accession[3:]
    url = f"{_GEO}/GDS{digits[:-3]}nnn/{accession}/soft/{name}"
    handle, partial = tempfile.mkstemp(dir=folder or ".", prefix=f".{name}.")
    os.close(handle)
    try:
        _download(url, partial, timeout)
        os.replace(partial, path)
    except urllib.error.HTTPError as error:
        raise ValueError(f"GEO has no DataSet {accession} ({error.code} at {url}).") from None
    except (urllib.error.URLError, OSError) as error:
        raise RuntimeError(f"GEO could not be reached at {url}: {error}.") from None
    finally:
        if os.path.exists(partial):
            os.remove(partial)
    return path


def _download(url: str, path: str, timeout: float) -> None:
    import shutil
    import urllib.request
    with urllib.request.urlopen(url, timeout=timeout) as response, open(path, "wb") as handle:
        shutil.copyfileobj(response, handle)
