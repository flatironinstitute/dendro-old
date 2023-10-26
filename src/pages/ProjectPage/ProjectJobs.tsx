import { FunctionComponent, useState } from "react";
import Splitter from "../../components/Splitter";
import JobsTable from "./JobsWindow/JobsTable";
import JobView from "./JobView/JobView";
import { useProject } from "./ProjectPageContext";

const ProjectJobs: FunctionComponent<{}> = ({ }) => {
    const {jobs} = useProject()
    const [selectedJobId, setSelectedJobId] = useState<string | undefined>(undefined)

    return (
        <Splitter
            initialPosition={1 / 2}
            direction="horizontal"
            hideSecondChild={selectedJobId === undefined || (!jobs?.map(j => j.jobId).includes(selectedJobId))}
        >
            <JobsTable
                height={0}
                fileName=""
                jobs={jobs}
                onJobClicked={jobId => setSelectedJobId(jobId)}
            />
            <JobView
                jobId={selectedJobId || ''}
            />
        </Splitter>
    )
}

export default ProjectJobs