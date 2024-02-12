import os


def get_url_for_project_file_uri(uri: str) -> str:
    job_id = os.environ.get('JOB_ID')
    if not job_id:
        raise Exception('Cannot get url for project file uri when JOB_ID is not set')
    job_private_key = os.environ.get('JOB_PRIVATE_KEY')
    if not job_private_key:
        raise Exception('Cannot get url for project file uri when JOB_PRIVATE_KEY is not set')
    from .Job import _get_download_url_for_uri
    return _get_download_url_for_uri(uri=uri, job_id=job_id, job_private_key=job_private_key)

class _LazyFileForProjectFileUri:
    def __init__(self, uri: str):
        self.uri = uri

    def get_url(self):
        return get_url_for_project_file_uri(self.uri)

def get_file_for_project_file_uri(uri: str):
    import remfile
    # We need to do it this way so that the url gets renewed
    x = _LazyFileForProjectFileUri(uri)
    return remfile.File(x)
