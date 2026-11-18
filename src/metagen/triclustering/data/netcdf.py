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

# Reading and writing a cube in NetCDF.

import numbers
from typing import Any, Dict, List, Literal, Mapping, Optional, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import AXES, Cube


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
            kind, data = coordinate_of(names)
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


def coordinate_of(names: Sequence[Any]) -> Tuple[str, np.ndarray]:
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
        text = coordinate_of(names)[0] == "c"
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
