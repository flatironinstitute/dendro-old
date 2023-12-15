import os
from ..common._api_request import _processor_get_api_request


def _get_upload_url(*, job_id: str, job_private_key: str, output_name: str) -> str:
    """Get a signed upload URL for the output (console or resource log) of a job"""
    url_path = f'/api/processor/jobs/{job_id}/outputs/{output_name}/upload_url'
    headers = {
        'job-private-key': job_private_key
    }
    res = _processor_get_api_request(
        url_path=url_path,
        headers=headers
    )
    return res['uploadUrl']

def _process_is_alive(pid: str) -> bool:
    """
    Check if a process is alive.
    """
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False
