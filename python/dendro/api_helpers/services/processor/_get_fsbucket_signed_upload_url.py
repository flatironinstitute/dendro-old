from typing import Optional
import time
import hashlib


def _get_fsbucket_signed_upload_url(
    *, fsbucket_api_url, secret_key: str, object_key: str, size: Optional[int] = None
):
    # expires in one hour
    expires = int(time.time()) + 3600
    signature = _create_signature(
        secret_key=secret_key, object_key=object_key, expires=expires, method="PUT"
    )
    url = f"{fsbucket_api_url}/{object_key}?signature={signature}&expires={expires}"
    return url


def _create_signature(*, secret_key: str, object_key: str, expires: int, method: str):
    path = f'/{object_key}'
    string_to_sign = f"{method}\n{path}\n{expires}\n{secret_key}"
    hash = hashlib.sha256()
    hash.update(string_to_sign.encode("utf-8"))
    return hash.hexdigest()
