from typing import List
from pydantic import BaseModel


class FileManifestFile(BaseModel):
    name: str
    url: str
    size: int

class FileManifest(BaseModel):
    files: List[FileManifestFile]
