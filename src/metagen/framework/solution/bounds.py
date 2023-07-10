from typing import TypeVar
import metagen.framework.solution as types

BaseTypeClass = TypeVar('BaseTypeClass', bound=types.BaseType)
SolutionClass = TypeVar('SolutionClass', bound=types.Solution)
