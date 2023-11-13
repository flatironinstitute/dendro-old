from typing import Any, List, Union, Dict, Type
from dataclasses import dataclass
import inspect
from .. import BaseModel
from pydantic_core import PydanticUndefined
from .ProcessorBase import ProcessorBase
from .InputFile import InputFile
from .OutputFile import OutputFile

@dataclass
class AppProcessorInput:
    """An input file of a processor in an app"""
    name: str
    description: str
    list: bool
    def get_spec(self):
        ret: Dict[str, Any] = {
            'name': self.name,
            'description': self.description
        }
        if self.list:
            ret['list'] = True
        return ret
    @staticmethod
    def from_spec(spec):
        return AppProcessorInput(
            name=spec['name'],
            description=spec['description'],
            list=spec.get('list', False)
        )

@dataclass
class AppProcessorOutput:
    """An output file of a processor in an app"""
    name: str
    description: str
    def get_spec(self):
        return {
            'name': self.name,
            'description': self.description
        }
    @staticmethod
    def from_spec(spec):
        return AppProcessorOutput(
            name=spec['name'],
            description=spec['description']
        )

@dataclass
class AppProcessorParameter:
    """A parameter of a processor in an app"""
    name: str
    description: str
    type: Any
    default: Any
    options: Union[List[str], List[int], List[float], None]
    secret: bool = False
    def get_spec(self):
        ret: Dict[str, Any] = {
            'name': self.name,
            'description': self.description,
            'type': _type_to_string(self.type)
        }
        if self.default != PydanticUndefined:
            ret['default'] = self.default
        if self.options is not None:
            ret['options'] = self.options
        if self.secret:
            ret['secret'] = True
        return ret
    @staticmethod
    def from_spec(spec):
        default = spec.get('default', PydanticUndefined)
        options = spec.get('options', None)
        secret = spec.get('secret', False)
        return AppProcessorParameter(
            name=spec['name'],
            description=spec['description'],
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
        description: str,
        label: str,
        inputs: List[AppProcessorInput],
        outputs: List[AppProcessorOutput],
        parameters: List[AppProcessorParameter],
        attributes: List[AppProcessorAttribute],
        tags: List[AppProcessorTag],
        processor_class: Union[Type[ProcessorBase], None] = None
    ) -> None:
        self._name = name
        self._description = description
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
            'description': self._description,
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
            description=spec['description'],
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
        description = processor_class.description
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
            description=description,
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

    return _get_context_inputs_outputs_parameters_for_model(context_param.annotation)

def _get_context_inputs_outputs_parameters_for_model(context_class: Type[BaseModel]):
    context_fields = []
    try:
        # This works in pydantic v2
        model_fields = context_class.model_fields # type: ignore
    except AttributeError:
        # This is the alternative for pydantic v1
        model_fields = context_class.__fields__
    for name, field in model_fields.items():
        if name is None:
            continue
        if name == 'model_config':
            # necessary to skip for our version of pydantic BaseModel
            continue
        if hasattr(field, 'json_schema_extra'):
            json_schema_extra = field.json_schema_extra # type: ignore
            secret = json_schema_extra.get('secret', None) if json_schema_extra is not None else None # type: ignore
            assert isinstance(secret, bool) or secret is None
            options = json_schema_extra.get('options', None) if json_schema_extra is not None else None # type: ignore
        else:
            secret: Union[bool, None] = None
            options = None
        # support both pydantic v1 and v2
        annotation = field.annotation if hasattr(field, 'annotation') else None # type: ignore
        if annotation is None:
            # support pydantic v1
            annotation = _get_annotation_for_field_using_python_type_hints(context_class, name)
        if annotation is None:
            # Note: in pydantic < 1.10.0, the field.type_ picks up List[InputFile] as just InputFile, so that's why we are not using field.type_
            raise Exception(f'No type annotation for field: {name}')
        context_fields.append({
            'name': name,
            'description': field.description if hasattr(field, 'description') else '', # type: ignore
            'annotation': annotation,
            'default': field.default if hasattr(field, 'default') else PydanticUndefined,
            'options': options,
            'secret': secret,
        })

    inputs: List[AppProcessorInput] = []
    outputs: List[AppProcessorOutput] = []
    parameters: List[AppProcessorParameter] = []
    for context_field in context_fields:
        name: str = context_field['name']
        description: str = context_field['description']
        annotation: Any = context_field['annotation']
        default: Any = context_field['default']
        secret: Union[bool, None] = context_field['secret']
        options: Union[List[str], None] = context_field['options']
        if annotation == InputFile or annotation == List[InputFile]:
            is_list = annotation == List[InputFile]
            inputs.append(AppProcessorInput(
                name=name,
                description=description,
                list=is_list
            ))
            # check to make sure other fields are not set
            if options is not None:
                raise AppProcessorException(f"Input {name} has options set - only parameters can have options")
            if secret is not None:
                raise AppProcessorException(f"Input {name} has secret set - only parameters can have secret set")
            if default is not PydanticUndefined and default is not None: # None case only necessary for pydantic v1
                raise AppProcessorException(f"Input {name} has default set - only parameters can have default set")
        elif annotation == OutputFile:
            outputs.append(AppProcessorOutput(
                name=name,
                description=description
            ))
            # check to make sure other fields are not set
            if options is not None:
                raise AppProcessorException(f"Input {name} has options set - only parameters can have options")
            if secret is not None:
                raise AppProcessorException(f"Input {name} has secret set - only parameters can have secret set")
            if default is not PydanticUndefined and default is not None: # None case only necessary for pydantic v1
                raise AppProcessorException(f"Input {name} has default set - only parameters can have default set")
        elif _is_valid_parameter_type(annotation):
            parameters.append(AppProcessorParameter(
                name=name,
                description=description,
                type=annotation,
                default=default,
                options=options,
                secret=secret if secret is not None else False
            ))
        elif _is_pydantic_model_class(annotation):
            inputs0, outputs0, parameters0 = _get_context_inputs_outputs_parameters_for_model(annotation)
            for input0 in inputs0:
                input0.name = f'{name}.{input0.name}'
                inputs.append(input0)
            for output0 in outputs0:
                output0.name = f'{name}.{output0.name}'
                outputs.append(output0)
            for parameter0 in parameters0:
                parameter0.name = f'{name}.{parameter0.name}'
                parameters.append(parameter0)
        else:
            raise AppProcessorException(f"Unsupported type for {name}: {annotation}")
    return inputs, outputs, parameters

def _is_pydantic_model_class(type: Any):
    return inspect.isclass(type) and issubclass(type, BaseModel)

_type_map = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'List[str]': List[str],
    'List[int]': List[int],
    'List[float]': List[float],
    'List[bool]': List[bool],
    'Optional[int]': Union[int, None],
    'Optional[float]': Union[float, None],
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

def _get_annotation_for_field_using_python_type_hints(model_class: Type[BaseModel], field_name: str):
    # This is a workaround for pydantic v1 where field.annotation is not set and field.type_ doesn't cut it for List[InputFile] when pydantic version is < 1.10.0
    from typing import get_type_hints
    type_hints = get_type_hints(model_class)
    return type_hints.get(field_name, None)
