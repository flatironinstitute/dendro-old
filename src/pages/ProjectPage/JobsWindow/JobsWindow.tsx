import { FunctionComponent, useMemo } from "react";
import { useProject } from "../ProjectPageContext";
import JobsTable from "./JobsTable";

type Props = {
    width: number,
    height: number,
    fileName: string
    createJobEnabled?: boolean
    createJobTitle?: string
}

const JobsWindow: FunctionComponent<Props> = ({ width, height, fileName, createJobEnabled, createJobTitle }) => {
    const {jobs, openTab} = useProject()

    const filteredJobs = useMemo(() => {
        if (!jobs) return undefined
        if (fileName) {
            return jobs.filter(jj => (
                jj.inputFiles.map(x => (x.fileName)).includes(fileName) ||
                jj.outputFiles.map(x => (x.fileName)).includes(fileName)
            ))
        }
        else return jobs
    }, [jobs, fileName])

    // const iconFontSize = 20

    return (
        <JobsTable
            width={width}
            height={height}
            fileName={fileName}
            jobs={filteredJobs}
            onJobClicked={jobId => openTab(`job:${jobId}`)}
            createJobEnabled={createJobEnabled}
            createJobTitle={createJobTitle}
        />
        // <>
        //     <div>
        //         {fileName.endsWith('.py') && (
        //             <SmallIconButton
        //                 icon={<PlayArrow />}
        //                 onClick={handleCreateScriptJob}
        //                 disabled={!canCreateJob}
        //                 title={createJobTitle}
        //                 label="Run"
        //                 fontSize={iconFontSize}
        //             />
        //         )}
        //         &nbsp;&nbsp;&nbsp;&nbsp;
        //         <SmallIconButton
        //             icon={<Refresh />}
        //             onClick={refreshJobs}
        //             title="Refresh jobs"
        //             label="Refresh"
        //             fontSize={iconFontSize}
        //         />                
        //     </div>
        // </>
    )
}

export default JobsWindow