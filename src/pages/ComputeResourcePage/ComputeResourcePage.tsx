import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react";
import ComputeResourceNameDisplay from "../../ComputeResourceNameDisplay";
import { App, fetchComputeResource, fetchJobsForComputeResource, setComputeResourceApps } from "../../dbInterface/dbInterface";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { timeAgoString } from "../../timeStrings";
import { DendroComputeResource, DendroJob } from "../../types/dendro-types";
import UserIdComponent from "../../UserIdComponent";
import JobsTable from "../ProjectPage/JobsWindow/JobsTable";
import ComputeResourceAppsTable from "./ComputeResourceAppsTable";

type Props = {
    width: number
    height: number
    computeResourceId: string
}

const ComputeResourcesPage: FunctionComponent<Props> = ({width, height, computeResourceId}) => {
    const [computeResource, setComputeResources] = useState<DendroComputeResource>()

    const auth = useGithubAuth()

    const [refreshCode, setRefreshCode] = useState(0)
    const refreshComputeResource = useCallback(() => {
        setRefreshCode(c => c + 1)
    }, [])

    useEffect(() => {
        let canceled = false
        ;(async () => {
            const cr = await fetchComputeResource(computeResourceId, auth)
            if (canceled) return
            setComputeResources(cr)
        })()
        return () => {canceled = true}
    }, [computeResourceId, auth, refreshCode])

    const [jobs, setJobs] = useState<DendroJob[] | undefined>()

    useEffect(() => {
        (async () => {
            const sj = await fetchJobsForComputeResource(computeResourceId, auth)
            setJobs(sj)
        })()
    }, [computeResourceId, auth])

    const sortedJobs = useMemo(() => {
        return jobs ? [...jobs].sort((a, b) => (b.timestampCreated - a.timestampCreated))
            .sort((a, b) => {
                const statuses = ['running', 'starting', 'pending', 'failed', 'completed']
                return statuses.indexOf(a.status) - statuses.indexOf(b.status)
            }) : undefined
    }, [jobs])

    const handleNewApp = useCallback((name: string, specUri: string) => {
        if (!computeResource) return
        const oldApps = computeResource.apps
        const newApps: App[] = [...oldApps.filter(a => (a.name !== name)), {name, specUri}]
        setComputeResourceApps(computeResource.computeResourceId, newApps, auth).then(() => {
            refreshComputeResource()
        })
    }, [computeResource, refreshComputeResource, auth])

    const handleDeleteApps = useCallback((appNames: string[]) => {
        if (!computeResource) return
        const oldApps = computeResource.apps
        const newApps = oldApps.filter(a => !appNames.includes(a.name))
        setComputeResourceApps(computeResource.computeResourceId, newApps, auth).then(() => {
            refreshComputeResource()
        })
    }, [computeResource, refreshComputeResource, auth])

    const appsTableHeight = 200
    const jobsTableHeight = 500

    const userOwnsComputeResource = useMemo(() => {
        return computeResource?.ownerId === auth?.userId
    }, [computeResource, auth])

    return (
        <div style={{padding: 20, overflowY: 'auto', position: 'absolute', width, height}}>
            <h3>
                Compute resource: {computeResource?.name}
            </h3>
            <hr />
            <table className="table1" style={{maxWidth: 550}}>
                <tbody>
                    <tr>
                        <td>Compute resource name</td>
                        <td>{computeResource?.name}</td>
                    </tr>
                    <tr>
                        <td>Compute resource ID</td>
                        <td><ComputeResourceNameDisplay computeResourceId={computeResourceId} /></td>
                    </tr>
                    <tr>
                        <td>Owner</td>
                        <td><UserIdComponent userId={computeResource?.ownerId || ''} /></td>
                    </tr>
                    <tr>
                        <td>Created</td>
                        <td>{timeAgoString(computeResource?.timestampCreated)}</td>
                    </tr>
                </tbody>
            </table>
            <hr />
            <p>Full ID: {computeResource?.computeResourceId}</p>
            <hr />
            <h4>Apps</h4>
            {computeResource && <ComputeResourceAppsTable
                width={width}
                height={appsTableHeight}
                computeResource={computeResource}
                onNewApp={handleNewApp}
                onEditApp={handleNewApp}
                onDeleteApps={handleDeleteApps}
            />}
            <hr />
            <h4>Jobs</h4>
            <JobsTable
                width={width}
                height={jobsTableHeight}
                jobs={sortedJobs}
                fileName={""}
                onJobClicked={() => {}}
                userCanApproveJobs={userOwnsComputeResource}
            />
        </div>
    )
}

export default ComputeResourcesPage