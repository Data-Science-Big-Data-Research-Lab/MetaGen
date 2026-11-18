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


def test_the_algorithms_the_suite_runs_are_every_metaheuristic_the_package_exports():
    # A metaheuristic added to the package and not to the list in conftest.py would go
    # untested by every test that runs "every algorithm", and nothing would say so.
    import inspect
    import metagen.metaheuristics as metaheuristics
    from conftest import ALGORITHMS, GENETIC
    from metagen.framework import Domain
    from metagen.metaheuristics import Metaheuristic

    # Not searches of a Domain on their own: a strain of CVOA runs through a launcher, and
    # TriGenGA is the search of TriGen, on its own domain. By name: DistributedCVOA needs Ray.
    apart = {"CVOA", "ProbabilisticCVOA", "DistributedCVOA", "TriGenGA"}
    exported = {getattr(metaheuristics, name) for name in metaheuristics.__all__ if name not in apart}
    concrete = {cls for cls in exported if inspect.isclass(cls) and issubclass(cls, Metaheuristic)
                and not inspect.isabstract(cls)}
    assert set(ALGORITHMS) == concrete

    domain = Domain()
    domain.define_real("x", -1.0, 1.0)
    refused = set()
    for algorithm in ALGORITHMS:
        try:
            algorithm(domain, lambda solution: solution["x"] ** 2)
        except ValueError:
            refused.add(algorithm)
    assert refused == set(GENETIC)


def test_what_is_removed_in_version_2_warns_and_still_works():
    # Unused by the package, and public: kept until version 2.0, with a warning.
    from metagen.framework import Domain
    from metagen.framework.domain.preconditions import Primitives

    domain = Domain()
    domain.define_real("x", 0.0, 1.0)
    domain.define_static_structure("v", 2)
    domain.set_structure_to_integer("v", 0, 9)
    core = domain.get_core()
    structure = core.get("v")
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        assert core.get_by_index(0) is core.get("x")
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        assert structure.is_base()
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        assert structure.check_base_value(3) and not structure.check_base_value(12)
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        assert Primitives.is_basic_vector_sequence_value([1, 2])
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        assert not Primitives.is_layer_vector_sequence_value(3)
    with pytest.warns(DeprecationWarning, match="version 2.0"):
        from metagen.framework.solution.literals import VectorDef  # noqa: F401
