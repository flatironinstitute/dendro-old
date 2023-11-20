from ...clients.db import fetch_compute_resource
from ..common import AuthException


async def _verify_compute_resource_api_key(*, compute_resource_id: str, compute_resource_api_key: str):
    # get compute resource
    compute_resource = await fetch_compute_resource(compute_resource_id, raise_on_not_found=True, include_api_key=True)
    assert compute_resource

    if compute_resource.apiKey is None:
        raise AuthException('No api key set for compute resource')

    if compute_resource_api_key != compute_resource.apiKey:
        raise AuthException('Invalid api key')
