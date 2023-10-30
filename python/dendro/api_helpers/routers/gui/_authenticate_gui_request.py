from typing import List
import time
import aiohttp
import uuid


_user_ids_for_access_tokens = {} # github access token -> {user_id: string, timestamp: float}

_mock_github_access_tokens: List[str] = []
def _create_mock_github_access_token():
    token = 'mock:' + str(uuid.uuid4())
    _mock_github_access_tokens.append(token)
    return token

async def _authenticate_gui_request(github_access_token: str, raise_on_not_authenticated=False):
    if github_access_token.startswith('mock:'):
        if github_access_token not in _mock_github_access_tokens:
            raise AuthException('Invalid mock github access token')
        return 'github|__mock__user'
    if not github_access_token:
        raise AuthException('User is not authenticated')
    if github_access_token in _user_ids_for_access_tokens:
        a = _user_ids_for_access_tokens[github_access_token]
        elapsed = time.time() - a['timestamp']
        if elapsed > 60 * 60: # one hour
            del _user_ids_for_access_tokens[github_access_token]
        else:
            return a['user_id']
    user_id = await _get_user_id_for_access_token(github_access_token)
    user_id = 'github|' + user_id
    _user_ids_for_access_tokens[github_access_token] = {
        'user_id': user_id,
        'timestamp': time.time()
    }
    return user_id

class AuthException(Exception):
    pass

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
            data = await response.json()
            return data['login']
