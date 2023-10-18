from typing import List
import queue
from pubnub.pnconfiguration import PNConfiguration
from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub import PubNub

class MySubscribeCallback(SubscribeCallback):
    def __init__(self, message_queue: queue.Queue, compute_resource_id: str):
        self._message_queue = message_queue
        self._compute_resource_id = compute_resource_id
    def message(self, pubnub, message):
        msg = message.message
        if msg.get('computeResourceId', None) == self._compute_resource_id:
            self._message_queue.put(msg)

class PubsubClient:
    def __init__(self, *,
        pubnub_subscribe_key: str,
        pubnub_channel: str,
        pubnub_user: str,
        compute_resource_id: str
    ):
        self._message_queue = queue.Queue()
        pnconfig = PNConfiguration()
        pnconfig.subscribe_key = pubnub_subscribe_key
        pnconfig.user_id = pubnub_user
        pubnub = PubNub(pnconfig)
        pubnub.add_listener(MySubscribeCallback(message_queue=self._message_queue, compute_resource_id=compute_resource_id))
        pubnub.subscribe().channels([pubnub_channel]).execute()
    def take_messages(self) -> List[dict]:
        ret = []
        while True:
            try:
                msg = self._message_queue.get(block=False)
                ret.append(msg)
            except queue.Empty:
                break
        return ret
