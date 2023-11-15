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
        pnconfig.subscribe_key = pubnub_subscribe_key # type: ignore (not sure why we need to type ignore this)
        pnconfig.user_id = pubnub_user
        self._pubnub = PubNub(pnconfig)
        self._listener = MySubscribeCallback(message_queue=self._message_queue, compute_resource_id=compute_resource_id)
        self._pubnub.add_listener(self._listener)
        self._pubnub.subscribe().channels([pubnub_channel]).execute()
    def take_messages(self) -> List[dict]:
        ret = []
        while True:
            try:
                msg = self._message_queue.get(block=False)
                ret.append(msg)
            except queue.Empty:
                break
        return ret
    def close(self):
        self._pubnub.unsubscribe_all()
        self._pubnub.stop()
        self._pubnub.remove_listener(self._listener)
        # unfortunately this doesn't actually kill the thread
        # I submitted a ticket to pubnub about this
        # and they acknowledged that it's a problem
        # but they don't seem to be fixing it
