from typing import Any, Optional, List

_default_not_specified = object()


class _Field:
    def __init__(self, *,
        help: str = '',
        default: Optional[Any] = _default_not_specified, # only applies to parameters
        options: Optional[List[Any]] = None, # only applies to parameters
        secret: Optional[bool] = None # only applies to parameters
    ):
        self.default = default
        self.help = help
        self.options = options
        self.secret = secret

# We need to use a function here rather than a class so that we can return the Any type
def field(*,
    help: str = '',
    default: Optional[Any] = _default_not_specified, # only applies to parameters
    options: Optional[List[Any]] = None, # only applies to parameters
    secret: Optional[bool] = None # only applies to parameters
) -> Any: # it's important that this returns Any so that the linter is okay with using it
    return _Field(
        help=help,
        default=default,
        options=options,
        secret=secret
    )

class ProcessorBase:
    name: str
    label: str
    help: str
    tags: List[str]
    attributes: dict

    @staticmethod
    def run(
        context: Any
    ):
        raise NotImplementedError()
