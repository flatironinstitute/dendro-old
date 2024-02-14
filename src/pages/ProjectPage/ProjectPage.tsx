import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react";
import { useModalWindow } from "@fi-sci/modal-window"
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import ModalWindow from "@fi-sci/modal-window";
import { setProjectTags, setUrlFile } from "../../dbInterface/dbInterface";
import useRoute from "../../useRoute";
// import ManualNwbSelector from "./ManualNwbSelector/ManualNwbSelector";
import { PluginAction } from "../../plugins/DendroFrontendPlugin";
import { SetupComputeResources } from "../ComputeResourcesPage/ComputeResourcesContext";
import { getDandiApiHeaders } from "../DandiBrowser/DandiBrowser";
import DandisetView from "../DandiBrowser/DandisetView";
import { AssetResponse, AssetsResponseItem } from "../DandiBrowser/types";
import DandiUploadWindow from "./DandiUpload/DandiUploadWindow";
import { DandiUploadTask } from "./DandiUpload/prepareDandiUploadTask";
import MearecGenerateTemplatesWindow from "./MearecGenerateTemplatesWindow/MearecGenerateTemplatesWindow";
import ProcessorsView from "./ProcessorsView";
import ProjectFiles from "./ProjectFiles";
import ProjectHome from "./ProjectHome";
import ProjectJobs from "./ProjectJobs";
import { SetupProjectPage, useProject } from "./ProjectPageContext";
import RunBatchSpikeSortingWindow from "./RunBatchSpikeSortingWindow/RunBatchSpikeSortingWindow";
import UploadSmallFileWindow from "./UploadSmalFileWindow/UploadSmallFileWindow";
import { HBoxLayout, Hyperlink } from "@fi-sci/misc";
import openFilesInNeurosift from "./openFilesInNeurosift";
import ProjectAnalysis from "./ProjectAnalysis/ProjectAnalysis";
import { DendroProject } from "../../types/dendro-types";
import RunFileActionWindow from "./RunFileActionWindow/RunFileActionWindow";
import ProjectScripts from "./ProjectScripts";

type Props = {
    width: number
    height: number
    onCurrentProjectChanged: (project: DendroProject | undefined) => void
}

const ProjectPage: FunctionComponent<Props> = ({width, height, onCurrentProjectChanged}) => {
    const {route} = useRoute()
    if (route.page !== 'project') throw Error('route.page != project')
    const projectId = route.projectId
    return (
        <SetupProjectPage
            projectId={projectId}
            onCurrentProjectChanged={onCurrentProjectChanged}
        >
            <ProjectPageChild
                width={width}
                height={height}
            />
        </SetupProjectPage>
    )
}

export type ProjectPageViewType = 'project-home' | 'project-files' | 'project-jobs' | 'project-scripts' | 'project-linked-analysis' | 'dandi-import' /*| 'manual-import'*/ | 'processors'

type ProjectPageView = {
    type: ProjectPageViewType
    label: string
}

const projectPageViews: ProjectPageView[] = [
    {
        type: 'project-home',
        label: 'Project home'
    },
    {
        type: 'project-files',
        label: 'Files'
    },
    {
        type: 'project-jobs',
        label: 'Jobs'
    },
    {
        type: 'project-scripts',
        label: 'Scripts'
    },
    {
        type: 'project-linked-analysis',
        label: 'Linked analysis'
    },
    {
        type: 'dandi-import',
        label: 'DANDI Import'
    },
    // {
    //     type: 'manual-import',
    //     label: 'Manual import'
    // },
    {
        type: 'processors',
        label: 'Processors'
    }
]

const ProjectPageChild: FunctionComponent<{width: number, height: number}> = ({width, height}) => {
    const leftMenuPanelWidth = 150
    const statusBarHeight = 16
    return (
        <SetupComputeResources>
            <div style={{position: 'absolute', width, height: height - statusBarHeight, overflow: 'hidden'}}>
                <HBoxLayout
                    widths={[leftMenuPanelWidth, width - leftMenuPanelWidth]}
                    height={height - statusBarHeight}
                >
                    <LeftMenuPanel
                        width={0}
                        height={0}
                    />
                    <MainPanel
                        width={0}
                        height={0}
                    />
                </HBoxLayout>
            </div>
            <div style={{position: 'absolute', width, height: statusBarHeight, bottom: 0, background: '#ddd', borderTop: 'solid 1px #aaa', fontSize: 12, paddingRight: 10, textAlign: 'right'}}>
                <StatusBar />
            </div>
        </SetupComputeResources>
    )
}

type LeftMenuPanelProps = {
    width: number
    height: number
}

const LeftMenuPanel: FunctionComponent<LeftMenuPanelProps> = ({width, height}) => {
    const {route, setRoute} = useRoute()
    const {projectId} = useProject()
    if (route.page !== 'project') throw Error(`Unexpected route ${JSON.stringify(route)}`)
    const currentView = route.tab || 'project-home'
    return (
        <div style={{position: 'absolute', width, height, overflow: 'hidden', background: '#fafafa'}}>
            {
                projectPageViews.map(view => (
                    <div
                        key={view.type}
                        style={{padding: 10, cursor: 'pointer', background: currentView === view.type ? '#ddd' : 'white'}}
                        onClick={() => setRoute({page: 'project', projectId, tab: view.type})}
                    >
                        {view.label}
                    </div>
                ))
            }
        </div>
    )
}

type MainPanelProps = {
    width: number
    height: number
}

const MainPanel: FunctionComponent<MainPanelProps> = ({width, height}) => {
    const {project, projectId, refreshFiles, files, refreshProject} = useProject()
    const auth = useGithubAuth()
    const {route, staging} = useRoute()
    if (route.page !== 'project') throw Error(`Unexpected route ${JSON.stringify(route)}`)
    const currentView = (route.tab || 'project-home') as ProjectPageViewType

    const handleCreateFiles = useCallback(async (files: {fileName: string, url: string, metadata: any}[]) => {
        if (!project) {
            console.warn('No project')
            return
        }
        for (const file of files) {
            await setUrlFile(project.projectId, file.fileName, file.url, file.metadata, auth)
        }
        refreshFiles()
        // if (files.length === 1) {
        //     openTab(`file:${files[0].fileName}`)
        // }
        // setRoute({page: 'project', projectId: project.projectId, tab: 'project-files'})
    }, [project, refreshFiles, auth])

    const handleImportDandiNwbFiles = useCallback(async (files: {nwbUrl: string, dandisetId: string, dandisetVersion: string, assetId: string, assetPath: string, staging: boolean}[]) => {
        const files2: {
            fileName: string
            url: string
            metadata: {
                dandisetId: string
                dandisetVersion: string
                dandiAssetId: string
                dandiAssetPath: string
                dandiStaging: boolean
            }
        }[] = []
        for (const file of files) {
            const stagingStr = file.staging ? 'staging-' : ''
            const fileName = 'imported/' + stagingStr + file.dandisetId + '/' + file.assetPath
            const metadata = {
                dandisetId: file.dandisetId,
                dandisetVersion: file.dandisetVersion,
                dandiAssetId: file.assetId,
                dandiAssetPath: file.assetPath,
                dandiStaging: file.staging
            }
            files2.push({fileName, url: file.nwbUrl, metadata})
        }
        await handleCreateFiles(files2)
    }, [handleCreateFiles])

    // const handleImportManualNwbFile = useCallback((nwbUrl: string, fileName: string) => {
    //     const metadata = {}
    //     handleCreateFiles([{fileName, url: nwbUrl, metadata}])
    // }, [handleCreateFiles])

    const {visible: runSpikeSortingWindowVisible, handleOpen: openRunSpikeSortingWindow, handleClose: closeRunSpikeSortingWindow} = useModalWindow()
    const [spikeSortingFilePaths, setSpikeSortingFilePaths] = useState<string[]>([])
    const handleRunSpikeSorting = useCallback((filePaths: string[]) => {
        setSpikeSortingFilePaths(filePaths)
        openRunSpikeSortingWindow()
    }, [openRunSpikeSortingWindow])

    const {visible: runFileActionWindowVisible, handleOpen: openRunFileActionWindow, handleClose: closeRunFileActionWindow} = useModalWindow()
    const [runActionFilePaths, setRunActionFilePaths] = useState<string[]>([])
    const [runActionActionName, setRunActionActionName] = useState<string>('')
    const handleRunFileAction = useCallback((actionName: string, filePaths: string[]) => {
        setRunActionActionName(actionName)
        setRunActionFilePaths(filePaths)
        openRunFileActionWindow()
    }, [openRunFileActionWindow])

    const handleOpenInNeurosift = useCallback((filePaths: string[]) => {
        if (!files) {
            console.warn('No files')
            return
        }
        if (filePaths.length > 5) {
            alert('Too many files to open in Neurosift')
            return
        }

        const files2 = filePaths.map(filePath => {
            const file = files.find(file => file.fileName === filePath)
            if (!file) throw Error(`Unexpected: file not found: ${filePath}`)
            return file
        }, [files])

        openFilesInNeurosift(files2, projectId).then(() => {
            console.info('Opened in Neurosift')
        }, err => {
            console.warn(err)
            alert(`Problem opening in Neurosift: ${err.message}`)
        })
    }, [files, projectId])

    const {visible: dandiUploadWindowVisible, handleOpen: openDandiUploadWindow, handleClose: closeDandiUploadWindow} = useModalWindow()
    const [dandiUploadTask, setDandiUploadTask] = useState<DandiUploadTask | undefined>(undefined)
    const handleDandiUpload = useCallback((dandiUploadTask: DandiUploadTask) => {
        setDandiUploadTask(dandiUploadTask)
        openDandiUploadWindow()
    }, [openDandiUploadWindow])

    const {visible: uploadSmallFileWindowVisible, handleOpen: openUploadSmallFileWindow, handleClose: closeUploadSmallFileWindow} = useModalWindow()
    const handleUploadSmallFile = useCallback(() => {
        openUploadSmallFileWindow()
    }, [openUploadSmallFileWindow])

    const stagingStr = staging ? '-staging' : ''
    const handleImportItems = useCallback(async (items: {dandisetId: string, dandisetVersion: string, assetItem: AssetsResponseItem}[]) => {
        const files: {nwbUrl: string, dandisetId: string, dandisetVersion: string, assetId: string, assetPath: string, staging: boolean}[] = []
        for (const item of items) {
            const {headers} = getDandiApiHeaders(staging)
            const response = await fetch(
                `https://api${stagingStr}.dandiarchive.org/api/dandisets/${item.dandisetId}/versions/${item.dandisetVersion}/assets/${item.assetItem.asset_id}/`,
                {
                    headers
                }
            )
            if (response.status === 200) {
                const json = await response.json()
                const assetResponse: AssetResponse = json
                let nwbUrl: string | undefined
                if (!nwbUrl) nwbUrl = assetResponse.contentUrl.find(url => url.startsWith('https://api.dandiarchive.org/api/'))
                if (!nwbUrl) nwbUrl = assetResponse.contentUrl.find(url => url.startsWith('https://api-staging.dandiarchive.org/api/'))
                if (!nwbUrl) nwbUrl = assetResponse.contentUrl.find(url => url.includes('amazonaws.com'))
                if (!nwbUrl) nwbUrl = assetResponse.contentUrl[0]
                if (!nwbUrl) return
                files.push({nwbUrl, dandisetId: item.dandisetId, dandisetVersion: item.dandisetVersion, assetId: item.assetItem.asset_id, assetPath: item.assetItem.path, staging})
            }
        }
        await handleImportDandiNwbFiles(files)
    }, [handleImportDandiNwbFiles, stagingStr, staging])

    const {visible: mearecGenerateTemplatesWindowVisible, handleOpen: openMearecGenerateTemplatesWindow, handleClose: closeMearecGenerateTemplatesWindow} = useModalWindow()

    const handleAction = useCallback(async (action: PluginAction) => {
        if (action.name === 'mearec-generate-templates') {
            openMearecGenerateTemplatesWindow()
        }
    }, [openMearecGenerateTemplatesWindow])

    const [viewsThatHaveBeenVisible, setViewsThatHaveBeenVisible] = useState<ProjectPageViewType[]>([])
    useEffect(() => {
        if (!viewsThatHaveBeenVisible.includes(currentView)) {
            setViewsThatHaveBeenVisible(viewsThatHaveBeenVisible.concat([currentView]))
        }
    }, [currentView, viewsThatHaveBeenVisible])

    const taggedDandisetIds = useMemo(() => {
        if (!project) return []
        if (!staging) {
            return project.tags.filter(tag => tag.startsWith('dandiset.')).map(tag => tag.slice('dandiset.'.length))
        }
        else {
            return project.tags.filter(tag => tag.startsWith('dandiset-staging.')).map(tag => tag.slice('dandiset-staging.'.length))
        }
    }, [project, staging])

    const handleAddDandisetId = useCallback((dandisetId: string) => {
        if (!auth) return
        const newTag = staging ? `dandiset-staging.${dandisetId}` : `dandiset.${dandisetId}`
        if (!project) return
        setProjectTags(project.projectId, [...project.tags, newTag], auth).then(() => {
            refreshProject()
        })
    }, [project, staging, auth, refreshProject])

    const [selectedDandisetId, setSelectedDandisetId] = useState<string>('')
    useEffect(() => {
        if (selectedDandisetId) return
        if (taggedDandisetIds.length === 0) return
        setSelectedDandisetId(taggedDandisetIds[0])
    }, [selectedDandisetId, taggedDandisetIds])

    return (
        <div style={{position: 'absolute', width, height, overflow: 'hidden', background: 'white'}}>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-home' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('project-home') && (
                        <ProjectHome
                            width={width}
                            height={height}
                        />
                    )
                }
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-files' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('project-files') && (
                        <ProjectFiles
                            width={width}
                            height={height}
                            onRunFileAction={handleRunFileAction}
                            onRunBatchSpikeSorting={handleRunSpikeSorting}
                            onOpenInNeurosift={handleOpenInNeurosift}
                            onDandiUpload={handleDandiUpload}
                            onUploadSmallFile={handleUploadSmallFile}
                            onAction={handleAction}
                        />
                    )
                }
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-jobs' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('project-jobs') && (
                        <ProjectJobs
                            width={width}
                            height={height}
                        />
                    )
                }
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-scripts' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('project-scripts') && (
                        <ProjectScripts
                            width={width}
                            height={height}
                        />
                    )
                }
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-linked-analysis' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('project-linked-analysis') && (
                        <ProjectAnalysis
                            width={width}
                            height={height}
                        />
                    )
                }
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'dandi-import' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('dandi-import') && (
                        <div>
                            <div style={{position: 'absolute', width, height: 40, overflowY: 'auto'}}>
                                <DandisetIdSelector dandisetId={selectedDandisetId} setDandisetId={setSelectedDandisetId} taggedDandisetIds={taggedDandisetIds} onAddDandisetId={handleAddDandisetId} />
                            </div>
                            <div style={{position: 'absolute', width, top: 40, height: height - 40, overflow: 'hidden'}}>
                                {selectedDandisetId && <DandisetView
                                    width={width}
                                    height={height - 60}
                                    useStaging={staging}
                                    onImportItems={handleImportItems}
                                    dandisetId={selectedDandisetId}
                                />}
                            </div>
                        </div>
                    )
                }
            </div>
            {/* <div style={{position: 'absolute', width, height, visibility: currentView === 'manual-import' ? undefined : 'hidden'}}>
                <ManualNwbSelector
                    width={width}
                    height={height}
                    onNwbFileSelected={handleImportManualNwbFile}
                />
            </div> */}
            <div style={{position: 'absolute', width, height, visibility: currentView === 'processors' ? undefined : 'hidden'}}>
                {
                    viewsThatHaveBeenVisible.includes('processors') && (
                        <ProcessorsView
                            width={width}
                            height={height}
                        />
                    )
                }
            </div>
            <ModalWindow
                visible={runSpikeSortingWindowVisible}
            >
                <RunBatchSpikeSortingWindow
                    width={0}
                    height={0}
                    filePaths={spikeSortingFilePaths}
                    onClose={closeRunSpikeSortingWindow}
                />
            </ModalWindow>
            <ModalWindow
                visible={runFileActionWindowVisible}
            >
                <RunFileActionWindow
                    width={0}
                    height={0}
                    actionName={runActionActionName}
                    filePaths={runActionFilePaths}
                    onClose={closeRunFileActionWindow}
                />
            </ModalWindow>
            <ModalWindow
                visible={dandiUploadWindowVisible}
                onClose={closeDandiUploadWindow}
            >
                {
                    dandiUploadTask && (
                        <DandiUploadWindow
                            dandiUploadTask={dandiUploadTask}
                            onClose={closeDandiUploadWindow}
                        />
                    )
                }
            </ModalWindow>
            <ModalWindow
                visible={uploadSmallFileWindowVisible}
                onClose={closeUploadSmallFileWindow}
            >
                <UploadSmallFileWindow
                    onClose={closeUploadSmallFileWindow}
                />
            </ModalWindow>
            <ModalWindow
                visible={mearecGenerateTemplatesWindowVisible}
                onClose={closeMearecGenerateTemplatesWindow}
            >
                <MearecGenerateTemplatesWindow
                    width={0}
                    height={0}
                    onClose={closeMearecGenerateTemplatesWindow}
                />
            </ModalWindow>
        </div>
    )
}

type DandisetIdSelectorProps = {
    dandisetId: string
    setDandisetId: (dandisetId: string) => void
    taggedDandisetIds: string[]
    onAddDandisetId: (dandisetId: string) => void
}

const DandisetIdSelector: FunctionComponent<DandisetIdSelectorProps> = ({dandisetId, setDandisetId, taggedDandisetIds, onAddDandisetId}) => {
    const handleAdd = useCallback(() => {
        const newDandisetId = prompt('Enter dandiset ID')
        if (!newDandisetId) return
        onAddDandisetId(newDandisetId)
    }, [onAddDandisetId])
    // radio buttons
    return (
        <div>
            <span style={{fontWeight: 'bold'}}>Select a dandiset: </span>
            {
                taggedDandisetIds.map(taggedDandsetId => (
                    <span key={taggedDandsetId}>
                        <input type="radio" id={taggedDandsetId} name="dandiset" value={taggedDandsetId} checked={dandisetId === taggedDandsetId} onChange={() => setDandisetId(taggedDandsetId)} />
                        <label htmlFor={taggedDandsetId}>{taggedDandsetId}</label>
                        &nbsp;&nbsp;
                    </span>
                ))
            }
            &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            <Hyperlink onClick={handleAdd}>Add new dandiset to project</Hyperlink>
        </div>
    )
}

const StatusBar: FunctionComponent = () => {
    const {statusStrings} = useProject()
    const statusStringsSorted = useMemo(() => (statusStrings || []).sort((a, b) => a.localeCompare(b)), [statusStrings])
    return (
        <span>
            {statusStringsSorted.join(' ')}
        </span>
    )
}

export default ProjectPage