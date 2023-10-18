from fastapi import FastAPI

# Here's the reason that all the other Python files are in ../api_helpers
# I was noticing very long build times (~15 minutes)...
# Apparently, vercel treats every .py file in /api as a lambda function.
# So it was building each and every one of them, even though index.py should be the only one.
# See https://github.com/orgs/vercel/discussions/46

import sys
sys.path.append("..")
from api_helpers.routers.processor.router import router as processor_router
from api_helpers.routers.compute_resource.router import router as compute_resource_router
from api_helpers.routers.client.router import router as client_router
from api_helpers.routers.gui.router import router as gui_router


app = FastAPI()

# requests from a processing job
app.include_router(processor_router, prefix="/api/processor", tags=["Processor"])

# requests from a compute resource
app.include_router(compute_resource_router, prefix="/api/compute_resource", tags=["Compute Resource"])

# requests from a client (usually Python)
app.include_router(client_router, prefix="/api/client", tags=["Client"])

# requests from the GUI
app.include_router(gui_router, prefix="/api/gui", tags=["GUI"])