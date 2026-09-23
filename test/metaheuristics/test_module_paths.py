"""
The module paths of earlier releases keep working.

Each former path imports, is the very module of its current name, and warns once with the
name to use instead. Run in a subprocess, because a module already imported by the suite
would not warn again.
"""
import json
import subprocess
import sys

import pytest

from metagen.metaheuristics._renamed_modules import RENAMED_MODULES

_PROBE = r"""
import importlib, json, sys, warnings
from metagen.metaheuristics._renamed_modules import RENAMED_MODULES
results = {}
for former, current in RENAMED_MODULES.items():
    if former.startswith("mm.mm_distributed") or former == "cvoa.distributed_tools" or former == "cvoa.cvoa_distributed":
        try:
            import ray  # noqa: F401
        except ImportError:
            continue
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        old = importlib.import_module("metagen.metaheuristics." + former)
    new = importlib.import_module("metagen.metaheuristics." + current)
    warned = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    results[former] = {"same": old is new, "warned": any(current in m for m in warned)}
print(json.dumps(results))
"""


@pytest.fixture(scope="module")
def probe():
    output = subprocess.run([sys.executable, "-c", _PROBE], capture_output=True, text=True, check=True).stdout
    return json.loads(output.strip().splitlines()[-1])


@pytest.mark.parametrize("former", sorted(RENAMED_MODULES))
def test_a_former_module_path_is_the_current_module_and_warns(probe, former):
    if former not in probe:
        pytest.skip("needs Ray")
    assert probe[former]["same"], f"metagen.metaheuristics.{former} is not the current module"
    assert probe[former]["warned"], f"importing metagen.metaheuristics.{former} does not name its current path"


def test_the_public_names_are_where_they_were():
    from metagen import metaheuristics
    from metagen.metaheuristics.genetic import GA
    assert metaheuristics.GA is GA
    for name in metaheuristics.__all__:
        assert hasattr(metaheuristics, name)
