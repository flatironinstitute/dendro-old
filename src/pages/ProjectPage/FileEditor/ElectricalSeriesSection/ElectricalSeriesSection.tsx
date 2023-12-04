import { FunctionComponent, useCallback, useState } from "react"
import { useElectricalSeriesPaths, useNwbFile } from "../NwbFileEditor"
import { Hyperlink } from "@hodj/misc";
import ModalWindow from "@hodj/modal-window";
import { useModalWindow } from "@hodj/modal-window"
import { useProject } from "../../ProjectPageContext"
import LoadElectricalSeriesScriptWindow from "./LoadElectricalSeriesScriptWindow"

type ElectricalSeriesSectionProps = {
    fileName: string
    nwbUrl?: string
}

const ElectricalSeriesSection: FunctionComponent<ElectricalSeriesSectionProps> = ({fileName, nwbUrl}) => {
    const nwbFile = useNwbFile(nwbUrl)
    const electricalSeriesPaths = useElectricalSeriesPaths(nwbFile)
    const [selectedElectricalSeriesPath, setSelectedElectricalSeriesPath] = useState<string>('')
    const {visible: loadInScriptVisible, handleOpen: openLoadInScriptWindow, handleClose: closeLoadInScriptWindow} = useModalWindow()
    const {project} = useProject()
    const loadInScript = useCallback((path: string) => {
        setSelectedElectricalSeriesPath(path)
        openLoadInScriptWindow()
    }, [openLoadInScriptWindow])
    if ((!electricalSeriesPaths) || (electricalSeriesPaths.length === 0)) return (
        <></>
    )
    return (
        <div>
            <p>
                <b>Electrical series:</b> {fileName}
            </p>
            <ul>
                {
                    electricalSeriesPaths.map((path, ii) => (
                        <li key={ii}>
                            {path} - <Hyperlink onClick={() => loadInScript(path)}>load in script</Hyperlink>
                        </li>
                    ))
                }
            </ul>
            <ModalWindow
                visible={loadInScriptVisible}
                onClose={closeLoadInScriptWindow}
            >
                {selectedElectricalSeriesPath && project && fileName && (
                    <LoadElectricalSeriesScriptWindow
                        project={project}
                        electricalSeriesPath={selectedElectricalSeriesPath}
                        fileName={fileName}
                        onClose={closeLoadInScriptWindow}
                    />
                )}
            </ModalWindow>
        </div>
    )
}

export default ElectricalSeriesSection