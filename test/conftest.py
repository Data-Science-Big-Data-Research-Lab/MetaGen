"""Shared fixtures for the whole suite.

Its presence also puts this directory on sys.path, so modules the tests share
resolve the same from every subdirectory.
"""
import pytest

from metagen.framework import Domain, Solution
from metagen.framework.rng import set_seed


@pytest.fixture
def full_domain() -> Domain:
    """A domain with one of everything: integers, reals and categoricals, at the top
    level and inside a group; static structures of each basic type and of groups;
    dynamic structures of integers and reals. It is the domain the original tests
    were written against, built fresh for every test rather than shared."""
    domain = Domain()
    domain.define_integer("I", 0, 100)
    domain.define_real("R", 0.0, 1.0)
    domain.define_categorical("C", ["C1", "C2", "C3", "C4"])
    domain.define_group("L")
    domain.define_integer_in_group("L", "EI", 0, 100)
    domain.define_real_in_group("L", "ER", 0., 1.0)
    domain.define_categorical_in_group("L", "EC", ["C1", "C2", "C3", "C4"])
    domain.define_static_structure("SSI", 10)
    domain.set_structure_to_integer("SSI", -5, 10)
    domain.define_static_structure("SSR", 20)
    domain.set_structure_to_real("SSR", 0.0, 1.)
    domain.define_static_structure("SSC", 100)
    domain.set_structure_to_categorical("SSC", ["V1", "V2", "V3"])
    domain.define_static_structure("SSL", 2)
    domain.define_group("L2")
    domain.define_integer_in_group("L2", "EI2", 0, 100)
    domain.define_real_in_group("L2", "ER2", 0., 1.0)
    domain.define_categorical_in_group("L2", "EC2", ["C1", "C2", "C3", "C4"])
    domain.set_structure_to_variable("SSL", "L2")
    domain.define_dynamic_structure("DSI", 10, 100)
    domain.set_structure_to_integer("DSI", 1, 10)
    domain.define_dynamic_structure("DSR", 1, 10)
    domain.set_structure_to_real("DSR", 0.0, 1.)
    domain.define_dynamic_structure("DSC", 10, 15)
    domain.set_structure_to_categorical("DSC", ["V1", "V2", "V3"])
    domain.define_dynamic_structure("DSL", 2, 4)
    domain.define_group("L2")
    domain.define_integer_in_group("L2", "EI2", 0, 100)
    domain.define_real_in_group("L2", "ER2", 0., 1.0)
    domain.define_categorical_in_group("L2", "EC2", ["C1", "C2", "C3", "C4"])
    domain.set_structure_to_variable("DSL", "L2")
    return domain


@pytest.fixture
def solution(full_domain: Domain) -> Solution:
    """A freshly initialized solution of the full domain, from a fixed seed."""
    set_seed(0)
    return Solution(full_domain)
