"""The notebooks of the documentation run against the code of the repository: their code
cells in order, in one namespace, without the cell that installs the package from PyPI or
any other line for the shell or IPython. The one that needs TensorFlow is skipped where it
is not installed."""
import json
import os
from pathlib import Path

import pytest

NOTEBOOKS = Path(__file__).resolve().parents[2] / "notebooks"
NEEDS = {"suc_p3.ipynb": "sklearn", "suc_p4.ipynb": "tensorflow"}


def _code(notebook: Path) -> str:
    cells = [cell for cell in json.loads(notebook.read_text(encoding="utf-8"))["cells"]
             if cell["cell_type"] == "code"]
    lines = []
    for cell in cells:
        for line in "".join(cell["source"]).splitlines():
            # %pip, !pip and the like are IPython, not Python; the package is the checkout's.
            if not line.lstrip().startswith(("%", "!")):
                lines.append(line)
        lines.append("")
    return "\n".join(lines)


@pytest.mark.parametrize("notebook", sorted(NOTEBOOKS.glob("*.ipynb")), ids=lambda path: path.name)
def test_the_notebook_runs(notebook, tmp_path, monkeypatch):
    if notebook.name in NEEDS:
        pytest.importorskip(NEEDS[notebook.name])
    monkeypatch.chdir(tmp_path)
    exec(compile(_code(notebook), notebook.name, "exec"), {"__name__": "__main__"})
