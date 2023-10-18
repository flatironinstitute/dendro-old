import { faPython } from '@fortawesome/free-brands-svg-icons';
import { faCaretDown, faCaretRight, faFile, faFolder } from '@fortawesome/free-solid-svg-icons';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { FunctionComponent, useCallback, useEffect, useMemo, useReducer } from "react";
import Hyperlink from '../../../components/Hyperlink';
import { timeAgoString } from '../../../timeStrings';
import { ProtocaasFile } from '../../../types/protocaas-types';
import { useProject } from '../ProjectPageContext';
import './file-browser-table.css';
import FileBrowserMenuBar from './FileBrowserMenuBar';
import formatByteCount from './formatByteCount';
import { DandiUploadTask } from '../DandiUpload/prepareDandiUploadTask';

type Props = {
    width: number
    height: number
    files: ProtocaasFile[] | undefined
    onOpenFile: (path: string) => void
    onDeleteFile: (path: string) => void
    hideSizeColumn?: boolean
    onRunBatchSpikeSorting?: (filePaths: string[]) => void
    onDandiUpload?: (dandiUploadTask: DandiUploadTask) => void
}

type FileItem = {
    type: 'file'
    id: string
    name: string
    selected: boolean
    size: number
    timestampCreated: number
    content?: string
} | {
    type: 'folder'
    id: string
    name: string
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

type TreeNode = {
    type: 'file' | 'folder'
    name: string
    subNodes: TreeNode[]
    file?: ProtocaasFile
}

const FileBrowser2: FunctionComponent<Props> = ({width, height, onOpenFile, files, hideSizeColumn, onRunBatchSpikeSorting, onDandiUpload}) => {
    const {currentTabName} = useProject()

    const rootNode = useMemo(() => {
        const defineSubnodesForNode = (node: TreeNode) => {
            if (node.type === 'folder') {
                const subFoldersSet = new Set<string>()
                for (const ff of files || []) {
                    const aa = ff.fileName.split('/')
                    const bb = node.name ? node.name.split('/') : []
                    const cc = bb.length > 0 ? aa.slice(0, bb.length).join('/') : ''
                    if (bb.join('/') === cc) {
                        if (aa.length > bb.length + 1) {
                            subFoldersSet.add(aa[bb.length])
                        }
                    }
                }
                const subFoldersListSorted = Array.from(subFoldersSet).sort()
                for (const subFolderName of subFoldersListSorted) {
                    const subNode: TreeNode = {
                        type: 'folder',
                        name: node.name ? node.name + '/' + subFolderName : subFolderName,
                        subNodes: [],
                        file: undefined
                    }
                    node.subNodes.push(subNode)
                    defineSubnodesForNode(subNode)
                }
                for (const ff of files || []) {
                    const aa = ff.fileName.split('/')
                    const bb = node.name ? node.name.split('/') : []
                    const cc = bb.length > 0 ? aa.slice(0, bb.length).join('/') : ''
                    if (bb.join('/') === cc) {
                        if (aa.length === bb.length + 1) {
                            node.subNodes.push({
                                type: 'file',
                                name: ff.fileName,
                                subNodes: [],
                                file: ff
                            })
                        }
                    }
                }
            }
        }
        const rootNode: TreeNode = {
            type: 'folder',
            name: '',
            subNodes: [],
            file: undefined
        }
        defineSubnodesForNode(rootNode)
        return rootNode
    }, [files])

    const [selectedFileNames, selectedFileNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const [expandedFolders, expandedFoldersDispatch] = useReducer(expandedFoldersReducer, new Set<string>())
    const itemIsVisible = useMemo(() => ((path: string) => {
        if (!path) return false
        const aa = path.split('/')
        if (aa.length === 1) return true
        for (let i = 1; i < aa.length; i++) {
            const bb = aa.slice(0, i).join('/')
            if (!expandedFolders.has(bb)) return false
        }
        return true
    }), [expandedFolders])
    useEffect(() => {
        // initialize expanded state
        const newExpandedFolders = new Set<string>()
        const handleNode = (node: TreeNode) => {
            if (node.type === 'folder') {
                const isTopLevelHiddenFolder = (!node.name.includes('/')) && node.name.startsWith('.')
                if ((node.name) && (!isTopLevelHiddenFolder) && (node.subNodes.length <= 5)) {
                    newExpandedFolders.add(node.name)
                }
                for (const subNode of node.subNodes) {
                    handleNode(subNode)
                }
            }
        }
        handleNode(rootNode)
        expandedFoldersDispatch({type: 'set', paths: newExpandedFolders})
    }, [rootNode])

    const fileItems = useMemo(() => {
        const ret: FileItem[] = []
        const handleNode = (node: TreeNode) => {
            if (node.type === 'folder') {
                if (node.name !== '') {
                    ret.push({
                        type: 'folder',
                        id: node.name,
                        name: node.name
                    })
                }
                for (const subNode of node.subNodes) {
                    handleNode(subNode)
                }
            }
            else {
                ret.push({
                    type: 'file',
                    id: node.name,
                    name: node.name,
                    selected: 'file:' + node.name === currentTabName,
                    size: node.file?.size || 0,
                    timestampCreated: node.file?.timestampCreated || 0,
                    content: node.file?.content
                })
            }
        }
        handleNode(rootNode)
        return ret
    }, [rootNode, currentTabName])

    const handleClickFile = useCallback((fileId: string) => {
        onOpenFile(fileId)
    }, [onOpenFile])

    const menuBarHeight = 30
    const hPadding = 20
    const vPadding = 5

    const colWidth = 15

    const determineCheckedStateForFolder = useCallback((folderName: string) => {
        if (!files) return false
        const ff = files.filter(f => f.fileName.startsWith(folderName + '/'))
        const ff2 = ff.filter(f => selectedFileNames.has(f.fileName))
        if (ff2.length === 0)  return false
        if (ff2.length === ff.length) return true
        return null // indeterminate
    }, [files, selectedFileNames])

    const handleClickFolderCheckbox = useCallback((folderName: string) => {
        if (!files) return
        const ff = files.filter(f => f.fileName.startsWith(folderName + '/'))
        if (ff.length === 0) return
        const ff2 = ff.filter(f => selectedFileNames.has(f.fileName))
        if (ff2.length === ff.length) {
            // all selected, so unselect all
            selectedFileNamesDispatch({type: 'set-multiple', paths: ff.map(f => f.fileName), selected: false})
        }
        else {
            // some or none selected, so select all
            selectedFileNamesDispatch({type: 'set-multiple', paths: ff.map(f => f.fileName), selected: true})
        }
    }, [files, selectedFileNames])
    
    return (
        <div style={{position: 'absolute', width, height, userSelect: 'none'}}>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: menuBarHeight - vPadding * 2, paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <FileBrowserMenuBar
                    width={width - hPadding * 2}
                    height={menuBarHeight - vPadding * 2}
                    selectedFileNames={Array.from(selectedFileNames)}
                    onResetSelection={() => selectedFileNamesDispatch({type: 'set', values: new Set()})}
                    onRunBatchSpikeSorting={onRunBatchSpikeSorting}
                    onDandiUpload={onDandiUpload}
                />
            </div>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: height - menuBarHeight - vPadding * 2, top: menuBarHeight, overflowY: 'scroll', paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <table className="file-browser-table">
                    <thead>
                        <tr>
                            <th style={{width: colWidth}}></th>
                            <th style={{width: colWidth}}></th>
                            <th>File</th>
                            <th>Modified</th>
                            {!hideSizeColumn && <th>Size</th>}
                        </tr>
                    </thead>
                    <tbody>
                        {
                            fileItems.filter(fi => (itemIsVisible(fi.name))).map(x => (
                                <tr key={x.id}>
                                    <td style={{width: colWidth}}>
                                        {
                                            x.type === 'file' ? (
                                                <Checkbox checked={selectedFileNames.has(x.name)} onClick={() => selectedFileNamesDispatch({type: 'toggle', value: x.name})} />
                                            ) : (
                                                <Checkbox checked={determineCheckedStateForFolder(x.name)} onClick={() => handleClickFolderCheckbox(x.name)} />
                                            )
                                        }
                                    </td>
                                    <td style={{width: colWidth}}>
                                        {
                                            x.type === 'file' ? (
                                                <FileIcon fileName={x.name} />
                                            ) : (
                                                <FolderIcon />
                                            )
                                        }
                                    </td>
                                    <td>
                                        {
                                            x.type === 'file' ? (
                                                <Hyperlink
                                                    onClick={() => handleClickFile(x.name)}
                                                    color={x.content?.startsWith('pending:') ? x.content === 'pending:failed' ? 'red' : 'gray' : undefined}
                                                >{depthIndentation(x.name)}{baseName(x.name)}{x.content?.startsWith('pending:') ? ` (${x.content.slice('pending:'.length)})` : ""}</Hyperlink>
                                            ) : (
                                                <span style={{cursor: 'pointer'}} onClick={() => expandedFoldersDispatch({type: 'toggle', path: x.name})}>
                                                    {depthIndentation(x.name)}
                                                    {
                                                        expandedFolders.has(x.name) ? (
                                                            <span><FontAwesomeIcon icon={faCaretDown} style={{color: 'gray'}} /> </span>
                                                        ) : (
                                                            <span><FontAwesomeIcon icon={faCaretRight} style={{color: 'gray'}} /> </span>
                                                        )
                                                    }
                                                    {baseName(x.name)}
                                                </span>
                                            )
                                        }
                                    </td>
                                    <td>
                                        {(x.type === 'file' && x.timestampCreated) ? (
                                            <span style={{whiteSpace: 'nowrap'}}>{timeAgoString(x.timestampCreated)}</span>
                                        ): ''}
                                    </td>
                                    {!hideSizeColumn && (
                                        x.type === 'file' && x.size ? <td>{formatByteCount(x.size)}</td> : <td />
                                    )}
                                </tr>
                            ))
                        }
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export const FileIcon: FunctionComponent<{fileName: string}> = ({fileName}) => {
    const ext = fileName.split('.').pop()
    if (ext === 'py') {
        return <FontAwesomeIcon icon={faPython} style={{color: 'darkblue'}} />
    }
    else if (ext === 'json') {
        return <FontAwesomeIcon icon={faFile as any} style={{color: 'black'}} />
    }
    else if (ext === 'stan') {
        // return <FontAwesomeIcon icon={faFile as any} style={{color: 'darkorange'}} />
        return <img src="/protocaas-logo.png" alt="logo" height={14} style={{paddingBottom: 0, cursor: 'pointer'}} />
    }
    else if (ext === 'nwb') {
        return <FontAwesomeIcon icon={faFile as any} style={{color: 'red'}} />
    }
    else {
        return <FontAwesomeIcon icon={faFile as any} style={{color: 'gray'}} />
    }
}

export const Checkbox: FunctionComponent<{checked: boolean | null, onClick: () => void}> = ({checked, onClick}) => {
    // null means indeterminate
    return (
        <input
            ref={input => {
                if (!input) return
                input.indeterminate = checked === null
            }}
            type="checkbox"
            checked={checked === true}
            onChange={onClick}
        />
    )
}

const baseName = (path: string) => {
    if (!path) return ''
    const aa = path.split('/')
    return aa[aa.length - 1]
}

const FolderIcon = () => {
    return <FontAwesomeIcon icon={faFolder} />
}

const depthIndentation = (path: string) => {
    if (!path) return <span />
    const depth = path.split('/').length - 1
    if (!depth) return <span />
    return <span style={{paddingLeft: depth * 10}} />
}

export default FileBrowser2