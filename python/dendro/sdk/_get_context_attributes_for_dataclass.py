from typing import get_type_hints, Any, Type, List
from dataclasses import dataclass
import inspect
from dendro.sdk.ProcessorBase import _Field


@dataclass
class ContextAttribute:
    name: str
    field: _Field
    type_hint: Any = None

def _get_context_attributes_for_dataclass(x: Type[Any]) -> List[ContextAttribute]:
    context_attributes = inspect.getmembers(x, lambda a: not (inspect.isroutine(a))) # exclude methods
    context_attributes = [
        ContextAttribute(
            name=attribute[0],
            field=attribute[1]
        )
        for attribute in context_attributes
        if not (attribute[0].startswith('__') and attribute[0].endswith('__')) # exclude attributes such as __module__, __dict__, etc.
    ]
    for ca in context_attributes:
        if not isinstance(ca.field, _Field):
            raise Exception(f"Attribute {ca.name} is not a _Field")
    type_hints = get_type_hints(x)
    for attr_name, attr_type in type_hints.items():
        ca = next((ca for ca in context_attributes if ca.name == attr_name), None)
        if not ca:
            raise Exception(f"Unexpected: Attribute {attr_name} is not defined in the context class")
        ca.type_hint = attr_type
    return context_attributes
