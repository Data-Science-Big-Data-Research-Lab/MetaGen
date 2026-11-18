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

# Four modules in one, of 940 lines, that took Cube inside its functions to break a cycle with
# cube.py (O-16 of the independent audit). The names it documents are here, as they were.
from metagen.triclustering.data.genes import check, collapse_genes, drop_genes, rename_genes
from metagen.triclustering.data.geo import fetch_gds, read_gds
from metagen.triclustering.data.netcdf import (NETCDF_DIMENSIONS, NetCDFFormat, netcdf_attributes,  # noqa: F401
                                               read_netcdf, write_netcdf)
from metagen.triclustering.data.text import MISSING, read_long, read_slices  # noqa: F401
from metagen.triclustering.data import genes, geo, netcdf, text  # noqa: F401

__all__ = ["check", "collapse_genes", "drop_genes", "fetch_gds", "netcdf_attributes", "read_gds", "read_long", "read_netcdf", "read_slices", "rename_genes", "write_netcdf"]
