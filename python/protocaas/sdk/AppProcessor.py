from typing import Any, List, Union, Dict, Type
from dataclasses import dataclass
import inspect

from ._get_context_attributes_for_dataclass import _get_context_attributes_for_dataclass
from .ProcessorBase import ProcessorBase, _default_not_specified
from .InputFile import InputFile
from .OutputFile import OutputFile

@dataclass
class AppProcessorInput:
    """An input file of a processor in an app"""
    name: str
    help: str
    list: bool
    def get_spec(self):
        ret: Dict[str, Any] = {
            'name': self.name,
            'help': self.help
        }
        if self.list:
            ret['list'] = True
        return ret
    @staticmethod
    def from_spec(spec):
        return AppProcessorInput(
            name=spec['name'],
            help=spec['help'],
            list=spec.get('list', False)
        )

@dataclass
class AppProcessorOutput:
    """An output file of a processor in an app"""
    name: str
    help: str
    def get_spec(self):
        return {
            'name': self.name,
            'help': self.help
        }
    @staticmethod
    def from_spec(spec):
        return AppProcessorOutput(
            name=spec['name'],
            help=spec['help']
        )

@dataclass
class AppProcessorParameter:
    """A parameter of a processor in an app"""
    name: str
    help: str
    type: Any
    default: Any
    options: Union[List[str], List[int], List[float], None]
    secret: bool = False
    def get_spec(self):
        ret: Dict[str, Any] = {
            'name': self.name,
            'help': self.help,
            'type': _type_to_string(self.type)
        }
        if self.default != _default_not_specified:
            ret['default'] = self.default
        if self.options is not None:
            ret['options'] = self.options
        if self.secret:
            ret['secret'] = True
        return ret
    @staticmethod
    def from_spec(spec):
        default = spec.get('default', _default_not_specified)
        options = spec.get('options', None)
        secret = spec.get('secret', False)
        return AppProcessorParameter(
            name=spec['name'],
            help=spec['help'],
            type=_type_from_string(spec['type']),
            default=default,
            options=options,
            secret=secret
        )

@dataclass
class AppProcessorAttribute:
    """An attribute of a processor in an app"""
    name: str
    value: str
    def get_spec(self):
        return {
            'name': self.name,
            'value': self.value
        }
    @staticmethod
    def from_spec(spec):
        return AppProcessorAttribute(
            name=spec['name'],
            value=spec['value']
        )

@dataclass
class AppProcessorTag:
    """A tag of a processor in an app"""
    tag: str
    def get_spec(self):
        return {
            'tag': self.tag
        }
    @staticmethod
    def from_spec(spec):
        return AppProcessorTag(
            tag=spec['tag']
        )

class AppProcessorException(Exception):
    pass

class AppProcessor:
    """A processor in an app"""
    def __init__(self, *,
        name: str,
        help: str,
        label: str,
        inputs: List[AppProcessorInput],
        outputs: List[AppProcessorOutput],
        parameters: List[AppProcessorParameter],
        attributes: List[AppProcessorAttribute],
        tags: List[AppProcessorTag],
        processor_class: Union[Type[ProcessorBase], None] = None
    ) -> None:
        self._name = name
        self._help = help
        self._label = label
        self._inputs = inputs
        self._outputs = outputs
        self._parameters = parameters
        self._attributes = attributes
        self._tags = tags
        self._processor_class = processor_class
    def get_spec(self):
        return {
            'name': self._name,
            'help': self._help,
            'label': self._label,
            'inputs': [i.get_spec() for i in self._inputs],
            'outputs': [o.get_spec() for o in self._outputs],
            'parameters': [p.get_spec() for p in self._parameters],
            'attributes': [a.get_spec() for a in self._attributes],
            'tags': [t.get_spec() for t in self._tags]
        }
    @staticmethod
    def from_spec(spec):
        inputs = [AppProcessorInput.from_spec(i) for i in spec['inputs']]
        outputs = [AppProcessorOutput.from_spec(o) for o in spec['outputs']]
        parameters = [AppProcessorParameter.from_spec(p) for p in spec['parameters']]
        attributes = [AppProcessorAttribute.from_spec(a) for a in spec['attributes']]
        tags = [AppProcessorTag.from_spec(t) for t in spec['tags']]
        return AppProcessor(
            name=spec['name'],
            help=spec['help'],
            label=spec['label'],
            inputs=inputs,
            outputs=outputs,
            parameters=parameters,
            attributes=attributes,
            tags=tags
        )
    @staticmethod
    def from_processor_class(processor_class: Type[ProcessorBase]):
        name = processor_class.name
        help = processor_class.help
        label = processor_class.label
        tags = processor_class.tags
        attributes = processor_class.attributes

        _attributes: List[AppProcessorAttribute] = []
        for key, value in attributes.items():
            _attributes.append(AppProcessorAttribute(
                name=key,
                value=value
            ))
        _tags = [AppProcessorTag(tag=tag) for tag in tags]

        inputs, outputs, parameters = _get_context_inputs_outputs_parameters_for_processor(processor_class)

        return AppProcessor(
            name=name,
            help=help,
            label=label,
            inputs=inputs,
            outputs=outputs,
            parameters=parameters,
            attributes=_attributes,
            tags=_tags,
            processor_class=processor_class
        )

def _get_context_inputs_outputs_parameters_for_processor(processor_class: Type[ProcessorBase]):
    run_signature = inspect.signature(processor_class.run)
    run_parameters = run_signature.parameters
    if len(run_parameters) != 1:
        raise Exception('The run method should have exactly one parameter')
    context_param = list(run_parameters.values())[0]

    return _get_context_inputs_outputs_parameters_for_dataclass(context_param.annotation)

def _get_context_inputs_outputs_parameters_for_dataclass(x: Type[Any]):
    context_attributes = _get_context_attributes_for_dataclass(x)

    inputs: List[AppProcessorInput] = []
    outputs: List[AppProcessorOutput] = []
    parameters: List[AppProcessorParameter] = []
    for context_attribute in context_attributes:
        if context_attribute.type_hint == InputFile or context_attribute.type_hint == List[InputFile]:
            is_list = context_attribute.type_hint == List[InputFile]
            field = context_attribute.field
            inputs.append(AppProcessorInput(
                name=context_attribute.name,
                help=field.help,
                list=is_list
            ))
            # check to make sure other fields are not set
            if field.options is not None:
                raise AppProcessorException(f"Input {context_attribute.name} has options set - only parameters can have options")
            if field.secret is not None:
                raise AppProcessorException(f"Input {context_attribute.name} has secret set - only parameters can have secret set")
            if field.default is not _default_not_specified:
                raise AppProcessorException(f"Input {context_attribute.name} has default set - only parameters can have default set")
        elif context_attribute.type_hint == OutputFile:
            field = context_attribute.field
            outputs.append(AppProcessorOutput(
                name=context_attribute.name,
                help=field.help
            ))
            # check to make sure other fields are not set
            if field.options is not None:
                raise AppProcessorException(f"Input {context_attribute.name} has options set - only parameters can have options")
            if field.secret is not None:
                raise AppProcessorException(f"Input {context_attribute.name} has secret set - only parameters can have secret set")
            if field.default is not _default_not_specified:
                raise AppProcessorException(f"Input {context_attribute.name} has default set - only parameters can have default set")
        elif _is_valid_parameter_type(context_attribute.type_hint):
            parameters.append(AppProcessorParameter(
                name=context_attribute.name,
                help=context_attribute.field.help,
                type=context_attribute.type_hint,
                default=context_attribute.field.default,
                options=context_attribute.field.options,
                secret=context_attribute.field.secret if context_attribute.field.secret is not None else False
            ))
        elif _is_dataclass(context_attribute.type_hint):
            inputs0, outputs0, parameters0 = _get_context_inputs_outputs_parameters_for_dataclass(context_attribute.type_hint)
            for input0 in inputs0:
                input0.name = f'{context_attribute.name}.{input0.name}'
                inputs.append(input0)
            for output0 in outputs0:
                output0.name = f'{context_attribute.name}.{output0.name}'
                outputs.append(output0)
            for parameter0 in parameters0:
                parameter0.name = f'{context_attribute.name}.{parameter0.name}'
                parameters.append(parameter0)
        else:
            raise AppProcessorException(f"Unsupported type for {context_attribute.name}: {context_attribute.type_hint}")
    return inputs, outputs, parameters

def _is_dataclass(type: Any):
    return hasattr(type, '__dataclass_fields__')

_type_map = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'List[str]': List[str],
    'List[int]': List[int],
    'List[float]': List[float],
    'List[bool]': List[bool]
}

def _type_to_string(type: Any):
    for key, value in _type_map.items():
        if value == type:
            return key
    raise ValueError(f'Unexpected type: {type}')

def _type_from_string(type: str):
    try:
        return _type_map[type]
    except KeyError as exc:
        raise ValueError(f'Unexpected type: {type}') from exc

def _is_valid_parameter_type(type: Any):
    return type in _type_map.values()
