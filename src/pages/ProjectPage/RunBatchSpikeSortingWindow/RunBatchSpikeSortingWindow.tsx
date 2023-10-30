import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import Hyperlink from "../../../components/Hyperlink"
import { DendroProcessingJobDefinition, createJob, defaultJobDefinition, fetchFile, dendroJobDefinitionReducer } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecProcessor, DendroFile } from "../../../types/dendro-types"
import EditJobDefinitionWindow from "../EditJobDefinitionWindow/EditJobDefinitionWindow"
import { useNwbFile } from "../FileEditor/NwbFileEditor"
import { useProject } from "../ProjectPageContext"

type Props = {
    filePaths: string[]
    onClose: () => void
}

const RunBatchSpikeSortingWindow: FunctionComponent<Props> = ({ filePaths, onClose }) => {
    const {projectId, files, projectRole, computeResource} = useProject()
    const auth = useGithubAuth()

    const [operating, setOperating] = useState(false)
    const [operatingMessage, setOperatingMessage] = useState<string | undefined>(undefined)

    const [selectedSpikeSortingProcessor, setSelectedSpikeSortingProcessor] = useState<string | undefined>(undefined)

    const spikeSorterProcessors = useMemo(() => {
        const ret: ComputeResourceSpecProcessor[] = []
        for (const app of computeResource?.spec?.apps || []) {
            for (const p of app.processors || []) {
                if (p.tags.map(t => t.tag).includes('spike_sorter')) {
                    ret.push(p)
                }
            }
        }
        return ret
    }, [computeResource])

    const processor = useMemo(() => {
        if (!selectedSpikeSortingProcessor) return undefined
        return spikeSorterProcessors.find(p => (p.name === selectedSpikeSortingProcessor))
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
            inputParameters: processor.parameters.map(p => ({
                name: p.name,
                value: p.default
            })),
            processorName: processor.name
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
        setDescriptionString(formDescriptionStringFromProcessorName(processor.name))
    }, [processor])

    const handleSubmit = useCallback(async () => {
        if (!processor) return
        if (!files) return
        if (!selectedSpikeSortingProcessor) return
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
                processorSpec: processor,
                files,
                batchId
            }
            console.log('CREATING JOB', job)
            await createJob(job, auth)
        }
        setOperatingMessage(undefined)
        setOperating(false)
        onClose()
    }, [projectId, jobDefinition, processor, filePaths, files, overwriteExistingOutputs, descriptionString, auth, onClose, selectedSpikeSortingProcessor])

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

    if (!['editor', 'admin'].includes(projectRole || '')) {
        return (
            <div>
                <span style={{color: 'red'}}>You are not authorized to run spike sorting in this project</span>
            </div>
        )
    }

    if (!selectedSpikeSortingProcessor) {
        return (
            <SelectProcessor
                processors={spikeSorterProcessors}
                onSelected={setSelectedSpikeSortingProcessor}
            />
        )
    }
    return (
        <div>
            <h3>Batch spike sorting of {filePaths.length} files using {selectedSpikeSortingProcessor}</h3>
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
                                <input type="text" value={descriptionString} onChange={evt => setDescriptionString(evt.target.value)} /> {`*_desc-${descriptionString}.nwb`}
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
            <div>
                <button disabled={!okayToSubmit} onClick={handleSubmit}>Submit</button>
                &nbsp;
                {
                    operatingMessage && (
                        <span>{operatingMessage}</span>
                    )
                }
            </div>
            {
                !valid ? (
                    <div>
                        <span style={{color: 'red'}}>There are errors in the job definition.</span>
                    </div>
                ) : <div>&nbsp;</div>
            }
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

type SelectProcessorProps = {
    processors: ComputeResourceSpecProcessor[]
    onSelected: (processorName: string) => void
}

const SelectProcessor: FunctionComponent<SelectProcessorProps> = ({processors, onSelected}) => {
    return (
        <div>
            <h3>Select a spike sorter</h3>
            <ul>
                {
                    processors.map((processor, i) => (
                        <li key={i}>
                            <Hyperlink onClick={() => {onSelected(processor.name)}}>
                                {processor.name}
                            </Hyperlink>
                        </li>
                    ))
                }
            </ul>
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
    // for example, sub-paired-english_ses-paired-english-m26-190524-100859-cell3_ecephys.nwb goes to sub-paired-english_ses-paired-english-m26-190524-100859-cell3_ecephys_desc-{processorName}.nwb
    const parts = nwbPath.split('.')
    const ext = parts.pop()
    const pp = replaceUnderscoreWithDash(desc)
    return `${parts.join('.')}_desc-${pp}.${ext}`
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

export default RunBatchSpikeSortingWindow