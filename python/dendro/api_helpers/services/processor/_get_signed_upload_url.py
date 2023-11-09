from typing import Optional, Dict, Any
import boto3
from boto3.session import Config
import json


async def _get_signed_upload_url(*,
    bucket_uri: str,
    bucket_credentials: str,
    object_key: str,
    size: Optional[int] = None
):
    creds = json.loads(bucket_credentials)
    access_key_id = creds['accessKeyId']
    secret_access_key = creds['secretAccessKey']
    endpoint = creds.get('endpoint', None)

    region_name = _get_region_name_from_uri(bucket_uri)
    bucket_name = _get_bucket_name_from_uri(bucket_uri)

    s3_client = boto3.client(
        's3',
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        endpoint_url=endpoint,
        region_name=region_name,
        config=Config(signature_version='s3v4')
    )

    params: Dict[str, Any] = {
        'Bucket': bucket_name,
        'Key': object_key
    }
    if size is not None:
        params['ContentLength'] = size

    return s3_client.generate_presigned_url(
        'put_object',
        Params=params,
        ExpiresIn=30 * 60 # 30 minutes
    )

def _get_bucket_name_from_uri(bucket_uri: str) -> str:
    if not bucket_uri:
        return ''
    return bucket_uri.split('?')[0].split('/')[2]

def _get_region_name_from_uri(bucket_uri: str) -> str:
    # for example: s3://bucket-name?region=us-west-2
    if not bucket_uri:
        return ''
    default_region = 'auto' # for cloudflare
    a = bucket_uri.split('?')
    if len(a) == 1:
        return default_region
    b = a[1].split('&')
    c = [x for x in b if x.startswith('region=')]
    if len(c) == 0:
        return default_region
    d = c[0].split('=')
    if len(d) != 2:
        return default_region
    return d[1]
