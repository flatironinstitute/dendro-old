import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { ComputeResourceSpecProcessor, DendroFile, DendroJob } from "../../../../types/dendro-types"
import { useProject } from "../../ProjectPageContext"
import { RunScriptAddJob, RunScriptResult } from "./RunScriptWorkerTypes"
import { Hyperlink } from "@fi-sci/misc"
import { useGithubAuth } from "../../../../GithubAuth/useGithubAuth"
import { DendroProcessingJobDefinition, createJob, setUrlFile } from "../../../../dbInterface/dbInterface"

type RunScriptWindowProps = {
    width: number
    height: number
    scriptContent: string
    saved: boolean
}

const RunScriptWindow: FunctionComponent<RunScriptWindowProps> = ({width, height, scriptContent, saved}) => {
    const {files, jobs, computeResource, projectId, refreshFiles, refreshJobs} = useProject()
    const topBarHeight = 30
    const {result, log, error} = useRunScript(scriptContent, files)

    const computeResourceProcessorsByName = useMemo(() => {
        if (!computeResource) return {}
        const ret: {[key: string]: ComputeResourceSpecProcessor} = {}
        for (const a of computeResource.spec?.apps || []) {
            for (const p of a.processors) {
                ret[p.name] = p
            }
        }
        return ret
    }, [computeResource])

    const projectJobHashes = useMemo(() => {
        const ret = new Set<string>()
        if (!jobs) return ret
        if (!computeResourceProcessorsByName) return ret
        for (const j of jobs) {
            const p = computeResourceProcessorsByName[j.processorName]
            if (p) {
                ret.add(hashOfJob(j, p))
            }
        }
        return ret
    }, [jobs, computeResourceProcessorsByName])
    const {newJobs, existingJobs} = useMemo(() => {
        if (!jobs) return {newJobs: undefined, existingJobs: undefined}
        if (!result) return {newJobs: undefined, existingJobs: undefined}
        if (!projectJobHashes) return {newJobs: undefined, existingJobs: undefined}
        const existingJobs: RunScriptAddJob[] = []
        const newJobs: RunScriptAddJob[] = []
        for (const j of result.jobs) {
            const p = computeResourceProcessorsByName[j.processorName]
            if (!p) return {newJobs: undefined, existingJobs: undefined}
            const h = hashOfJob(j, p)
            if (projectJobHashes.has(h)) {
                existingJobs.push(j)
            } else {
                newJobs.push(j)
            }
        }
        return {newJobs, existingJobs}
    }, [jobs, result, projectJobHashes, computeResourceProcessorsByName])

    const {newFiles} = useMemo(() => {
        if (!files) return {newFiles: undefined, existingFiles: undefined}
        if (!result) return {newFiles: undefined, existingFiles: undefined}
        const newFiles: {fileName: string, url: string}[] = []
        for (const f of result.addedFiles) {
            if (!files.find(f1 => f1.fileName === f.fileName)) {
                newFiles.push(f)
            }
        }
        return {newFiles}
    }, [files, result])

    const jobProblems = useMemo(() => {
        if (!result) return undefined
        if (!computeResourceProcessorsByName) return undefined
        const ret: string[] = []
        for (const j of result.jobs) {
            const p = computeResourceProcessorsByName[j.processorName]
            if (p) {
                const jobProblem = getJobProblem(j, p)
                if (jobProblem) {
                    ret.push(jobProblem)
                }
            }
            else {
                ret.push(`Processor not found: ${j.processorName}`)
            }
        }
        return ret
    }, [result, computeResourceProcessorsByName])

    const auth = useGithubAuth()

    const handleSubmit = useCallback(async () => {
        const jobsToSubmit = newJobs
        const filesToAdd = newFiles
        if (!jobsToSubmit) return
        if (!filesToAdd) return
        if (!auth.signedIn) return
        if (!files) return
        for (const f of filesToAdd) {
            const metaData = {}
            await setUrlFile(projectId, f.fileName, f.url, metaData, auth)
        }
        const batchId = createRandomId(8)
        for (const j of jobsToSubmit) {
            console.info(`Submitting job: ${j.processorName}`)
            const jobDefinition: DendroProcessingJobDefinition = {
                processorName: j.processorName,
                inputFiles: j.inputFiles,
                outputFiles: j.outputFiles,
                inputParameters: j.inputParameters
            }
            const p = computeResourceProcessorsByName[j.processorName]
            if (!p) {
                console.error(`Unexpected: processor not found: ${j.processorName}`)
                return
            }
            await createJob({
                projectId,
                jobDefinition,
                processorSpec: p,
                files,
                batchId,
                requiredResources: {
                    numCpus: j.requiredResources.numCpus,
                    numGpus: j.requiredResources.numGpus,
                    memoryGb: j.requiredResources.memoryGb,
                    timeSec: j.requiredResources.timeSec
                },
                runMethod: 'local'
            }, auth)
        }
        refreshFiles()
        refreshJobs()
        if ((newFiles.length > 0) && (newJobs.length > 0)) {
            alert('New files and jobs have been submitted')
        }
        else if (newFiles.length > 0) {
            alert('New files have been submitted')
        }
        else if (newJobs.length > 0) {
            alert('New jobs have been submitted')
        }
    }, [auth, projectId, files, computeResourceProcessorsByName, refreshFiles, refreshJobs, newJobs, newFiles])
    
    return (
        <div style={{position: 'absolute', width, height}}>
            <div style={{position: 'absolute', width, height: topBarHeight}}>
                {/* <SmallIconButton
                    icon={<PlayArrow />}
                    title='Run this script'
                    label="Run script"
                    disabled={!enabled || !files}
                    onClick={handleRunScript}
                /> */}
            </div>
            <div style={{position: 'absolute', width, height: height - topBarHeight, top: topBarHeight, overflowY: 'auto'}}>
                <div>
                    {
                        jobProblems && jobProblems.length > 0 ? (
                            <div style={{color: 'red'}}>
                                {jobProblems.map((p, i) => <div key={i}>{p}</div>)}
                            </div>
                        ) : (
                            newJobs && existingJobs && newFiles && (
                                <div>
                                    <div>{newJobs.length} new jobs ({newJobs.length + existingJobs.length} total); {newFiles.length} new files</div>
                                    {newJobs.length + newFiles.length > 0 && (
                                        saved ? (
                                            <div>
                                                <Hyperlink
                                                    onClick={() => {
                                                        handleSubmit()
                                                    }}
                                                >
                                                    SUBMIT
                                                </Hyperlink>
                                            </div>
                                        ) : (
                                            <div>
                                                You must save changes to your your script in order to submit new jobs.
                                            </div>
                                        )
                                    )}
                                </div>
                            )
                        )
                    }
                    {error && <pre style={{color: 'red'}}>{error}</pre>}
                    <hr />
                    {log.map((l, i) => <pre key={i}>{l}</pre>)}
                </div>
            </div>
        </div>
    )
}

const useRunScript = (scriptContent: string, files?: DendroFile[]) => {
    const [result, setResult] = useState<RunScriptResult>()
    const [error, setError] = useState<string>()
    const [log, setLog] = useState<any[]>([])
    useEffect(() => {
        setError('')
        setResult(undefined)
        setLog([])
        let canceled = false
        let finished = false
        if (!files) return
        const worker = new Worker(new URL('./runScriptWorker.ts', import.meta.url))
        worker.postMessage({
            type: 'run',
            script: scriptContent,
            files
        })
        worker.onmessage = (e) => {
            if (canceled) return
            if (finished) return
            if (e.data.type === 'result') {
                finished = true
                setResult(e.data.result)
                setLog(e.data.log)
            }
            else if (e.data.type === 'error') {
                finished = true
                setError(e.data.error)
                setLog(e.data.log)
            }
        }
        setTimeout(() => {
            if (canceled) return
            if (finished) return
            finished = true
            setError('Timeout')
            worker.terminate()
        }, 2500)
        return () => {
            worker.terminate()
            canceled = true
        }
    }, [scriptContent, files])
    return {result, error, log}
}

const getJobProblem = (j: RunScriptAddJob, p: ComputeResourceSpecProcessor) => {
    // make sure we have all the inputs
    for (const x1 of p.inputs) {
        const x2 = j.inputFiles.find(x => x.name === x1.name)
        if (!x2) return `Input file "${x1.name}" not found for processor ${j.processorName}`
        if (x2.isFolder) return `Input "${x1.name}" cannot be a folder for processor ${j.processorName}`
    }
    // make sure we have no extra inputs
    for (const x of j.inputFiles) {
        if (!x.isFolder) {
            if (!p.inputs.find(x1 => x1.name === x.name)) {
                return `Extra input file "${x.name}" for processor ${j.processorName}`
            }
        }
    }
    // make sure we have all the input folders
    for (const x1 of p.inputFolders || []) {
        const x2 = j.inputFiles.find(x => x.name === x1.name)
        if (!x2) return `Input folder "${x1.name}" not found for processor ${j.processorName}`
        if (!x2.isFolder) return `Input "${x1.name}" must be a folder for processor ${j.processorName}`
    }
    // make sure we have no extra input folders
    for (const x of j.inputFiles) {
        if (x.isFolder) {
            if (!p.inputFolders?.find(x1 => x1.name === x.name)) {
                return `Extra input folder "${x.name}" for processor ${j.processorName}`
            }
        }
    }
    // make sure we have all the outputs
    for (const x1 of p.outputs) {
        const x2 = j.outputFiles.find(x => x.name === x1.name)
        if (!x2) return `Output file "${x1.name}" not found for processor ${j.processorName}`
        if (x2.isFolder) return `Output "${x1.name}" cannot be a folder for processor ${j.processorName}`
    }
    // make sure we have no extra outputs
    for (const x of j.outputFiles) {
        if (!x.isFolder) {
            if (!p.outputs.find(x1 => x1.name === x.name)) {
                return `Extra output file "${x.name}" for processor ${j.processorName}`
            }
        }
    }
    // make sure we have all the output folders
    for (const x1 of p.outputFolders || []) {
        const x2 = j.outputFiles.find(x => x.name === x1.name)
        if (!x2) return `Output folder "${x1.name}" not found for processor ${j.processorName}`
        if (!x2.isFolder) return `Output "${x1.name}" must be a folder for processor ${j.processorName}`
    }
    // make sure we have no extra output folders
    for (const x of j.outputFiles) {
        if (x.isFolder) {
            if (!p.outputFolders?.find(x1 => x1.name === x.name)) {
                return `Extra output folder "${x.name}" for processor ${j.processorName}`
            }
        }
    }
    // make sure we have all the required parameters
    for (const x1 of p.parameters) {
        if ((x1.default !== undefined)) continue
        const x2 = j.inputParameters.find(x => x.name === x1.name)
        if (!x2) return `Parameter "${x1.name}" not found for processor ${j.processorName}`
    }
    // make sure we have no extra parameters
    for (const x of j.inputParameters) {
        if (!p.parameters.find(x1 => x1.name === x.name)) {
            return `Extra parameter "${x.name}" for processor ${j.processorName}`
        }
    }
    return undefined
}

const hashOfJob = (j: DendroJob | RunScriptAddJob, p: ComputeResourceSpecProcessor) => {
    // important that these arrays have the same order as in the processor
    const inputFiles = p.inputs.map(x => {
        const y = j.inputFiles.find(x1 => x1.name === x.name)
        if (!y) return {}
        return {
            name: x.name,
            fileName: y.fileName
        }
    })
    const inputFolders = (p.inputFolders || []).map(x => {
        const y = j.inputFiles.find(x1 => x1.name === x.name)
        if (!y) return {}
        return {
            name: x.name,
            fileName: y.fileName
        }
    })
    const outputFiles = p.outputs.map(x => {
        const y = j.outputFiles.find(x1 => x1.name === x.name)
        if (!y) return {}
        return {
            name: x.name,
            fileName: y.fileName
        }
    })
    const outputFolders = (p.outputFolders || []).map(x => {
        const y = j.outputFiles.find(x1 => x1.name === x.name)
        if (!y) return {}
        return {
            name: x.name,
            fileName: y.fileName
        }
    })
    const parameters=  p.parameters.map(x => {
        const y = j.inputParameters.find(x1 => x1.name === x.name)
        if (y === undefined) {
            if ((x.default !== undefined) && (x.default !== null)) {
                return {
                    name: x.name,
                    value: x.default
                }
            }
            else {
                return {}
            }
        }
        else {
            return {
                name: x.name,
                value: y.value
            }
        }
    })
    const obj = {
        processorName: j.processorName,
        inputFiles,
        inputFolders,
        outputFiles,
        outputFolders,
        parameters
    }
    return deterministicJsonStringify(obj)
}

const deterministicJsonStringify = (obj: any) => {
    return JSON.stringify(obj, (key, value) => {
        if (value && value.constructor === Object) {
            return Object.keys(value).sort().reduce((sorted: any, key: string) => {
                sorted[key] = value[key]
                return sorted
            }, {})
        }
        return value
    })
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

export default RunScriptWindow