from pydantic import BaseModel
from fastapi import APIRouter
import aiohttp
from ...core.settings import get_settings


router = APIRouter()

# github auth
class GithubAuthResponse(BaseModel):
    access_token: str

@router.get("/github_auth/{code}")
async def github_auth(code) -> GithubAuthResponse:
    settings = get_settings()
    GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
    GITHUB_CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET
    assert GITHUB_CLIENT_ID, 'Env var not set: VITE_GITHUB_CLIENT_ID'
    assert GITHUB_CLIENT_SECRET, 'Env var not set: VITE_GITHUB_CLIENT_SECRET'
    url = f'https://github.com/login/oauth/access_token?client_id={GITHUB_CLIENT_ID}&client_secret={GITHUB_CLIENT_SECRET}&code={code}'
    headers = {
        'accept': 'application/json'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            r = await resp.json()
            if 'access_token' not in r:
                print('No access_token in response from github auth')
                print(url)
                print(r)
                raise Exception(f'No access_token in response: {r.get("error")} ({r.get("error_description")}')
            return GithubAuthResponse(access_token=r['access_token'])
