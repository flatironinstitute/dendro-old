import { FunctionComponent, PropsWithChildren, useCallback, useEffect, useMemo, useState } from "react";
import ComputeResourceNameDisplay from "../../../ComputeResourceNameDisplay";
import { defaultJobDefinition, fetchJob, ProtocaasProcessingJobDefinition } from "../../../dbInterface/dbInterface";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";
import { ProtocaasJob } from "../../../types/protocaas-types";
import UserIdComponent from "../../../UserIdComponent";
import EditJobDefinitionWindow from "../EditJobDefinitionWindow/EditJobDefinitionWindow";
import { ElapsedTimeComponent } from "../FileEditor/NwbFileEditor";

type Props = {
    width: number,
    height: number,
    jobId: string
}

const useJob = (jobId: string) => {
    const [job, setJob] = useState<ProtocaasJob | undefined>()

    const [refreshCode, setRefreshCode] = useState(0)
    const refreshJob = useCallback(() => {
        setRefreshCode(rc => rc + 1)
    }, [])

    const [jobConsoleOutput, setJobConsoleOutput] = useState<string | undefined>()

    const {accessToken, userId} = useGithubAuth()
    const auth = useMemo(() => (accessToken ? {githubAccessToken: accessToken, userId} : {}), [accessToken, userId])

    useEffect(() => {
        let canceled = false
        ;(async () => {
            setJob(undefined)
            if (!jobId) return
            const job = await fetchJob(jobId, auth)
            if (canceled) return

            setJob(job)

            if (job?.consoleOutput) {
                setJobConsoleOutput(job.consoleOutput)
            }
            else if (job?.consoleOutputUrl) {
                // fetch console output
                const resp = await fetch(job.consoleOutputUrl)
                if (resp.ok) {
                    const text = await resp.text()
                    setJobConsoleOutput(text)
                }
            }
        })()
        return () => {
            canceled = true
        }
    }, [jobId, auth, refreshCode])
    return {job, refreshJob, jobConsoleOutput}
}

const JobView: FunctionComponent<Props> = ({ width, height, jobId }) => {
    const {job, refreshJob, jobConsoleOutput} = useJob(jobId)
    const secretParameterNames = useMemo(() => {
        if (!job) return []
        return job.processorSpec.parameters.filter(p => p.secret).map(p => p.name)
    }, [job])
    const jobDefinition: ProtocaasProcessingJobDefinition = useMemo(() => {
        if (!job) return defaultJobDefinition
        const ret: ProtocaasProcessingJobDefinition = {
            inputFiles: job.inputFiles.map(f => ({
                name: f.name,
                fileName: f.fileName
            })),
            outputFiles: job.outputFiles.map(f => ({
                name: f.name,
                fileName: f.fileName
            })),
            inputParameters: job.inputParameters.map(p => ({
                name: p.name,
                value: p.value
            })),
            processorName: job.processorName
        }
        return ret
    }, [job])
    if (!job) {
        return (
            <p>Loading job {jobId}</p>
        )
    }
    return (
        <div style={{position: 'absolute', width, height, background: 'white', overflowY: 'auto'}}>
            <hr />
            <button onClick={refreshJob}>Refresh</button>
            <hr />
            <table className="table1">
                <tbody>
                    <tr>
                        <td>Job ID:</td>
                        <td>{job.jobId}</td>
                    </tr>
                    <tr>
                        <td>User:</td>
                        <td><UserIdComponent userId={job.userId} /></td>
                    </tr>
                    <tr>
                        <td>Processor:</td>
                        <td>{job.processorName}</td>
                    </tr>
                    <tr>
                        <td>Compute resource:</td>
                        <td><ComputeResourceNameDisplay computeResourceId={job.computeResourceId} link={true} /></td>
                    </tr>
                    <tr>
                        <td>Node:</td>
                        <td>{job.computeResourceNodeId ? `${job.computeResourceNodeName} (${job.computeResourceNodeId})`: ''}</td>
                    </tr>
                    <tr>
                        <td>Job status:</td>
                        <td>{job.status}</td>
                    </tr>
                    <tr>
                        <td>Error:</td>
                        <td style={{color: 'red'}}>{job.error}</td>
                    </tr>
                    <tr>
                        <td>Elapsed time (sec):</td>
                        <td><ElapsedTimeComponent job={job} /></td>
                    </tr>
                </tbody>
            </table>
            <hr />
            <ExpandableSection title="Files" defaultExpanded={true}>
                <EditJobDefinitionWindow
                    processor={job.processorSpec}
                    jobDefinition={jobDefinition}
                    readOnly={true}
                    show={'inputs+outputs'}
                    fileLinks={true}
                />
            </ExpandableSection>
            <hr />
            <ExpandableSection title="Parameters">
                <EditJobDefinitionWindow
                    processor={job.processorSpec}
                    jobDefinition={jobDefinition}
                    secretParameterNames={secretParameterNames}
                    readOnly={true}
                    show={'parameters'}
                    fileLinks={true}
                />
            </ExpandableSection>
            <hr />
            <ExpandableSection title="Console output" defaultExpanded={true}>
                <pre style={{fontSize: 10}}>
                    {jobConsoleOutput}
                </pre>
            </ExpandableSection>
            <hr />
        </div>
    )
}

type ExpandableSectionProps = {
    title: string
    defaultExpanded?: boolean
}

const ExpandableSection: FunctionComponent<PropsWithChildren<ExpandableSectionProps>> = ({ title, children, defaultExpanded }) => {
    const [expanded, setExpanded] = useState(false)
    useEffect(() => {
        if (defaultExpanded) setExpanded(true)
    }, [defaultExpanded])
    return (
        <div>
            <div style={{ cursor: 'pointer' }} onClick={() => { setExpanded(!expanded) }}>{expanded ? '▼' : '►'} {title}</div>
            {
                expanded && (
                    <div>
                        {children}
                    </div>
                )
            }
        </div>
    )
}

export default JobView