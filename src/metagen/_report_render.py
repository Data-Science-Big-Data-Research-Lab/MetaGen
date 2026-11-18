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
import datetime
import html
import io
import platform
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

# What the report of a run and the report of TriGen share: the style, the figures, the tables
# and the pages, HTML and PDF. Private to the package by the name of the module; trigen/report.py
# imported eight private names of reporting.py and wrote its page and its PDF figures again
# (O-08 of the independent audit).

# The categorical colors in a fixed order, the same series always taking the same one; the
# first three can share a plot with every pair in view.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e8e7e3", "#fcfcfb"


def text(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(text(item) for item in value) + "]"
    return str(value)


def axes_style(axes: Any) -> None:
    axes.grid(color=GRID, linewidth=0.6)
    axes.set_axisbelow(True)
    for side in ("top", "right"):
        axes.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        axes.spines[side].set_color(MUTED)
    axes.tick_params(colors=MUTED, labelsize=8)


def new_figure(height: float = 3.2, columns: int = 1, rows: int = 1) -> Tuple[Any, Any]:
    import matplotlib.pyplot as plt
    figure, axes = plt.subplots(rows, columns, figsize=(8, height), squeeze=False)
    figure.patch.set_facecolor(SURFACE)
    return figure, axes


def version() -> str:
    """The version of MetaGen, as metagen reads it when it is imported."""
    from metagen import __version__
    return __version__


def svg(figure: Any) -> str:
    import matplotlib.pyplot as plt
    buffer = io.StringIO()
    figure.savefig(buffer, format="svg", facecolor=figure.get_facecolor())
    plt.close(figure)
    text = buffer.getvalue()
    return text[text.index("<svg"):]


def table(header: Optional[Sequence[str]], rows: Sequence[Sequence[str]]) -> str:
    """A table, or with no header, a compact one of names and values."""
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>" for row in rows)
    if header is None:
        return f"<table class='pairs'><tbody>{body}</tbody></table>"
    head = "".join(f"<th>{html.escape(cell)}</th>" for cell in header)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


STYLE = """
:root { color-scheme: light; }
body { background: #fcfcfb; color: #0b0b0b; font: 15px/1.5 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
       max-width: 960px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 24px; margin: 0 0 4px; } h2 { font-size: 19px; margin: 36px 0 8px; border-bottom: 1px solid #e8e7e3; }
h3 { font-size: 16px; margin: 24px 0 8px; } .meta { color: #52514e; font-size: 13px; margin-bottom: 24px; }
table { border-collapse: collapse; margin: 8px 0 16px; font-size: 13px; width: 100%; }
th, td { text-align: left; padding: 4px 10px 4px 0; border-bottom: 1px solid #e8e7e3; vertical-align: top; }
th { color: #52514e; font-weight: 600; } table.pairs { width: auto; } table.pairs td:first-child { color: #52514e; padding-right: 32px; }
figure { margin: 12px 0 24px; } figure svg { width: 100%; height: auto; }
figcaption { color: #52514e; font-size: 13px; } .wrap { overflow-x: auto; }
@media print { body { max-width: none; } h2 { break-after: avoid; } figure { break-inside: avoid; } }
"""


def now() -> str:
    """The moment a report is written, as the line under its heading shows it."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def page_head(heading: str, product: str, when: str) -> str:
    """The start of an HTML report: its head, its style, its heading and the line under it."""
    return (f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' "
            f"content='width=device-width, initial-scale=1'><title>{html.escape(heading)}</title>"
            f"<style>{STYLE}</style></head><body>"
            f"<h1>{html.escape(heading)}</h1><div class='meta'>{product}MetaGen {html.escape(version())} · Python "
            f"{platform.python_version()} · {html.escape(when)}</div>")


def pdf_meta(product: str, when: str) -> str:
    """The line under the heading of a PDF report."""
    return f"{product}MetaGen {version()} · Python {platform.python_version()} · {when}"


def pdf_figures(pages: Any, figures: Iterable[Tuple[str, Any]], tallest: Optional[float] = None) -> None:
    """
    The figures on A4 pages, one under the other with their captions, as many as fit.

    :param pages: The PDF being written.
    :param figures: Each caption with its figure, which is closed once drawn.
    :param tallest: The most of the height of a page a figure may take, or None.
    """
    import matplotlib.pyplot as plt
    page, top = None, 0.0
    for caption, figure in figures:
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png", dpi=200, facecolor=figure.get_facecolor())
        width, height = figure.get_size_inches()
        plt.close(figure)
        shown = 0.88 * (8.27 / 11.69) * height / width       # its height as a share of the page
        if tallest is not None:
            shown = min(shown, tallest)
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


def pdf_tables(pages: Any, heading: Sequence[str],
                blocks: Sequence[Tuple[str, Optional[Sequence[str]], Sequence[Sequence[str]]]]) -> None:
    """
    A4 pages with a heading and tables, each with its title: a table with a header, or
    without one a compact table of names and values. A table that does not fit goes on in
    the next page, with its header again.
    """
    import matplotlib.pyplot as plt
    row_height, left, width = 0.0175, 0.06, 0.88
    state: Dict[str, Any] = {"page": None, "top": 0.0}

    def new_page() -> None:
        if state["page"] is not None:
            pages.savefig(state["page"])
            plt.close(state["page"])
        state["page"] = plt.figure(figsize=(8.27, 11.69))
        state["page"].patch.set_facecolor("white")
        state["top"] = 0.95

    new_page()
    state["page"].text(left, state["top"], heading[0], fontsize=14, weight="bold", color=INK, va="top")
    state["top"] -= 0.026
    for line in heading[1:]:
        state["page"].text(left, state["top"], line, fontsize=8, color=MUTED, va="top")
        state["top"] -= 0.016
    state["top"] -= 0.012
    for title, header, rows in blocks:
        cells = [[str(cell) for cell in row] for row in rows] or [[""] * (len(header) if header else 2)]
        columns = len(header) if header else len(cells[0])
        values = [max([len(row[column]) for row in cells if column < len(row)] + [1]) for column in range(columns)]
        # A name longer than the values of its column goes on two lines
        labels = [str(name) if len(str(name)) <= values[column] + 2 or " " not in str(name)
                  else "\n".join(str(name).rsplit(" ", 1)) for column, name in enumerate(header or ())]
        lengths = [min(max([values[column]] + [len(line) for line in (labels[column] if header else "").split("\n")]),
                       60) + 2 for column in range(columns)]
        widths = [length / sum(lengths) for length in lengths] if header else [0.32, 0.68]
        font = 7.0 if not header or sum(lengths) <= 125 else max(5.0, 7.0 * 125 / sum(lengths))
        tall = 2 if any("\n" in label for label in labels) else 1
        start, first = 0, True
        while start < len(cells):
            room = int((state["top"] - 0.04 - 0.03) / row_height) - (tall if header else 0)
            if room < 3:
                new_page()
                continue
            chunk = cells[start:start + room]
            state["page"].text(left, state["top"], title + ("" if first else " (continued)"), fontsize=10,
                               weight="bold", color=INK, va="top")
            state["top"] -= 0.022
            height = row_height * (len(chunk) + (tall if header else 0))
            axes = state["page"].add_axes((left, state["top"] - height, width if header else 0.6, height))
            axes.axis("off")
            table = axes.table(cellText=chunk, colLabels=labels if header else None, cellLoc="left",
                               colLoc="left", colWidths=widths, bbox=(0, 0, 1, 1))
            table.auto_set_font_size(False)
            table.set_fontsize(font)
            for (row, column), cell in table.get_celld().items():
                cell.set_edgecolor(GRID)
                cell.visible_edges = "B"
                if header and row == 0:
                    # The table scales its rows to fill its box, keeping their proportions
                    cell.set_height(cell.get_height() * tall)
                    cell.set_facecolor("#f3f2ee")
                    cell.set_text_props(weight="bold", color=MUTED)
                elif not header and column == 0:
                    cell.set_text_props(color=MUTED)
            state["top"] -= height + 0.03
            start += len(chunk)
            first = False
    pages.savefig(state["page"])
    plt.close(state["page"])
