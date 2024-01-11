from fastapi import FastAPI

# Here's the reason that all the other Python files are in ../python/dendro/api_helpers
# I was noticing very long build times (~15 minutes)...
# Apparently, vercel treats every .py file in /api as a lambda function.
# So it was building each and every one of them, even though index.py should be the only one.
# See https://github.com/orgs/vercel/discussions/46

import os
thisdir = os.path.dirname(os.path.realpath(__file__))

import sys
print(f'This dir: {thisdir}')
sys.path.append(thisdir + "/../python")
from dendro.api_helpers.routers.processor.router import router as processor_router
from dendro.api_helpers.routers.compute_resource.router import router as compute_resource_router
from dendro.api_helpers.routers.client.router import router as client_router
from dendro.api_helpers.routers.gui.router import router as gui_router

from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

# Set up CORS
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "https://dendro.vercel.app",
    "https://flatironinstitute.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# requests from a processing job
app.include_router(processor_router, prefix="/api/processor", tags=["Processor"])

# requests from a compute resource
app.include_router(compute_resource_router, prefix="/api/compute_resource", tags=["Compute Resource"])

# requests from a client (usually Python)
app.include_router(client_router, prefix="/api/client", tags=["Client"])

# requests from the GUI
app.include_router(gui_router, prefix="/api/gui", tags=["GUI"])
