import { Hyperlink, SmallIconButton } from "@fi-sci/misc"
import { Save, Square } from "@mui/icons-material"
import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File"
import { DendroProcessingJobDefinition, DendroProcessingJobDefinitionAction, createFileAndInitiateUpload } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecProcessor } from "../../../types/dendro-types"
import EditJobDefinitionWindow from "../EditJobDefinitionWindow/EditJobDefinitionWindow"
import ModalWindow, { useModalWindow } from "@fi-sci/modal-window"
import { useProject } from "../ProjectPageContext"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { fetchTextFile } from "../FileView/OtherFileView"


type RightColumnProps = {
    width: number
    height: number
    processor?: ComputeResourceSpecProcessor
    operating: boolean
    valid: boolean
    setValid: (val: boolean) => void
    jobDefinition: DendroProcessingJobDefinition
    jobDefinitionDispatch: React.Dispatch<DendroProcessingJobDefinitionAction>
    representativeNwbFile?: RemoteH5File
    processorName: string
}

type SaveParametersBarProps = {
    jobDefinition: DendroProcessingJobDefinition
    processor?: ComputeResourceSpecProcessor
    onLoadParameters?: (parameterSetName: string, inputParameters: {name: string, value: any}[]) => void
    usingParameterSetName?: string
}

export const SaveParametersBar: FunctionComponent<SaveParametersBarProps> = ({jobDefinition, processor, onLoadParameters, usingParameterSetName}) => {
    const {visible: saveParametersVisible, handleOpen: openSaveParameters, handleClose: closeSaveParameters} = useModalWindow()
    const {visible: loadParametersVisible, handleOpen: openLoadParameters, handleClose: closeLoadParameters} = useModalWindow()
    return (
        <div>
            <SmallIconButton icon={<Save />} onClick={openSaveParameters} label="Save parameters" />
            &nbsp;&nbsp;
            {onLoadParameters && <SmallIconButton icon={<Square />} onClick={openLoadParameters} label="Load parameters" />}
            &nbsp;&nbsp;
            {usingParameterSetName && <span style={{color: '#733'}}>Using parameter set: {usingParameterSetName}</span>}
            <ModalWindow
                visible={saveParametersVisible}
                onClose={closeSaveParameters}
            >
                <SaveParametersWindow
                    jobDefinition={jobDefinition}
                    processor={processor}
                    onClose={closeSaveParameters}
                />
            </ModalWindow>
            <ModalWindow
                visible={loadParametersVisible}
                onClose={closeLoadParameters}
            >
                {onLoadParameters && <LoadParametersWindow
                    onLoad={(parameterSetName: string, inputParameters: {name: string, value: any}[]) => {
                        if (!onLoadParameters) return
                        onLoadParameters(parameterSetName, inputParameters)
                        closeLoadParameters()
                    }}
                    onClose={closeLoadParameters}
                />}
            </ModalWindow>
        </div>
    )
}

type LoadParametersWindowProps = {
    onLoad: (parameterSetName: string, inputParameters: {name: string, value: any}[]) => void
    onClose: () => void
}

const LoadParametersWindow: FunctionComponent<LoadParametersWindowProps> = ({onLoad, onClose}) => {
    const {files} = useProject()
    const candidateParameterSetNames = useMemo(() => {
        if (!files) return []
        const filesFiltered = files.filter(f => (f.fileName.startsWith('parameter-sets/') && f.fileName.endsWith('.json')))
        return filesFiltered.map(f => f.fileName.slice('parameter-sets/'.length).slice(0, -'.json'.length))
    }, [files])
    const handleLoadParameters = useCallback(async (name: string) => {
        const fileName = `parameter-sets/${name}.json`
        const file = files?.find(f => f.fileName === fileName)
        if (!file) {
            alert(`File not found: ${fileName}`)
            return
        }
        if (!file.content.startsWith('url:')) {
            console.warn('Unexpected file content: ' + file.content)
            return
        }
        let canceled = false
        const u = await fetchTextFile(file.content.slice('url:'.length))
        if (canceled) return
        const xx = JSON.parse(u)
        if ((!xx.inputParameters) || !Array.isArray(xx.inputParameters)) {
            alert(`Unexpected file content for ${fileName}`)
            return
        }
        for (const aaa of xx.inputParameters) {
            if ((typeof aaa.name !== 'string')) {
                alert(`Unexpected file content for ${fileName}`)
                return
            }
        }
        onLoad(name, xx.inputParameters)
        return () => {canceled = true}
    }, [files, onLoad])
    if (!candidateParameterSetNames) {
        return <div>No parameter sets found</div>
    }
    return (
        <div>
            <h3>Load parameters</h3>
            <div>From project file:</div>
            <ul>
                {
                    candidateParameterSetNames.map(name => (
                        <li key={name}>
                            <Hyperlink onClick={() => {handleLoadParameters(name)}}>{name}</Hyperlink>
                        </li>
                    ))
                }
            </ul>
            <div>Or upload .json file from computer:&nbsp;
                <input type="file" onChange={e => {
                    if (!e.target.files) return
                    const file = e.target.files[0]
                    const reader = new FileReader()
                    reader.onload = () => {
                        const text = reader.result as string
                        const xx = JSON.parse(text)
                        if ((!xx.inputParameters) || !Array.isArray(xx.inputParameters)) {
                            alert(`Unexpected file content`)
                            return
                        }
                        for (const aaa of xx.inputParameters) {
                            if ((typeof aaa.name !== 'string')) {
                                alert(`Unexpected file content`)
                                return
                            }
                        }
                        onLoad(file.name, xx.inputParameters)
                    }
                    reader.readAsText(file)
                }} />
            </div>
            <hr />
            <button onClick={onClose}>Cancel</button>
        </div>
    )
}

const RightColumn: FunctionComponent<RightColumnProps> = ({
    width, height,
    operating, processor, setValid,
    jobDefinition,
    jobDefinitionDispatch,
    representativeNwbFile,
    processorName
}) => {
    const [usingParameterSetState, setUsingParameterSetState] = useState<{parameterSetName: string, inputParameters: {name: string, value: any}[]} | undefined>(undefined)
    useEffect(() => {
        if (!usingParameterSetState) return
        if (!inputParametersMatch(jobDefinition.inputParameters, usingParameterSetState.inputParameters)) {
            setUsingParameterSetState(undefined)
        }
    }, [usingParameterSetState, jobDefinition.inputParameters])
    useEffect(() => {
    }, [jobDefinition])
    useEffect(() => {
    }, [processor])
    useEffect(() => {
    }, [representativeNwbFile])
    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Sorting parameters for {processorName}</h3>
            <div>
                <SaveParametersBar
                    jobDefinition={jobDefinition}
                    processor={processor}
                    onLoadParameters={(parameterSetName, inputParameters) => {
                        jobDefinitionDispatch({
                            type: 'setInputParameters',
                            inputParameters
                        })
                        setTimeout(() => { // this is indeed a hack and a race condition, but we want to make sure the job definition is updated before we set the usingParameterSetName
                            setUsingParameterSetState({
                                parameterSetName,
                                inputParameters
                            })
                        }, 500)
                    }}
                    usingParameterSetName={usingParameterSetState?.parameterSetName}
                />
            </div>
            {processor && (
                <EditJobDefinitionWindow
                    jobDefinition={jobDefinition}
                    jobDefinitionDispatch={jobDefinitionDispatch}
                    processor={processor}
                    nwbFile={representativeNwbFile}
                    setValid={setValid}
                    readOnly={operating}
                />
            )}
        </div>
    )
}

type SaveParametersProps = {
    jobDefinition: DendroProcessingJobDefinition
    processor?: ComputeResourceSpecProcessor
    onClose: () => void
}

const SaveParametersWindow: FunctionComponent<SaveParametersProps> = ({jobDefinition, processor, onClose}) => {
    const [parameterSetName, setParameterSetName] = useState('')
    const {projectId, refreshFiles, files} = useProject()
    const auth = useGithubAuth()
    const projectFileName = `parameter-sets/${parameterSetName}.json`
    const projectFileAlreadyExists = useMemo(() => (
        files && files.find(f => f.fileName === projectFileName)
    ), [files, projectFileName])
    const parameterSetJsonText = useMemo(() => {
        if (!processor) return undefined
        const parameterSetJson = {
            type: 'dendro-parameter-set',
            version: 1,
            processorName: jobDefinition.processorName,
            inputParameters: jobDefinition.inputParameters,
            processorSpecParameters: processor.parameters
        }
        return JSON.stringify(parameterSetJson, null, 4)
    }, [jobDefinition, processor])
    const handleSaveToProject = useCallback(() => {
        if (!parameterSetJsonText) return
        if (!auth) return

        if (projectFileAlreadyExists) {
            const ok = window.confirm(`Parameter set already exists. Overwrite?`)
            if (!ok) return
        }

        (async () => {
            const {uploadUrl} = await createFileAndInitiateUpload(
                projectId,
                projectFileName,
                parameterSetJsonText.length,
                auth
            )
            const uploadRequest = new XMLHttpRequest()
            uploadRequest.open("PUT", uploadUrl)
            uploadRequest.setRequestHeader("Content-Type", "application/octet-stream")
            uploadRequest.send(parameterSetJsonText)
            uploadRequest.addEventListener("load", () => {
                refreshFiles()
                onClose()
            })
            uploadRequest.addEventListener("error", (e) => {
                console.error(e)
                alert("Upload failed")
            }, {once: true})
        })()

        onClose()
    }, [parameterSetJsonText, projectFileAlreadyExists, projectId, projectFileName, auth, refreshFiles, onClose])
    const handleSaveToJson = useCallback(() => {
        if (!parameterSetJsonText) return
        downloadTextFile(parameterSetJsonText, `${parameterSetName}.json`)
    }, [parameterSetJsonText, parameterSetName])
    const isValidParameterSetName = useMemo(() => {
        if (!parameterSetName) return false
        if (!parameterSetName.match(/^[a-zA-Z0-9_.-]+$/)) return false
        if (parameterSetName.endsWith('.json')) return false
        return true
    },  [parameterSetName])
    return (
        <div>
            <h3>Save parameters</h3>
            <div>
                <label>Parameter set name: </label>
                <input type="text" value={parameterSetName} onChange={e => setParameterSetName(e.target.value)} />
                {!isValidParameterSetName && <span style={{color: 'red'}}>&nbsp;invalid name</span>}
            </div>
            <div>&nbsp;</div>
            <div>
                <button onClick={handleSaveToProject} disabled={!isValidParameterSetName}>Save to project</button>
                &nbsp;
                <button onClick={handleSaveToJson} disabled={!isValidParameterSetName}>Save to file</button>
                &nbsp;
                <button onClick={onClose}>Cancel</button>
            </div>
        </div>
    )
}

const inputParametersMatch = (a: {name: string, value: any}[], b: {name: string, value: any}[]) => {
    if (a.length !== b.length) return false
    for (let i = 0; i < a.length; i++) {
        const pp = b.find(p => (p.name === a[i].name))
        if (!pp) return false
        if (pp.value !== a[i].value) return false
    }
    return true
}

const downloadTextFile = (text: string, fileName: string) => {
    const element = document.createElement("a")
    const file = new Blob([text], {type: 'text/plain'})
    element.href = URL.createObjectURL(file)
    element.download = fileName
    document.body.appendChild(element) // Required for this to work in FireFox (according to gh copilot)
    element.click()
}

export default RightColumn