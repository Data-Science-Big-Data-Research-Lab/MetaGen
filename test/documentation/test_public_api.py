"""The public API: what the documentation imports and documents comes from the public
packages, and every name they export resolves.

A program written from the documentation keeps working when a module inside a package is
reorganized: that is why the documentation must not reach past the ``__all__`` of these
packages.
"""
import importlib
import importlib.util
import re
from importlib import metadata
from pathlib import Path

import pytest

import metagen

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "source"

#: The packages whose ``__all__`` is the public API, as docs/source/api.rst says.
PUBLIC = ("metagen.framework", "metagen.framework.domain", "metagen.framework.solution", "metagen.metaheuristics",
          "metagen.triclustering", "metagen.triclustering.data", "metagen.reporting", "metagen.logging")

_HAS_RAY = importlib.util.find_spec("ray") is not None


def _exported(module_name):
    module = importlib.import_module(module_name)
    return set(module.__all__) | set(getattr(module, "_WITH_RAY", {}))


def _pages():
    return sorted(DOCS.rglob("*.rst")) + [ROOT / "README.md"]


def _imports(text):
    """Every ``from metagen... import names`` in a text, with its names, parentheses joined."""
    for match in re.finditer(r"from (metagen[A-Za-z0-9_.]*) import (\([^)]*\)|[^\n]+)", text):
        names = re.sub(r"[()\s]", " ", match.group(2)).replace(",", " ").split()
        yield match.group(1), [name for name in names if name != "as"]


def _documented(text):
    """Every object an autodoc directive documents, by its full name."""
    return re.findall(r"^\.\. auto(?:class|function|method|attribute|data|exception):: (metagen\.[A-Za-z0-9_.]+)", text,
                      re.M)


def _split(dotted):
    """The public package a full name belongs to, and the name inside it."""
    for package in sorted(PUBLIC, key=len, reverse=True):
        if dotted.startswith(package + "."):
            return package, dotted[len(package) + 1:].split(".")[0]
    return None, dotted


@pytest.mark.parametrize("package", PUBLIC)
def test_every_name_a_public_package_exports_resolves(package):
    module = importlib.import_module(package)
    for name in module.__all__:
        assert hasattr(module, name), f"{package}.__all__ lists {name}, which it does not have"


def test_the_names_that_need_ray_resolve_when_it_is_there():
    pytest.importorskip("ray")
    from metagen.metaheuristics import DistributedCVOA, distributed_cvoa_launcher  # noqa: F401
    import metagen.metaheuristics as metaheuristics
    assert {"DistributedCVOA", "distributed_cvoa_launcher"} <= set(metaheuristics.__all__)


def test_the_documentation_imports_only_from_the_public_packages():
    offending = []
    for page in _pages():
        for module, names in _imports(page.read_text(encoding="utf-8")):
            if module not in PUBLIC:
                offending.append(f"{page.relative_to(ROOT)}: from {module} import {', '.join(names)}")
                continue
            missing = [name for name in names if name not in _exported(module)]
            if missing:
                offending.append(f"{page.relative_to(ROOT)}: {module} does not export {', '.join(missing)}")
    assert not offending, "\n".join(offending)


def test_the_api_reference_documents_the_public_names():
    offending = []
    for page in sorted(DOCS.rglob("*.rst")):
        for dotted in _documented(page.read_text(encoding="utf-8")):
            package, name = _split(dotted)
            if package is None or name not in _exported(package):
                offending.append(f"{page.relative_to(ROOT)}: {dotted}")
    assert not offending, "\n".join(offending)


def test_the_version_is_the_installed_one():
    assert metagen.__version__ == metadata.version("pymetagen-datalabupo")
