import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { useModalDialog } from "../../ApplicationBar";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import HBoxLayout from "../../components/HBoxLayout";
import ModalWindow from "../../components/ModalWindow/ModalWindow";
import { setUrlFile } from "../../dbInterface/dbInterface";
import useRoute from "../../useRoute";
import ComputeResourcePage from "../ComputeResourcePage/ComputeResourcePage";
// import ManualNwbSelector from "./ManualNwbSelector/ManualNwbSelector";
import { SetupComputeResources } from "../ComputeResourcesPage/ComputeResourcesContext";
import DandiUploadWindow from "./DandiUpload/DandiUploadWindow";
import { DandiUploadTask } from "./DandiUpload/prepareDandiUploadTask";
import ProcessorsView from "./ProcessorsView";
import ProjectFiles from "./ProjectFiles";
import ProjectHome from "./ProjectHome";
import ProjectJobs from "./ProjectJobs";
import { SetupProjectPage, useProject } from "./ProjectPageContext";
import RunBatchSpikeSortingWindow from "./RunBatchSpikeSortingWindow/RunBatchSpikeSortingWindow";
import { getDandiApiHeaders } from "../DandiBrowser/DandiBrowser";
import DandisetView from "../DandiBrowser/DandisetView";
import { AssetResponse, AssetsResponseItem } from "../DandiBrowser/types";

type Props = {

}

const ProjectPage: FunctionComponent<Props> = ({ }) => {
    const {route} = useRoute()
    if (route.page !== 'project') throw Error('route.page != project')
    const projectId = route.projectId
    return (
        <SetupProjectPage
            projectId={projectId}
        >
            <ProjectPageChild/>
        </SetupProjectPage>
    )
}

export type ProjectPageViewType = 'project-home' | 'project-files' | 'project-jobs' | 'dandi-import' /*| 'manual-import'*/ | 'processors' | 'compute-resource'

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
        label: 'DANDI import'
    },
    // {
    //     type: 'manual-import',
    //     label: 'Manual import'
    // },
    {
        type: 'processors',
        label: 'Processors'
    },
    {
        type: 'compute-resource',
        label: 'Compute resource'
    }
]

const ProjectPageChild: FunctionComponent<Props> = ({ }) => {
    const leftMenuPanelWidth = 150
    return (
        <SetupComputeResources>
            <LeftMenuPanel/>
            <MainPanel/>
        </SetupComputeResources>
    )
}

type LeftMenuPanelProps = {

}

const LeftMenuPanel: FunctionComponent<LeftMenuPanelProps> = ({ }) => {
    const {route, setRoute} = useRoute()
    const {projectId} = useProject()
    if (route.page !== 'project') throw Error(`Unexpected route ${JSON.stringify(route)}`)
    const currentView = route.tab || 'project-home'
    return (
        <div style={{gridArea: 'b', background: '#fafafa'}}>
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
  
}

const MainPanel: FunctionComponent<MainPanelProps> = ({ }) => {
    const {openTab, project, refreshFiles, computeResourceId} = useProject()
    const auth = useGithubAuth()
    const {route, setRoute, staging} = useRoute()
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
        if (files.length === 1) {
            openTab(`file:${files[0].fileName}`)
        }
        setRoute({page: 'project', projectId: project.projectId, tab: 'project-files'})
    }, [project, openTab, auth, refreshFiles, setRoute])

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

    const {visible: runSpikeSortingWindowVisible, handleOpen: openRunSpikeSortingWindow, handleClose: closeRunSpikeSortingWindow} = useModalDialog()
    const [spikeSortingFilePaths, setSpikeSortingFilePaths] = useState<string[]>([])
    const handleRunSpikeSorting = useCallback((filePaths: string[]) => {
        setSpikeSortingFilePaths(filePaths)
        openRunSpikeSortingWindow()
    }, [openRunSpikeSortingWindow])

    const {visible: dandiUploadWindowVisible, handleOpen: openDandiUploadWindow, handleClose: closeDandiUploadWindow} = useModalDialog()
    const [dandiUploadTask, setDandiUploadTask] = useState<DandiUploadTask | undefined>(undefined)
    const handleDandiUpload = useCallback((dandiUploadTask: DandiUploadTask) => {
        setDandiUploadTask(dandiUploadTask)
        openDandiUploadWindow()
    }, [openDandiUploadWindow])

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

    return (
        <div className="main" style={{overflow: 'auto', background: 'white'}}>
            <div style={{display: currentView === 'project-home' ? undefined : 'none'}}>
                <ProjectHome />
            </div>
            <div style={{display: currentView === 'project-files' ? undefined : 'none'}}>
                <ProjectFiles
                    onRunBatchSpikeSorting={handleRunSpikeSorting}
                    onDandiUpload={handleDandiUpload}
                />
            </div>
            <div style={{display: currentView === 'project-jobs' ? undefined : 'none'}}>
                <ProjectJobs/>
            </div>
            {dandisetId && (
                <div style={{display: currentView === 'dandi-import' ? undefined : 'none'}}>
                    <DandisetView
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
            <div style={{display: currentView === 'processors' ? undefined : 'none'}}>
                <ProcessorsView/>
            </div>
            <div style={{display: currentView === 'compute-resource' ? undefined : 'none'}}>
                {
                    computeResourceId && (
                        <ComputeResourcePage
                            computeResourceId={computeResourceId}
                        />
                    )
                }
            </div>
            <ModalWindow
                open={runSpikeSortingWindowVisible}
                onClose={closeRunSpikeSortingWindow}
            >
                <RunBatchSpikeSortingWindow
                    filePaths={spikeSortingFilePaths}
                    onClose={closeRunSpikeSortingWindow}
                />
            </ModalWindow>
            <ModalWindow
                open={dandiUploadWindowVisible}
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
        </div>
    )
}

export default ProjectPage