import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { Checkbox, selectedStringsReducer } from "../FileBrowser/FileBrowser2"
import { useModalDialog } from "../../../ApplicationBar"
import { ComputeResourceAwsBatchOpts, ComputeResourceSlurmOpts, DendroComputeResource } from "../../../types/dendro-types"
import { App, fetchComputeResource, setComputeResourceApps } from "../../../dbInterface/dbInterface"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import ComputeResourceAppsTableMenuBar2 from "./ComputeResourceAppsTableMenuBar2"
import Hyperlink from "../../../components/Hyperlink"
import ModalWindow from "../../../components/ModalWindow/ModalWindow"
import NewAppWindow from "../../ComputeResourcePage/NewAppWindow"

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

    const {visible: newAppWindowVisible, handleOpen: openNewAppWindow, handleClose: closeNewAppWindow} = useModalDialog()
    const {visible: editAppWindowVisible, handleOpen: openEditAppWindow, handleClose: closeEditAppWindow} = useModalDialog()

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

    const handleNewApp = useCallback((name: string, specUri: string, awsBatch?: ComputeResourceAwsBatchOpts, slurm?: ComputeResourceSlurmOpts) => {
        if (!computeResource) return
        const oldApps = computeResource.apps
        const newApps: App[] = [...oldApps.filter(a => (a.name !== name)), {name, specUri, awsBatch, slurm}]
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
                            <th>AWS Batch</th>
                            <th>Slurm</th>
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
                                    <td>
                                        {app.awsBatch ? `Using AWS Batch: ${app.awsBatch.useAwsBatch ? "true" : "false"}` : ''}
                                    </td>
                                    <td>
                                        {app.slurm ? (
                                            <span>
                                                <span>{app.slurm.cpusPerTask ? `CPUs per task: ${app.slurm.cpusPerTask}` : ''}</span>
                                                &nbsp;
                                                <span>{app.slurm.partition ? `Partition: ${app.slurm.partition}` : ''}</span>
                                                &nbsp;
                                                <span>{app.slurm.time ? `Time: ${app.slurm.time}` : ''}</span>
                                                &nbsp;
                                                <span>{app.slurm.otherOpts ? `Other options: ${app.slurm.otherOpts}` : ''}</span>
                                            </span>
                                        ) : ''}
                                    </td>
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
            <ModalWindow
                open={newAppWindowVisible}
                onClose={closeNewAppWindow}
            >
                {computeResource && <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri, awsBatch, slurmOpts) => {closeNewAppWindow(); handleNewApp(name, specUri, awsBatch, slurmOpts);}}
                />}
            </ModalWindow>
            <ModalWindow
                open={editAppWindowVisible}
                onClose={closeEditAppWindow}
            >
                {computeResource && <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri, awsBatch, slurmOpts) => {closeEditAppWindow(); handleNewApp(name, specUri, awsBatch, slurmOpts);}}
                    appBeingEdited={selectedAppForEditing}
                />}
            </ModalWindow>
        </div>
    )
}

export default ComputeResourceAppsTable2