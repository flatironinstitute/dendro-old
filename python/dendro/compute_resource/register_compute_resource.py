import os
import time
import yaml
from typing import Optional, Tuple
from ..common._crypto_keys import sign_message, generate_keypair


env_var_keys = [
    'COMPUTE_RESOURCE_ID',
    'COMPUTE_RESOURCE_PRIVATE_KEY',
    'CONTAINER_METHOD',
    'SINGLETON_JOB_ID',
    'BATCH_AWS_ACCESS_KEY_ID',
    'BATCH_AWS_SECRET_ACCESS_KEY',
    'BATCH_AWS_REGION'
]

def register_compute_resource(*, dir: str, compute_resource_id: Optional[str] = None, compute_resource_private_key: Optional[str] = None) -> Tuple[str, str]:
    """Initialize a Dendro compute resource node.

    Args:
        dir: The directory associated with the compute resource node.
    """

    # Let's make sure pubnub is installed, because it's required for the daemon
    try:
        import pubnub # noqa
    except ImportError:
        raise ImportError('The pubnub package is not installed. You should use "pip install dendro[compute_resource]".')

    env_fname = os.path.join(dir, '.dendro-compute-resource-node.yaml')

    the_env = {}
    for k in env_var_keys:
        the_env[k] = ''
    if not os.path.exists(env_fname):
        if not compute_resource_id:
            if compute_resource_private_key:
                raise ValueError('Cannot specify compute_resource_private_key without specifying compute_resource_id.')
            public_key_hex, private_key_hex = generate_keypair()
            compute_resource_id = public_key_hex
            compute_resource_private_key = private_key_hex
        else:
            if not compute_resource_private_key:
                raise ValueError('Cannot specify compute_resource_id without specifying compute_resource_private_key.')
        the_env['COMPUTE_RESOURCE_ID'] = compute_resource_id
        the_env['COMPUTE_RESOURCE_PRIVATE_KEY'] = compute_resource_private_key
        the_env['CONTAINER_METHOD'] = os.getenv('CONTAINER_METHOD', '')

        with open(env_fname, 'w', encoding='utf8') as f:
            yaml.dump(the_env, f)
    elif compute_resource_id is not None or compute_resource_private_key is not None:
        raise ValueError('Cannot specify compute_resource_id or compute_resource_private_key if compute resource node is already initialized.')

    with open(env_fname, 'r', encoding='utf8') as f:
        the_env = yaml.safe_load(f)

    COMPUTE_RESOURCE_ID = the_env['COMPUTE_RESOURCE_ID']
    COMPUTE_RESOURCE_PRIVATE_KEY = the_env['COMPUTE_RESOURCE_PRIVATE_KEY']

    timestamp = int(time.time())
    msg = {
        'timestamp': timestamp
    }
    signature = sign_message(msg, COMPUTE_RESOURCE_ID, COMPUTE_RESOURCE_PRIVATE_KEY)
    resource_code = f'{timestamp}-{signature}'

    url = f'https://dendro.vercel.app/register-compute-resource/{COMPUTE_RESOURCE_ID}/{resource_code}'
    print('')
    print('Please visit the following URL in your browser to register your compute resource:')
    print('')
    print(url)
    print('')

    assert COMPUTE_RESOURCE_ID is not None
    assert COMPUTE_RESOURCE_PRIVATE_KEY is not None
    return COMPUTE_RESOURCE_ID, COMPUTE_RESOURCE_PRIVATE_KEY

def _random_string(length: int) -> str:
    import random
    import string
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))
