import validateObject, { isArrayOf, isBoolean, isEqualTo, isNumber, isOneOf, isString, optional, isNull } from "./validateObject"

export type DendroProjectUser = {
    userId: string
    role: 'admin' | 'editor' | 'viewer'
}

export const isDendroProjectUser = (x: any): x is DendroProjectUser => {
    return validateObject(x, {
        userId: isString,
        role: isOneOf([isEqualTo('admin'), isEqualTo('editor'), isEqualTo('viewer')])
    })
}

export type DendroProject = {
    projectId: string
    name: string
    description: string
    ownerId: string
    users: DendroProjectUser[]
    publiclyReadable: boolean
    computeResourceId?: string | null
    tags: string[]
    timestampCreated: number
    timestampModified: number
}

export const isDendroProject = (x: any): x is DendroProject => {
    return validateObject(x, {
        projectId: isString,
        name: isString,
        description: isString,
        ownerId: isString,
        users: isArrayOf(isDendroProjectUser),
        publiclyReadable: isBoolean,
        computeResourceId: optional(isOneOf([isString, isNull])),
        tags: isArrayOf(isString),
        timestampCreated: isNumber,
        timestampModified: isNumber
    })
}

export type DendroJobInputFile = {
    name: string
    fileId: string
    fileName: string
}

export const isDendroJobInputFile = (x: any): x is DendroJobInputFile => {
    return validateObject(x, {
        name: isString,
        fileId: isString,
        fileName: isString
    })
}

export type DendroJobInputParameter = {
    name: string
    value?: any
    secret?: boolean
}

export const isDendroJobInputParameter = (x: any): x is DendroJobInputParameter => {
    return validateObject(x, {
        name: isString,
        value: optional(isString),
        secret: optional(isBoolean)
    })
}

export type DendroJobOutputFile = {
    name: string
    fileName: string
    fileId?: string
}

export const isDendroJobOutputFile = (x: any): x is DendroJobOutputFile => {
    return validateObject(x, {
        name: isString,
        fileName: isString,
        fileId: optional(isString)
    })
}

export type ComputeResourceSpecProcessorParameter = {
    name: string
    help: string
    type: string
    default?: any
    options?: string[] | number[]
    secret: boolean
}

export const isComputeResourceSpecProcessorParameter = (x: any): x is ComputeResourceSpecProcessorParameter => {
    return validateObject(x, {
        name: isString,
        help: isString,
        type: isString,
        default: optional(isString),
        options: optional(isArrayOf(isOneOf([isString, isNumber]))),
        secret: isBoolean
    })
}

export type ComputeResourceSpecProcessorInput = {
    name: string
    help: string
    list: boolean
}

export const isComputeResourceSpecProcessorInput = (x: any): x is ComputeResourceSpecProcessorInput => {
    return validateObject(x, {
        name: isString,
        help: isString,
        list: isBoolean
    })
}

export type ComputeResourceSpecProcessorOutput = {
    name: string
    help: string
}

export const isComputeResourceSpecProcessorOutput = (x: any): x is ComputeResourceSpecProcessorOutput => {
    return validateObject(x, {
        name: isString,
        help: isString
    })
}

export type ComputeResourceSpecProcessorAttribute = {
    name: string
    value: any
}

export const isComputeResourceSpecProcessorAttribute = (x: any): x is ComputeResourceSpecProcessorAttribute => {
    return validateObject(x, {
        name: isString,
        value: isString
    })
}

export type ComputeResourceSpecProcessorTag = {
    tag: string
}

export const isComputeResourceSpecProcessorTag = (x: any): x is ComputeResourceSpecProcessorTag => {
    return validateObject(x, {
        tag: isString
    })
}

export type ComputeResourceSpecProcessor = {
    name: string
    help: string
    inputs: ComputeResourceSpecProcessorInput[]
    outputs: ComputeResourceSpecProcessorOutput[]
    parameters: ComputeResourceSpecProcessorParameter[]
    attributes: ComputeResourceSpecProcessorAttribute[]
    tags: ComputeResourceSpecProcessorTag[]
}

export const isComputeResourceSpecProcessor = (x: any): x is ComputeResourceSpecProcessor => {
    return validateObject(x, {
        name: isString,
        help: isString,
        inputs: isArrayOf(isComputeResourceSpecProcessorInput),
        outputs: isArrayOf(isComputeResourceSpecProcessorOutput),
        parameters: isArrayOf(isComputeResourceSpecProcessorParameter),
        attributes: isArrayOf(isComputeResourceSpecProcessorAttribute),
        tags: isArrayOf(isComputeResourceSpecProcessorTag)
    })
}

export type DendroJob = {
    projectId: string
    jobId: string
    jobPrivateKey: string
    userId: string
    processorName: string
    batchId?: string
    inputFiles: DendroJobInputFile[]
    inputFileIds: string[]
    inputParameters: DendroJobInputParameter[]
    outputFiles: DendroJobOutputFile[]
    timestampCreated: number
    computeResourceId: string
    status: 'pending' | 'queued' | 'starting' | 'running' | 'completed' | 'failed'
    error?: string
    processorVersion?: string
    computeResourceNodeId?: string
    computeResourceNodeName?: string
    consoleOutputUrl?: string
    timestampQueued?: number
    timestampStarting?: number
    timestampStarted?: number
    timestampFinished?: number
    outputFileIds?: string[]
    processorSpec: ComputeResourceSpecProcessor
    dandiApiKey?: string
}

export const isDendroJob = (x: any): x is DendroJob => {
    return validateObject(x, {
        projectId: isString,
        jobId: isString,
        jobPrivateKey: isString,
        userId: isString,
        processorName: isString,
        batchId: optional(isString),
        inputFiles: isArrayOf(isDendroJobInputFile),
        inputFileIds: isArrayOf(isString),
        inputParameters: isArrayOf(isDendroJobInputParameter),
        outputFiles: isArrayOf(isDendroJobOutputFile),
        timestampCreated: isNumber,
        computeResourceId: isString,
        status: isOneOf([isEqualTo('pending'), isEqualTo('queued'), isEqualTo('starting'), isEqualTo('running'), isEqualTo('completed'), isEqualTo('failed')]),
        error: optional(isString),
        processorVersion: optional(isString),
        computeResourceNodeId: optional(isString),
        computeResourceNodeName: optional(isString),
        consoleOutputUrl: optional(isString),
        timestampQueued: optional(isNumber),
        timestampStarting: optional(isNumber),
        timestampStarted: optional(isNumber),
        timestampFinished: optional(isNumber),
        outputFileIds: optional(isArrayOf(isString)),
        processorSpec: isComputeResourceSpecProcessor,
        dandiApiKey: optional(isString)
    })
}

export type DendroFile = {
    projectId: string
    fileId: string
    userId: string
    fileName: string
    size: number
    timestampCreated: number
    content: string
    metadata: any
    jobId?: string | null
}

export const isDendroFile = (x: any): x is DendroFile => {
    return validateObject(x, {
        projectId: isString,
        fileId: isString,
        userId: isString,
        fileName: isString,
        size: isNumber,
        timestampCreated: isNumber,
        content: isString,
        metadata: () => true,
        jobId: optional(isOneOf([isString, isNull]))
    })
}

export type ComputeResourceAwsBatchOpts = {
    jobQueue: string
    jobDefinition: string
}

export const isComputeResourceAwsBatchOpts = (x: any): x is ComputeResourceAwsBatchOpts => {
    return validateObject(x, {
        jobQueue: isString,
        jobDefinition: isString
    })
}


export type ComputeResourceSlurmOpts = {
    partition?: string
    time?: string
    cpusPerTask?: number
    otherOpts?: string
}

export const isComputeResourceSlurmOpts = (x: any): x is ComputeResourceSlurmOpts => {
    return validateObject(x, {
        partition: optional(isString),
        time: optional(isString),
        cpusPerTask: optional(isNumber),
        otherOpts: optional(isString)
    })
}

export type DendroComputeResourceApp = {
    name: string
    specUri?: string
    executablePath?: string // to be removed
    container?: string // to be removed
    awsBatch?: ComputeResourceAwsBatchOpts
    slurm?: ComputeResourceSlurmOpts
}

export const isDendroComputeResourceApp = (x: any): x is DendroComputeResourceApp => {
    return validateObject(x, {
        name: isString,
        specUri: optional(isString),
        executablePath: optional(isString), // to be removed
        container: optional(isString), // to be removed
        awsBatch: optional(isComputeResourceAwsBatchOpts),
        slurm: optional(isComputeResourceSlurmOpts)
    })
}

export type ComputeResourceSpecApp = {
    name: string
    help: string
    processors: ComputeResourceSpecProcessor[]
    appImage?: string
    appExecutable?: string
}

export const isComputeResourceSpecApp = (x: any): x is ComputeResourceSpecApp => {
    return validateObject(x, {
        name: isString,
        help: isString,
        processors: isArrayOf(isComputeResourceSpecProcessor),
        appImage: isString,
        appExecutable: isString
    })
}

export type ComputeResourceSpec = {
    apps: ComputeResourceSpecApp[]
}

export const isComputeResourceSpec = (x: any): x is ComputeResourceSpec => {
    return validateObject(x, {
        apps: isArrayOf(isComputeResourceSpecApp)
    })
}

export type DendroComputeResource = {
    computeResourceId: string
    ownerId: string
    name: string
    timestampCreated: number
    apps: DendroComputeResourceApp[]
    spec?: ComputeResourceSpec
}

export const isDendroComputeResource = (x: any): x is DendroComputeResource => {
    return validateObject(x, {
        computeResourceId: isString,
        ownerId: isString,
        name: isString,
        timestampCreated: isNumber,
        apps: isArrayOf(isDendroComputeResourceApp),
        spec: optional(isComputeResourceSpec)
    })
}

export type PubsubSubscription = {
    pubnubSubscribeKey: string
    pubnubChannel: string
    pubnubUser: string
}

export const isPubsubSubscription = (x: any): x is PubsubSubscription => {
    return validateObject(x, {
        pubnubSubscribeKey: isString,
        pubnubChannel: isString,
        pubnubUser: isString
    })
}

export type ProcessorGetJobResponseInput = {
    name: string
    url: string
}

export const isProcessorGetJobResponseInput = (x: any): x is ProcessorGetJobResponseInput => {
    return validateObject(x, {
        name: isString,
        url: isString
    })
}

export type ProcessorGetJobResponseOutput = {
    name: string
}

export const isProcessorGetJobResponseOutput = (x: any): x is ProcessorGetJobResponseOutput => {
    return validateObject(x, {
        name: isString
    })
}

export type ProcessorGetJobResponseParameter = {
    name: string
    value: any
}

export const isProcessorGetJobResponseParameter = (x: any): x is ProcessorGetJobResponseParameter => {
    return validateObject(x, {
        name: isString,
        value: isString
    })
}

export type ProcessorGetJobResponse = {
    jobId: string
    status: string
    processorName: string
    inputs: ProcessorGetJobResponseInput[]
    outputs: ProcessorGetJobResponseOutput[]
    parameters: ProcessorGetJobResponseParameter[]
}

export const isProcessorGetJobResponse = (x: any): x is ProcessorGetJobResponse => {
    return validateObject(x, {
        jobId: isString,
        status: isString,
        processorName: isString,
        inputs: isArrayOf(isProcessorGetJobResponseInput),
        outputs: isArrayOf(isProcessorGetJobResponseOutput),
        parameters: isArrayOf(isProcessorGetJobResponseParameter)
    })
}
