import { FunctionComponent, useState } from "react";
import Splitter from "../../components/Splitter";
import JobsTable from "./JobsWindow/JobsTable";
import JobView from "./JobView/JobView";
import { useProject } from "./ProjectPageContext";

const ProjectJobs: FunctionComponent<{width: number, height: number}> = ({width, height}) => {
    const {jobs} = useProject()
    const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined)

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