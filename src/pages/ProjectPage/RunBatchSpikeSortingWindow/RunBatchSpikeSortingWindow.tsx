import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File"
import HBoxLayout from "../../../components/HBoxLayout"
import Hyperlink from "../../../components/Hyperlink"
import { DendroProcessingJobDefinition, DendroProcessingJobDefinitionAction, createJob, defaultJobDefinition, dendroJobDefinitionReducer, fetchFile } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecApp, ComputeResourceSpecProcessor, DendroComputeResourceApp, DendroFile, DendroJobRequiredResources } from "../../../types/dendro-types"
import EditJobDefinitionWindow from "../EditJobDefinitionWindow/EditJobDefinitionWindow"
import { useNwbFile } from "../FileEditor/NwbFileEditor"
import { useProject } from "../ProjectPageContext"
import RunMethodSelector from "./RunMethodSelector"

type Props = {
    filePaths: string[]
    onClose: () => void
    width: number
    height: number
}

const RunBatchSpikeSortingWindow: FunctionComponent<Props> = ({ filePaths, onClose, width, height }) => {
    const {projectId, files, projectRole, computeResource} = useProject()
    const auth = useGithubAuth()

    const [operating, setOperating] = useState(false)
    const [operatingMessage, setOperatingMessage] = useState<string | undefined>(undefined)

    const [selectedSpikeSortingProcessor, setSelectedSpikeSortingProcessor] = useState<string | undefined>(undefined)

    const spikeSorterProcessors = useMemo(() => {
        const ret: {appSpec: ComputeResourceSpecApp, app?: DendroComputeResourceApp, processor: ComputeResourceSpecProcessor}[] = []
        for (const appSpec of computeResource?.spec?.apps || []) {
            const app = computeResource?.apps.find(a => (a.name === appSpec.name))
            for (const p of appSpec.processors || []) {
                if (p.tags.map(t => t.tag).includes('spike_sorter')) {
                    ret.push({appSpec, app, processor: p})
                }
            }
        }
        return ret
    }, [computeResource])

    const processor = useMemo(() => {
        if (!selectedSpikeSortingProcessor) return undefined
        return spikeSorterProcessors.find(p => (p.processor.name === selectedSpikeSortingProcessor))
    }, [spikeSorterProcessors, selectedSpikeSortingProcessor])

    const [jobDefinition, jobDefinitionDispatch] = useReducer(dendroJobDefinitionReducer, defaultJobDefinition)
    useEffect(() => {
        if (!processor) return
        const jd: DendroProcessingJobDefinition = {
            inputFiles: [
                {
                    name: 'input',
                    fileName: '*'
                }
            ],
            outputFiles: [
                {
                    name: 'output',
                    fileName: `*`
                }
            ],
            inputParameters: processor.processor.parameters.map(p => ({
                name: p.name,
                value: p.default
            })),
            processorName: processor.processor.name
        }
        jobDefinitionDispatch({
            type: 'setJobDefinition',
            jobDefinition: jd
        })
    }, [processor])

    const [representativeDendroFile, setRepresentativeDendroFile] = useState<DendroFile | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        if (filePaths.length === 0) return
        ; (async () => {
            const f = await fetchFile(projectId, filePaths[0], auth)
            if (canceled) return
            setRepresentativeDendroFile(f)
        })()
        return () => {canceled = true}
    }, [filePaths, projectId, auth])

    const cc = representativeDendroFile?.content || ''
    const nwbUrl = cc.startsWith('url:') ? cc.slice('url:'.length) : ''
    const representativeNwbFile = useNwbFile(nwbUrl)

    const [valid, setValid] = useState(false)

    const [overwriteExistingOutputs, setOverwriteExistingOutputs] = useState(true)
    const [descriptionString, setDescriptionString] = useState('')
    useEffect(() => {
        if (!processor) return
        setDescriptionString(formDescriptionStringFromProcessorName(processor.processor.name))
    }, [processor])

    const [requiredResources, setRequiredResources] = useState<DendroJobRequiredResources | undefined>(undefined)
    useEffect(() => {
        if (!processor) return
        const rr = getDefaultRequiredResources(processor.processor)
        setRequiredResources(rr)
    }, [processor])

    const defaultRunMethod = computeResource?.spec?.defaultJobRunMethod
    const [runMethod, setRunMethod] = useState<'local' | 'aws_batch' | 'slurm'>(defaultRunMethod || 'local')

    const availableRunMethods: ('local' | 'aws_batch' | 'slurm')[] = useMemo(() => {
        return computeResource?.spec?.availableJobRunMethods || ['local']
    }, [computeResource])

    const handleSubmit = useCallback(async () => {
        if (!processor) return
        if (!files) return
        if (!selectedSpikeSortingProcessor) return
        if (!requiredResources) return
        setOperating(true)
        setOperatingMessage('Preparing...')
        const batchId = createRandomId(8)
        for (let i = 0; i < filePaths.length; i++) {
            const filePath = filePaths[i]
            const filePath2 = filePath.startsWith('imported/') ? filePath.slice('imported/'.length) : filePath
            const jobDefinition2: DendroProcessingJobDefinition = deepCopy(jobDefinition)
            const outputFileName = `generated/${appendDescToNwbPath(filePath2, descriptionString)}`
            const outputExists = files.find(f => (f.fileName === outputFileName))
            if (outputExists && !overwriteExistingOutputs) {
                continue
            }
            setOperatingMessage(`Submitting job ${filePath} (${i + 1} of ${filePaths.length})`)
            jobDefinition2.inputFiles[0].fileName = filePath
            jobDefinition2.outputFiles[0].fileName = outputFileName

            const job = {
                projectId,
                jobDefinition: jobDefinition2,
                processorSpec: processor.processor,
                files,
                batchId,
                requiredResources,
                runMethod
            }
            console.log('CREATING JOB', job)
            await createJob(job, auth)
        }
        setOperatingMessage(undefined)
        setOperating(false)
        onClose()
    }, [projectId, jobDefinition, processor, filePaths, files, overwriteExistingOutputs, descriptionString, auth, onClose, selectedSpikeSortingProcessor, requiredResources, runMethod])

    const descriptionStringIsValid = useMemo(() => {
        // description string must be alphanumeric with dashes but not underscores
        if (!descriptionString) return false
        if (!descriptionString.match(/^[a-zA-Z0-9-]+$/)) return false
        return true
    }, [descriptionString])

    const okayToSubmit = useMemo(() => {
        if (!valid) return false
        if (operating) return false
        if (!processor) return false
        if (!descriptionStringIsValid) return false
        return true
    }, [valid, operating, processor, descriptionStringIsValid])

    const cancelButton = useMemo(() => {
        return (
            <div>
                <div>&nbsp;</div>
                <button onClick={onClose}>Cancel</button>
            </div>
        )
    }, [onClose])

    if (!['editor', 'admin'].includes(projectRole || '')) {
        return (
            <div>
                <span style={{color: 'red'}}>You are not authorized to run spike sorting in this project</span>
                {cancelButton}
            </div>
        )
    }

    if (!selectedSpikeSortingProcessor) {
        return (
            <div>
                <SelectProcessor
                    processors={spikeSorterProcessors}
                    onSelected={setSelectedSpikeSortingProcessor}
                />
                {cancelButton}
            </div>
        )
    }
    const W1 = Math.min(500, width / 2)
    const spacing = 20
    return (
        <HBoxLayout
            widths={[W1, width - W1 - spacing]}
            height={height}
            spacing={spacing}
        >
            <LeftColumn
                width={0}
                height={0}
                overwriteExistingOutputs={overwriteExistingOutputs}
                setOverwriteExistingOutputs={setOverwriteExistingOutputs}
                descriptionString={descriptionString}
                setDescriptionString={setDescriptionString}
                descriptionStringIsValid={descriptionStringIsValid}
                filePaths={filePaths}
                selectedSpikeSortingProcessor={selectedSpikeSortingProcessor}
                valid={valid}
                setValid={setValid}
                operating={operating}
                operatingMessage={operatingMessage}
                okayToSubmit={okayToSubmit}
                handleSubmit={handleSubmit}
                requiredResources={requiredResources}
                setRequiredResources={setRequiredResources}
                app={processor?.app}
                appSpec={processor?.appSpec}
                onClose={onClose}
                runMethod={runMethod}
                setRunMethod={setRunMethod}
                availableRunMethods={availableRunMethods}
            />
            <RightColumn
                width={0}
                height={0}
                operating={operating}
                processor={processor?.processor}
                valid={valid}
                setValid={setValid}
                jobDefinition={jobDefinition}
                jobDefinitionDispatch={jobDefinitionDispatch}
                representativeNwbFile={representativeNwbFile}
                processorName={selectedSpikeSortingProcessor}
            />
        </HBoxLayout>
    )
}

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

const RightColumn: FunctionComponent<RightColumnProps> = ({
    width, height,
    operating, processor, setValid,
    jobDefinition,
    jobDefinitionDispatch,
    representativeNwbFile,
    processorName
}) => {
    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Sorting parameters for {processorName}</h3>
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

type LeftColumnProps = {
    width: number
    height: number
    overwriteExistingOutputs: boolean
    setOverwriteExistingOutputs: (val: boolean) => void
    descriptionString: string
    setDescriptionString: (val: string) => void
    descriptionStringIsValid: boolean
    filePaths: string[]
    selectedSpikeSortingProcessor: string
    valid: boolean
    setValid: (val: boolean) => void
    okayToSubmit: boolean
    handleSubmit: () => void
    operating: boolean
    operatingMessage?: string
    requiredResources?: DendroJobRequiredResources
    setRequiredResources: (val: DendroJobRequiredResources) => void
    appSpec?: ComputeResourceSpecApp
    app?: DendroComputeResourceApp
    onClose: () => void
    runMethod: 'local' | 'aws_batch' | 'slurm'
    setRunMethod: (val: 'local' | 'aws_batch' | 'slurm') => void
    availableRunMethods: ('local' | 'aws_batch' | 'slurm')[]
}

const LeftColumn: FunctionComponent<LeftColumnProps> = ({
    width, height,
    overwriteExistingOutputs, setOverwriteExistingOutputs,
    descriptionString, setDescriptionString, descriptionStringIsValid,
    filePaths, selectedSpikeSortingProcessor,
    valid,
    okayToSubmit, handleSubmit,
    operatingMessage,
    requiredResources, setRequiredResources,
    app,
    onClose,
    runMethod, setRunMethod,
    availableRunMethods
}) => {
    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Batch spike sorting of {filePaths.length === 1 ? `1 file` : `${filePaths.length} files`} using {selectedSpikeSortingProcessor}</h3>
            <div>&nbsp;</div>
            <div>
                <table className="table1" style={{maxWidth: 500}}>
                    <tbody>
                        <tr>
                            <td>Overwrite existing outputs</td>
                            <td>
                                <input type="checkbox" checked={overwriteExistingOutputs} onChange={evt => setOverwriteExistingOutputs(evt.target.checked)} />
                            </td>
                        </tr>
                        <tr>
                            <td>Description string in output file name</td>
                            <td>
                                <input type="text" value={descriptionString} onChange={evt => setDescriptionString(evt.target.value)} />
                                {
                                    !descriptionStringIsValid && (
                                        <span style={{color: 'red'}}>Invalid description string</span>
                                    )
                                }
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div>&nbsp;</div>
            {requiredResources && <RequiredResourcesEditor
                requiredResources={requiredResources}
                setRequiredResources={setRequiredResources}
                runMethod={runMethod}
                setRunMethod={setRunMethod}
                availableRunMethods={availableRunMethods}
            />}
            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            <div>
                {/* Large submit button */}
                <button
                    disabled={!okayToSubmit}
                    onClick={handleSubmit}
                    style={{
                        fontSize: 16,
                        padding: 10,
                        color: 'white',
                        background: okayToSubmit ? '#080' : '#ccc',
                        border: 'none',
                        borderRadius: 5,
                        cursor: okayToSubmit ? 'pointer' : 'default'
                    }}
                >
                    Submit spike sorting job(s)
                </button>
                &nbsp;
                {/* Large cancel button */}
                <button
                    onClick={onClose}
                    style={{
                        fontSize: 16,
                        padding: 10,
                        color: 'white',
                        background: '#444',
                        border: 'none',
                        borderRadius: 5,
                        cursor: 'pointer'
                    }}
                >
                    Cancel
                </button>
            </div>
            <div>
                {
                    operatingMessage && (
                        <span>{operatingMessage}</span>
                    )
                }
            </div>
            <div>&nbsp;</div>
            {
                !valid ? (
                    <div>
                        <span style={{color: 'red'}}>There are errors in the job definition.</span>
                    </div>
                ) : <div>&nbsp;</div>
            }
            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            {
                app && (
                    <>
                        <div>Dendro app: {app.name}</div>
                    </>
                )
            }
        </div>
    )

}

type SelectProcessorProps = {
    processors: {appSpec: ComputeResourceSpecApp, app?: DendroComputeResourceApp, processor: ComputeResourceSpecProcessor}[]
    onSelected: (processorName: string) => void
}

const SelectProcessor: FunctionComponent<SelectProcessorProps> = ({processors, onSelected}) => {
    return (
        <div>
            <h3>Select a spike sorter</h3>
            <table className="table1" style={{maxWidth: 900}}>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>App</th>
                    </tr>
                </thead>
                <tbody>
                {
                    processors.map((processor, i) => (
                        <tr key={i}>
                            <td>
                                <Hyperlink onClick={() => {onSelected(processor.processor.name)}}>
                                    {processor.processor.name}
                                </Hyperlink>
                            </td>
                            <td>
                                {processor.appSpec.name}
                            </td>
                        </tr>
                    ))
                }
                </tbody>
            </table>
        </div>
    )
}

const deepCopy = (x: any) => {
    return JSON.parse(JSON.stringify(x))
}

const createRandomId = (numChars: number) => {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    let ret = ''
    for (let i = 0; i < numChars; i++) {
        const j = Math.floor(Math.random() * chars.length)
        ret += chars[j]
    }
    return ret
}

const appendDescToNwbPath = (nwbPath: string, desc: string) => {
    // for example, sub-paired-english_ses-paired-english-m26-190524-100859-cell3_ecephys.nwb goes to sub-paired-english_ses-paired-english-m26-190524-100859-cell3_desc-{processorName}_ecephys.nwb
    const desc2 = replaceUnderscoreWithDash(desc)
    const parts = nwbPath.split('_')
    const lastPart = parts.pop()
    return `${parts.join('_')}_desc-${desc2}_${lastPart}`
}

const replaceUnderscoreWithDash = (x: string) => {
    return x.split('_').join('-')
}

export const formDescriptionStringFromProcessorName = (processorName: string) => {
    let ret = processorName
    // replace spaces and underscores with dashes
    ret = ret.split(' ').join('-')
    ret = ret.split('_').join('-')
    // remove non-alphanumeric characters
    ret = ret.replace(/[^a-zA-Z0-9-]/g, '')
    return ret
}

type RequiredResourcesEditorProps = {
    runMethod: 'local' | 'aws_batch' | 'slurm'
    setRunMethod: (method: 'local' | 'aws_batch' | 'slurm') => void
    availableRunMethods: ('local' | 'aws_batch' | 'slurm')[]
    requiredResources: DendroJobRequiredResources
    setRequiredResources: (val: DendroJobRequiredResources) => void
}
const numCpusChoices = [1, 2, 4, 8, 16]
const numGpusChoices = [0, 1]
const memoryGbChoices = [2, 4, 8, 16, 32]
const timeMinChoices = [1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 1440, 1440 * 2, 1440 * 3, 1440 * 4, 1440 * 5, 1440 * 6, 1440 * 7]

const RequiredResourcesEditor: FunctionComponent<RequiredResourcesEditorProps> = ({requiredResources, setRequiredResources, runMethod, setRunMethod, availableRunMethods}) => {
    const {numCpus, numGpus, memoryGb, timeSec} = requiredResources
    const WW = 70
    return (
        <div>
            <h3>Resources</h3>
            <table className="table1" style={{maxWidth: 500}}>
                <tbody>
                    <tr>
                        <td>Run method</td>
                        <td>
                            <select value={runMethod} onChange={evt => setRunMethod(evt.target.value as any)}>
                                {
                                    availableRunMethods.map(method => (
                                        <option key={method} value={method}>{method}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Number of CPUs</td>
                        <td>
                            <select style={{width: WW}} value={numCpus} onChange={evt => setRequiredResources({...requiredResources, numCpus: Number(evt.target.value)})}>
                                {
                                    numCpusChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>                            
                        </td>
                    </tr>
                    <tr>
                        <td>Number of GPUs</td>
                        <td>
                            <select style={{width: WW}} value={numGpus} onChange={evt => setRequiredResources({...requiredResources, numGpus: Number(evt.target.value)})}>
                                {
                                    numGpusChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Memory (GB)</td>
                        <td>
                            <select style={{width: WW}} value={memoryGb} onChange={evt => setRequiredResources({...requiredResources, memoryGb: Number(evt.target.value)})}>
                                {
                                    memoryGbChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Time (minutes)</td>
                        <td>
                            <select style={{width: WW}} value={Math.floor(timeSec / 60)} onChange={evt => setRequiredResources({...requiredResources, timeSec: Number(evt.target.value) * 60})}>
                                {
                                    timeMinChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    )
}

const getDefaultRequiredResources = (processor: ComputeResourceSpecProcessor | undefined): DendroJobRequiredResources | undefined => {
    if (!processor) return undefined
    const tags = processor.tags.map(t => t.tag)
    if ((tags.includes('kilosort2_5') || tags.includes('kilosort3'))) {
        return {
            numCpus: 4,
            numGpus: 1,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
    else if (tags.includes('mountainsort5')) {
        return {
            numCpus: 8,
            numGpus: 0,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
    else {
        return {
            numCpus: 8,
            numGpus: 0,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
}

export default RunBatchSpikeSortingWindow