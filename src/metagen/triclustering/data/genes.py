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

# Preparing the genes of a cube, and checking what may be wrong with it.

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from metagen.triclustering.cube import Cube


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
