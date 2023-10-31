# flake8: noqa

from .InputFile import InputFile
from .OutputFile import OutputFile
from .App import App

from .ProcessorBase import ProcessorBase

from pydantic import BaseModel as PydanticBaseModel, Field

class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
