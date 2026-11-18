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

# Reading and downloading a DataSet of the Gene Expression Omnibus (GEO).

from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import Cube
from metagen.triclustering.data.text import cube_from, parsed_number


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
        group = (" / ".join(factors[factor][sample] for factor in chosen), factors[time][sample])
        groups.setdefault(group, []).append(column)
    counts = {len(groups.get((label, level), [])) for label in labels for level in times}
    if len(counts) != 1 or 0 in counts:
        raise ValueError(f"The conditions of {path} do not have as many replicates at every time ({sorted(counts)}): "
                         f"choose the factors of the conditions with conditions=.")
    copies = counts.pop()
    position = {column: index for index, column in enumerate(header)}
    columns = [position[sample] for sample in samples]
    raw = np.array([[parsed_number(row[column] if column < len(row) else "", {"null", "", "NA"}, path, line)
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
    return cube_from(values, [names, condition_names, times], path, drop_missing)


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
