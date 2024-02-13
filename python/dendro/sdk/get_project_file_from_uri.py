import os


def get_project_file_from_uri(uri: str):
    from .Job import _parse_dendro_uri
    from .InputFile import InputFile

    job_id = os.environ.get('JOB_ID')
    if not job_id:
        raise Exception('Cannot get project file when JOB_ID is not set')
    job_private_key = os.environ.get('JOB_PRIVATE_KEY')
    if not job_private_key:
        raise Exception('Cannot get project file when JOB_PRIVATE_KEY is not set')

    file_id, is_folder, label = _parse_dendro_uri(uri)
    if is_folder:
        raise Exception('Cannot get project file for a folder')
    ret = InputFile(
        name=None,
        url=None,
        local_file_name=None,
        project_file_uri=uri,  # use this instead of name
        project_file_name=label,
        job_id=job_id,
        job_private_key=job_private_key
    )
    ret._check_file_cache()
    return ret
