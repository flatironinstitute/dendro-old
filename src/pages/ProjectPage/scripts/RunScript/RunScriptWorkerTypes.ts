export type RunScriptAddJobInputFile = {
    name: string
    fileName: string
    isFolder?: boolean
}

export type RunScriptAddJobOutputFile = {
    name: string
    fileName: string
    isFolder?: boolean
}

export type RunScriptAddJobParameter = {
    name: string
    value: any
}

export type RunScriptAddJobRequiredResources = {
    numCpus: number
    numGpus: number
    memoryGb: number
    timeSec: number
}

export type RunScriptAddJob = {
    processorName: string
    inputFiles: RunScriptAddJobInputFile[]
    outputFiles: RunScriptAddJobOutputFile[]
    inputParameters: RunScriptAddJobParameter[]
    requiredResources: RunScriptAddJobRequiredResources
    runMethod: 'local' | 'aws_batch' | 'slurm'
}

export type RunScriptResult = {
    jobs: RunScriptAddJob[]
}

export {}