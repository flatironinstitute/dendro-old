# flake8: noqa

from .InputFile import InputFile
from .OutputFile import OutputFile
from .App import App

from .ProcessorBase import ProcessorBase

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
