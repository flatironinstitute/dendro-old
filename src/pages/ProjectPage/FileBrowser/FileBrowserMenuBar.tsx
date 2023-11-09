import { Delete, Refresh, Settings } from "@mui/icons-material"
import { FunctionComponent, useCallback, useMemo, useState } from "react"
import SmallIconButton from "../../../components/SmallIconButton"
import { confirm } from "../../../confirm_prompt_alert"
import prepareDandiUploadTask, { DandiUploadTask } from "../DandiUpload/prepareDandiUploadTask"
import { useProject } from "../ProjectPageContext"
import DropdownMenu from "./DropdownMenu"

type FileBrowserMenuBarProps = {
    width: number
    height: number
    selectedFileNames: string[]
    onResetSelection: () => void
    onRunBatchSpikeSorting?: (filePaths: string[]) => void
    onDandiUpload?: (dandiUploadTask: DandiUploadTask) => void
    onUploadSmallFile?: () => void
}

const FileBrowserMenuBar: FunctionComponent<FileBrowserMenuBarProps> = ({ width, height, selectedFileNames, onResetSelection, onRunBatchSpikeSorting, onDandiUpload, onUploadSmallFile }) => {
    const {deleteFile, refreshFiles, projectRole} = useProject()
    const [operating, setOperating] = useState(false)
    const handleDelete = useCallback(async () => {
        if (!['admin', 'editor'].includes(projectRole || '')) {
            alert('You are not authorized to delete files in this project.')
            return
        }
        const okay = await confirm(`Are you sure you want to delete these ${selectedFileNames.length} files?`)
        if (!okay) return
        try {
            setOperating(true)
            for (const fileName of selectedFileNames) {
                await deleteFile(fileName)
            }
        }
        finally {
            setOperating(false)
            refreshFiles()
            onResetSelection()
        }
    }, [selectedFileNames, deleteFile, refreshFiles, onResetSelection, projectRole])

    const dandiUploadTask = useMemo(() => (
        prepareDandiUploadTask(selectedFileNames)
    ), [selectedFileNames])

    return (
        <div style={{display: 'flex'}}>
            {/* <SmallIconButton
                icon={<Add />}
                disabled={operating}
                title="Add a new file"
                label="Add file"
                onClick={openNewFileWindow}
            />
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; */}
            {/* Refresh */}
            <SmallIconButton
                icon={<Refresh />}
                disabled={operating}
                title="Refresh"
                onClick={refreshFiles}
            />
            <SmallIconButton
                icon={<Delete />}
                disabled={(selectedFileNames.length === 0) || operating}
                title={selectedFileNames.length > 0 ? `Delete these ${selectedFileNames.length} files` : ''}
                onClick={handleDelete}
            />
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {
                onRunBatchSpikeSorting && (
                    <SmallIconButton
                        icon={<Settings />}
                        disabled={(selectedFileNames.length === 0) || operating}
                        title={selectedFileNames.length > 0 ? `Run spike sorting on these ${selectedFileNames.length} files` : ''}
                        onClick={() => onRunBatchSpikeSorting(selectedFileNames)}
                        label="Run spike sorting"
                    />
                )
            }
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {
                dandiUploadTask && onDandiUpload && (
                    <SmallIconButton
                        icon={<Settings />}
                        title={selectedFileNames.length > 0 ? `Upload these ${selectedFileNames.length} files to DANDI` : ''}
                        onClick={() => onDandiUpload(dandiUploadTask)}
                        label="Upload to DANDI"
                    />
                )
            }
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            {
                <DropdownMenu
                    options={[
                        {label: 'Upload small file', onClick: onUploadSmallFile}
                    ]}
                />
            }
        </div>
    )
}

export default FileBrowserMenuBar