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

Convert the datasets and the results of TrLab, the Java application TriGen came from, to
the formats of MetaGen: each dataset of a ``resources.xml`` to a NetCDF file, and each
``.sol`` result to a TriGen result file. It only reads what it converts.

    python tools/trlab/convert.py datasets <resources folder> <output folder> [--only NAME ...]
                                           [--rename NAMES.json]
    python tools/trlab/convert.py sol <file.sol> <dataset.nc> <output.json>

A dataset keeps every row, column and value TrLab read, with its missing values (``NA``)
as missing, and the sizes TrLab searched it with go to ``sizes.json`` beside it, since
they belong to a search and not to the data. ``--rename`` takes a JSON file with new names
for genes, by dataset, such as the gene names a spreadsheet turned into dates. A result
keeps its triclusters, the configuration TrLab ran with translated to TriGen's arguments
as closely as they go, and every original property under ``provenance["trlab"]``: running
it again runs MetaGen's TriGen, which is not TrLab's.
"""
import argparse
import json
import os
import re
import sys
import xml.etree.ElementTree as ElementTree
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.io import netcdf_file

from metagen.metaheuristics import TriGenResult
from metagen.triclustering import Cube, Tricluster
from metagen.triclustering.data import _converted, _coordinate

# TrLab's fitness names, as MetaGen's quality measure and views.
FITNESS = {"msl": ("msl", "trlab"), "mslts": ("msl", "time"), "lsl": ("lsl", "trlab"), "lslts": ("lsl", "time"),
           "msr3d": ("msr3d", "distinct")}
WEIGHTS = {"Wf": "quality", "Wg": "genes", "Wc": "conditions", "Wt": "times", "WOg": "overlap_genes",
           "WOc": "overlap_conditions", "WOt": "overlap_times"}


def _lines(path: str) -> List[str]:
    """The lines of a TrLab text file, whatever its line endings, up to the first empty one,
    as TrLab reads them."""
    text = open(path, "rb").read().decode("latin-1")
    lines = []
    for line in re.split(r"\r\n|\r|\n", text):
        if line == "":
            break
        lines.append(line)
    return lines


def read_dataset(folder: str, element: ElementTree.Element) -> Tuple[np.ndarray, Dict[str, List[str]]]:
    """The values and the names of a dataset of a resources.xml, as TrLab reads them, with
    ``NA`` as missing instead of zero."""
    attributes = element.attrib
    resources = element.find("resources")
    if resources is None:
        raise ValueError(f"The dataset {attributes.get('name')} lists no resources.")
    separator = resources.attrib.get("separator", ";")
    shape = (int(attributes["geneSize"]), int(attributes["sampleSize"]), int(attributes["timeSize"]))
    values = np.full(shape, np.nan)
    for time, resource in enumerate(resources.findall("resource")):
        for gene, line in enumerate(_lines(os.path.join(folder, resource.text or ""))[:shape[0]]):
            for condition, token in enumerate([t for t in re.split("[" + re.escape(separator) + "]", line) if t != ""]):
                if condition < shape[1]:
                    values[gene, condition, time] = np.nan if token.strip().lower() == "na" else float(token)
    names = {}
    for key in ("genes", "samples", "times"):
        child = element.find(key)
        names[key] = [line.strip() for line in _lines(os.path.join(folder, child.text or ""))] if child is not None else []
    # Times written as plain numbers are kept as numbers.
    names["times"] = _converted(names["times"]) or []
    return values, names


def write_dataset(path: str, values: np.ndarray, names: Dict[str, List[str]], attributes: Dict[str, Any]) -> None:
    """A NetCDF file in MetaGen's layout, missing values included."""
    with netcdf_file(path, "w", version=2) as handle:
        for key, value in {"Conventions": "CF-1.8", **attributes}.items():
            setattr(handle, key, value)
        for dimension, size, given in zip(("gene", "condition", "time"), values.shape,
                                          (names["genes"], names["samples"], names["times"])):
            handle.createDimension(dimension, size)
            labels = given if len(given) == size else list(range(size))
            kind, data = _coordinate(labels)
            if kind == "c":
                handle.createDimension(f"{dimension}_strlen", max(1, data.shape[1]))
                variable = handle.createVariable(dimension, "c", (dimension, f"{dimension}_strlen"))
                variable._Encoding = "utf-8"
            else:
                variable = handle.createVariable(dimension, kind, (dimension,))
            variable[:] = data
        data_variable = handle.createVariable("values", "d", ("gene", "condition", "time"))
        data_variable._FillValue = np.nan
        data_variable[:] = values


def convert_datasets(resources: str, output: str, only: Optional[List[str]] = None,
                     rename: Optional[Dict[str, Dict[str, str]]] = None) -> List[str]:
    """Convert the datasets of a resources.xml; returns what it did, a line per dataset."""
    os.makedirs(output, exist_ok=True)
    root = ElementTree.parse(os.path.join(resources, "resources.xml")).getroot()
    sizes, report = {}, []
    for element in root.iter("dataset"):
        name = element.attrib["name"]
        if only and name not in only:
            continue
        values, names = read_dataset(os.path.join(resources, element.attrib["id"]), element)
        renamed = (rename or {}).get(name, {})
        count = sum(gene in renamed for gene in names["genes"])
        names["genes"] = [renamed.get(gene, gene) for gene in names["genes"]]
        attributes = {"description": element.attrib.get("description", ""), "source": f"TrLab dataset {element.attrib['id']}",
                      "organism": element.attrib.get("organism", ""), "kind": element.attrib.get("type", "")}
        write_dataset(os.path.join(output, f"{name}.nc"), values, names, attributes)
        a = element.attrib
        sizes[name] = {"min_sizes": [int(a["minG"]), int(a["minC"]), int(a["minT"])],
                       "max_sizes": [int(a["maxG"]), int(a["maxC"]), int(a["maxT"])]}
        missing = int(np.isnan(values).sum())
        report.append(f"{name}: {values.shape}, {missing} missing values, "
                      f"{count} genes renamed")
    with open(os.path.join(output, "sizes.json"), "w") as handle:
        json.dump(sizes, handle, indent=2)
    return report


def read_sol(path: str) -> Dict[str, str]:
    """The properties of a .sol file, and the date of its first comment."""
    properties: Dict[str, str] = {}
    for line in _lines_all(path):
        if line.startswith("#"):
            if len(line) > 1 and "date" not in properties:
                properties["date"] = line[1:].strip()
            continue
        key, _, value = line.partition("=")
        properties[key.strip()] = value.strip()
    return properties


def _lines_all(path: str) -> List[str]:
    text = open(path, "rb").read().decode("latin-1")
    return [line for line in re.split(r"\r\n|\r|\n", text) if line.strip()]


def convert_sol(path: str, dataset: str, output: str) -> TriGenResult:
    """Convert a .sol result on the dataset it was found in, as converted to NetCDF."""
    properties = read_sol(path)
    cube = Cube.from_netcdf(dataset)
    triclusters = []
    for text in properties["solutions"].split("@"):
        genes, conditions, times = ([int(value) for value in part.split(",") if value] for part in text.split(";"))
        triclusters.append(Tricluster(genes, conditions, times))
    measure, views = FITNESS.get(properties.get("fitness", ""), ("msl", "trlab"))
    weights = {name: float(properties[key]) for key, name in WEIGHTS.items() if key in properties}
    configuration = {"n_triclusters": int(properties.get("N", len(triclusters))), "generations": int(properties["G"]),
                     "population_size": int(properties["I"]), "random_fraction": float(properties.get("Ale", 0.2)),
                     "selection_rate": float(properties.get("Sel", 0.5)),
                     "mutation_probability": float(properties.get("Mut", 0.1)),
                     "min_sizes": [int(properties[key]) for key in ("minG", "minC", "minT")],
                     "max_sizes": [int(properties[key]) for key in ("maxG", "maxC", "maxT")],
                     "measure": measure, "views": views, "flat_profiles": "exclude",
                     "weights": weights if len(weights) == 7 else None, "size_reference": "dataset", "seed": None,
                     "growth": None, "scoring": "weighted", "pruning": False, "shuffle_genes": False}
    provenance = {"converted_from": "TrLab", "date": properties.get("date"), "seconds": None, "complete": True,
                  "trlab": {key: value for key, value in properties.items() if key != "solutions"}}
    names = [tricluster.labels(cube) for tricluster in triclusters]
    result = TriGenResult(configuration=configuration, provenance=provenance,
                          data={"shape": list(cube.shape), "sha256": cube.fingerprint,
                                "label": os.path.splitext(os.path.basename(dataset))[0]},
                          triclusters=triclusters, names=[{axis: list(labels) for axis, labels in n.items()} for n in names],
                          terms=[{} for _ in triclusters], searches=[])
    result.save(output)
    return result


def main(arguments: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Convert TrLab datasets and results to MetaGen's formats.")
    commands = parser.add_subparsers(dest="command", required=True)
    datasets = commands.add_parser("datasets", help="the datasets of a resources.xml, to NetCDF")
    datasets.add_argument("resources")
    datasets.add_argument("output")
    datasets.add_argument("--only", nargs="*")
    datasets.add_argument("--rename", help="a JSON file with new gene names, by dataset")
    sol = commands.add_parser("sol", help="a .sol result, to a TriGen result file")
    sol.add_argument("sol")
    sol.add_argument("dataset")
    sol.add_argument("output")
    given = parser.parse_args(arguments)
    if given.command == "datasets":
        rename = json.load(open(given.rename)) if given.rename else None
        for line in convert_datasets(given.resources, given.output, given.only, rename):
            print(line)
    else:
        result = convert_sol(given.sol, given.dataset, given.output)
        print(f"{given.output}: {len(result.triclusters)} triclusters")


if __name__ == "__main__":
    main(sys.argv[1:])
