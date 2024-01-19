import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { DendroProcessingJobDefinition, createJob, defaultJobDefinition, dendroJobDefinitionReducer, fetchFile } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecApp, ComputeResourceSpecProcessor, DendroComputeResourceApp, DendroFile, DendroJobRequiredResources } from "../../../types/dendro-types"
import { useNwbFile } from "../FileView/NwbFileView"
import { useProject } from "../ProjectPageContext"
import LeftColumn from "./LeftColumn"
import RightColumn from "./RightColumn"
import SelectProcessorComponent from "./SelectProcessorComponent"
import getDefaultRequiredResources from "./getDefaultRequiredResources"
import { Splitter } from "@fi-sci/splitter";

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
                <SelectProcessorComponent
                    processors={spikeSorterProcessors}
                    onSelected={setSelectedSpikeSortingProcessor}
                />
                {cancelButton}
            </div>
        )
    }
    const W1 = Math.min(500, width / 2)
    return (
        <Splitter
            width={width}
            initialPosition={W1}
            height={height}
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
                representativeNwbFile={representativeNwbFile}
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
        </Splitter>
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

export default RunBatchSpikeSortingWindow