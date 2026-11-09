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

import datetime
import html
import io
import math
import os
import platform
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Sequence, Tuple

import numpy as np

from metagen.reporting import (INK, MUTED, SERIES, _STYLE, _axes_style, _new_figure, _pdf_tables, _svg, _table,
                               _text, _version)

if TYPE_CHECKING:
    from metagen.metaheuristics.trigen.results import TriGenResult
    from metagen.triclustering import Cube, Tricluster

#: The triclusters drawn one by one; the rest are in the table only.
MOST_DETAILED = 10
#: The most panels of a view, and the most lines of a panel, the median always drawn.
MOST_PANELS, MOST_LINES = 6, 40

#: The options of the run the report lists, those the configuration has.
OPTIONS = ("shape", "scoring", "measure", "views", "n_triclusters", "generations", "population_size", "min_sizes",
           "max_sizes", "growth", "pruning", "shuffle_genes", "ordered", "neighborhood", "pixels", "stop", "cover",
           "coverage", "noise_rule", "decline", "patience", "disjoint", "seed")


def trigen_report(result: "TriGenResult", cube: Optional["Cube"], path: str, title: Optional[str] = None,
                  detailed: int = MOST_DETAILED, enrichment: Any = None) -> str:
    """
    Write a report of a run of TriGen, an HTML page with everything in it or a PDF, by the
    extension of ``path``, and next to it the triclusters as a CSV table of coordinates
    (:py:meth:`TriGenResult.to_csv`). It shows the run (the data, the options, what it spent,
    why it ended and what it held), a table of the triclusters with their sizes, fitness, terms
    and cost, the best fitness of each search by generation, the share of the genes or pixels
    held as the triclusters were found, the cells two triclusters share, and, for each of the
    first ``detailed`` triclusters, its values: for a cube, the three views of TrLab, by time,
    by condition and over time; for a prism, the series of its pixels along its window, after a
    map of the plane with every prism. Without the cube, the values are left out. With the cube,
    the table also holds the TRIQ of each tricluster of a cube and its graphical, Pearson and
    Spearman qualities, with the views and the flat profiles of the run. Needs matplotlib, the
    ``report`` extra.

    With ``enrichment``, an engine such as :py:class:`~metagen.triclustering.LocalGO` or
    :py:class:`~metagen.triclustering.GProfiler`, or the enrichment of each tricluster already
    computed, it also shows the biological enrichment of the genes of the triclusters of cubes:
    their purity, their BIOQ, their significant terms and, with the cube, their TRIQ with BIOQ in
    the table; the most significant terms of every tricluster side by side; for each tricluster drawn, its
    terms by the share of its genes they annotate, and, when the engine gives the genes of each
    term as LocalGO does, which of its genes each term annotates and, with networkx installed, a
    map of its terms joined by the genes they share. Next to the report go the significant terms
    of every tricluster as a CSV table.

    :param result: The result of the run.
    :type result: TriGenResult
    :param cube: The data the run worked on, or None to leave out the values.
    :type cube: Cube or None
    :param path: The file, ``.html`` or ``.pdf``.
    :type path: str
    :param title: The title, defaults to the label of the data, or "TriGen".
    :type title: str, optional
    :param detailed: How many triclusters to draw one by one, defaults to 10.
    :type detailed: int, optional
    :param enrichment: An engine of enrichment, or an enrichment (or None) per tricluster,
        or None, the default, for no enrichment.
    :type enrichment: EnrichmentProvider or Sequence[Enrichment or None], optional
    :return: The file written.
    :rtype: str
    :raises ImportError: if matplotlib is not installed.
    :raises ValueError: if the extension is neither, the cube is not the one the run worked
        on, or an enrichment is asked of prisms, without the cube, or with not one per
        tricluster.
    """
    try:
        import matplotlib
    except ImportError as error:
        raise ImportError("A report needs matplotlib: pip install pymetagen-datalabupo[report]") from error
    matplotlib.use("Agg", force=False)
    extension = os.path.splitext(path)[1].lower()
    if extension not in (".html", ".htm", ".pdf"):
        raise ValueError(f"A report is an .html or a .pdf file, not {path!r}.")
    if cube is not None and not result.matches(cube):
        raise ValueError("The cube is not the one this run worked on: its shape or its values differ.")
    heading = title or result.data.get("label") or "TriGen"
    os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
    enrichments = _enrichments(result, cube, enrichment)
    table = os.path.splitext(path)[0] + ".csv"
    result.to_csv(table)
    if enrichments is not None:
        _terms_csv(enrichments, os.path.splitext(path)[0] + "_enrichment.csv")
    sections = _sections(result, cube, detailed, enrichments)
    if extension == ".pdf":
        _pdf(result, heading, sections, path, enrichments, cube)
    else:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_html(result, heading, sections, os.path.basename(table), enrichments,
                               os.path.basename(os.path.splitext(path)[0] + "_enrichment.csv"), cube))
    return path


# --- What the result says ----------------------------------------------------------------------

def _is_prism(result: "TriGenResult") -> bool:
    return result.configuration.get("shape") == "prism"


def _run_rows(result: "TriGenResult") -> List[Tuple[str, str]]:
    data, provenance, configuration = result.data, result.provenance, result.configuration
    rows = [("data", f"{data.get('label') or ''} {' × '.join(map(str, data['shape']))}".strip())]
    prism_only = () if _is_prism(result) else ("neighborhood", "pixels")
    rows += [(name, _text(configuration[name])) for name in OPTIONS if name in configuration
             and configuration[name] is not None and name not in prism_only]
    rows.append(("triclusters", str(len(result.triclusters))))
    for name, key in (("stop reason", "stop_reason"), ("held", "covered"), ("noise threshold", "noise_threshold"),
                      ("evaluations of the searches", "evaluations"), ("evaluations of growing", "growth_evaluations"),
                      ("evaluations of the model of chance", "chance_evaluations"), ("seconds", "seconds"),
                      ("complete", "complete"), ("MetaGen", "metagen"), ("date", "date")):
        if provenance.get(key) is not None:
            rows.append((name, _text(provenance[key])))
    return rows


def _units(result: "TriGenResult", tricluster: "Tricluster") -> set:
    if _is_prism(result) and result.configuration.get("cover", "pixels") == "pixels":
        from metagen.metaheuristics.trigen.shape import prism_parts
        return set(prism_parts(tricluster)[0])
    return set(tricluster.genes)


def _size(result: "TriGenResult", tricluster: "Tricluster") -> str:
    if _is_prism(result):
        from metagen.metaheuristics.trigen.shape import prism_parts
        pixels, times = prism_parts(tricluster)
        return f"{len(pixels)} pixels × {len(times)} times"
    return " × ".join(str(count) for count in tricluster.size)


def _tricluster_rows(result: "TriGenResult", enrichments: Optional[List[Any]] = None,
                     cube: Optional["Cube"] = None) -> Tuple[List[str], List[List[str]]]:
    searches = {search["tricluster"]: search for search in result.searches if search.get("tricluster") is not None}
    names = sorted({name for terms in result.terms for name in terms
                    if name in ("quality", "z", "z_found", "overlap_cells")})
    header = ["#", "size", "cells", "fitness"] + names + ["search ev.", "growth ev.", "seconds"]
    rows = []
    for index, (tricluster, terms) in enumerate(zip(result.triclusters, result.terms)):
        search = searches.get(index, {})
        rows.append([str(index), _size(result, tricluster), str(tricluster.n_cells), _text(tricluster.fitness)]
                    + [_text(terms.get(name)) for name in names]
                    + [_text(search.get("evaluations")), _text(search.get("growth_evaluations")),
                       _text(round(search["seconds"], 2)) if search.get("seconds") is not None else ""])
    # TRIQ and its parts with the views and the flat profiles of the run; with the enrichment,
    # also TRIQ with BIOQ, which weighs half and leaves out a BIOQ that is not defined
    quality: Optional[Callable[[Any, Optional[float]], List[float]]] = None
    if cube is not None and not _is_prism(result):
        from metagen.triclustering import grq, peq, spq, triq
        data = cube
        views = result.configuration.get("views", "distinct")
        flat = result.configuration.get("flat_profiles", "exclude")

        def quality(tricluster: Any, biological: Optional[float]) -> List[float]:
            if biological is not None:
                return [triq(data, tricluster, bioq=biological, views=views, flat_profiles=flat)]
            return [grq(data, tricluster, views), peq(data, tricluster, flat), spq(data, tricluster, flat),
                    triq(data, tricluster, views=views, flat_profiles=flat)]

        header += ["GRQ", "PEQ", "SPQ", "TRIQ"]
        for row, tricluster in zip(rows, result.triclusters):
            row += [_text(round(value, 4)) for value in quality(tricluster, None)]
    if enrichments is not None:
        from metagen.triclustering import bioq, purity
        header += ["purity", "BIOQ", "significant terms"] + (["TRIQ with BIOQ"] if quality else [])
        for row, tricluster, found in zip(rows, result.triclusters, enrichments):
            if found is None:
                row += [""] * (4 if quality else 3)
                continue
            biological = bioq(found)
            row += [_text(purity(found, ALPHA)), _text(biological), str(len(found.significant(ALPHA)))]
            if quality:
                row += [_text(round(value, 4)) for value in quality(tricluster, biological)]
    return header, rows


# --- The figures -------------------------------------------------------------------------------

def _sections(result: "TriGenResult", cube: Optional["Cube"], detailed: int,
              enrichments: Optional[List[Any]] = None) -> List[Tuple[str, str, Any]]:
    """The figures, each with its section and its caption."""
    figures: List[Tuple[str, str, Any]] = []
    if result.searches:
        figures.append(("Searches", "The best fitness of each search by generation; the lower, the better",
                        _searches(result)))
    if result.triclusters:
        figures.append(("Searches", _coverage_caption(result), _coverage(result)))
    if len(result.triclusters) > 1 and _shares(result).sum() > 0:
        figures.append(("Searches", "The share of the cells of each tricluster (row) another one (column) also "
                                    "holds", _overlap(result)))
    if not result.triclusters:
        return figures
    shown = result.triclusters[:detailed]
    if enrichments is not None and any(found is not None and found.significant(ALPHA) for found in enrichments):
        figures.append(("Biological enrichment", _compare_caption(enrichments), _compare_terms(enrichments)))
    if cube is None:
        # Without the values, the enrichment of each tricluster drawn, which does not need them
        for index in range(len(shown)):
            found = enrichments[index] if enrichments is not None else None
            if found is not None and found.significant(ALPHA):
                figures += [(f"Tricluster {index}", caption, figure)
                            for caption, figure in _enrichment_figures(found, index)]
        return figures
    if _is_prism(result):
        figures.append(("Prisms", "The plane, with the surface of each prism drawn in its number",
                        _plane(result, cube)))
        for index, tricluster in enumerate(shown):
            figures.append((f"Prism {index}", f"Prism {index}: the series of each of its pixels along its window, "
                                              f"with their median", _prism_series(cube, tricluster)))
        return figures
    for index, tricluster in enumerate(shown):
        for caption, figure in _views(cube, tricluster, index):
            figures.append((f"Tricluster {index}", caption, figure))
        found = enrichments[index] if enrichments is not None else None
        if found is not None and found.significant(ALPHA):
            figures += [(f"Tricluster {index}", caption, figure) for caption, figure in _enrichment_figures(found, index)]
    return figures


def _searches(result: "TriGenResult") -> Any:
    figure, axes = _new_figure()
    plot = axes[0][0]
    many = len(result.searches) > len(SERIES)
    for index, search in enumerate(result.searches):
        values = search.get("best_fitnesses") or []
        if not values:
            continue
        plot.plot(range(1, len(values) + 1), values, linewidth=1.4 if not many else 0.8,
                  color=SERIES[index % len(SERIES)] if not many else SERIES[0], alpha=1 if not many else 0.45,
                  label=f"search {index}" if not many else None)
    plot.set_xlabel("generation", fontsize=9, color=MUTED)
    plot.set_ylabel("best fitness", fontsize=9, color=MUTED)
    if not many:
        plot.legend(fontsize=7, frameon=False, ncol=4)
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _coverage_caption(result: "TriGenResult") -> str:
    unit = "pixels" if _is_prism(result) and result.configuration.get("cover", "pixels") == "pixels" else "genes"
    left = [search["left_out"]["significance"] for search in result.searches if search.get("left_out")]
    caption = f"The share of the {unit} the triclusters hold, as they were found"
    if left:
        caption += f"; left out as noise: {len(left)}, with significance {', '.join(_text(value) for value in left)}"
    reason = result.provenance.get("stop_reason")
    caption += f"; the run ended by {reason}" if reason else ""
    if len(result.triclusters) > 1 and _shares(result).sum() == 0:
        caption += "; no two triclusters share a cell"
    return caption


def _coverage(result: "TriGenResult") -> Any:
    shape = result.data["shape"]
    unit = "pixels" if _is_prism(result) and result.configuration.get("cover", "pixels") == "pixels" else "genes"
    total = shape[0] * shape[1] if unit == "pixels" else shape[0]
    held: set = set()
    shares = []
    for tricluster in result.triclusters:
        held |= _units(result, tricluster)
        shares.append(len(held) / total)
    figure, axes = _new_figure(height=2.6)
    plot = axes[0][0]
    plot.bar(range(len(shares)), shares, color=SERIES[0], width=0.7)
    target = result.configuration.get("coverage")
    if result.configuration.get("stop") == "coverage" and target is not None:
        plot.axhline(target, color=SERIES[1], linewidth=1.2, linestyle="--", label=f"coverage asked, {target:g}")
        plot.legend(fontsize=7, frameon=False)
    from matplotlib.ticker import MaxNLocator
    plot.xaxis.set_major_locator(MaxNLocator(integer=True))
    plot.set_ylim(0, 1)
    plot.set_xlabel("tricluster", fontsize=9, color=MUTED)
    plot.set_ylabel(f"share of the {unit} held", fontsize=9, color=MUTED)
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _shares(result: "TriGenResult") -> np.ndarray:
    """The share of the cells of each tricluster another one also holds, 0 on the diagonal."""
    cells = [set(zip(*[column.tolist() for column in tricluster.cells()])) for tricluster in result.triclusters]
    count = len(cells)
    shares = np.zeros((count, count))
    for row in range(count):
        for column in range(count):
            if row != column and cells[row]:
                shares[row, column] = len(cells[row] & cells[column]) / len(cells[row])
    return shares


def _overlap(result: "TriGenResult") -> Any:
    from matplotlib.ticker import MaxNLocator
    shares = _shares(result)
    count = len(shares)
    side = min(8.0, 2.0 + 0.35 * count)
    figure, axes = _new_figure(height=side)
    plot = axes[0][0]
    from matplotlib.colors import LinearSegmentedColormap
    ramp = LinearSegmentedColormap.from_list("share", ["#f3f6fb", SERIES[0]])
    image = plot.imshow(shares, cmap=ramp, vmin=0, vmax=1)
    if count <= 20:
        for row in range(count):
            for column in range(count):
                if row != column and shares[row, column] > 0:
                    share = shares[row, column]
                    plot.text(column, row, f"{share:.2f}" if share >= 0.005 else "<0.01", ha="center", va="center",
                              fontsize=6,
                              color=INK)
    plot.set_xlabel("tricluster", fontsize=9, color=MUTED)
    plot.set_ylabel("tricluster", fontsize=9, color=MUTED)
    plot.xaxis.set_major_locator(MaxNLocator(integer=True))
    plot.yaxis.set_major_locator(MaxNLocator(integer=True))
    plot.tick_params(labelsize=7, colors=MUTED)
    figure.colorbar(image, ax=plot, fraction=0.04)
    figure.tight_layout()
    return figure


def _panels(count: int) -> Tuple[int, int]:
    columns = min(3, count)
    return math.ceil(count / columns), columns


def _view(values: np.ndarray, panel_names: Sequence[Any], line_count: int, x_names: Sequence[Any], panel_label: str,
          x_label: str) -> Any:
    """Panels of lines: values (panels, lines, x), at most MOST_PANELS panels and MOST_LINES
    lines each, with the median of all the lines of a panel in black and the y axis shared."""
    panels = min(len(panel_names), MOST_PANELS)
    rows, columns = _panels(panels)
    figure, axes = _new_figure(height=2.3 * rows, columns=columns, rows=rows)
    low, high = np.nanmin(values[:panels]), np.nanmax(values[:panels])
    margin = 0.05 * (high - low or 1.0)
    x = np.arange(values.shape[2])
    for index in range(panels):
        plot = axes[index // columns][index % columns]
        for line in values[index][:MOST_LINES]:
            plot.plot(x, line, color=SERIES[0], linewidth=0.7, alpha=0.45)
        plot.plot(x, np.median(values[index], axis=0), color=INK, linewidth=1.8)
        plot.set_ylim(low - margin, high + margin)
        name = str(panel_names[index])
        # The name alone when it already says what it is, as "Time 6" does
        plot.set_title(name if name.lower().startswith(panel_label.lower()) else f"{panel_label} {name}",
                       fontsize=8, color=INK, loc="left")
        ticks = x if len(x) <= 12 else x[:: math.ceil(len(x) / 12)]
        plot.set_xticks(ticks, [str(x_names[tick]) for tick in ticks], rotation=45 if len(ticks) > 6 else 0,
                        ha="right" if len(ticks) > 6 else "center", fontsize=6)
        plot.set_xlabel(x_label, fontsize=7, color=MUTED)
        _axes_style(plot)
    for index in range(panels, rows * columns):
        axes[index // columns][index % columns].set_visible(False)
    figure.tight_layout()
    return figure


def _views(cube: "Cube", tricluster: "Tricluster", index: int) -> List[Tuple[str, Any]]:
    """The three views of TrLab of a cube."""
    genes, conditions, times = (list(tricluster.genes), list(tricluster.conditions), list(tricluster.times))
    values = cube.values[np.ix_(genes, conditions, times)]                     # (genes, conditions, times)
    gene_names = [cube.genes[g] for g in genes]
    condition_names = [cube.conditions[c] for c in conditions]
    time_names = [cube.times[t] for t in times]
    more = lambda count, what: f"; the first {MOST_PANELS} of {count} {what}" if count > MOST_PANELS else ""
    lines = lambda count, what: f", the first {MOST_LINES} of {count} {what} and" if count > MOST_LINES else ""
    return [
        (f"Tricluster {index} by time: a panel per time, a line per condition{lines(len(conditions), 'conditions')} "
         f"the median in black, over its genes{more(len(times), 'times')}",
         _view(np.transpose(values, (2, 1, 0)), time_names, len(conditions), gene_names, "time", "gene")),
        (f"Tricluster {index} by condition: a panel per condition, a line per time{lines(len(times), 'times')} "
         f"the median in black, over its genes{more(len(conditions), 'conditions')}",
         _view(np.transpose(values, (1, 2, 0)), condition_names, len(times), gene_names, "condition", "gene")),
        (f"Tricluster {index} over time: a panel per condition, a line per gene{lines(len(genes), 'genes')} "
         f"the median in black, along its times{more(len(conditions), 'conditions')}",
         _view(np.transpose(values, (1, 0, 2)), condition_names, len(genes), time_names, "condition", "time")),
    ]


def _plane(result: "TriGenResult", cube: "Cube") -> Any:
    from matplotlib.colors import ListedColormap
    from metagen.metaheuristics.trigen.shape import prism_parts
    rows, columns = cube.shape[0], cube.shape[1]
    plane = np.full((rows, columns), -1)
    for index, tricluster in enumerate(result.triclusters):
        for x, y in prism_parts(tricluster)[0]:
            plane[x, y] = index
    figure, axes = _new_figure(height=6.5)
    plot = axes[0][0]
    count = max(len(result.triclusters), 1)
    # A white edge between two prisms, since with more prisms than colors two neighbors may
    # share one: the plane enlarged, and its pixels on a border drawn white.
    scale = max(2, 512 // max(rows, columns))
    large = np.kron(plane, np.ones((scale, scale), dtype=int))
    edge = np.zeros(large.shape, dtype=bool)
    edge[:, :-1] |= large[:, :-1] != large[:, 1:]
    edge[:-1, :] |= large[:-1, :] != large[1:, :]
    large[edge] = -2
    colors = ["white", "#eeede9"] + [SERIES[index % len(SERIES)] for index in range(count)]
    plot.imshow(large, cmap=ListedColormap(colors), vmin=-2.5, vmax=count - 0.5, interpolation="nearest",
                extent=(-0.5, columns - 0.5, rows - 0.5, -0.5))
    if count <= 40:
        for index, tricluster in enumerate(result.triclusters):
            pixels = np.array(prism_parts(tricluster)[0])
            plot.text(pixels[:, 1].mean(), pixels[:, 0].mean(), str(index), ha="center", va="center", fontsize=7,
                      color="white", fontweight="bold")
    plot.set_xticks([]), plot.set_yticks([])
    figure.tight_layout()
    return figure


def _prism_series(cube: "Cube", tricluster: "Tricluster") -> Any:
    from metagen.metaheuristics.trigen.shape import prism_parts
    pixels, times = prism_parts(tricluster)
    window = list(times)
    series = np.array([cube.values[x, y, window] for x, y in pixels])[None, :, :]
    return _view(series, ["of the prism"], len(pixels), [cube.times[t] for t in window], "pixels", "time")


# --- Biological enrichment ---------------------------------------------------------------------

#: The adjusted p-value below which a term is significant.
ALPHA = 0.05
#: The most terms of a tricluster drawn, and of all of them side by side.
MOST_TERMS, MOST_COMPARED = 12, 25
#: The share of their genes two terms must share to be joined in the map of terms.
JOINED = 0.3


def _enrichments(result: "TriGenResult", cube: Optional["Cube"], enrichment: Any) -> Optional[List[Any]]:
    """The enrichment of each tricluster: given, or computed with the engine given."""
    if enrichment is None:
        return None
    if _is_prism(result):
        raise ValueError("An enrichment is of the genes of a cube; the triclusters of this run are prisms.")
    if isinstance(enrichment, (list, tuple)):
        if len(enrichment) != len(result.triclusters):
            raise ValueError(f"Give one enrichment per tricluster: {len(enrichment)} for {len(result.triclusters)}.")
        return list(enrichment)
    if cube is None:
        raise ValueError("An enrichment computed here needs the cube, with the names of its genes.")
    from metagen.triclustering import enrich
    return [enrich(cube, tricluster, enrichment) for tricluster in result.triclusters]


def _terms_csv(enrichments: List[Any], path: str) -> None:
    import csv
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["tricluster", "id", "name", "p_adjusted", "study_count", "study_size", "population_count",
                         "population_size", "genes"])
        for index, found in enumerate(enrichments):
            for term in (found.significant(ALPHA) if found is not None else ()):
                writer.writerow([index, term.id, term.name, term.p_adjusted, term.study_count, found.study_size,
                                 term.population_count, found.population_size, " ".join(term.genes)])


def _strength(p_adjusted: float) -> float:
    return -math.log10(max(p_adjusted, 1e-300))


def _ramp() -> Any:
    from matplotlib.colors import LinearSegmentedColormap
    return LinearSegmentedColormap.from_list("significance", ["#cfe0f6", SERIES[0], "#0d3d7a"])


def _short(name: str, most: int = 48) -> str:
    return name if len(name) <= most else name[:most - 1] + "…"


def _compare_caption(enrichments: List[Any]) -> str:
    engines = sorted({f"{found.engine} {found.version}".strip() for found in enrichments if found is not None})
    return (f"The most significant terms of each tricluster, side by side: a dot where the term is significant "
            f"(adjusted p < {ALPHA}), its size the share of the genes of the tricluster it annotates and its color "
            f"how significant it is; enrichment by {', '.join(engines)}")


def _compare_terms(enrichments: List[Any]) -> Any:
    """The most significant terms of every tricluster, three each, side by side."""
    chosen: List[Tuple[str, str]] = []
    for found in enrichments:
        for term in (found.significant(ALPHA)[:3] if found is not None else ()):
            if (term.id, term.name) not in chosen and len(chosen) < MOST_COMPARED:
                chosen.append((term.id, term.name))
    figure, axes = _new_figure(height=1.4 + 0.32 * len(chosen))
    plot = axes[0][0]
    xs, ys, sizes, colors = [], [], [], []
    for column, found in enumerate(enrichments):
        if found is None:
            continue
        significant = {term.id: term for term in found.significant(ALPHA)}
        for row, (identifier, _) in enumerate(chosen):
            term = significant.get(identifier)
            if term is not None and found.study_size:
                xs.append(column)
                ys.append(row)
                sizes.append(20 + 280 * (term.study_count or 0) / found.study_size)
                colors.append(_strength(term.p_adjusted))
    points = plot.scatter(xs, ys, s=sizes, c=colors, cmap=_ramp(), edgecolors="white", linewidths=0.6)
    plot.set_yticks(range(len(chosen)), [_short(name) for _, name in chosen], fontsize=7)
    plot.set_ylim(len(chosen) - 0.5, -0.5)
    plot.set_xticks(range(len(enrichments)), [str(index) for index in range(len(enrichments))], fontsize=7)
    plot.set_xlim(-0.6, len(enrichments) - 0.4)
    plot.set_xlabel("tricluster", fontsize=9, color=MUTED)
    figure.colorbar(points, ax=plot, fraction=0.04, label="−log10 adjusted p")
    _size_legend(plot)
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _size_legend(plot: Any) -> None:
    handles = [plot.scatter([], [], s=20 + 280 * share, color=MUTED, edgecolors="white") for share in (0.25, 0.5, 1.0)]
    plot.legend(handles, ["25 %", "50 %", "100 %"], title="genes annotated", fontsize=7, title_fontsize=7,
                frameon=False, loc="upper left", bbox_to_anchor=(1.12, 1.0))


def _enrichment_figures(found: Any, index: int) -> List[Tuple[str, Any]]:
    figures = [(f"Tricluster {index}: its most significant terms by the share of its genes they annotate, the size "
                f"of the dot their number and its color how significant the term is", _term_dots(found))]
    terms = [term for term in found.significant(ALPHA)[:MOST_TERMS] if term.genes]
    if terms:
        figures.append((f"Tricluster {index}: which of its genes each of its most significant terms annotates",
                        _gene_matrix(terms)))
        try:
            import networkx  # noqa: F401
        except ImportError:
            pass
        else:
            if len(terms) > 1:
                figures.append((f"Tricluster {index}: its most significant terms, joined when they share at least "
                                f"{JOINED:.0%} of their genes; the size of a term its genes and its color how "
                                f"significant it is", _term_map(terms)))
    return figures


def _term_dots(found: Any) -> Any:
    terms = found.significant(ALPHA)[:MOST_TERMS]
    figure, axes = _new_figure(height=1.2 + 0.3 * len(terms))
    plot = axes[0][0]
    shares = [(term.study_count or 0) / found.study_size if found.study_size else 0.0 for term in terms]
    points = plot.scatter(shares, range(len(terms)), s=[30 + 12 * (term.study_count or 0) for term in terms],
                          c=[_strength(term.p_adjusted) for term in terms], cmap=_ramp(), edgecolors="white",
                          linewidths=0.6)
    plot.set_yticks(range(len(terms)), [_short(term.name) for term in terms], fontsize=7)
    plot.set_ylim(len(terms) - 0.5, -0.5)
    plot.set_xlim(0, min(1.0, max(shares) * 1.15 + 0.05))
    plot.set_xlabel("share of the genes of the tricluster the term annotates", fontsize=8, color=MUTED)
    figure.colorbar(points, ax=plot, fraction=0.04, label="−log10 adjusted p")
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _gene_matrix(terms: Sequence[Any]) -> Any:
    counts: dict = {}
    for term in terms:
        for gene in term.genes:
            counts[gene] = counts.get(gene, 0) + 1
    genes = sorted(counts, key=lambda gene: (-counts[gene], gene))[:MOST_LINES]
    matrix = np.array([[gene in term.genes for gene in genes] for term in terms], dtype=float)
    figure, axes = _new_figure(height=1.4 + 0.3 * len(terms))
    plot = axes[0][0]
    from matplotlib.colors import ListedColormap
    plot.imshow(matrix, cmap=ListedColormap(["#f3f6fb", SERIES[0]]), vmin=0, vmax=1, aspect="auto")
    plot.set_yticks(range(len(terms)), [_short(term.name, 40) for term in terms], fontsize=7)
    plot.set_xticks(range(len(genes)), genes, rotation=60, ha="right", fontsize=6)
    plot.set_xticks(np.arange(-0.5, len(genes)), minor=True)
    plot.set_yticks(np.arange(-0.5, len(terms)), minor=True)
    plot.grid(which="minor", color="white", linewidth=1.2)
    plot.tick_params(which="minor", length=0)
    for side in plot.spines.values():
        side.set_visible(False)
    figure.tight_layout()
    return figure


def _term_map(terms: Sequence[Any]) -> Any:
    import networkx as nx
    graph = nx.Graph()
    for term in terms:
        graph.add_node(term.id)
    for first in range(len(terms)):
        for second in range(first + 1, len(terms)):
            a, b = set(terms[first].genes), set(terms[second].genes)
            shared = len(a & b) / len(a | b) if a | b else 0.0
            if shared >= JOINED:
                graph.add_edge(terms[first].id, terms[second].id, weight=shared)
    places = nx.spring_layout(graph, seed=0, k=1.2 / math.sqrt(max(len(terms), 1)))
    figure, axes = _new_figure(height=5.0)
    plot = axes[0][0]
    for first, second, data in graph.edges(data=True):
        (x1, y1), (x2, y2) = places[first], places[second]
        plot.plot([x1, x2], [y1, y2], color=MUTED, alpha=0.35, linewidth=0.6 + 3 * data["weight"], zorder=1)
    xs = [places[term.id][0] for term in terms]
    ys = [places[term.id][1] for term in terms]
    points = plot.scatter(xs, ys, s=[60 + 25 * len(term.genes) for term in terms],
                          c=[_strength(term.p_adjusted) for term in terms], cmap=_ramp(), edgecolors="white",
                          linewidths=0.8, zorder=2)
    for term, x, y in zip(terms, xs, ys):
        plot.text(x, y - 0.09, _short(term.name, 28), ha="center", va="top", fontsize=6.5, color=INK, zorder=3)
    figure.colorbar(points, ax=plot, fraction=0.04, label="−log10 adjusted p")
    plot.set_xticks([]), plot.set_yticks([])
    for side in plot.spines.values():
        side.set_visible(False)
    plot.margins(0.15)
    figure.tight_layout()
    return figure


# --- HTML and PDF ------------------------------------------------------------------------------

def _html(result: "TriGenResult", heading: str, sections: List[Tuple[str, str, Any]], table: str,
          enrichments: Optional[List[Any]] = None, terms_table: str = "", cube: Optional["Cube"] = None) -> str:
    when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
             f"content='width=device-width, initial-scale=1'><title>{html.escape(heading)}</title>"
             f"<style>{_STYLE}</style></head><body>",
             f"<h1>{html.escape(heading)}</h1><div class='meta'>TriGen · MetaGen {html.escape(_version())} · Python "
             f"{platform.python_version()} · {html.escape(when)}</div>",
             "<h2>Run</h2><div class='wrap'>" + _table(None, _run_rows(result)) + "</div>"]
    header, rows = _tricluster_rows(result, enrichments, cube)
    terms_note = (f" Their significant terms are in <a href='{html.escape(terms_table)}'>{html.escape(terms_table)}"
                  f"</a>." if enrichments is not None else "")
    parts.append(f"<h2>Triclusters</h2><p class='meta'>Their coordinates, a row each, are in "
                 f"<a href='{html.escape(table)}'>{html.escape(table)}</a>.{terms_note}</p>"
                 f"<div class='wrap'>{_table(header, rows)}</div>")
    current = None
    for section, caption, figure in sections:
        if section != current:
            parts.append(f"<h2>{html.escape(section)}</h2>")
            current = section
        parts.append(f"<figure>{_svg(figure)}<figcaption>{html.escape(caption)}</figcaption></figure>")
    parts.append("</body></html>")
    return "".join(parts)


def _pdf(result: "TriGenResult", heading: str, sections: List[Tuple[str, str, Any]], path: str,
         enrichments: Optional[List[Any]] = None, cube: Optional["Cube"] = None) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    header, rows = _tricluster_rows(result, enrichments, cube)
    with PdfPages(path) as pages:
        _pdf_tables(pages, [heading, f"TriGen · MetaGen {_version()} · Python {platform.python_version()} · {when}"],
                    [("Run", None, _run_rows(result)), ("Triclusters", header, rows)])
        page, top = None, 0.0
        for _, caption, chart in sections:
            buffer = io.BytesIO()
            chart.savefig(buffer, format="png", dpi=200, facecolor=chart.get_facecolor())
            width, height = chart.get_size_inches()
            plt.close(chart)
            shown = min(0.88 * (8.27 / 11.69) * height / width, 0.85)
            if page is None or top - shown - 0.05 < 0.04:
                if page is not None:
                    pages.savefig(page)
                    plt.close(page)
                page, top = plt.figure(figsize=(8.27, 11.69)), 0.96
                page.patch.set_facecolor("white")
            page.text(0.06, top, caption, va="top", ha="left", fontsize=7.5, color=MUTED, wrap=True)
            buffer.seek(0)
            axes = page.add_axes((0.06, top - 0.02 - shown, 0.88, shown))
            axes.imshow(plt.imread(buffer))
            axes.axis("off")
            top -= shown + 0.05
        if page is not None:
            pages.savefig(page)
            plt.close(page)
