import { FunctionComponent, useCallback, useMemo, useReducer } from "react";
import { PluginAction } from '../../../plugins/DendroFrontendPlugin';
import { DendroFile, DendroJob } from '../../../types/dendro-types';
import { DandiUploadTask } from '../DandiUpload/prepareDandiUploadTask';
import { useProject } from '../ProjectPageContext';
import FileBrowserMenuBar from './FileBrowserMenuBar';
import FileBrowserTable, { FileBrowserTableFile } from './FileBrowserTable';
import './file-browser-table.css';
import { approveJob } from "../../../dbInterface/dbInterface";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";

type Props = {
    width: number
    height: number
    files: DendroFile[] | undefined
    onOpenFile: (path: string) => void
    onDeleteFile: (path: string) => void
    hideSizeColumn?: boolean
    onRunBatchSpikeSorting?: (filePaths: string[]) => void
    onGenerateSpikeSortingSummary?: (filePaths: string[]) => void
    onOpenInNeurosift?: (filePaths: string[]) => void
    onDandiUpload?: (dandiUploadTask: DandiUploadTask) => void
    onUploadSmallFile?: () => void
    onAction?: (action: PluginAction) => void
}

export type SelectedStrings = Set<string>

export type SelectedStringsAction = {
    type: 'toggle'
    value: string
} | {
    type: 'set'
    values: Set<string>
} | {
    type: 'set-multiple'
    paths: string[]
    selected: boolean
} | {
    type: 'add'
    value: string
}

export const selectedStringsReducer = (state: SelectedStrings, action: SelectedStringsAction): SelectedStrings => {
    if (action.type === 'toggle') {
        const ret = new Set(state)
        if (ret.has(action.value)) {
            ret.delete(action.value)
        }
        else {
            ret.add(action.value)
        }
        return ret
    }
    else if (action.type === 'set') {
        return new Set(action.values)
    }
    else if (action.type === 'set-multiple') {
        const ret = new Set(state)
        for (const path of action.paths) {
            if (action.selected) {
                if (!ret.has(path)) ret.add(path)
            }
            else {
                if (ret.has(path)) ret.delete(path)
            }
        }
        return ret
    }
    else if (action.type === 'add') {
        const ret = new Set(state)
        ret.add(action.value)
        return ret
    }
    else {
        return state
    }
}

type ExpandedFoldersState = Set<string>

type ExpandedFoldersAction = {
    type: 'toggle'
    path: string
} | {
    type: 'set'
    paths: Set<string>
}

export const expandedFoldersReducer = (state: ExpandedFoldersState, action: ExpandedFoldersAction): ExpandedFoldersState => {
    if (action.type === 'toggle') {
        const ret = new Set(state)
        if (ret.has(action.path)) {
            ret.delete(action.path)
        }
        else {
            ret.add(action.path)
        }
        return ret
    }
    else if (action.type === 'set') {
        return new Set(action.paths)
    }
    else {
        return state
    }
}

const FileBrowser2: FunctionComponent<Props> = ({width, height, onOpenFile, files, hideSizeColumn, onRunBatchSpikeSorting, onGenerateSpikeSortingSummary, onOpenInNeurosift, onDandiUpload, onUploadSmallFile, onAction}) => {
    const {currentTabName, jobs, computeResource} = useProject()

    const [selectedFileNames, selectedFileNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const menuBarHeight = 30
    const hPadding = 20
    const vPadding = 5

    const files2: FileBrowserTableFile[] | undefined = useMemo(() => {
        if (!files) return undefined
        if (!jobs) return undefined
        const jobsById: {[key: string]: DendroJob} = {}
        for (const job of jobs) {
            jobsById[job.jobId] = job
        }
        return files.map(file => ({
            fileName: file.fileName,
            size: file.size,
            timestampCreated: file.timestampCreated,
            content: file.content,
            associatedJob: file.jobId ? jobsById[file.jobId] : undefined
        }))
    }, [files, jobs])

    const [jobsApprovedInThisSession, jobsApprovedInThisSessionDispatch] = useReducer(selectedStringsReducer, new Set<string>())
    
    const auth = useGithubAuth()

    const handleApproveJob = useCallback((jobId: string) => {
        approveJob(jobId, auth).then(() => {
            jobsApprovedInThisSessionDispatch({type: 'set', values: new Set([jobId])})
        })
    }, [auth])

    const userIsComputeResourceOwner = useMemo(() => {
        if (!computeResource) return false
        if (!auth.userId) return false
        return computeResource.ownerId === auth.userId
    }, [computeResource, auth.userId])
    
    return (
        <div style={{position: 'absolute', width, height, userSelect: 'none'}}>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: menuBarHeight - vPadding * 2, paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <FileBrowserMenuBar
                    width={width - hPadding * 2}
                    height={menuBarHeight - vPadding * 2}
                    selectedFileNames={Array.from(selectedFileNames)}
                    onResetSelection={() => selectedFileNamesDispatch({type: 'set', values: new Set()})}
                    onRunBatchSpikeSorting={onRunBatchSpikeSorting}
                    onGenerateSpikeSortingSummary={onGenerateSpikeSortingSummary}
                    onOpenInNeurosift={onOpenInNeurosift}
                    onDandiUpload={onDandiUpload}
                    onUploadSmallFile={onUploadSmallFile}
                    onAction={onAction}
                />
            </div>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: height - menuBarHeight - vPadding * 2, top: menuBarHeight, overflowY: 'scroll', paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <FileBrowserTable
                    hideSizeColumn={hideSizeColumn}
                    files={files2}
                    selectedFileNames={selectedFileNames}
                    selectedFileNamesDispatch={selectedFileNamesDispatch}
                    currentTabName={currentTabName}
                    onOpenFile={onOpenFile}
                    multiSelect={true}
                    userCanApproveJobs={userIsComputeResourceOwner}
                    onApproveJob={handleApproveJob}
                    jobsApprovedInThisSession={jobsApprovedInThisSession}
                />
            </div>
        </div>
    )
}

export default FileBrowser2