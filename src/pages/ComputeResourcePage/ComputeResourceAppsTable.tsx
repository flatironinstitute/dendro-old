import { FunctionComponent, useCallback, useMemo, useReducer } from "react"
import { useModalWindow } from "@fi-sci/modal-window"
import { Hyperlink } from "@fi-sci/misc";
import ModalWindow from "@fi-sci/modal-window";
import { DendroComputeResource } from "../../types/dendro-types"
import { Checkbox, selectedStringsReducer } from "../ProjectPage/FileBrowser/FileBrowser2"
import ComputeResourceAppsTableMenuBar from "./ComputeResourceAppsTableMenuBar"
import NewAppWindow from "./NewAppWindow"

type Props = {
    width: number
    height: number
    computeResource: DendroComputeResource
    onNewApp: (name: string, specUri: string) => void
    onEditApp: (name: string, specUri: string) => void
    onDeleteApps: (appNames: string[]) => void
}

const menuBarHeight = 30
const hPadding = 20
const vPadding = 5

const ComputeResourceAppsTable: FunctionComponent<Props> = ({width, height, computeResource, onNewApp, onEditApp, onDeleteApps}) => {
    const [selectedAppNames, selectedAppNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const {visible: newAppWindowVisible, handleOpen: openNewAppWindow, handleClose: closeNewAppWindow} = useModalWindow()
    const {visible: editAppWindowVisible, handleOpen: openEditAppWindow, handleClose: closeEditAppWindow} = useModalWindow()

    const onAppClicked = useCallback((appName: string) => {
        // TODO
    }, [])

    const colWidth = 15

    const selectedAppForEditing = useMemo(() => {
        if (selectedAppNames.size !== 1) return undefined
        const appName = selectedAppNames.values().next().value
        return computeResource.apps.find(a => (a.name === appName))
    }, [selectedAppNames, computeResource])

    return (
        <div style={{position: 'relative', width, height}}>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: menuBarHeight - vPadding * 2, paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <ComputeResourceAppsTableMenuBar
                    width={width - hPadding * 2}
                    height={menuBarHeight - vPadding * 2}
                    selectedAppNames={Array.from(selectedAppNames)}
                    onAddApp={openNewAppWindow}
                    onDeleteApps={onDeleteApps}
                    onEditApp={openEditAppWindow}
                />
            </div>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: height - menuBarHeight - vPadding * 2, top: menuBarHeight, overflowY: 'scroll', paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
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
                            computeResource.apps.map((app) => (
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
                <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri) => {closeNewAppWindow(); onNewApp(name, specUri);}}
                />
            </ModalWindow>
            <ModalWindow
                visible={editAppWindowVisible}
                onClose={closeEditAppWindow}
            >
                <NewAppWindow
                    computeResource={computeResource}
                    onNewApp={(name, specUri) => {closeEditAppWindow(); onEditApp(name, specUri);}}
                    appBeingEdited={selectedAppForEditing}
                />
            </ModalWindow>
        </div>
    )
}

export default ComputeResourceAppsTable