"""What the examples and the benchmark import from MetaGen exists: nothing runs, the
imports are read from the source. The notebooks run in test_notebooks.py."""
import ast
import importlib
import importlib.util
import json
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _sources():
    for folder in ("examples", "benchmark"):
        for path in sorted((ROOT / folder).rglob("*.py")):
            yield path, path.read_text(encoding="utf-8")
        for path in sorted((ROOT / folder).rglob("*.ipynb")):
            cells = json.loads(path.read_text(encoding="utf-8"))["cells"]
            code = "\n".join("".join(cell["source"]) for cell in cells if cell["cell_type"] == "code")
            # Lines of the notebook's shell, such as %pip install, are not Python
            yield path, "\n".join(line for line in code.splitlines() if not line.lstrip().startswith(("%", "!")))


def _imports():
    for path, source in _sources():
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "metagen":
                for alias in node.names:
                    yield pytest.param(node.module, alias.name, id=f"{path.relative_to(ROOT)}:{node.module}.{alias.name}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] == "metagen":
                        yield pytest.param(alias.name, None, id=f"{path.relative_to(ROOT)}:{alias.name}")


#: What exists only with an optional extra installed, and the package that extra brings.
_WITH_AN_EXTRA = {"distributed_cvoa_launcher": "ray"}


# Nothing checked that examples/ and benchmark/ import what exists (OF-18 of the independent
# audit). Their imports are of the public interface today; this keeps them so.
@pytest.mark.parametrize("module,name", list(_imports()))
def test_what_the_examples_and_the_benchmark_import_from_metagen_exists(module, name):
    if name in _WITH_AN_EXTRA:
        pytest.importorskip(_WITH_AN_EXTRA[name])
    imported = importlib.import_module(module)
    if name is not None and name != "*":
        assert hasattr(imported, name) or importlib.util.find_spec(f"{module}.{name}") is not None, (
            f"{module} has no {name}")
