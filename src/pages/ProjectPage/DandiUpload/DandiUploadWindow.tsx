import { FunctionComponent, useCallback, useMemo } from "react";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";
import { DendroProcessingJobDefinition, createJob } from "../../../dbInterface/dbInterface";
import { useProject } from "../ProjectPageContext";
import { DandiUploadTask } from "./prepareDandiUploadTask";
import { DendroFile, DendroJob } from "../../../types/dendro-types";

type DandiUploadWindowProps = {
    dandiUploadTask: DandiUploadTask
    onClose: () => void
}

const DandiUploadWindow: FunctionComponent<DandiUploadWindowProps> = ({ dandiUploadTask, onClose }) => {
    const {projectId, files, jobs, projectRole, computeResource} = useProject()
    const processor = useMemo(() => {
        if (!computeResource) return undefined
        for (const app of computeResource.spec?.apps || []) {
            for (const p of app.processors || []) {
                if (p.name === 'dandi_upload') {
                    return p
                }
            }
        }
        return undefined
    }, [computeResource])
    const dandiApiKey = useMemo(() => {
        if (dandiUploadTask.dandiInstance === 'dandi') {
            return localStorage.getItem('dandiApiKey') || ''
        }
        else if (dandiUploadTask.dandiInstance === 'dandi-staging') {
            return localStorage.getItem('dandiStagingApiKey') || ''
        }
        else return ''
    }, [dandiUploadTask.dandiInstance])

    const auth = useGithubAuth()

    const handleUpload = useCallback(async () => {
        if (!processor) return
        if (!files) return
        if (!jobs) return
        const wasGeneratedByList: any[] = []
        for (const fileName of dandiUploadTask.fileNames) {
            const file = files.find(f => f.fileName === fileName)
            if (!file) {
                throw new Error(`Unexpected: file not found in project: ${fileName}`)
            }
            const job = file.jobId ? jobs.find(j => j.jobId === file.jobId) : undefined
            wasGeneratedByList.push(createWasGeneratedByForFile(file, job, files))
        }
        const jobDef: DendroProcessingJobDefinition = {
            processorName: processor.name,
            inputFiles: dandiUploadTask.fileNames.map((fileName, ii) => ({
                name: `inputs[${ii}]`,
                fileName
            })),
            inputParameters: [
                {
                    name: 'dandiset_id',
                    value: dandiUploadTask.dandisetId
                },
                {
                    name: 'dandi_instance',
                    value: dandiUploadTask.dandiInstance
                },
                {
                    name: 'dandi_api_key',
                    value: dandiApiKey
                },
                {
                    name: 'names',
                    value: dandiUploadTask.names
                },
                {
                    name: 'was_generated_by_jsons',
                    value: wasGeneratedByList.map(x => JSON.stringify(x))
                }
            ],
            outputFiles: []
        }
        const job = {
            projectId,
            jobDefinition: jobDef,
            processorSpec: processor,
            files,
            batchId: undefined
        }
        console.log('CREATING JOB', job)
        await createJob(job, auth)
        onClose()
    }, [processor, dandiUploadTask, projectId, files, auth, dandiApiKey, onClose, jobs])

    if (!['admin', 'editor'].includes(projectRole || '')) {
        return (
            <div>
                <span style={{color: 'red'}}>You are not authorized to upload to DANDI from this project.</span>
            </div>
        )
    }

    return (
        <div style={{padding: 30}}>
            <h3>DANDI Upload</h3>
            <hr />
            <div>
                <table className="table1">
                    <tbody>
                        <tr>
                            <td>Dandiset ID: </td>
                            <td>{dandiUploadTask.dandisetId}</td>
                        </tr>
                        <tr>
                            <td>Dandiset version: </td>
                            <td>draft</td>
                        </tr>
                        <tr>
                            <td>DANDI Instance: </td>
                            <td>{dandiUploadTask.dandiInstance}</td>
                            <td></td>
                        </tr>
                        <tr>
                            <td>Files: </td>
                            <td>{dandiUploadTask.names.map(name => (
                                <span key={name}><span>{name}</span><br /></span>
                            ))}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <hr />
            <div>
                {!processor && (
                    <div style={{color: 'red'}}>
                        <p>Processor not found: dandi_upload</p>
                    </div>
                )}
                {!dandiApiKey && (
                    <div style={{color: 'red'}}>
                        <p>{dandiUploadTask.dandiInstance} API key not found</p>
                    </div>
                )}
            </div>
            <div>
                <button disabled={!processor || !dandiApiKey} onClick={handleUpload}>Upload</button>
                &nbsp;&nbsp;
                <button onClick={onClose}>Cancel</button>
            </div>
        </div>
    )
}

const createWasGeneratedByForFile = (file: DendroFile, job: DendroJob | undefined, files: DendroFile[]) => {
    return {
        name: "dendro",
        projectId: file.projectId,
        jobId: job?.jobId,
        processorName: job?.processorName,
        processorVersion: job?.processorVersion,
        job: job ? {
            inputParameters: job?.inputParameters.map(p => {
                return {name: p.name, value: p.value} // don't include the "secret" boolean here
            }),
            inputFiles: job?.inputFiles.map(f => {
                const f2 = files.find(f2 => f2.fileName === f.fileName)
                const metadata = f2?.metadata
                return {name: f.name, fileName: f.fileName, metadata}
            }),
            outputFiles: job?.outputFiles.map(f => {
                return {name: f.name, fileName: f.fileName}
            }),
            timestampCreated: job.timestampCreated,
            timestampFinished: job.timestampFinished,
            computeResourceId: job.computeResourceId,
        } : undefined
    }
}

export default DandiUploadWindow