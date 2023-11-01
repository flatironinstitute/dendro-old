from pydantic import BaseModel as PydanticBaseModel, ConfigDict, VERSION as pydantic_version
from pydantic import Field # noqa

class BaseModel(PydanticBaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

if pydantic_version.startswith('1.'):
    # Handle the case where the installed pydantic is version 1.x.x
    class V2CompatiblePydanticBaseModel(BaseModel):
        def model_dump(self, *, exclude_none=False):
            return self.dict(exclude_none=exclude_none)
        class Config:
            arbitrary_types_allowed = True
    BaseModel = V2CompatiblePydanticBaseModel
