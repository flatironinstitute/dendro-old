import { FunctionComponent, useCallback, useEffect, useReducer, useState } from "react"
import { useGithubAuth } from "../GithubAuth/useGithubAuth"
import { createDendroApiKeyForUser } from "../dbInterface/dbInterface"
import UserIdComponent from "../UserIdComponent"
import { confirm } from "../confirm_prompt_alert"
import { Hyperlink } from "@hodj/misc"

type ApiKeysWindowProps = {
    onClose: () => void
}

type KeysState = {
    dandiApiKey: string
    dandiStagingApiKey: string
}

const defaultKeysState: KeysState = {
    dandiApiKey: '',
    dandiStagingApiKey: ''
}

type KeysAction = {
    type: 'setDandiApiKey' | 'setDandiStagingApiKey'
    value: string
}

const keysReducer = (state: KeysState, action: KeysAction): KeysState => {
    switch (action.type) {
        case 'setDandiApiKey':
            return {...state, dandiApiKey: action.value}
        case 'setDandiStagingApiKey':
            return {...state, dandiStagingApiKey: action.value}
        default:
            throw new Error('invalid action type')
    }
}

const ApiKeysWindow: FunctionComponent<ApiKeysWindowProps> = ({onClose}) => {
    const [keys, keysDispatch] = useReducer(keysReducer, defaultKeysState)
    useEffect(() => {
        // initialize from local storage
        const dandiApiKey = localStorage.getItem('dandiApiKey') || ''
        const dandiStagingApiKey = localStorage.getItem('dandiStagingApiKey') || ''
        keysDispatch({type: 'setDandiApiKey', value: dandiApiKey})
        keysDispatch({type: 'setDandiStagingApiKey', value: dandiStagingApiKey})
    }, [])
    const auth = useGithubAuth()

    const handleSaveDandiApiKey = useCallback(() => {
        localStorage.setItem('dandiApiKey', keys.dandiApiKey)
    }, [keys.dandiApiKey])

    const handleSaveDandiStagingApiKey = useCallback(() => {
        localStorage.setItem('dandiStagingApiKey', keys.dandiStagingApiKey)
    }, [keys.dandiStagingApiKey])

    const [newDendroApiKey, setNewDendroApiKey] = useState<string>('')
    const handleGenerateDendroApiKey = useCallback(async () => {
        const okay = await confirm('Are you sure you want to generate a new Dendro API key? Any previously generated keys will be revoked.')
        if (!okay) return
        const apiKey = await createDendroApiKeyForUser(auth)
        setNewDendroApiKey(apiKey)
    }, [auth])

    return (
        <div style={{padding: 30}}>
            <h3>Set API Keys</h3>
            <hr />
            <table className="table-1" style={{maxWidth: 500}}>
                <tbody>
                    <tr>
                        <td>DANDI API Key: </td>
                        <td><input type="password" value={keys.dandiApiKey} onChange={e => keysDispatch({type: 'setDandiApiKey', value: e.target.value})} /></td>
                        <td><button onClick={handleSaveDandiApiKey}>Save</button></td>
                    </tr>
                    <tr>
                        <td>DANDI Staging API Key: </td>
                        <td><input type="password" value={keys.dandiStagingApiKey} onChange={e => keysDispatch({type: 'setDandiStagingApiKey', value: e.target.value})} /></td>
                        <td><button onClick={handleSaveDandiStagingApiKey}>Save</button></td>
                    </tr>
                </tbody>
            </table>
            <hr />
            {auth.userId && !newDendroApiKey && (
                <Hyperlink onClick={handleGenerateDendroApiKey}>Re-generate Dendro API key for user <UserIdComponent userId={auth.userId} /></Hyperlink>
            )}
            {newDendroApiKey && (
                <div>
                    <p>Here is the new Dendro API key for your user. Save it somewhere safe. Any previously generated keys have been revoked.</p>
                    <p>{newDendroApiKey}</p>
                </div>
            )}
            <hr />
            <div>
                <button onClick={onClose}>Close</button>
            </div>
        </div>
    )
}

export default ApiKeysWindow