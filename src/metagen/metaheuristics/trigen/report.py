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
from typing import TYPE_CHECKING, Any, List, Optional, Sequence, Tuple

import numpy as np

from metagen.reporting import (INK, MUTED, SERIES, _STYLE, _axes_style, _new_figure, _svg, _table, _text,
                               _version)

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
                  detailed: int = MOST_DETAILED) -> str:
    """
    Write a report of a run of TriGen, an HTML page with everything in it or a PDF, by the
    extension of ``path``, and next to it the triclusters as a CSV table of coordinates
    (:py:meth:`TriGenResult.to_csv`). It shows the run (the data, the options, what it spent,
    why it ended and what it held), a table of the triclusters with their sizes, fitness,
    terms and cost, the best fitness of each search by generation, the share of the genes or
    pixels held as the triclusters were found, the cells two triclusters share, and, for each
    of the first ``detailed`` triclusters, its values: for a cube, the three views of TrLab,
    by time, by condition and over time; for a prism, the series of its pixels along its
    window, after a map of the plane with every prism. Without the cube, the values are left
    out. Needs matplotlib, the ``report`` extra.

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
    :return: The file written.
    :rtype: str
    :raises ImportError: if matplotlib is not installed.
    :raises ValueError: if the extension is neither, or the cube is not the one the run
        worked on.
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
    table = os.path.splitext(path)[0] + ".csv"
    result.to_csv(table)
    sections = _sections(result, cube, detailed)
    if extension == ".pdf":
        _pdf(result, heading, sections, path)
    else:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_html(result, heading, sections, os.path.basename(table)))
    return path


# --- What the result says ----------------------------------------------------------------------

def _is_prism(result: "TriGenResult") -> bool:
    return result.configuration.get("shape") == "prism"


def _run_rows(result: "TriGenResult") -> List[Tuple[str, str]]:
    data, provenance, configuration = result.data, result.provenance, result.configuration
    rows = [("data", f"{data.get('label') or ''} {' × '.join(map(str, data['shape']))}".strip())]
    rows += [(name, _text(configuration[name])) for name in OPTIONS if name in configuration
             and configuration[name] is not None]
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


def _tricluster_rows(result: "TriGenResult") -> Tuple[List[str], List[List[str]]]:
    searches = {search["tricluster"]: search for search in result.searches if search.get("tricluster") is not None}
    names = sorted({name for terms in result.terms for name in terms
                    if name in ("quality", "z", "z_found", "overlap_cells")})
    header = ["#", "size", "cells", "fitness"] + names + ["search evaluations", "growth evaluations", "seconds"]
    rows = []
    for index, (tricluster, terms) in enumerate(zip(result.triclusters, result.terms)):
        search = searches.get(index, {})
        rows.append([str(index), _size(result, tricluster), str(tricluster.n_cells), _text(tricluster.fitness)]
                    + [_text(terms.get(name)) for name in names]
                    + [_text(search.get("evaluations")), _text(search.get("growth_evaluations")),
                       _text(round(search["seconds"], 2)) if search.get("seconds") is not None else ""])
    return header, rows


# --- The figures -------------------------------------------------------------------------------

def _sections(result: "TriGenResult", cube: Optional["Cube"], detailed: int) -> List[Tuple[str, str, Any]]:
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
    if cube is None or not result.triclusters:
        return figures
    shown = result.triclusters[:detailed]
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
                    plot.text(column, row, f"{shares[row, column]:.2f}", ha="center", va="center", fontsize=6,
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
        plot.set_title(f"{panel_label} {panel_names[index]}", fontsize=8, color=INK, loc="left")
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


# --- HTML and PDF ------------------------------------------------------------------------------

def _html(result: "TriGenResult", heading: str, sections: List[Tuple[str, str, Any]], table: str) -> str:
    when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
             f"content='width=device-width, initial-scale=1'><title>{html.escape(heading)}</title>"
             f"<style>{_STYLE}</style></head><body>",
             f"<h1>{html.escape(heading)}</h1><div class='meta'>TriGen · MetaGen {html.escape(_version())} · Python "
             f"{platform.python_version()} · {html.escape(when)}</div>",
             "<h2>Run</h2><div class='wrap'>" + _table(None, _run_rows(result)) + "</div>"]
    header, rows = _tricluster_rows(result)
    parts.append(f"<h2>Triclusters</h2><p class='meta'>Their coordinates, a row each, are in "
                 f"<a href='{html.escape(table)}'>{html.escape(table)}</a>.</p>"
                 f"<div class='wrap'>{_table(header, rows)}</div>")
    current = None
    for section, caption, figure in sections:
        if section != current:
            parts.append(f"<h2>{html.escape(section)}</h2>")
            current = section
        parts.append(f"<figure>{_svg(figure)}<figcaption>{html.escape(caption)}</figcaption></figure>")
    parts.append("</body></html>")
    return "".join(parts)


def _pdf(result: "TriGenResult", heading: str, sections: List[Tuple[str, str, Any]], path: str) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    when = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    header, rows = _tricluster_rows(result)
    with PdfPages(path) as pages:
        lines = [heading, f"TriGen · MetaGen {_version()} · Python {platform.python_version()} · {when}", ""]
        lines += [f"{name:<36}{value}" for name, value in _run_rows(result)]
        lines += ["", "Triclusters", "  " + " | ".join(header)] + ["  " + " | ".join(row) for row in rows[:60]]
        if len(rows) > 60:
            lines.append(f"  ... and {len(rows) - 60} more, in the CSV table next to this report")
        figure = plt.figure(figsize=(8.27, 11.69))
        figure.patch.set_facecolor("white")
        figure.text(0.05, 0.97, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=6.5, color=INK)
        pages.savefig(figure)
        plt.close(figure)
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
