from ....common.dendro_types import ComputeResourceUserUsage
from ...clients.db import fetch_jobs_including_deleted


async def get_compute_resource_user_usage(*, compute_resource_id: str, user_id: str) -> ComputeResourceUserUsage:
    jobs_including_deleted = await fetch_jobs_including_deleted(compute_resource_id=compute_resource_id, user_id=user_id)
    return ComputeResourceUserUsage(
        computeResourceId=compute_resource_id,
        userId=user_id,
        jobsIncludingDeleted=jobs_including_deleted
    )
