from typing import List, Union
import time
import aiohttp
import uuid
from ..common import AuthException
from ...clients.db import fetch_user_for_dendro_api_key


_user_ids_for_github_access_tokens = {} # github access token -> {user_id: string, timestamp: float}
_user_ids_for_dendro_api_keys = {} # dendro api key -> {user_id: string, timestamp: float}

_mock_github_access_tokens: List[str] = []
def _create_mock_github_access_token():
    token = 'mock:' + str(uuid.uuid4())
    _mock_github_access_tokens.append(token)
    return token

async def _authenticate_gui_request(*,
    github_access_token: Union[str, None] = None,
    dendro_api_key: Union[str, None] = None,
    raise_on_not_authenticated: bool
) -> Union[str, None]:
    try:
        if github_access_token:
            if github_access_token in _user_ids_for_github_access_tokens:
                a = _user_ids_for_github_access_tokens[github_access_token]
                elapsed = time.time() - a['timestamp']
                if elapsed > 60 * 60: # one hour
                    del _user_ids_for_github_access_tokens[github_access_token] # pragma: no cover
                else:
                    return a['user_id']
            if not github_access_token.startswith('mock:'):
                user_id = await _get_user_id_for_access_token(github_access_token)
                if not user_id:
                    raise AuthException('Invalid github access token')
                user_id = 'github|' + user_id # pragma: no cover
            else:
                if github_access_token not in _mock_github_access_tokens:
                    raise AuthException('Invalid mock github access token')
                user_id = 'github|' + github_access_token[len('mock:'):]
            _user_ids_for_github_access_tokens[github_access_token] = {
                'user_id': user_id,
                'timestamp': time.time()
            }
            return user_id
        elif dendro_api_key:
            if dendro_api_key in _user_ids_for_dendro_api_keys:
                a = _user_ids_for_dendro_api_keys[dendro_api_key]
                elapsed = time.time() - a['timestamp']
                if elapsed > 60 * 1: # one minute (the api key might get revoked so we don't want to cache it for too long)
                    del _user_ids_for_dendro_api_keys[dendro_api_key]
                else:
                    return a['user_id']
            user = await fetch_user_for_dendro_api_key(dendro_api_key)
            assert user.dendroApiKey == dendro_api_key
            assert user.userId
            user_id = user.userId
            _user_ids_for_dendro_api_keys[dendro_api_key] = {
                'user_id': user_id,
                'timestamp': time.time()
            }
            return user_id
        else:
            raise AuthException('User is not authenticated')
    except AuthException as e:
        if raise_on_not_authenticated:
            raise e
        else:
            return None

async def _get_user_id_for_access_token(github_access_token: str):
    url = 'https://api.github.com/user'
    headers = {
        'Authorization': f'token {github_access_token}'
    }
    # do async request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise AuthException(f'Error getting user ID from github access token: {response.status}')
            data = await response.json() # pragma: no cover
            return data['login'] # pragma: no cover
