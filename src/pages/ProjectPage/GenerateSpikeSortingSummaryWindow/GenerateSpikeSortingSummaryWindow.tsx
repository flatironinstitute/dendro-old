import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { DendroProcessingJobDefinition, createJob, defaultJobDefinition, dendroJobDefinitionReducer, fetchFile } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecApp, ComputeResourceSpecProcessor, DendroComputeResourceApp, DendroFile, DendroJobRequiredResources } from "../../../types/dendro-types"
import { useNwbFile } from "../FileView/NwbFileView"
import { useProject } from "../ProjectPageContext"
import LeftColumn from "../RunBatchSpikeSortingWindow/LeftColumn"
import RightColumn from "../RunBatchSpikeSortingWindow/RightColumn"
import getDefaultRequiredResources from "../RunBatchSpikeSortingWindow/getDefaultRequiredResources"
import { Splitter } from "@fi-sci/splitter";

type Props = {
    filePaths: string[]
    onClose: () => void
    width: number
    height: number
}

const GenerateSpikeSortingSummaryWindow: FunctionComponent<Props> = ({ filePaths, onClose, width, height }) => {
    const {projectId, files, projectRole, computeResource} = useProject()
    const auth = useGithubAuth()

    const [operating, setOperating] = useState(false)
    const [operatingMessage, setOperatingMessage] = useState<string | undefined>(undefined)

    const processorInfo: {appSpec: ComputeResourceSpecApp, app?: DendroComputeResourceApp, processor: ComputeResourceSpecProcessor} | undefined = useMemo(() => {
        for (const appSpec of computeResource?.spec?.apps || []) {
            const app = computeResource?.apps.find(a => (a.name === appSpec.name))
            for (const p of appSpec.processors || []) {
                if (p.name === 'dandi-vis-1.spike_sorting_summary') {
                    return {appSpec, app, processor: p}
                }
            }
        }
        return undefined
    }, [computeResource])

    const [jobDefinition, jobDefinitionDispatch] = useReducer(dendroJobDefinitionReducer, defaultJobDefinition)
    useEffect(() => {
        if (!processorInfo) return
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
            inputParameters: processorInfo.processor.parameters.map(p => ({
                name: p.name,
                value: p.default
            })),
            processorName: processorInfo.processor.name
        }
        jobDefinitionDispatch({
            type: 'setJobDefinition',
            jobDefinition: jd
        })
    }, [processorInfo])

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

    const [requiredResources, setRequiredResources] = useState<DendroJobRequiredResources | undefined>(undefined)
    useEffect(() => {
        if (!processorInfo) return
        const rr = getDefaultRequiredResources(processorInfo.processor)
        setRequiredResources(rr)
    }, [processorInfo])

    const defaultRunMethod = computeResource?.spec?.defaultJobRunMethod
    const [runMethod, setRunMethod] = useState<'local' | 'aws_batch' | 'slurm'>(defaultRunMethod || 'local')

    const availableRunMethods: ('local' | 'aws_batch' | 'slurm')[] = useMemo(() => {
        return computeResource?.spec?.availableJobRunMethods || ['local']
    }, [computeResource])

    const handleSubmit = useCallback(async () => {
        if (!processorInfo) return
        if (!files) return
        if (!requiredResources) return
        setOperating(true)
        setOperatingMessage('Preparing...')
        const batchId = createRandomId(8)
        for (let i = 0; i < filePaths.length; i++) {
            const filePath = filePaths[i]
            const filePath2 = filePath.startsWith('imported/') ? filePath.slice('imported/'.length) : filePath
            const jobDefinition2: DendroProcessingJobDefinition = deepCopy(jobDefinition)
            const outputFileName = `generated/${filePath2}/spike_sorting_summary.nh5`
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
                processorSpec: processorInfo.processor,
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
    }, [projectId, jobDefinition, processorInfo, filePaths, files, overwriteExistingOutputs, auth, onClose, requiredResources, runMethod])

    const okayToSubmit = useMemo(() => {
        if (!valid) return false
        if (operating) return false
        if (!processorInfo) return false
        return true
    }, [valid, operating, processorInfo])

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
                <span style={{color: 'red'}}>You are not authorized to run jobs in this project</span>
                {cancelButton}
            </div>
        )
    }

    if (!processorInfo) {
        return (
            <div>
                <span style={{color: 'red'}}>No processor found for spike sorting summary</span>
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
                selectedProcessorName={processorInfo?.processor.name || ''}
                overwriteExistingOutputs={overwriteExistingOutputs}
                setOverwriteExistingOutputs={setOverwriteExistingOutputs}
                filePaths={filePaths}
                valid={valid}
                setValid={setValid}
                operating={operating}
                operatingMessage={operatingMessage}
                okayToSubmit={okayToSubmit}
                handleSubmit={handleSubmit}
                requiredResources={requiredResources}
                setRequiredResources={setRequiredResources}
                app={processorInfo?.app}
                appSpec={processorInfo?.appSpec}
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
                processor={processorInfo?.processor}
                valid={valid}
                setValid={setValid}
                jobDefinition={jobDefinition}
                jobDefinitionDispatch={jobDefinitionDispatch}
                representativeNwbFile={representativeNwbFile}
                processorName={processorInfo?.processor.name || ''}
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

export const formDescriptionStringFromProcessorName = (processorName: string) => {
    let ret = processorName
    // replace spaces and underscores with dashes
    ret = ret.split(' ').join('-')
    ret = ret.split('_').join('-')
    // remove non-alphanumeric characters
    ret = ret.replace(/[^a-zA-Z0-9-]/g, '')
    return ret
}

export default GenerateSpikeSortingSummaryWindow