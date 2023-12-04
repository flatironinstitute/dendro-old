import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useModalWindow } from "@hodj/modal-window"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { Hyperlink } from "@hodj/misc";
import ModalWindow from "@hodj/modal-window";
import { App, fetchComputeResource, setComputeResourceApps } from "../../../dbInterface/dbInterface"
import { DendroComputeResource } from "../../../types/dendro-types"
import NewAppWindow from "../../ComputeResourcePage/NewAppWindow"
import { Checkbox, selectedStringsReducer } from "../FileBrowser/FileBrowser2"
import ComputeResourceAppsTableMenuBar2 from "./ComputeResourceAppsTableMenuBar2"

type Props = {
    computeResourceId: string
}

const menuBarHeight = 30
// const hPadding = 20
const vPadding = 5

const ComputeResourceAppsTable2: FunctionComponent<Props> = ({computeResourceId}) => {
    const [computeResource, setComputeResources] = useState<DendroComputeResource>()
    const [refreshCode, setRefreshCode] = useState(0)
    const refreshComputeResource = useCallback(() => {
        setRefreshCode(c => c + 1)
    }, [])

    const [selectedAppNames, selectedAppNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const {visible: newAppWindowVisible, handleOpen: openNewAppWindow, handleClose: closeNewAppWindow} = useModalWindow()
    const {visible: editAppWindowVisible, handleOpen: openEditAppWindow, handleClose: closeEditAppWindow} = useModalWindow()

    const auth = useGithubAuth()

    const isComputeResourceAdmin = computeResource?.ownerId && (computeResource?.ownerId === auth.userId)

    useEffect(() => {
        let canceled = false
        ;(async () => {
            const cr = await fetchComputeResource(computeResourceId, auth)
            if (canceled) return
            setComputeResources(cr)
        })()
        return () => {canceled = true}
    }, [computeResourceId, auth, refreshCode])

    const onAppClicked = useCallback((appName: string) => {
        // TODO
    }, [])

    const handleNewApp = useCallback((name: string, specUri: string) => {
        if (!computeResource) return
        const oldApps = computeResource.apps
        const newApps: App[] = [...oldApps.filter(a => (a.name !== name)), {name, specUri}]
        setComputeResourceApps(computeResource.computeResourceId, newApps, auth).then(() => {
            refreshComputeResource()
        })
    }, [computeResource, refreshComputeResource, auth])

    const handleDeleteApps = useCallback((appNames: string[]) => {
        if (!computeResource) return
        const oldApps = computeResource.apps
        const newApps = oldApps.filter(a => !appNames.includes(a.name))
        setComputeResourceApps(computeResource.computeResourceId, newApps, auth).then(() => {
            refreshComputeResource()
        })
    }, [computeResource, refreshComputeResource, auth])

    const colWidth = 15

    const selectedAppForEditing = useMemo(() => {
        if (selectedAppNames.size !== 1) return undefined
        if (!computeResource) return undefined
        const appName = selectedAppNames.values().next().value
        return computeResource.apps.find(a => (a.name === appName))
    }, [selectedAppNames, computeResource])

    return (
        <div>
            {
                isComputeResourceAdmin && (
                    <div style={{position: 'relative', height: menuBarHeight - vPadding * 2, paddingTop: vPadding, paddingBottom: vPadding}}>
                        <ComputeResourceAppsTableMenuBar2
                            selectedAppNames={Array.from(selectedAppNames)}
                            onAddApp={openNewAppWindow}
                            onDeleteApps={handleDeleteApps}
                            onEditApp={openEditAppWindow}
                        />
                    </div>
                )
            }
            <div style={{position: 'relative'}}>
                <table className="scientific-table" style={{fontSize: 12}}>
                    <thead>
                        <tr>
                            <th style={{width: colWidth}} />
                            <th>App</th>
                            <th>Spec URI</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            computeResource?.apps.map((app) => (
                                <tr key={app.name}>
                                    <td style={{width: colWidth}}>
                                        <Checkbox checked={selectedAppNames.has(app.name)} onClick={() => selectedAppNamesDispatch({type: 'toggle', value: app.name})} />
                                    </td>
                                    <td>
                                        <Hyperlink onClick={() => onAppClicked(app.name)}>
                                            {app.name}
                                        </Hyperlink>
                                    </td>
                                    <td>
                                        {app.specUri || ''}
                                    </td>
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
            <ModalWindow
                visible={newAppWindowVisible}
                onClose={closeNewAppWindow}
            >
                {computeResource && <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri) => {closeNewAppWindow(); handleNewApp(name, specUri);}}
                />}
            </ModalWindow>
            <ModalWindow
                visible={editAppWindowVisible}
                onClose={closeEditAppWindow}
            >
                {computeResource && <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri) => {closeEditAppWindow(); handleNewApp(name, specUri);}}
                    appBeingEdited={selectedAppForEditing}
                />}
            </ModalWindow>
        </div>
    )
}

export default ComputeResourceAppsTable2