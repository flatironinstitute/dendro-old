from ....common.dendro_types import DendroProject
from ...clients.db import delete_all_files_in_project, delete_all_jobs_in_project, delete_project as db_delete_project


async def delete_project(project: DendroProject):
    await delete_all_files_in_project(project.projectId)
    await delete_all_jobs_in_project(project.projectId)
    await db_delete_project(project.projectId)
    return None
