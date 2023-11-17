import os

from pydantic import VERSION as pydantic_version # noqa

# In the future we may want to intercept and override the pydantic BaseModel
from pydantic import BaseModel, Field # noqa

# read the version from thisdir/version.txt
thisdir = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(thisdir, 'version.txt')) as f:
    __version__ = f.read().strip()
