from typing import Optional
from dendro.mock import using_mock
from ...core.settings import get_settings
from ._get_signed_upload_url import _get_signed_upload_url


# note that output_name of "_console_output" and "_resource_utilization_log" are special cases
async def get_upload_url(job_id: str, output_name: str):
    if output_name == "_console_output":
        pass
    elif output_name == "_resource_utilization_log":
        pass
    else:
        pass
        # not going to check this because it would require excessive database queries to get the job - there may be a way around it
        # aa = [x for x in job.outputFiles if x.name == output_name]
        # if len(aa) == 0:
        #     raise Exception(f"No output with name {output_name} **")

    object_key = f"dendro-outputs/{job_id}/{output_name}"

    upload_url, download_url = await _get_upload_url_for_object_key(object_key)
    return upload_url

async def get_upload_url_for_folder_file(job_id: str, output_folder_name: str, output_folder_file_name: str):
    object_key = f"dendro-outputs/{job_id}/{output_folder_name}/{output_folder_file_name}"

    upload_url, download_url = await _get_upload_url_for_object_key(object_key)
    return upload_url

async def get_additional_upload_url(*, job_id: str, sha1: str):
    if not _is_valid_sha1(sha1):
        raise Exception('Invalid sha1 string')

    object_key = f"dendro-outputs/{job_id}/sha1/{sha1}"

    upload_url, download_url = await _get_upload_url_for_object_key(object_key)
    return upload_url, download_url

async def _get_upload_url_for_object_key(object_key: str, size: Optional[int] = None):
    settings = get_settings()

    if using_mock():
        return f"https://mock-bucket.s3.amazonaws.com/{object_key}?mock-signature", f"https://mock-bucket/{object_key}"

    OUTPUT_BUCKET_URI = settings.OUTPUT_BUCKET_URI
    if OUTPUT_BUCKET_URI is None:
        raise Exception('Environment variable not set: OUTPUT_BUCKET_URI')
    OUTPUT_BUCKET_CREDENTIALS = settings.OUTPUT_BUCKET_CREDENTIALS
    if OUTPUT_BUCKET_CREDENTIALS is None:
        raise Exception('Environment variable not set: OUTPUT_BUCKET_CREDENTIALS')
    OUTPUT_BUCKET_BASE_URL = settings.OUTPUT_BUCKET_BASE_URL
    if OUTPUT_BUCKET_BASE_URL is None:
        raise Exception('Environment variable not set: OUTPUT_BUCKET_BASE_URL')
    if using_mock():
        output_bucket_base_url = 'https://mock-bucket'
    else:
        output_bucket_base_url = OUTPUT_BUCKET_BASE_URL

    signed_upload_url = await _get_signed_upload_url(
        bucket_uri=OUTPUT_BUCKET_URI,
        bucket_credentials=OUTPUT_BUCKET_CREDENTIALS,
        object_key=object_key,
        size=size
    )

    download_url = f'{output_bucket_base_url}/{object_key}'

    return signed_upload_url, download_url

def _is_valid_sha1(sha1: str):
    if len(sha1) != 40:
        return False
    for c in sha1:
        if c not in '0123456789abcdef':
            return False
    return True
