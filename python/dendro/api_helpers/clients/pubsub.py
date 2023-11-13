import json
import aiohttp
import urllib.parse
from ..core.settings import get_settings
from ...mock import using_mock


class PubsubError(Exception):
    pass

async def publish_pubsub_message(*, channel: str, message: dict):
    settings = get_settings()
    # see https://www.pubnub.com/docs/sdks/rest-api/publish-message-to-channel
    sub_key = settings.PUBNUB_SUBSCRIBE_KEY
    pub_key = settings.PUBNUB_PUBLISH_KEY
    uuid = 'dendro'
    # payload is url encoded json
    payload = json.dumps(message)
    payload = urllib.parse.quote(payload)
    url = f"https://ps.pndsn.com/publish/{pub_key}/{sub_key}/0/{channel}/0/{payload}?uuid={uuid}"

    headers = {
        'Accept': 'application/json'
    }

    if using_mock():
        # don't actually publish the message for the mock case
        return True

    # async http get request
    async with aiohttp.ClientSession() as session: # pragma: no cover
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                raise PubsubError(f"Error publishing to pubsub: {resp.status} {resp.text}")
            return True
