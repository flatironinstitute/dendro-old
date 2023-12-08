import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { useModalWindow } from "@hodj/modal-window"
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import ModalWindow from "@hodj/modal-window";
import { setUrlFile } from "../../dbInterface/dbInterface";
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
import { HBoxLayout } from "@hodj/misc";
import openFilesInNeurosift from "./openFilesInNeurosift";
import { DendroFile } from "../../types/dendro-types";

type Props = {
    width: number
    height: number
}

const ProjectPage: FunctionComponent<Props> = ({width, height}) => {
    const {route} = useRoute()
    if (route.page !== 'project') throw Error('route.page != project')
    const projectId = route.projectId
    return (
        <SetupProjectPage
            projectId={projectId}
        >
            <ProjectPageChild
                width={width}
                height={height}
            />
        </SetupProjectPage>
    )
}

export type ProjectPageViewType = 'project-home' | 'project-files' | 'project-jobs' | 'dandi-import' /*| 'manual-import'*/ | 'processors'

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

const ProjectPageChild: FunctionComponent<Props> = ({width, height}) => {
    const leftMenuPanelWidth = 150
    return (
        <SetupComputeResources>
            <div style={{position: 'absolute', width, height, overflow: 'hidden'}}>
                <HBoxLayout
                    widths={[leftMenuPanelWidth, width - leftMenuPanelWidth]}
                    height={height}
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
    const {project, projectId, refreshFiles, files} = useProject()
    const auth = useGithubAuth()
    const {route, staging} = useRoute()
    if (route.page !== 'project') throw Error(`Unexpected route ${JSON.stringify(route)}`)
    const currentView = route.tab || 'project-home'

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

    const handleOpenInNeurosift = useCallback((filePaths: string[]) => {
        if (!files) {
            console.warn('No files')
            return
        }
        if (filePaths.length > 5) {
            alert('Too many files to open in NeuroSIFT')
            return
        }

        const files2 = filePaths.map(filePath => {
            const file = files.find(file => file.fileName === filePath)
            if (!file) throw Error(`Unexpected: file not found: ${filePath}`)
            return file
        }, [files])

        openFilesInNeurosift(files2, projectId).then(() => {
            console.info('Opened in NeuroSIFT')
        }, err => {
            console.warn(err)
            alert(`Problem opening in NeuroSIFT: ${err.message}`)
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

    const dandisetId = useMemo(() => {
        if (!project) return undefined
        if (project.tags.length === 0) return undefined
        const t = project.tags[0]
        if (!staging) {
            if (t.startsWith('dandiset.')) {
                return t.slice('dandiset.'.length)
            }
        }
        else {
            if (t.startsWith('dandiset-staging.')) {
                return t.slice('dandiset-staging.'.length)
            }
        }
        return undefined

    }, [project, staging])

    const stagingStr = staging ? '-staging' : ''
    const handleImportItems = useCallback(async (items: {dandisetId: string, dandisetVersion: string, assetItem: AssetsResponseItem}[]) => {
        const files: {nwbUrl: string, dandisetId: string, dandisetVersion: string, assetId: string, assetPath: string, staging: boolean}[] = []
        for (const item of items) {
            const headers = getDandiApiHeaders(staging)
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

    return (
        <div style={{position: 'absolute', width, height, overflow: 'hidden', background: 'white'}}>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-home' ? undefined : 'hidden'}}>
                <ProjectHome
                    width={width}
                    height={height}
                />
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-files' ? undefined : 'hidden'}}>
                <ProjectFiles
                    width={width}
                    height={height}
                    onRunBatchSpikeSorting={handleRunSpikeSorting}
                    onOpenInNeurosift={handleOpenInNeurosift}
                    onDandiUpload={handleDandiUpload}
                    onUploadSmallFile={handleUploadSmallFile}
                    onAction={handleAction}
                />
            </div>
            <div style={{position: 'absolute', width, height, visibility: currentView === 'project-jobs' ? undefined : 'hidden'}}>
                <ProjectJobs
                    width={width}
                    height={height}
                />
            </div>
            {dandisetId && (
                <div style={{position: 'absolute', width, height, visibility: currentView === 'dandi-import' ? undefined : 'hidden'}}>
                    <DandisetView
                        width={width}
                        height={height}
                        useStaging={staging}
                        dandisetId={dandisetId}
                        onImportItems={handleImportItems}
                    />
                </div>
            )}
            {/* <div style={{position: 'absolute', width, height, visibility: currentView === 'manual-import' ? undefined : 'hidden'}}>
                <ManualNwbSelector
                    width={width}
                    height={height}
                    onNwbFileSelected={handleImportManualNwbFile}
                />
            </div> */}
            <div style={{position: 'absolute', width, height, visibility: currentView === 'processors' ? undefined : 'hidden'}}>
                <ProcessorsView
                    width={width}
                    height={height}
                />
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

export default ProjectPage