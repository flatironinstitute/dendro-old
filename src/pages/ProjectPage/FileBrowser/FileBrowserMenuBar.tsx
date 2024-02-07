import { Add, Delete, Preview, Refresh, Settings } from "@mui/icons-material"
import { FunctionComponent, useCallback, useMemo, useState } from "react"
import { SmallIconButton } from "@fi-sci/misc";
import { confirm } from "../../../confirm_prompt_alert"
import { PluginAction } from "../../../plugins/DendroFrontendPlugin"
import initializePlugins from "../../../plugins/initializePlugins"
import useRoute from "../../../useRoute"
import prepareDandiUploadTask, { DandiUploadTask } from "../DandiUpload/prepareDandiUploadTask"
import { useProject } from "../ProjectPageContext"
import DropdownMenu from "./DropdownMenu"

type FileBrowserMenuBarProps = {
    width: number
    height: number
    selectedFileNames: string[]
    onResetSelection: () => void
    onRunBatchSpikeSorting?: (filePaths: string[]) => void
    onGenerateSpikeSortingSummary?: (filePaths: string[]) => void
    onOpenInNeurosift?: (filePaths: string[]) => void
    onDandiUpload?: (dandiUploadTask: DandiUploadTask) => void
    onUploadSmallFile?: () => void
    onAction?: (action: PluginAction) => void
}

const {actions} = initializePlugins()

const FileBrowserMenuBar: FunctionComponent<FileBrowserMenuBarProps> = ({ width, height, selectedFileNames, onResetSelection, onRunBatchSpikeSorting, onGenerateSpikeSortingSummary, onOpenInNeurosift, onDandiUpload, onUploadSmallFile, onAction }) => {
    const {deleteFile, refreshFiles, projectRole} = useProject()
    const {route, setRoute} = useRoute()
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

    const okayToRunSpikeSorting = useMemo(() => (
        selectedFileNames.length > 0 && selectedFileNames.every(fn => fn.startsWith('imported/'))
    ), [selectedFileNames])

    const okayToOpenInNeurosift = useMemo(() => (
        selectedFileNames.length > 0 && selectedFileNames.every(fn => fn.endsWith('.nwb')) && selectedFileNames.length <= 5
    ), [selectedFileNames])

    const okayToGenerateSpikeSortingSummary = useMemo(() => (
        selectedFileNames.length > 0 && selectedFileNames.every(fn => fn.endsWith('.nwb')) && selectedFileNames.length <= 5
    ), [selectedFileNames])

    const dropdownMenuOptions = useMemo(() => {
        const opts = []
        if (onUploadSmallFile) {
            opts.push({label: 'Upload small file', onClick: onUploadSmallFile})
        }
        if (onAction) {
            actions.forEach(action => {
                opts.push({
                    label: action.label,
                    onClick: () => {
                        onAction(action)
                    }
                })
            })
        }
        return opts
    }, [onUploadSmallFile, onAction])

    if (route.page !== 'project') {
        throw Error(`Unexpected route page: ${route.page}`)
    }

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
            
            {
                okayToRunSpikeSorting && onRunBatchSpikeSorting && (
                    <>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <SmallIconButton
                            icon={<Settings />}
                            disabled={(selectedFileNames.length === 0) || operating}
                            title={selectedFileNames.length > 0 ? `Run spike sorting on these ${selectedFileNames.length} files` : ''}
                            onClick={() => onRunBatchSpikeSorting(selectedFileNames)}
                            label="Run spike sorting"
                        />
                    </>
                )
            }
            {
                okayToGenerateSpikeSortingSummary && onGenerateSpikeSortingSummary && (
                    <>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <SmallIconButton
                            icon={<Settings />}
                            disabled={(selectedFileNames.length === 0) || operating}
                            title={selectedFileNames.length > 0 ? `Generate spike sorting summary for these ${selectedFileNames.length} files` : ''}
                            onClick={() => onGenerateSpikeSortingSummary(selectedFileNames)}
                            label="SSS"
                        />
                    </>
                )
            }
            {
                okayToOpenInNeurosift && onOpenInNeurosift && (
                    <>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <SmallIconButton
                            icon={<Preview />}
                            disabled={(selectedFileNames.length === 0) || operating}
                            title={selectedFileNames.length > 0 ? `Open these ${selectedFileNames.length} files in Neurosift` : ''}
                            onClick={() => onOpenInNeurosift(selectedFileNames)}
                            label="Open in Neurosift"
                        />
                    </>
                )
            }
            {
                dandiUploadTask && onDandiUpload && (
                    <>
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                        <SmallIconButton
                            icon={<Settings />}
                            title={selectedFileNames.length > 0 ? `Upload these ${selectedFileNames.length} files to DANDI` : ''}
                            onClick={() => onDandiUpload(dandiUploadTask)}
                            label="Upload to DANDI"
                        />
                    </>
                )
            }
            <>
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <SmallIconButton
                    icon={<Add />}
                    title="Import files from DANDI"
                    onClick={() => {setRoute({page: 'project', projectId: route.projectId, tab: 'dandi-import'})}}
                    label="DANDI Import"
                />
            </>
            &nbsp;&nbsp;&nbsp;
            {
                <DropdownMenu
                    options={dropdownMenuOptions}
                />
            }
        </div>
    )
}

export default FileBrowserMenuBar