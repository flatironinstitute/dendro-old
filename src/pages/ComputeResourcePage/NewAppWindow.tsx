import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { App } from "../../dbInterface/dbInterface"
import { DendroComputeResource } from "../../types/dendro-types"

type Props = {
    computeResource: DendroComputeResource
    onNewApp: (name: string, specUri: string) => void
    appBeingEdited?: App
}

const NewAppWindow: FunctionComponent<Props> = ({computeResource, onNewApp, appBeingEdited}) => {
    const [newAppName, setNewAppName] = useState('')
    const [newSpecUri, setNewSpecUri] = useState('')

    useEffect(() => {
        if (!appBeingEdited) return
        setNewAppName(appBeingEdited.name)
        setNewSpecUri(appBeingEdited.specUri || '')
    }, [appBeingEdited])
    
    const isValidAppName = useMemo(() => ((appName: string) => {
        if (!appName) return false
        if (!appBeingEdited) {
            if (computeResource.apps.find(a => a.name === appName)) return false
        }
        return true
    }), [computeResource, appBeingEdited])

    const isValid = useMemo(() => {
        if (!isValidAppName(newAppName)) return false
        if (!isValidSpecUri(newSpecUri)) return false
        return true
    }, [newAppName, newSpecUri, isValidAppName])

    return (
        <div style={{fontSize: 11}}>
            <h3>
                {
                    appBeingEdited ? (
                        <span>Edit app</span>
                    ) : (
                        <span>Add new app</span>
                    )
                }
            </h3>
            <hr />
            {/* Input field for the app name */}
            <div>
                <table>
                    <tbody>
                        <tr>
                            <td>App name</td>
                            <td>
                                {
                                    !appBeingEdited ? (
                                        <input type="text" id="new-app-name" value={newAppName} onChange={e => setNewAppName(e.target.value)} />
                                    ) : (
                                        <span>{newAppName}</span>
                                    )
                                }          
                                {/* Indicator on whether the app name is valid */}
                                &nbsp;&nbsp;
                                {
                                    isValidAppName(newAppName) ? (
                                        <span style={{color: 'green'}}>
                                            {/* Checkmark character */}
                                            &#10004;
                                        </span>
                                    ) : (
                                        <span style={{color: 'red'}}>
                                            {/* Cross character */}
                                            &#10008;
                                        </span>
                                    )
                                }
                            </td>
                        </tr>
                        <tr>
                            <td>Spec URI</td>
                            <td>
                                <input style={{width: 600}} type="text" id="new-spec-uri" value={newSpecUri} onChange={e => setNewSpecUri(e.target.value)} />                
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <br />
            <hr />
            {/* Indicator on whether the app is valid */}
            {
                isValid ? (
                    <span style={{color: 'green'}}>
                        {/* Checkmark character */}
                        &#10004;
                    </span>
                ) : (
                    <span style={{color: 'red'}}>
                        {/* Cross character */}
                        &#10008;
                    </span>
                )
            }
            <hr />
            <p style={{fontWeight: 'bold'}}>
                Important: for any changes to take effect, you must reload this page after saving the changes.
            </p>
            <div>&nbsp;</div>
            {/* Button to create the app */}
            <button disabled={!isValid} onClick={() => onNewApp(newAppName, newSpecUri)}>
                {
                    !appBeingEdited ? (
                        <span>Add new app</span>
                    ) : (
                        <span>Save changes</span>
                    )
                }
            </button>
        </div>
    )
}

const isValidSpecUri = (specUri: string) => {
    if (!specUri) return false
    if (specUri.startsWith('file://')) return true
    if (specUri.startsWith('http')) return true
    return false
}

export default NewAppWindow