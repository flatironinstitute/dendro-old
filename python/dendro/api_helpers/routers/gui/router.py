from fastapi import APIRouter
from .create_job_route import router as create_job_router
from .project_routes import router as project_router
from .compute_resource_routes import router as compute_resource_router
from .file_routes import router as file_router
from .job_routes import router as job_router
from .github_auth_routes import router as github_auth_router
from .user_routes import router as user_router

router = APIRouter()

router.include_router(create_job_router)
router.include_router(project_router, prefix="/projects")
router.include_router(compute_resource_router, prefix="/compute_resources")
router.include_router(file_router)
router.include_router(job_router, prefix="/jobs")
router.include_router(github_auth_router)
router.include_router(user_router, prefix="/users")
