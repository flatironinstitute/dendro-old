import os
import requests
from ._crypto_keys import _sign_message_str

protocaas_url = os.getenv('PROTOCAAS_URL', 'https://protocaas.vercel.app')

def _compute_resource_get_api_request(*,
    url_path: str,
    compute_resource_id: str,
    compute_resource_private_key: str,
    compute_resource_node_name: str,
    compute_resource_node_id: str
):
    payload = url_path
    signature = _sign_message_str(payload, compute_resource_id, compute_resource_private_key)

    headers = {
        'compute-resource-id': compute_resource_id,
        'compute-resource-payload': payload,
        'compute-resource-signature': signature,
        'compute-resource-node-name': compute_resource_node_name,
        'compute-resource-node-id': compute_resource_node_id
    }

    url = f'{protocaas_url}{url_path}'
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'Error getting {url}: {resp.status_code} {resp.text}')
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

    url = f'{protocaas_url}{url_path}'
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code != 200:
        raise Exception(f'Error posting {url}: {resp.status_code} {resp.text}')
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

    url = f'{protocaas_url}{url_path}'
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code != 200:
        raise Exception(f'Error putting {url}: {resp.status_code} {resp.text}')
    return resp.json()

def _processor_get_api_request(*,
    url_path: str,
    headers: dict
):
    url = f'{protocaas_url}{url_path}'
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f'Error getting {url}: {resp.status_code} {resp.text}')
    return resp.json()

def _processor_put_api_request(*,
    url_path: str,
    headers: dict,
    data: dict
):
    url = f'{protocaas_url}{url_path}'
    resp = requests.put(url, headers=headers, json=data)
    if resp.status_code != 200:
        raise Exception(f'Error putting {url}: {resp.status_code} {resp.text}')
    return resp.json()

def _client_get_api_request(*,
    url_path: str
):
    url = f'{protocaas_url}{url_path}'
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f'Error getting {url}: {resp.status_code} {resp.text}')
    return resp.json()