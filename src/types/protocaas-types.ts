import validateObject, { isArrayOf, isBoolean, isEqualTo, isNumber, isOneOf, isString, optional } from "./validateObject"

export type ProtocaasProjectUser = {
    userId: string
    role: 'admin' | 'editor' | 'viewer'
}

export const isProtocaasProjectUser = (x: any): x is ProtocaasProjectUser => {
    return validateObject(x, {
        userId: isString,
        role: isOneOf([isEqualTo('admin'), isEqualTo('editor'), isEqualTo('viewer')])
    })
}

export type ProtocaasProject = {
    projectId: string
    name: string
    description: string
    ownerId: string
    users: ProtocaasProjectUser[]
    publiclyReadable: boolean
    computeResourceId?: string
    tags: string[]
    timestampCreated: number
    timestampModified: number
}

export const isProtocaasProject = (x: any): x is ProtocaasProject => {
    return validateObject(x, {
        projectId: isString,
        name: isString,
        description: isString,
        ownerId: isString,
        users: isArrayOf(isProtocaasProjectUser),
        publiclyReadable: isBoolean,
        computeResourceId: optional(isString),
        tags: isArrayOf(isString),
        timestampCreated: isNumber,
        timestampModified: isNumber
    })
}

export type ProtocaasJobInputFile = {
    name: string
    fileId: string
    fileName: string
}

export const isProtocaasJobInputFile = (x: any): x is ProtocaasJobInputFile => {
    return validateObject(x, {
        name: isString,
        fileId: isString,
        fileName: isString
    })
}

export type ProtocaasJobInputParameter = {
    name: string
    value?: any
    secret?: boolean
}

export const isProtocaasJobInputParameter = (x: any): x is ProtocaasJobInputParameter => {
    return validateObject(x, {
        name: isString,
        value: optional(isString),
        secret: optional(isBoolean)
    })
}

export type ProtocaasJobOutputFile = {
    name: string
    fileName: string
    fileId?: string
}

export const isProtocaasJobOutputFile = (x: any): x is ProtocaasJobOutputFile => {
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

export type ProtocaasJob = {
    projectId: string
    jobId: string
    jobPrivateKey: string
    userId: string
    processorName: string
    batchId?: string
    inputFiles: ProtocaasJobInputFile[]
    inputFileIds: string[]
    inputParameters: ProtocaasJobInputParameter[]
    outputFiles: ProtocaasJobOutputFile[]
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

export const isProtocaasJob = (x: any): x is ProtocaasJob => {
    return validateObject(x, {
        projectId: isString,
        jobId: isString,
        jobPrivateKey: isString,
        userId: isString,
        processorName: isString,
        batchId: optional(isString),
        inputFiles: isArrayOf(isProtocaasJobInputFile),
        inputFileIds: isArrayOf(isString),
        inputParameters: isArrayOf(isProtocaasJobInputParameter),
        outputFiles: isArrayOf(isProtocaasJobOutputFile),
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

export type ProtocaasFile = {
    projectId: string
    fileId: string
    userId: string
    fileName: string
    size: number
    timestampCreated: number
    content: string
    metadata: any
    jobId?: string
}

export const isProtocaasFile = (x: any): x is ProtocaasFile => {
    return validateObject(x, {
        projectId: isString,
        fileId: isString,
        userId: isString,
        fileName: isString,
        size: isNumber,
        timestampCreated: isNumber,
        content: isString,
        metadata: () => true,
        jobId: optional(isString)
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

export type ProtocaasComputeResourceApp = {
    name: string
    executablePath: string
    container?: string
    awsBatch?: ComputeResourceAwsBatchOpts
    slurm?: ComputeResourceSlurmOpts
}

export const isProtocaasComputeResourceApp = (x: any): x is ProtocaasComputeResourceApp => {
    return validateObject(x, {
        name: isString,
        executablePath: isString,
        container: optional(isString),
        awsBatch: optional(isComputeResourceAwsBatchOpts),
        slurm: optional(isComputeResourceSlurmOpts)
    })
}

export type ProtocaasComputeResource = {
    computeResourceId: string
    ownerId: string
    name: string
    timestampCreated: number
    apps: ProtocaasComputeResourceApp[]
    spec?: Record<string, any>
}

export const isProtocaasComputeResource = (x: any): x is ProtocaasComputeResource => {
    return validateObject(x, {
        computeResourceId: isString,
        ownerId: isString,
        name: isString,
        timestampCreated: isNumber,
        apps: isArrayOf(isProtocaasComputeResourceApp),
        spec: optional(() => true)
    })
}

export type ComputeResourceSpecApp = {
    name: string
    help: string
    processors: ComputeResourceSpecProcessor[]
}

export const isComputeResourceSpecApp = (x: any): x is ComputeResourceSpecApp => {
    return validateObject(x, {
        name: isString,
        help: isString,
        processors: isArrayOf(isComputeResourceSpecProcessor)
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
