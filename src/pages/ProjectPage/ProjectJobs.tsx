import { FunctionComponent, useMemo, useState } from "react";
import { Splitter } from "@fi-sci/splitter";
import JobsTable from "./JobsWindow/JobsTable";
import JobView from "./JobView/JobView";
import { useProject } from "./ProjectPageContext";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";

const ProjectJobs: FunctionComponent<{width: number, height: number}> = ({width, height}) => {
    const {jobs, computeResource} = useProject()
    const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined)

    const auth = useGithubAuth()

    const userIsComputeResourceOwner = useMemo(() => {
        if (!computeResource) return false
        if (!auth.userId) return false
        return computeResource.ownerId === auth.userId
    }, [computeResource, auth.userId])

    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={width / 2}
            direction="horizontal"
            hideSecondChild={selectedJobId === undefined || (!jobs?.map(j => j.jobId).includes(selectedJobId))}
        >
            <JobsTable
                width={0}
                height={0}
                fileName=""
                jobs={jobs}
                onJobClicked={jobId => setSelectedJobId(jobId)}
                userCanApproveJobs={userIsComputeResourceOwner}
            />
            <JobView
                width={0}
                height={0}
                jobId={selectedJobId || ''}
            />
        </Splitter>
    )
}

export default ProjectJobs