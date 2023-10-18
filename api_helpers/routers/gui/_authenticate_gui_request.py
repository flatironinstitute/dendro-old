import time
import aiohttp


_user_ids_for_access_tokens = {} # github access token -> {user_id: string, timestamp: float}

async def _authenticate_gui_request(github_access_token: str):
    if not github_access_token:
        return None
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

async def _get_user_id_for_access_token(github_access_token: str):
    url = 'https://api.github.com/user'
    headers = {
        'Authorization': f'token {github_access_token}'
    }
    # do async request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                raise Exception(f'Error getting user ID from github access token: {response.status}')
            data = await response.json()
            return data['login']