import PubNub from 'pubnub'

const PUBNUB_SUBSCRIBE_KEY = import.meta.env.VITE_PUBNUB_SUBSCRIBE_KEY

let pnClient: PubNub | undefined = undefined
if (PUBNUB_SUBSCRIBE_KEY) {
    pnClient = new PubNub({
        subscribeKey: PUBNUB_SUBSCRIBE_KEY,
        userId: 'browser'
    })
}
else {
    console.warn('PUBNUB_SUBSCRIBE_KEY not set. Not connecting to PubNub.')
}

export const onPubsubMessage = (callback: (message: any) => void) => {
    const listener = {
        message: (messageEvent: any) => {
            callback(messageEvent.message)
        }
    }
    if (pnClient) {   
        pnClient.addListener(listener)
    }
    const cancel = () => {
        if (pnClient) {
            pnClient.removeListener(listener)
        }
    }
    return cancel
}

export const setPubNubListenChannel = (channel: string) => {
    if (pnClient) {
        pnClient.unsubscribeAll()
        pnClient.subscribe({
            channels: [channel]
        })
    }
}