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

import html
import math
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Sequence, Tuple, Union, cast

from metagen._report_render import (INK, MUTED, SERIES, axes_style as _axes_style, new_figure as _new_figure,
                                    now as _now, page_head as _page_head, pdf_figures as _pdf_figures,
                                    pdf_meta as _pdf_meta, pdf_tables as _pdf_tables, svg as _svg, table as _table,
                                    text as _text)

if TYPE_CHECKING:
    from metagen.metaheuristics.base import Metaheuristic

__all__ = ["report"]

#: The most panels of the trajectory of the best solution, one per variable.
MOST_VARIABLES = 12



def report(runs: Union["Metaheuristic", Sequence["Metaheuristic"]], path: str, title: Optional[str] = None,
           labels: Optional[Sequence[str]] = None) -> str:
    """
    Write a report of one or more runs of metaheuristics: an HTML page with everything in
    it, or a PDF, by the extension of ``path``. For each run, the algorithm and its
    parameters, the domain, the budget and what stopped it, the best solution, how the best
    fitness and the population evolved with the evaluations, how each variable of the best
    solution changed, and the cost of each iteration; for several, also their convergence
    side by side. Needs matplotlib, the ``report`` extra.

    :param runs: A metaheuristic that has run, or several.
    :type runs: Metaheuristic or Sequence[Metaheuristic]
    :param path: The file, ``.html`` or ``.pdf``.
    :type path: str
    :param title: The title, defaults to the algorithms of the runs.
    :type title: str, optional
    :param labels: A label per run, defaults to the name of its algorithm, numbered when
        two share it.
    :type labels: Sequence[str], optional
    :return: The file written.
    :rtype: str
    :raises ImportError: if matplotlib is not installed.
    :raises ValueError: if the extension is neither, a run has not run, or the labels are
        not one per run.
    """
    try:
        import matplotlib
    except ImportError as error:
        raise ImportError("A report needs matplotlib: pip install pymetagen-datalabupo[report]") from error
    matplotlib.use("Agg", force=False)
    sequence: List["Metaheuristic"] = (list(cast(Sequence["Metaheuristic"], runs))
                                       if isinstance(runs, (list, tuple)) else [cast("Metaheuristic", runs)])
    if not sequence:
        raise ValueError("A report needs at least one run.")
    for run in sequence:
        if getattr(run, "stop_reason", None) is None and not run.history:
            raise ValueError(f"The {type(run).__name__} has not run: there is nothing to report.")
    names = list(labels) if labels is not None else _labels(sequence)
    if len(names) != len(sequence):
        raise ValueError(f"Give one label per run: {len(names)} labels for {len(sequence)} runs.")
    extension = os.path.splitext(path)[1].lower()
    if extension not in (".html", ".htm", ".pdf"):
        raise ValueError(f"A report is an .html or a .pdf file, not {path!r}.")
    heading = title or " · ".join(dict.fromkeys(type(run).__name__ for run in sequence))
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    if extension == ".pdf":
        _pdf(sequence, names, heading, path)
    else:
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(_html(sequence, names, heading))
    return path


def _labels(runs: Sequence["Metaheuristic"]) -> List[str]:
    names = [type(run).__name__ for run in runs]
    seen: Dict[str, int] = {}
    labels = []
    for name in names:
        seen[name] = seen.get(name, 0) + 1
        labels.append(f"{name} {seen[name]}" if names.count(name) > 1 else name)
    return labels


# --- What a run says about itself ------------------------------------------------------------

def _summary(run: "Metaheuristic") -> List[Tuple[str, str]]:
    best = run.history[-1]["best"] if run.history else None
    rows = [("algorithm", type(run).__name__)]
    rows += [(name, _text(value)) for name, value in run.parameters().items()]
    rows += [("stop reason", _text(run.stop_reason)), ("evaluations", _text(run.evaluations)),
             ("seconds", f"{run.seconds:.2f}"), ("iterations", _text(len(run.history))),
             ("best fitness", _text(best))]
    return rows


def _domain(run: "Metaheuristic") -> List[Tuple[str, str, str, str]]:
    """Each variable of the domain: its name, its type, its values and its notes."""
    core = run.domain.get_core()
    rows = []
    for name, attributes in core.get_attributes()[1].items():
        kind, values, notes = _definition(attributes)
        definition = core.get(name)
        if getattr(definition, "log", False):
            notes.append("logarithmic scale")
        condition = core.get_condition(name)
        if condition:
            notes.append(f"only when {condition[0]} is {', '.join(map(str, condition[1]))}")
        rows.append((name, kind, values, "; ".join(notes)))
    return rows


def _definition(attributes: Tuple[Any, ...]) -> Tuple[str, str, List[str]]:
    kind = str(attributes[0]).lower()
    if kind in ("integer", "real"):
        notes = [f"step {attributes[3]}"] if attributes[3] else []
        return kind, f"[{attributes[1]}, {attributes[2]}]", notes
    if kind == "categorical":
        return kind, ", ".join(map(str, attributes[1])), []
    if kind == "dynamic":
        inner = _definition(attributes[4])
        return "dynamic structure", f"{attributes[1]} to {attributes[2]} of {inner[0]} {inner[1]}", []
    if kind == "static":
        inner = _definition(attributes[2])
        return "static structure", f"{attributes[1]} of {inner[0]} {inner[1]}", []
    if kind == "definition":
        return "group", ", ".join(attributes[1]), []
    return kind, _text(attributes[1:]), []


def _best_solution(run: "Metaheuristic") -> List[Tuple[str, str]]:
    if not run.history:
        return []
    return [(name, _text(value)) for name, value in run.history[-1]["best_solution"].items()]




# --- The figures -------------------------------------------------------------------------------

def _figures(runs: Sequence["Metaheuristic"], names: Sequence[str]) -> List[Tuple[str, Any]]:
    """The figures of the report, each with its caption."""
    figures = []
    if len(runs) > 1:
        figures.append(("The best fitness of each run against the evaluations", _together(runs, names)))
    for run, name in zip(runs, names):
        if not run.history:
            continue
        figures.append((f"{name}: the best fitness, the best of each iteration and the population "
                        f"(mean ± standard deviation) against the evaluations", _convergence(run)))
        trajectory = _trajectory(run)
        if trajectory is not None:
            caption = f"{name}: the value of each variable of the best solution so far"
            inactive = _never_active(run)
            if inactive:
                caption += f"; never active in it, so not shown: {', '.join(inactive)}"
            figures.append((caption, trajectory))
        figures.append((f"{name}: the evaluations and the seconds of each iteration", _cost(run)))
    return figures


def _never_active(run: "Metaheuristic") -> List[str]:
    """The variables the best solution never held a value of, conditional ones never active."""
    names = run.history[-1]["best_solution"].keys() if run.history else []
    return [name for name in names if all(record["best_solution"].get(name) is None for record in run.history)]


def _fitness_scale(axes: Any, values: Sequence[float]) -> None:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    if finite and min(finite) > 0 and max(finite) / min(finite) > 100:
        axes.set_yscale("log")


def _convergence(run: "Metaheuristic") -> Any:
    figure, axes = _new_figure()
    plot = axes[0][0]
    history = run.history
    evaluations = [record["evaluations"] for record in history]
    mean = [record["mean"] for record in history]
    deviation = [record["std"] or 0.0 for record in history]
    if all(value is not None for value in mean):
        plot.fill_between(evaluations, [m - d for m, d in zip(mean, deviation)],
                          [m + d for m, d in zip(mean, deviation)], color=SERIES[0], alpha=0.12, linewidth=0,
                          label="population, mean ± sd")
        plot.plot(evaluations, mean, color=SERIES[0], linewidth=1, alpha=0.5)
    plot.scatter(evaluations, [record["iteration_best"] for record in history], s=10, color=SERIES[1],
                 label="best of the iteration", zorder=3)
    plot.step(evaluations, [record["best"] for record in history], where="post", color=INK, linewidth=2,
              label="best so far", zorder=4)
    _fitness_scale(plot, [record["best"] for record in history] + [m for m in mean if m is not None])
    plot.set_xlabel("evaluations", fontsize=9, color=MUTED)
    plot.set_ylabel("fitness", fontsize=9, color=MUTED)
    plot.legend(fontsize=8, frameon=False)
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _together(runs: Sequence["Metaheuristic"], names: Sequence[str]) -> Any:
    figure, axes = _new_figure()
    plot = axes[0][0]
    every = []
    for index, (run, name) in enumerate(zip(runs, names)):
        if not run.history:
            continue
        best = [record["best"] for record in run.history]
        every += best
        plot.step([record["evaluations"] for record in run.history], best, where="post", linewidth=2,
                  color=SERIES[index % len(SERIES)], label=name)
    _fitness_scale(plot, every)
    plot.set_xlabel("evaluations", fontsize=9, color=MUTED)
    plot.set_ylabel("best fitness", fontsize=9, color=MUTED)
    plot.legend(fontsize=8, frameon=False)
    _axes_style(plot)
    figure.tight_layout()
    return figure


def _trajectory(run: "Metaheuristic") -> Optional[Any]:
    """A panel per variable of the domain that holds a number or a category, at most
    MOST_VARIABLES of them: its value in the best solution so far, against the evaluations."""
    core = run.domain.get_core()
    variables = []
    for name, attributes in core.get_attributes()[1].items():
        if str(attributes[0]).lower() in ("integer", "real", "categorical"):
            variables.append((name, str(attributes[0]).lower(), attributes))
    if not variables:
        return None
    # A conditional variable inactive throughout has nothing to show; one active part of the
    # time shows a gap where it was not.
    variables = [entry for entry in variables
                 if any(record["best_solution"].get(entry[0]) is not None for record in run.history)]
    if not variables:
        return None
    variables = variables[:MOST_VARIABLES]
    columns = min(3, len(variables))
    rows = math.ceil(len(variables) / columns)
    figure, axes = _new_figure(height=2.2 * rows, columns=columns, rows=rows)
    evaluations = [record["evaluations"] for record in run.history]
    for index, (name, kind, attributes) in enumerate(variables):
        plot = axes[index // columns][index % columns]
        values = [record["best_solution"].get(name) for record in run.history]
        if kind == "categorical":
            categories = list(cast(Sequence[Any], attributes[1]))
            positions = [categories.index(value) if value in categories else math.nan for value in values]
            plot.step(evaluations, positions, where="post", color=SERIES[0], linewidth=1.6)
            plot.set_yticks(range(len(categories)), [str(category) for category in categories])
            plot.set_ylim(-0.5, len(categories) - 0.5)
        else:
            numbers = [math.nan if value is None else value for value in values]
            plot.step(evaluations, numbers, where="post", color=SERIES[0], linewidth=1.6)
            if getattr(core.get(name), "log", False):
                plot.set_yscale("log")
        plot.set_title(name, fontsize=9, color=INK, loc="left")
        _axes_style(plot)
    for index in range(len(variables), rows * columns):
        axes[index // columns][index % columns].set_visible(False)
    figure.tight_layout()
    return figure


def _cost(run: "Metaheuristic") -> Any:
    figure, axes = _new_figure(height=2.6, columns=2)
    history = run.history
    iterations = [record["iteration"] for record in history]
    counts = [record["evaluations"] for record in history]
    seconds = [record["seconds"] for record in history]
    per_iteration = [later - earlier for earlier, later in zip([0] + counts, counts)]
    time_per_iteration = [later - earlier for earlier, later in zip([0.0] + seconds, seconds)]
    for plot, values, label in ((axes[0][0], per_iteration, "evaluations"), (axes[0][1], time_per_iteration, "seconds")):
        plot.bar(iterations, values, color=SERIES[0], width=0.8)
        plot.set_xlabel("iteration (the first includes the warmup and the initialization)", fontsize=7, color=MUTED)
        plot.set_title(label, fontsize=9, color=INK, loc="left")
        _axes_style(plot)
    figure.tight_layout()
    return figure


# --- HTML and PDF ------------------------------------------------------------------------------

def _html(runs: Sequence["Metaheuristic"], names: Sequence[str], heading: str) -> str:
    parts = [_page_head(heading, "", _now())]
    if len(runs) > 1:
        rows = [(name, type(run).__name__, _text(run.history[-1]["best"] if run.history else None),
                 _text(run.evaluations), f"{run.seconds:.2f}", _text(run.stop_reason)) for run, name in zip(runs, names)]
        parts.append("<h2>Runs</h2><div class='wrap'>" + _table(
            ("run", "algorithm", "best fitness", "evaluations", "seconds", "stop reason"), rows) + "</div>")
    captioned = {caption: figure for caption, figure in _figures(runs, names)}
    for caption, figure in list(captioned.items()):
        if caption.startswith("The best fitness of each run"):
            parts.append(f"<figure>{_svg(figure)}<figcaption>{html.escape(caption)}</figcaption></figure>")
    for run, name in zip(runs, names):
        if len(runs) > 1:
            parts.append(f"<h2>{html.escape(name)}</h2>")
        parts.append("<h3>Run</h3><div class='wrap'>" + _table(None, _summary(run)) + "</div>")
        parts.append("<h3>Domain</h3><div class='wrap'>" + _table(("variable", "type", "values", "notes"),
                                                                     _domain(run)) + "</div>")
        best = _best_solution(run)
        if best:
            parts.append("<h3>Best solution</h3><div class='wrap'>" + _table(None, best) + "</div>")
        for caption, figure in list(captioned.items()):
            if caption.startswith(f"{name}:"):
                parts.append(f"<figure>{_svg(figure)}<figcaption>{html.escape(caption)}</figcaption></figure>")
    parts.append("</body></html>")
    return "".join(parts)


def _pdf(runs: Sequence["Metaheuristic"], names: Sequence[str], heading: str, path: str) -> None:
    from matplotlib.backends.backend_pdf import PdfPages
    when = _now()
    with PdfPages(path) as pages:
        blocks: List[Tuple[str, Optional[Sequence[str]], Sequence[Sequence[str]]]] = []
        if len(runs) > 1:
            blocks.append(("Runs", ("run", "algorithm", "best fitness", "evaluations", "seconds", "stop reason"),
                           [(name, type(run).__name__, _text(run.history[-1]["best"] if run.history else None),
                             _text(run.evaluations), f"{run.seconds:.2f}", _text(run.stop_reason))
                            for run, name in zip(runs, names)]))
        for run, name in zip(runs, names):
            prefix = f"{name}: " if len(runs) > 1 else ""
            blocks.append((f"{prefix}run", None, _summary(run)))
            blocks.append((f"{prefix}domain", ("variable", "type", "values", "notes"), _domain(run)))
            best = _best_solution(run)
            if best:
                blocks.append((f"{prefix}best solution", None, best))
        _pdf_tables(pages, [heading, _pdf_meta("", when)], blocks)
        _pdf_figures(pages, _figures(runs, names))
