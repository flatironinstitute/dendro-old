from typing import List, Union
from pydantic import BaseModel


class FileManifestFile(BaseModel):
    name: str
    url: str
    size: Union[int, None] = None

class FileManifest(BaseModel):
    files: List[FileManifestFile]
