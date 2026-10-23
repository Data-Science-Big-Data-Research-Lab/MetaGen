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

import csv
import datetime
import json
import math
import os
import platform
import tempfile
from dataclasses import dataclass, field
from importlib import metadata
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional

import numpy as np

from metagen.triclustering import Cube, Tricluster
from metagen.triclustering.cube import AXES

if TYPE_CHECKING:
    from metagen.metaheuristics.trigen.trigen import TriGen

#: The name and the version of the format a result is saved in.
FORMAT = "metagen-trigen"
VERSION = 2

# Version 2 adds the cells of a tricluster that is not a cube; a result whose triclusters
# are all cubes is still written in version 1, as it was before.
_CUBES_VERSION = 1

#: The arguments of TriGen a result keeps: all but the cube and the history file.
CONFIGURATION = ("n_triclusters", "generations", "population_size", "random_fraction", "selection_rate",
                 "mutation_probability", "min_sizes", "max_sizes", "measure", "views", "flat_profiles", "weights",
                 "size_reference", "seed", "growth", "scoring", "pruning", "shuffle_genes", "overlap",
                 "hierarchy", "shape", "ordered", "neighborhood", "pixels", "stop", "cover", "coverage",
                 "noise_rule", "decline")


# The options TriGen gained after the format was set, with the value a result saved before
# them ran with.
_LATER_OPTIONS: Dict[str, Any] = {"shuffle_genes": False, "overlap": "coordinates", "hierarchy": "coordinates",
                                  "shape": "cube", "ordered": [], "neighborhood": 4, "pixels": None,
                                  "stop": "count", "cover": "genes", "coverage": 1.0, "noise_rule": None,
                                  "decline": 0.5}


@dataclass
class TriGenResult:
    """
    What a run of TriGen found and how: the triclusters, with the names of their genes,
    conditions and times and the terms of their fitness; the configuration of the run and
    where it comes from, enough to run it again; a fingerprint of the data, to tell whether
    a cube is the one the run worked on; and the progress of each search.

    It is saved as a JSON file that describes itself, with the name and the version of its
    format, readable from any language, and it holds neither the data nor a path to them.
    Names that are neither text nor numbers, such as dates, are kept as their text, and a
    value that is not a number as null.

    .. code-block:: python

        from metagen.metaheuristics import TriGen, TriGenResult
        from metagen.triclustering import plant

        cube, planted = plant((60, 6, 8), [(12, 3, 5)], noise=0.05, seed=0)
        trigen = TriGen(cube, n_triclusters=2, generations=10, population_size=20,
                        min_sizes=(4, 2, 3), max_sizes=(15, 4, 6), seed=0)
        trigen.run()
        trigen.save("run.json", label="planted example")

        result = TriGenResult.load("run.json")
        print(result.triclusters == trigen.triclusters, result.matches(cube))    # True True
        print(result.trigen(cube).run() == result.triclusters)                   # True

    :param configuration: The arguments TriGen was built with, all but the cube and the
        history file.
    :param provenance: The versions, the platform, the date and the seconds of the run, the
        evaluations of its searches, of growing and of fitting the model of chance, and
        whether it ran to its end.
    :param data: The shape of the cube, its fingerprint and a label.
    :param triclusters: The triclusters found, in order, each with its fitness.
    :param names: For each tricluster, the names of its genes, conditions and times.
    :param terms: For each tricluster, the terms of its fitness.
    :param searches: For each search, its progress, evaluations and seconds, and the index
        of the tricluster it found, or None.
    :raises ValueError: if the configuration is not that of a TriGen, or the names or the
        terms are not those of the triclusters.
    """

    configuration: Dict[str, Any]
    provenance: Dict[str, Any]
    data: Dict[str, Any]
    triclusters: List[Tricluster]
    names: List[Dict[str, List[Any]]] = field(default_factory=list)
    terms: List[Dict[str, Any]] = field(default_factory=list)
    searches: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if isinstance(self.configuration, dict):
            # Saved before TriGen had these options, which is to say with what they default to.
            self.configuration = {**_LATER_OPTIONS, **self.configuration}
        if not isinstance(self.configuration, dict) or set(self.configuration) != set(CONFIGURATION):
            given = sorted(self.configuration) if isinstance(self.configuration, dict) else self.configuration
            raise ValueError(f"The configuration of a TriGen holds {sorted(CONFIGURATION)}, not {given}")
        if not (isinstance(self.data, dict) and isinstance(self.data.get("sha256"), str)
                and isinstance(self.data.get("shape"), list) and len(self.data["shape"]) == 3
                and all(isinstance(size, int) and not isinstance(size, bool) for size in self.data["shape"])):
            raise ValueError("The data of a result are the shape of the cube and its fingerprint")
        if not isinstance(self.provenance, dict) or not isinstance(self.searches, list):
            raise ValueError("The provenance of a result is a mapping and its searches a list")
        if not len(self.triclusters) == len(self.names) == len(self.terms):
            raise ValueError(f"There are {len(self.triclusters)} triclusters, {len(self.names)} sets of names and "
                             f"{len(self.terms)} sets of terms")
        for tricluster, names in zip(self.triclusters, self.names):
            sizes = tuple(len(names[axis]) for axis in AXES) if isinstance(names, dict) and all(
                isinstance(names.get(axis), list) for axis in AXES) else None
            if sizes != tricluster.size:
                raise ValueError(f"The names of a tricluster are one per gene, condition and time: {tricluster.size}")
            if any(position >= size for positions, size in zip(
                    (tricluster.genes, tricluster.conditions, tricluster.times), self.data["shape"])
                   for position in positions):
                raise ValueError(f"A tricluster holds positions beyond the shape of the data, {self.data['shape']}")

    @classmethod
    def from_run(cls, trigen: TriGen, label: Optional[str] = None) -> TriGenResult:
        """
        The result of the last run of a TriGen: what its searches found, as each recorded
        it, with the configuration the run started with.

        :param trigen: The TriGen, after its run.
        :type trigen: TriGen
        :param label: A free label for the data, such as the name of the dataset.
        :type label: str, optional
        :return: The result.
        :rtype: TriGenResult
        :raises ValueError: if the TriGen has not run.
        """
        if not trigen.history or trigen.started is None:
            raise ValueError("This TriGen has not run: there is no result to keep.")
        cube = trigen.cube
        triclusters: List[Tricluster] = []
        names: List[Dict[str, List[Any]]] = []
        terms: List[Dict[str, Any]] = []
        searches: List[Dict[str, Any]] = []
        for record in trigen.history:
            found = record["tricluster"]
            searches.append({"search": record["search"], "tricluster": len(triclusters) if found is not None else None,
                             "best_fitnesses": list(record["best_fitnesses"]),
                             "evaluations": record["evaluations"],
                             "growth_evaluations": record["growth_evaluations"], "seconds": record["seconds"]})
            if found is not None:
                tricluster = (Tricluster(found["genes"], found["conditions"], found["times"], fitness=record["fitness"])
                              if "cells" not in found else
                              Tricluster.from_cells(found["cells"][0], found["cells"][1], found["cells"][2],
                                                    fitness=record["fitness"]))
                triclusters.append(tricluster)
                terms.append(dict(record["terms"]))
                names.append({axis: [_plain(labels[position]) for position in positions] for axis, labels, positions in
                              zip(AXES, (cube.genes, cube.conditions, cube.times),
                                  (tricluster.genes, tricluster.conditions, tricluster.times))})
        configuration = trigen.started["configuration"]
        provenance = {"metagen": _installed_version(), "python": platform.python_version(),
                      "numpy": np.__version__, "platform": platform.platform(),
                      "date": trigen.started["date"], "seed": configuration["seed"], "seconds": trigen.seconds,
                      "evaluations": sum(search["evaluations"] for search in searches),
                      "growth_evaluations": sum(search["growth_evaluations"] for search in searches),
                      "chance_evaluations": trigen.started["chance_evaluations"],
                      "complete": trigen.finished and (configuration["stop"] == "coverage"
                                                       or len(trigen.history) == configuration["n_triclusters"]),
                      "stop_reason": trigen.stop_reason if trigen.finished else None, "covered": trigen.covered,
                      "noise_threshold": trigen.noise_threshold}
        data = {"shape": list(cube.shape), "sha256": cube.fingerprint, "label": label}
        return cls(configuration=dict(configuration), provenance=provenance, data=data, triclusters=triclusters,
                   names=names, terms=terms, searches=searches)

    def save(self, path: str) -> None:
        """
        Write the result to a JSON file, replacing it whole if it exists: it is written
        aside and then renamed over, so a cut while writing leaves the file as it was.

        :param path: The file.
        :type path: str
        """
        version = VERSION if any(not tricluster.is_cube for tricluster in self.triclusters) else _CUBES_VERSION
        document = {"format": FORMAT, "version": version, "provenance": self.provenance,
                    "configuration": self.configuration, "data": self.data,
                    "triclusters": [
                        {"genes": list(tricluster.genes), "conditions": list(tricluster.conditions),
                         "times": list(tricluster.times), "gene_names": names["genes"],
                         "condition_names": names["conditions"], "time_names": names["times"],
                         "fitness": tricluster.fitness, "terms": terms,
                         **({} if tricluster.is_cube else {"cells": [column.tolist() for column in tricluster.cells()]})}
                        for tricluster, names, terms in zip(self.triclusters, self.names, self.terms)],
                    "searches": self.searches}
        text = json.dumps(_plain(document), indent=1, allow_nan=False) + "\n"
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=os.path.basename(path) + ".", suffix=".tmp", dir=directory)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        except BaseException:
            if os.path.exists(temporary):
                os.remove(temporary)
            raise

    @classmethod
    def load(cls, path: str) -> TriGenResult:
        """
        Read a result from a file written by :py:meth:`save`.

        :param path: The file.
        :type path: str
        :return: The result.
        :rtype: TriGenResult
        :raises ValueError: if the file is not a TriGen result, or its version of the format
            is later than this one.
        """
        try:
            with open(path, encoding="utf-8") as handle:
                document = json.load(handle, parse_constant=_not_json)
            if not isinstance(document, dict) or document.get("format") != FORMAT:
                raise ValueError("it does not say it is one")
            version = document.get("version")
            if isinstance(version, bool) or not isinstance(version, int) or version < 1:
                raise ValueError(f"its version is {version!r}")
        except (ValueError, RecursionError) as error:
            raise ValueError(f"{path} is not a TriGen result: {error}.") from None
        if version > VERSION:
            raise ValueError(f"{path} is a TriGen result in version {version} of its format, and this MetaGen reads "
                             f"up to version {VERSION}: update MetaGen.")
        try:
            found = document["triclusters"]
            triclusters = [Tricluster(entry["genes"], entry["conditions"], entry["times"], fitness=entry["fitness"])
                           if "cells" not in entry else
                           Tricluster.from_cells(entry["cells"][0], entry["cells"][1], entry["cells"][2],
                                                 fitness=entry["fitness"]) for entry in found]
            names = [{"genes": entry["gene_names"], "conditions": entry["condition_names"],
                      "times": entry["time_names"]} for entry in found]
            return cls(configuration=document["configuration"], provenance=document["provenance"],
                       data=document["data"], triclusters=triclusters, names=names,
                       terms=[entry["terms"] for entry in found], searches=document["searches"])
        except KeyError as error:
            raise ValueError(f"{path} is not a TriGen result: it lacks {error}.") from None
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError(f"{path} is not a TriGen result: {str(error).rstrip('.')}.") from None

    def matches(self, cube: Cube) -> bool:
        """
        Whether a cube holds the data the run worked on: the same shape and values.

        :param cube: The cube.
        :type cube: Cube
        :return: Whether its fingerprint is the one kept with the result.
        :rtype: bool
        """
        return list(cube.shape) == list(self.data["shape"]) and cube.fingerprint == self.data["sha256"]

    def trigen(self, cube: Cube) -> TriGen:
        """
        A TriGen with the configuration of the run, to run it again on its data: with the
        same seed, on the same platform and versions, it finds the same triclusters.

        :param cube: The cube the run worked on.
        :type cube: Cube
        :return: The TriGen, not yet run.
        :rtype: TriGen
        :raises ValueError: if the cube is not the one the run worked on.
        """
        from metagen.metaheuristics.trigen.trigen import TriGen
        if not self.matches(cube):
            raise ValueError("The cube is not the one this run worked on: its shape or its values differ.")
        return TriGen(cube, **{name: self.configuration[name] for name in CONFIGURATION})

    def to_csv(self, path: str) -> None:
        """
        Write the triclusters as a long table, a row per coordinate: the tricluster, the
        dimension, the position in the cube and the name.

        :param path: The file.
        :type path: str
        """
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["tricluster", "dimension", "position", "name"])
            for index, (tricluster, names) in enumerate(zip(self.triclusters, self.names)):
                for axis, positions in zip(AXES, (tricluster.genes, tricluster.conditions, tricluster.times)):
                    for position, name in zip(positions, names[axis]):
                        writer.writerow([index, axis, position, _plain(name)])


def _installed_version() -> Optional[str]:
    try:
        return metadata.version("pymetagen-datalabupo")
    except metadata.PackageNotFoundError:
        return None


def _not_json(constant: str) -> Any:
    raise ValueError(f"it holds {constant}, which JSON does not")


def _plain(value: Any) -> Any:
    """A value as JSON holds it: NumPy numbers as numbers, what is not a number (NaN, the
    infinities) as null, tuples as lists, and any other object, dates among them, as its
    text."""
    if isinstance(value, Mapping):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    if isinstance(value, (np.datetime64, np.timedelta64)):
        return str(value)
    if isinstance(value, np.generic):
        value = value.item()
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)
