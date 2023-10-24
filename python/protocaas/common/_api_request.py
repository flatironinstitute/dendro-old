import os
from typing import Optional
import requests
from ._crypto_keys import _sign_message_str

protocaas_url = os.getenv('PROTOCAAS_URL', 'https://protocaas.vercel.app')

_globals = {
    'test_client': None
}
def _use_api_test_client(test_client):
    _globals['test_client'] = test_client

def _compute_resource_get_api_request(*,
    url_path: str,
    compute_resource_id: str,
    compute_resource_private_key: str,
    compute_resource_node_name: Optional[str],
    compute_resource_node_id: Optional[str]
):
    payload = url_path
    signature = _sign_message_str(payload, compute_resource_id, compute_resource_private_key)

    headers = {
        'compute-resource-id': compute_resource_id,
        'compute-resource-payload': payload,
        'compute-resource-signature': signature
    }
    if compute_resource_node_name is not None:
        headers['compute-resource-node-name'] = compute_resource_node_name
    if compute_resource_node_id is not None:
        headers['compute-resource-node-id'] = compute_resource_node_id

    test_client = _globals['test_client']
    if test_client is None:
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in compute resource get api request for {url}')
        raise
    return resp.json()

def _compute_resource_post_api_request(*,
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
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.post(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in compute resource post api request for {url}')
        raise
    return resp.json()

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
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.put(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in compute resource put api request for {url}')
        raise
    return resp.json()

def _processor_get_api_request(*,
    url_path: str,
    headers: dict
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, headers=headers, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in processor get api request for {url}')
        raise
    return resp.json()

def _processor_put_api_request(*,
    url_path: str,
    headers: dict,
    data: dict
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.put(url, headers=headers, json=data, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in processor put api request for {url}')
        raise
    return resp.json()

def _client_get_api_request(*,
    url_path: str
):
    test_client = _globals['test_client']
    if test_client is None:
        url = f'{protocaas_url}{url_path}'
        client = requests
    else:
        assert url_path.startswith('/api')
        url = url_path
        client = test_client
    try:
        resp = client.get(url, timeout=60)
        resp.raise_for_status()
    except: # noqa E722
        print(f'Error in client get api request for {url}')
        raise
    return resp.json()
