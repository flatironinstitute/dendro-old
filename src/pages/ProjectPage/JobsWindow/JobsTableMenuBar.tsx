import { Delete, Refresh } from "@mui/icons-material"
import { FunctionComponent, useCallback, useState } from "react"
import SmallIconButton from "../../../components/SmallIconButton"
import { confirm } from "../../../confirm_prompt_alert"
import { useProject } from "../ProjectPageContext"

type JobsTableMenuBarProps = {
    width: number
    height: number
    selectedJobIds: string[]
    onResetSelection: () => void
    createJobEnabled?: boolean
    createJobTitle?: string
}

const JobsTableMenuBar: FunctionComponent<JobsTableMenuBarProps> = ({width, height, selectedJobIds, onResetSelection, createJobEnabled, createJobTitle}) => {
    const {deleteJob, refreshJobs, projectRole} = useProject()
    const [operating, setOperating] = useState(false)
    const handleDelete = useCallback(async () => {
        if (!['admin', 'editor'].includes(projectRole || '')) {
            alert('You are not authorized to delete jobs in this project.')
            return
        }
        const okay = await confirm(`Are you sure you want to delete these ${selectedJobIds.length} jobs?`)
        if (!okay) return
        try {
            setOperating(true)
            for (const jobId of selectedJobIds) {
                await deleteJob(jobId)
            }
        }
        finally {
            setOperating(false)
            refreshJobs()
            onResetSelection()
        }
    }, [selectedJobIds, deleteJob, refreshJobs, onResetSelection, projectRole])

    return (
        <div>
            <SmallIconButton
                icon={<Refresh />}
                disabled={operating}
                title='Refresh'
                onClick={refreshJobs}
            />
            <SmallIconButton
                icon={<Delete />}
                disabled={(selectedJobIds.length === 0) || operating}
                title={selectedJobIds.length > 0 ? `Delete these ${selectedJobIds.length} jobs` : ''}
                onClick={handleDelete}
            />
        </div>
    )
}

export default JobsTableMenuBar