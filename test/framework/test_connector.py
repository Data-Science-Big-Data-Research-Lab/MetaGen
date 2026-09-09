"""The connector is the framework's extension point: it maps each definition to the
solution type that represents it and to the builtin that reads it. The three
connectors the package ships must all answer the same questions, in both
directions, for classes and for instances."""
import pytest

from metagen.framework import BaseConnector, Domain, Solution
from metagen.framework.domain.core import (BaseDefinition, CategoricalDefinition,
                                           DynamicStructureDefinition, IntegerDefinition,
                                           RealDefinition, StaticStructureDefinition)
from metagen.framework.rng import set_seed
from metagen.framework.solution.types import Categorical, Integer, Real, Structure
from metagen.metaheuristics.ga.ga_tools import GAConnector, GAInteger, GAReal, GASolution, GAStructure
from metagen.metaheuristics.tools import solution_class
from metagen.metaheuristics.tpe.tpe_tools import (TPECategorical, TPEConnector, TPEInteger,
                                                  TPEReal, TPESolution, TPEStructure)

# connector -> definition -> (solution type, builtin). A structure is registered
# under a discriminator, because list stands for both structure definitions.
TABLE = {
    BaseConnector: {
        BaseDefinition: (Solution, dict),
        IntegerDefinition: (Integer, int),
        RealDefinition: (Real, float),
        CategoricalDefinition: (Categorical, str),
        StaticStructureDefinition: ((Structure, "static"), list),
        DynamicStructureDefinition: ((Structure, "dynamic"), list),
    },
    GAConnector: {
        BaseDefinition: (GASolution, dict),
        IntegerDefinition: (GAInteger, int),
        RealDefinition: (GAReal, float),
        CategoricalDefinition: (Categorical, str),
        StaticStructureDefinition: ((GAStructure, "static"), list),
        DynamicStructureDefinition: ((GAStructure, "dynamic"), list),
    },
    TPEConnector: {
        BaseDefinition: (TPESolution, dict),
        IntegerDefinition: (TPEInteger, int),
        RealDefinition: (TPEReal, float),
        CategoricalDefinition: (TPECategorical, str),
        StaticStructureDefinition: ((TPEStructure, "static"), list),
        DynamicStructureDefinition: ((TPEStructure, "dynamic"), list),
    },
}
CONNECTORS = list(TABLE)


def _bare(entry):
    return entry[0] if isinstance(entry, tuple) else entry


@pytest.mark.parametrize("connector_class", CONNECTORS)
def test_each_definition_maps_to_its_type_and_back(connector_class):
    connector = connector_class()
    for definition, (entry, builtin) in TABLE[connector_class].items():
        assert connector.get_type(definition) is _bare(entry)
        assert connector.get_definition(entry) is definition
        assert connector.get_builtin(entry) is builtin


@pytest.mark.parametrize("connector_class", CONNECTORS)
def test_each_builtin_maps_to_a_type(connector_class):
    connector = connector_class()
    for definition, (entry, builtin) in TABLE[connector_class].items():
        assert connector.get_type(builtin) is _bare(entry)


@pytest.mark.parametrize("connector_class", CONNECTORS)
def test_instances_answer_like_their_classes(connector_class):
    domain = Domain(connector=connector_class())
    domain.define_integer("i", 0, 9)
    domain.define_real("r", 0.0, 1.0)
    domain.define_categorical("c", ["a", "b"])
    domain.define_group("g")
    domain.define_integer_in_group("g", "gi", 0, 9)
    domain.define_static_structure("s", 3)
    domain.set_structure_to_integer("s", 0, 9)
    domain.define_dynamic_structure("d", 1, 3)
    domain.set_structure_to_real("d", 0.0, 1.0)
    set_seed(0)
    solution = solution_class(domain)(domain)
    table = TABLE[connector_class]

    assert type(solution) is table[BaseDefinition][0]
    for name, definition in (("i", IntegerDefinition), ("r", RealDefinition),
                             ("c", CategoricalDefinition), ("g", BaseDefinition)):
        variable = solution.get(name)
        assert type(variable) is table[definition][0]
        assert domain.get_connector().get_definition(variable) is definition
        assert domain.get_connector().get_builtin(variable) is table[definition][1]
    for name, definition in (("s", StaticStructureDefinition), ("d", DynamicStructureDefinition)):
        variable = solution.get(name)
        assert type(variable) is _bare(table[definition][0])
        assert isinstance(variable.get_definition(), definition)
        # A structure instance answers get_builtin since F-34. It does not answer
        # get_definition yet: see F-36 in the regression suite.
        assert domain.get_connector().get_builtin(variable) is list


def test_a_connector_of_its_own_can_replace_one_type():
    class Doubled(Integer):
        pass

    connector = BaseConnector()
    connector.register(IntegerDefinition, Doubled, int)
    domain = Domain(connector=connector)
    domain.define_integer("i", 0, 9)
    domain.define_real("r", 0.0, 1.0)
    set_seed(0)
    solution = Solution(domain)
    assert type(solution.get("i")) is Doubled
    assert type(solution.get("r")) is Real
    # A domain with the default connector is untouched by that registration (F-12).
    plain = Domain()
    plain.define_integer("i", 0, 9)
    assert type(Solution(plain).get("i")) is Integer
