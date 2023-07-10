from typing import TypeVar

import metagen.framework.domain as definitions

BaseClass = TypeVar('BaseClass', bound=definitions.Base)
BaseDefinitionClass = TypeVar('BaseDefinitionClass', bound=definitions.BaseDefinition)
IntegerDefinitionClass = TypeVar('IntegerDefinitionClass', bound=definitions.IntegerDefinition)
RealDefinitionClass = TypeVar('RealDefinitionClass', bound=definitions.RealDefinition)
CategoricalDefinitionClass = TypeVar('CategoricalDefinitionClass', bound=definitions.CategoricalDefinition)
DynamicStructureDefinitionClass = TypeVar('DynamicStructureDefinitionClass', bound=definitions.DynamicStructureDefinition)
StaticStructureDefinitionClass = TypeVar('StaticStructureDefinitionClass', bound=definitions.StaticStructureDefinition)
