from typing import Any, List, Union
from dataclasses import dataclass


_NO_DEFAULT = object()

@dataclass
class AppProcessorInput:
    """An input file of a processor in an app"""
    name: str
    help: str
    list: str
    def get_spec(self):
        ret = {
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
        ret = {
            'name': self.name,
            'help': self.help,
            'type': _type_to_string(self.type)
        }
        if self.default != _NO_DEFAULT:
            ret['default'] = self.default
        if self.options is not None:
            ret['options'] = self.options
        if self.secret:
            ret['secret'] = True
        return ret
    @staticmethod
    def from_spec(spec):
        default = spec.get('default', _NO_DEFAULT)
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

class AppProcessor:
    """A processor in an app"""
    def __init__(self, *,
        name: str,
        help: str,
        inputs: List[AppProcessorInput],
        outputs: List[AppProcessorOutput],
        parameters: List[AppProcessorParameter],
        attributes: List[AppProcessorAttribute],
        tags: List[AppProcessorTag],
        func=None
    ) -> None:
        self._name = name
        self._help = help
        self._inputs = inputs
        self._outputs = outputs
        self._parameters = parameters
        self._attributes = attributes
        self._tags = tags
        self._processor_func = func
    def get_spec(self):
        return {
            'name': self._name,
            'help': self._help,
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
            inputs=inputs,
            outputs=outputs,
            parameters=parameters,
            attributes=attributes,
            tags=tags
        )
    @staticmethod
    def from_func(processor_func):
        pp = getattr(processor_func, 'protocaas_processor', None)
        if pp is None:
            raise Exception('Processor function must be decorated with @processor')
        name = pp['name']
        help = pp['help']
        inputs = getattr(processor_func, 'protocaas_inputs', [])
        outputs = getattr(processor_func, 'protocaas_outputs', [])
        parameters = getattr(processor_func, 'protocaas_parameters', [])
        attributes = getattr(processor_func, 'protocaas_attributes', [])
        tags = getattr(processor_func, 'protocaas_tags', [])
        _inputs = [AppProcessorInput(name=i['name'], help=i['help'], list=i['list']) for i in inputs]
        _outputs = [AppProcessorOutput(name=o['name'], help=o['help']) for o in outputs]
        _parameters = [AppProcessorParameter(name=p['name'], help=p['help'], type=p['type'], default=p['default'], options=p.get('options', None), secret=p.get('secret', False)) for p in parameters]
        _attributes = [AppProcessorAttribute(name=a['name'], value=a['value']) for a in attributes]
        _tags = [AppProcessorTag(tag=t) for t in tags]
        return AppProcessor(
            name=name,
            help=help,
            inputs=_inputs,
            outputs=_outputs,
            parameters=_parameters,
            attributes=_attributes,
            tags=_tags,
            func=processor_func
        )

def _type_to_string(type):
    if type == str:
        return 'str'
    if type == int:
        return 'int'
    if type == float:
        return 'float'
    if type == bool:
        return 'bool'
    if type == List[str]:
        return 'List[str]'
    if type == List[int]:
        return 'List[int]'
    if type == List[float]:
        return 'List[float]'
    if type == List[bool]:
        return 'List[bool]'
    raise Exception(f'Unexpected type: {type}')

def _type_from_string(type):
    if type == 'str':
        return str
    if type == 'int':
        return int
    if type == 'float':
        return float
    if type == 'bool':
        return bool
    if type == 'List[str]':
        return List[str]
    if type == 'List[int]':
        return List[int]
    if type == 'List[float]':
        return List[float]
    if type == 'List[bool]':
        return List[bool]
    raise Exception(f'Unexpected type: {type}')