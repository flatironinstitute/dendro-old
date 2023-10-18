import os
import json
import aiohttp
import urllib.parse
from ..core.settings import get_settings

async def publish_pubsub_message(*, channel: str, message: dict):
    settings = get_settings()
    # see https://www.pubnub.com/docs/sdks/rest-api/publish-message-to-channel
    sub_key = settings.PUBNUB_SUBSCRIBE_KEY
    pub_key = settings.PUBNUB_PUBLISH_KEY
    uuid = 'protocaas'
    # payload is url encoded json
    payload = json.dumps(message)
    payload = urllib.parse.quote(payload)
    url = f"https://ps.pndsn.com/publish/{pub_key}/{sub_key}/0/{channel}/0/{payload}?uuid={uuid}"

    headers = {
    'Accept': 'application/json'
    }

    # async http get request
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"Error publishing to pubsub: {resp.status} {resp.text}")
            return True