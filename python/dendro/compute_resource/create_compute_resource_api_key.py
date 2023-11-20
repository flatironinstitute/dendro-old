import os
import yaml
import uuid
import hashlib
from .register_compute_resource import env_var_keys
from ..common._api_request import _compute_resource_put_api_request


def create_compute_resource_api_key(*, dir: str):
    config_fname = os.path.join(dir, '.dendro-compute-resource-node.yaml')
    if os.path.exists(config_fname):
        with open(config_fname, 'r', encoding='utf8') as f:
            the_config = yaml.safe_load(f)
    else:
        the_config = {}
    for k in env_var_keys:
        if k in the_config:
            os.environ[k] = the_config[k]

    compute_resource_id = os.getenv('COMPUTE_RESOURCE_ID', None)
    compute_resource_private_key = os.getenv('COMPUTE_RESOURCE_PRIVATE_KEY', None)
    if compute_resource_id is None:
        raise ValueError('Compute resource has not been initialized in this directory, and the environment variable COMPUTE_RESOURCE_ID is not set.')
    if compute_resource_private_key is None:
        raise ValueError('Compute resource has not been initialized in this directory, and the environment variable COMPUTE_RESOURCE_PRIVATE_KEY is not set.')

    # the randomly-generated api key is the sha1 hash of a uuid
    api_key = hashlib.sha1(str(uuid.uuid4()).encode('utf8')).hexdigest()

    print('Reporting the compute resource api key')
    url_path = f'/api/compute_resource/compute_resources/{compute_resource_id}/api_key'
    _compute_resource_put_api_request(
        url_path=url_path,
        compute_resource_id=compute_resource_id,
        compute_resource_private_key=compute_resource_private_key,
        data={
            'api_key': api_key
        }
    )
    return api_key
