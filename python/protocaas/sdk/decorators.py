from typing import List
from .AppProcessor import _NO_DEFAULT


# This decorator is used to define a processor
def processor(name, help=None):
    def decorator(func):
        setattr(func, 'protocaas_processor', {'name': name, 'help': help})
        return func
    return decorator

# This decorator is used to add an attribute to a processor
def attribute(name: str, value: str):
    def decorator(func):
        if not hasattr(func, 'protocaas_attributes'):
            setattr(func, 'protocaas_attributes', [])
        attributes: list = getattr(func, 'protocaas_attributes')
        attributes.insert(0, {'name': name, 'value': value})
        return func
    return decorator

# This decorator is used to add tags to a processor
def tags(tag_list: List[str]):
    def decorator(func):
        if not hasattr(func, 'protocaas_tags'):
            setattr(func, 'protocaas_tags', [])
        tags: list = getattr(func, 'protocaas_tags')
        for tag in tag_list[::-1]:
            tags.insert(0, tag)
        return func
    return decorator

# This decorator is used to add an input to a processor
def input(name, help=None):
    def decorator(func):
        if not hasattr(func, 'protocaas_inputs'):
            setattr(func, 'protocaas_inputs', [])
        inputs: list = getattr(func, 'protocaas_inputs')
        inputs.insert(0, {'name': name, 'help': help, 'list': False})
        return func
    return decorator

# This decorator is used to add an input list to a processor
def input_list(name, help=None):
    def decorator(func):
        if not hasattr(func, 'protocaas_inputs'):
            setattr(func, 'protocaas_inputs', [])
        inputs: list = getattr(func, 'protocaas_inputs')
        inputs.insert(0, {'name': name, 'help': help, 'list': True})
        return func
    return decorator

# This decorator is used to add an output to a processor
def output(name, help=None):
    def decorator(func):
        if not hasattr(func, 'protocaas_outputs'):
            setattr(func, 'protocaas_outputs', [])
        outputs: list = getattr(func, 'protocaas_outputs')
        outputs.insert(0, {'name': name, 'help': help})
        return func
    return decorator

# This decorator is used to add a parameter to a processor
def parameter(name, *, help: str, type, default=_NO_DEFAULT, options: list=None, secret: bool=False):
    def decorator(func):
        if not hasattr(func, 'protocaas_parameters'):
            setattr(func, 'protocaas_parameters', [])
        parameters: list = getattr(func, 'protocaas_parameters')
        pp = {'name': name, 'help': help, 'type': type, 'default': default}
        if options is not None:
            pp['options'] = options
        if secret:
            pp['secret'] = True
        parameters.insert(0, pp)
        return func
    return decorator