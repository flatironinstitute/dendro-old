import { FunctionComponent, useMemo, useState } from "react";
import Splitter from "../../../components/Splitter";
import JobsWindow from "../JobsWindow/JobsWindow";
import { useProject } from "../ProjectPageContext";
import TextEditor from "./TextEditor";

type Props = {
    fileName: string
    fileContent: string
    onSaveContent: (text: string) => void
    editedFileContent: string
    setEditedFileContent: (text: string) => void
    readOnly: boolean
    width: number
    height: number
}

const queryStringUrl = window.location.search
const queryParams = new URLSearchParams(queryStringUrl)

const ScriptFileEditor: FunctionComponent<Props> = ({fileName, fileContent, onSaveContent, editedFileContent, setEditedFileContent, readOnly, width, height}) => {
    const fileType = fileName.split('.').pop()

    const {jobs, openTabs, projectRole} = useProject()

    const [createJobTitle, setCreateJobTitle] = useState('Create job')

    const filteredJobs = useMemo(() => {
        if (!jobs) return undefined
        if (fileName.endsWith('.py')) {
            return jobs.filter(jj => (jj.processorName === 'script' && jj.inputParameters.map(f => (f.value).includes(fileName))))
        }
        else if (fileName.endsWith('.nwb')) {
            return jobs.filter(jj => (jj.inputFiles.map(x => (x.fileName)).includes(fileName)))
        }
        else return jobs
    }, [jobs, fileName])

    const canCreateJob = useMemo(() => {
        if (!jobs) return false // not loaded yet
        const openTab = openTabs.find(t => t.tabName === `file:${fileName}`)
        if (!openTab) {
            setCreateJobTitle('Unable to find open tab')
            return false
        }
        if (!openTab.content) {
            setCreateJobTitle('File is empty')
            return false
        }
        if (openTab.content !== openTab.editedContent) {
            setCreateJobTitle('File has unsaved changes')
            return false
        }
        const pendingJob = filteredJobs && filteredJobs.find(jj => (jj.status === 'pending'))
        const runningJob = filteredJobs && filteredJobs.find(jj => (jj.status === 'running'))
        if ((pendingJob) || (runningJob)) {
            if (!(queryParams.get('test') === '1')) {
                setCreateJobTitle('A job is already pending or running for this script.')
                return false
            }
        }
        if (projectRole === 'admin' || projectRole === 'editor') {
            setCreateJobTitle('Create job')
            return true
        }
        else {
            setCreateJobTitle('You do not have permission to run scripts for this project.')
        }
        return false
    }, [openTabs, jobs, filteredJobs, fileName, projectRole])

    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={height * 2 / 3}
            direction="vertical"
        >
            {
                <TextEditor
                    width={0}
                    height={0}
                    language={
                        fileType === 'py' ? 'python' :
                        'text'
                    }
                    label={fileName}
                    text={fileContent}
                    onSaveText={onSaveContent}
                    editedText={editedFileContent}
                    onSetEditedText={setEditedFileContent}
                    readOnly={readOnly}
                />
            }
            <JobsWindow
                width={0}
                height={0}
                fileName={fileName}
                createJobEnabled={canCreateJob}
                createJobTitle={createJobTitle}
            />
        </Splitter>
    )
}

export default ScriptFileEditor