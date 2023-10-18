import { GithubAuthData } from "../GithubAuth/GithubAuthContext";
import { ComputeResourceAwsBatchOpts, ComputeResourceSlurmOpts, ComputeResourceSpecProcessor, ProtocaasComputeResource, ProtocaasFile, ProtocaasJob, ProtocaasProject, isProtocaasFile, isProtocaasProject } from "../types/protocaas-types";
import getAuthorizationHeaderForUrl from "./getAuthorizationHeaderForUrl";

type Auth = GithubAuthData

export const getRequest = async (url: string, auth: Auth | undefined): Promise<any> => {
    const response = await fetch(url, {
        headers: {
            'github-access-token': auth?.accessToken || ''
        }
    })
    if (response.status !== 200) {
        throw Error(`Unable to fetch ${url}: ${response.status}`)
    }
    const json = await response.json()
    return json
}

export const postRequest = async (url: string, body: any, auth: Auth): Promise<any> => {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'github-access-token': auth.accessToken || ''
        },
        body: JSON.stringify(body)
    })
    if (response.status !== 200) {
        throw Error(`Unable to POST ${url}: ${response.status}`)
    }
    const json = await response.json()
    return json
}

export const putRequest = async (url: string, body: any, auth: Auth): Promise<any> => {
    const response = await fetch(url, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'github-access-token': auth.accessToken || ''
        },
        body: JSON.stringify(body)
    })
    if (response.status !== 200) {
        throw Error(`Unable to PUT ${url}: ${response.status}`)
    }
    const json = await response.json()
    return json
}

export const deleteRequest = async (url: string, auth: Auth): Promise<any> => {
    const response = await fetch(url, {
        method: 'DELETE',
        headers: {
            'github-access-token': auth.accessToken || ''
        }
    })
    if (response.status !== 200) {
        throw Error(`Unable to DELETE ${url}: ${response.status}`)
    }
    const json = await response.json()
    return json
}

export const fetchProjectsForTag = async (tag: string, auth: Auth): Promise<ProtocaasProject[]> => {
    const url = `/api/gui/projects?tag=${tag}`
    const json = await getRequest(url, auth)
    if (!json.success) {
        throw Error(`Error in fetchProjectsForTag: ${json.error}`)
    }
    const projects = json.projects
    for (const p of projects) {
        if (!isProtocaasProject(p)) {
            console.warn(p)
            throw Error('Invalid project.')
        }
    }
    return projects
}

export const fetchProjectsForUser = async (projectId: string, auth: Auth): Promise<ProtocaasProject[]> => {
    const url = `/api/gui/projects`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchProjects: ${response.error}`)
    return response.projects
}

export const createProject = async (projectName: string, auth: Auth): Promise<string> => {
    const url = `/api/gui/projects`
    const response = await postRequest(url, {name: projectName}, auth)
    if (!response.success) throw Error(`Error in createProject: ${response.error}`)
    return response.projectId
}

export const setProjectTags = async (projectId: string, tags: string[], auth: GithubAuthData) => {
    if (!auth.accessToken) return
    const url = `/api/gui/projects/${projectId}/tags`
    const data = {
        tags
    }
    const resp = await putRequest(url, data, auth)
    if (!resp.success) throw Error(`Error in setProjectTags: ${resp.error}`)
}

export const setProjectUsers = async (projectId: string, users: {userId: string, role: 'admin' | 'editor' | 'viewer'}[], auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/users`
    const response = await putRequest(url, {users}, auth)
    if (!response.success) throw Error(`Error in setProjectUsers: ${response.error}`)
}

export const setProjectPubliclyReadable = async (projectId: string, publiclyReadable: boolean, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/publicly_readable`
    const response = await putRequest(url, {publiclyReadable}, auth)
    if (!response.success) throw Error(`Error in setProjectPubliclyReadable: ${response.error}`)
}

export const setProjectComputeResourceId = async (projectId: string, computeResourceId: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/compute_resource_id`
    const response = await putRequest(url, {computeResourceId}, auth)
    if (!response.success) throw Error(`Error in setProjectComputeResourceId: ${response.error}`)
}

export const fetchProject = async (projectId: string, auth: Auth): Promise<ProtocaasProject | undefined> => {
    const url = `/api/gui/projects/${projectId}`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchProject: ${response.error}`)
    if (!isProtocaasProject(response.project)) {
        console.warn(response.project)
        throw Error('Invalid project.')
    }
    return response.project
}

export const fetchFiles = async (projectId: string, auth: Auth): Promise<ProtocaasFile[]> => {
    const url = `/api/gui/projects/${projectId}/files`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchFiles: ${response.error}`)
    for (const f of response.files) {
        if (!isProtocaasFile(f)) {
            console.warn(f)
            throw Error('Invalid file.')
        }
    }
    return response.files
}

export const fetchFile = async (projectId: string, fileName: string, auth: Auth): Promise<ProtocaasFile | undefined> => {
    const url = `/api/gui/projects/${projectId}/files/${fileName}`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchFile: ${response.error}`)
    if (!isProtocaasFile(response.file)) {
        console.warn(response.file)
        throw Error('Invalid file.')
    }
    return response.file
}

const headRequest = async (url: string, headers?: any) => {
    // Cannot use HEAD, because it is not allowed by CORS on DANDI AWS bucket
    // let headResponse
    // try {
    //     headResponse = await fetch(url, {method: 'HEAD'})
    //     if (headResponse.status !== 200) {
    //         return undefined
    //     }
    // }
    // catch(err: any) {
    //     console.warn(`Unable to HEAD ${url}: ${err.message}`)
    //     return undefined
    // }
    // return headResponse

    // Instead, use aborted GET.
    const controller = new AbortController();
    const signal = controller.signal;
    const response = await fetch(url, {
        signal,
        headers
    })
    controller.abort();
    return response
}

const getSizeForRemoteFile = async (url: string): Promise<number> => {
    const authorizationHeader = getAuthorizationHeaderForUrl(url)
    const headers = authorizationHeader ? {Authorization: authorizationHeader} : undefined
    const response = await headRequest(url, headers)
    if (!response) {
        throw Error(`Unable to HEAD ${url}`)
    }
    if ((response.redirected === true) && (response.status !== 200)) {
        // this is tricky -- there is a CORS problem which prevents the content-length from being on the redirected response
        if (url === response.url) {
            // to be safe, let's make sure we are not in an infinite loop
            throw Error(`Unable to HEAD ${url} -- infinite redirect`)
        }
        return await getSizeForRemoteFile(response.url)
    }
    const size = Number(response.headers.get('content-length'))
    if (isNaN(size)) {
        throw Error(`Unable to get content-length for ${url}`)
    }
    return size
}

export const setUrlFile = async (projectId: string, fileName: string, url: string, metadata: any, auth: Auth): Promise<void> => {
    const reqUrl = `/api/gui/projects/${projectId}/files/${fileName}`
    const size = await getSizeForRemoteFile(url)
    const body = {
        content: `url:${url}`,
        size,
        metadata
    }
    const response = await putRequest(reqUrl, body, auth)
    if (!response.success) throw Error(`Error in setUrlFile: ${response.error}`)
}

export const deleteFile = async (projectId: string, fileName: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/files/${fileName}`
    const resp = await deleteRequest(url, auth)
    if (!resp.success) throw Error(`Error in deleteFile: ${resp.error}`)
}

export const deleteProject = async (projectId: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}`
    const resp = await deleteRequest(url, auth)
    if (!resp.success) throw Error(`Error in deleteProject: ${resp.error}`)
}

export const setProjectName = async (projectId: string, name: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/name`
    const response = await putRequest(url, {name}, auth)
    if (!response.success) throw Error(`Error in setProjectName: ${response.error}`)
}

export const setProjectDescription = async (projectId: string, description: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/projects/${projectId}/description`
    const response = await putRequest(url, {description}, auth)
    if (!response.success) throw Error(`Error in setProjectDescription: ${response.error}`)
}

export const fetchComputeResources = async (auth: Auth): Promise<ProtocaasComputeResource[]> => {
    const url = `/api/gui/compute_resources`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchComputeResources: ${response.error}`)
    return response.computeResources
}

export const fetchComputeResource = async (computeResourceId: string, auth: Auth): Promise<ProtocaasComputeResource | undefined> => {
    const url = `/api/gui/compute_resources/${computeResourceId}`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchComputeResource: ${response.error}`)
    return response.computeResource
}

export const registerComputeResource = async (computeResourceId: string, resourceCode: string, name: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/compute_resources/register`
    const response = await postRequest(url, {computeResourceId, resourceCode, name}, auth)
    if (!response.success) throw Error(`Error in registerComputeResource: ${response.error}`)
}

export const deleteComputeResource = async (computeResourceId: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/compute_resources/${computeResourceId}`
    const resp = await deleteRequest(url, auth)
    if (!resp.success) throw Error(`Error in deleteComputeResource: ${resp.error}`)
}

export type App = {
    name: string
    executablePath: string
    container?: string
    awsBatch?: ComputeResourceAwsBatchOpts
    slurm?: ComputeResourceSlurmOpts
}

export const setComputeResourceApps = async (computeResourceId: string, apps: App[], auth: Auth): Promise<void> => {
    const url = `/api/gui/compute_resources/${computeResourceId}/apps`
    const response = await putRequest(url, {apps}, auth)
    if (!response.success) throw Error(`Error in setComputeResourceApps: ${response.error}`)
}

export type ProtocaasProcessingJobDefinition = {
    processorName: string,
    inputFiles: {
        name: string
        fileName: string
    }[],
    inputParameters: {
        name: string
        value: any
    }[],
    outputFiles: {
        name: string
        fileName: string
    }[]
}

export type ProtocaasProcessingJobDefinitionAction = {
    type: 'setInputFile'
    name: string
    fileName: string
} | {
    type: 'setInputParameter'
    name: string
    value: any
} | {
    type: 'setOutputFile'
    name: string
    fileName: string
} | {
    type: 'setProcessorName'
    processorName: string
} | {
    type: 'setJobDefinition'
    jobDefinition: ProtocaasProcessingJobDefinition
}

export const defaultJobDefinition: ProtocaasProcessingJobDefinition = {
    processorName: '',
    inputFiles: [],
    inputParameters: [],
    outputFiles: []
}

export const protocaasJobDefinitionReducer = (state: ProtocaasProcessingJobDefinition, action: ProtocaasProcessingJobDefinitionAction): ProtocaasProcessingJobDefinition => {

    switch (action.type) {
        case 'setInputFile':
            // check if no change
            if (state.inputFiles.find(f => f.name === action.name && f.fileName === action.fileName)) {
                return state
            }
            return {
                ...state,
                inputFiles: state.inputFiles.map(f => f.name === action.name ? {...f, fileName: action.fileName} : f)
            }
        case 'setInputParameter':
            // check if no change
            if (state.inputParameters.find(p => p.name === action.name && deepEqual(p.value, action.value))) {
                return state
            }
            return {
                ...state,
                inputParameters: state.inputParameters.map(p => p.name === action.name ? {...p, value: action.value} : p)
            }
        case 'setOutputFile':
            // check if no change
            if (state.outputFiles.find(f => f.name === action.name && f.fileName === action.fileName)) {
                return state
            }
            return {
                ...state,
                outputFiles: state.outputFiles.map(f => f.name === action.name ? {...f, fileName: action.fileName} : f)
            }
        case 'setProcessorName':
            // check if no change
            if (state.processorName === action.processorName) {
                return state
            }
            return {
                ...state,
                processorName: action.processorName
            }
        case 'setJobDefinition':
            return action.jobDefinition
        default:
            throw Error(`Unexpected action type ${(action as any).type}`)
    }
}

export const createJob = async (
    a: {
        projectId: string,
        jobDefinition: ProtocaasProcessingJobDefinition,
        processorSpec: ComputeResourceSpecProcessor,
        files: ProtocaasFile[],
        batchId?: string
    },
    auth: Auth
) : Promise<string> => {
    const {projectId, jobDefinition, processorSpec, files, batchId} = a
    const processorName = jobDefinition.processorName
    const inputFiles = jobDefinition.inputFiles
    const inputParameters = jobDefinition.inputParameters
    const outputFiles = jobDefinition.outputFiles
    const url = `/api/gui/jobs`
    let needToSendDandiApiKey = false
    let needToSendDandiStagingApiKey = false
    for (const inputFile of inputFiles) {
        const ff = files.find(f => f.fileName === inputFile.fileName)
        if (ff) {
            if (ff.content.startsWith('url:')) {
                const url = ff.content.slice('url:'.length)
                if (url.startsWith('https://api.dandiarchive.org/api/')) {
                    needToSendDandiApiKey = true
                }
                if (url.startsWith('https://api-staging.dandiarchive.org/api/')) {
                    needToSendDandiStagingApiKey = true
                }
            }
        }
    }
    let dandiApiKey: string | undefined = undefined
    if (needToSendDandiApiKey) {
        dandiApiKey = localStorage.getItem('dandiApiKey') || undefined
    }
    else if (needToSendDandiStagingApiKey) {
        dandiApiKey = localStorage.getItem('dandiStagingApiKey') || undefined
    }
    const body: {[key: string]: any} = {
        projectId,
        processorName,
        inputFiles,
        inputParameters,
        outputFiles,
        processorSpec,
        batchId
    }
    if (dandiApiKey) {
        body.dandiApiKey = dandiApiKey
    }
    const response = await postRequest(url, body, auth)
    if (!response.success) throw Error(`Error in createJob: ${response.error}`)
    return response.jobId
}

export const deleteJob = async (jobId: string, auth: Auth): Promise<void> => {
    const url = `/api/gui/jobs/${jobId}`
    const resp = await deleteRequest(url, auth)
    if (!resp.success) throw Error(`Error in deleteJob: ${resp.error}`)
}

export const fetchJobsForProject = async (projectId: string, auth: Auth): Promise<ProtocaasJob[]> => {
    const url = `/api/gui/projects/${projectId}/jobs`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchJobsForProject: ${response.error}`)
    return response.jobs
}

export const fetchJobsForComputeResource = async (computeResourceId: string, auth: Auth): Promise<ProtocaasJob[]> => {
    const url = `/api/gui/compute_resources/${computeResourceId}/jobs`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchJobsForComputeResource: ${response.error}`)
    return response.jobs
}

export const fetchJob = async (jobId: string, auth: Auth): Promise<ProtocaasJob | undefined> => {
    const url = `/api/gui/jobs/${jobId}`
    const response = await getRequest(url, auth)
    if (!response.success) throw Error(`Error in fetchJob: ${response.error}`)
    return response.job
}

export const getComputeResource = async (computeResourceId: string): Promise<any> => {
    const url = `/api/gui/compute_resources/${computeResourceId}`
    const response = await getRequest(url, undefined)
    if (!response.success) throw Error(`Error in getComputeResource: ${response.error}`)
    return response.computeResource
}

const deepEqual = (a: any, b: any): boolean => {
    if (typeof a !== typeof b) {
        return false
    }
    if (typeof a === 'object') {
        if (Array.isArray(a)) {
            if (!Array.isArray(b)) {
                return false
            }
            if (a.length !== b.length) {
                return false
            }
            for (let i = 0; i < a.length; i++) {
                if (!deepEqual(a[i], b[i])) {
                    return false
                }
            }
            return true
        }
        else {
            const aKeys = Object.keys(a)
            const bKeys = Object.keys(b)
            if (aKeys.length !== bKeys.length) {
                return false
            }
            for (const key of aKeys) {
                if (!deepEqual(a[key], b[key])) {
                    return false
                }
            }
            return true
        }
    }
    else {
        return a === b
    }
}