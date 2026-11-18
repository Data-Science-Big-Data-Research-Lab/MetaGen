"""
The module paths of the 1.x releases that were renamed are gone in 2.0: importing one fails,
as for any module that does not exist. The current paths are the ones the documentation uses.
"""
import importlib

import pytest

#: The paths the 1.x releases kept importable, with a warning, until 2.0.
FORMER_PATHS = [
    "cvoa.cvoa_distributed", "cvoa.cvoa_local", "cvoa.cvoa_probabilistic",
    "cvoa.distributed_tools", "cvoa.local_tools", "ga", "ga.ga", "ga.ga_tools", "ga.ssga", "hc",
    "hc.hill_climbing", "mm", "mm.memetic", "mm.mm_distributed_tools", "mm.mm_tools", "rs",
    "rs.random_search", "sa", "sa.sa", "ts", "ts.tabu_search"
]


@pytest.mark.parametrize("former", FORMER_PATHS)
def test_a_former_module_path_does_not_import(former):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("metagen.metaheuristics." + former)


def test_the_public_names_are_where_they_were():
    from metagen import metaheuristics
    from metagen.metaheuristics.genetic import GA
    assert metaheuristics.GA is GA
    for name in metaheuristics.__all__:
        assert hasattr(metaheuristics, name)
