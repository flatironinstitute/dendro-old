import os
import requests
from ._crypto_keys import _sign_message_str

dendro_url = os.getenv('DENDRO_URL', 'https://dendro.vercel.app')

_globals = {
    'test_client': None
}
def _use_api_test_client(test_client):
    _globals['test_client'] = test_client

def _compute_resource_get_api_request(*,
    url_path: str,
    compute_resource_id: str,
    compute_resource_private_key: str,
    _wrong_payload_for_testing: bool = False,
    _wrong_signature_for_testing: bool = False
):
    payload = url_path
    signature = _sign_message_str(payload, compute_resource_id, compute_resource_private_key)

    if _wrong_payload_for_testing:
        payload = 'wrong payload'
    if _wrong_signature_for_testing:
        signature = 'wrong signature'

    headers = {
        'compute-resource-id': compute_resource_id,
        'compute-resource-payload': payload,
        'compute-resource-signature': signature
    }

    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in compute resource get api request for {url}; {e}')
        raise
    return resp.json()

# not used right now
# def _compute_resource_post_api_request(*,
#     url_path: str,
#     compute_resource_id: str,
#     compute_resource_private_key: str,
#     data: dict
# ):
#     payload = url_path
#     signature = _sign_message_str(payload, compute_resource_id, compute_resource_private_key)

#     headers = {
#         'compute-resource-id': compute_resource_id,
#         'compute-resource-payload': payload,
#         'compute-resource-signature': signature
#     }

#     test_client = _globals['test_client']
#     if test_client is None:
#         url = f'{dendro_url}{url_path}'
#         client = requests
#     else:
#         assert url_path.startswith('/api')
#         url = url_path
#         client = test_client
#     try:
#         resp = client.post(url, headers=headers, json=data, timeout=60)
#         resp.raise_for_status()
#     except Exception as e:
#         print(f'Error in compute resource post api request for {url}; {e}')
#         raise
#     return resp.json()

def _compute_resource_put_api_request(*,
    url_path: str,
    compute_resource_id: str,
    compute_resource_private_key: str,
    data: dict
):
    payload = url_path
    signature = _sign_message_str(payload, compute_resource_id, compute_resource_private_key)

    headers = {
        'compute-resource-id': compute_resource_id,
        'compute-resource-payload': payload,
        'compute-resource-signature': signature
    }

    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.put(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in compute resource put api request for {url}; {e}')
        raise
    return resp.json()

def _processor_get_api_request(*,
    url_path: str,
    headers: dict
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in processor get api request for {url}; {e}')
        raise
    return resp.json()

def _processor_put_api_request(*,
    url_path: str,
    headers: dict,
    data: dict
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.put(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in processor put api request for {url}; {e}')
        raise
    return resp.json()

def _client_get_api_request(*,
    url_path: str
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in client get api request for {url}; {e}')
        raise
    return resp.json()

def _client_post_api_request(*,
    url_path: str,
    data: dict,
    dendro_api_key: str
):
    headers = {
        'dendro-api-key': dendro_api_key
    }
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f'Error in client post api request for {url}; {e}')
        raise
    return resp.json()

####################################################################################################
# The GUI API requests below are only here for use with pytest since the real GUI requests come from the browser using typescript

def _gui_get_api_request(*,
    url_path: str,
    github_access_token: str
):
    headers = {
        'github-access-token': github_access_token
    }
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in gui get api request for {url}')
        raise
    return resp.json()

def _gui_post_api_request(*,
    url_path: str,
    github_access_token: str,
    data: dict
):
    headers = {
        'github-access-token': github_access_token
    }
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in gui post api request for {url}')
        raise
    return resp.json()

def _gui_put_api_request(*,
    url_path: str,
    github_access_token: str,
    data: dict
):
    headers = {
        'github-access-token': github_access_token
    }
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.put(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in gui put api request for {url}')
        raise
    return resp.json()

def _gui_delete_api_request(*,
    url_path: str,
    github_access_token: str
):
    headers = {
        'github-access-token': github_access_token
    }
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{dendro_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.delete(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in gui delete api request for {url}')
        raise
    return resp.json()
