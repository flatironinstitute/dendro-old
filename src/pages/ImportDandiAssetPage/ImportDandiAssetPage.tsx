import { Button } from "@mui/material"
import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { useGithubAuth } from "../../GithubAuth/useGithubAuth"
import { createProject, setProjectTags, setUrlFile } from "../../dbInterface/dbInterface"
import useRoute from "../../useRoute"
import { SetupProjectPage, useProject } from "../ProjectPage/ProjectPageContext"
import useProjectsForUser from "../ProjectsPage/useProjectsForUser"
import { DendroProject } from "../../types/dendro-types"
import { Hyperlink } from "@fi-sci/misc"

type Props = {
    // none
}

const ImportDandiAssetPage: FunctionComponent<Props> = () => {
    const {route} = useRoute()
    if (route.page !== "importDandiAsset") {
        throw Error("ImportDandiAssetPage component rendered even though route.page is not 'importDandiAsset'")
    }

    const [projectIdToUse, setProjectIdToUse] = useState<string | undefined>(undefined)

    const {userId} = useGithubAuth()

    let content
    if (!userId) {
        content = (
            <div style={{color: 'red'}}>In order to proceed with the import, you must first sign in.</div>
        )
    }
    else if (projectIdToUse === undefined) {
        content = (
            <SelectProjectForImport
                defaultProjectName={route.projectName}
                onSelectProjectId={setProjectIdToUse}
            />
        )
    }
    else {
        content = (
            <SetupProjectPage
                projectId={projectIdToUse}
                onCurrentProjectChanged={() => {}}
            >
                <ImportDandiAssetIntoProjectComponent
                    dandisetId={route.dandisetId}
                    dandisetVersion={route.dandisetVersion}
                    assetPath={route.assetPath}
                    assetUrl={route.assetUrl}
                />
            </SetupProjectPage>
        )
    }

    return (
        <div style={{padding: 40}}>
            <h1>Import Dandi Asset</h1>
            <div>
                <table className="scientific-table" style={{maxWidth: 800}}>
                    <tbody>
                        <tr>
                            <td>DANDISET</td>
                            <td>{route.dandisetId} ({route.dandisetVersion})</td>
                        </tr>
                        <tr>
                            <td>Asset path</td>
                            <td>{route.assetPath}</td>
                        </tr>
                        <tr>
                            <td>Asset URL</td>
                            <td>{route.assetUrl}</td>
                        </tr>
                        <tr>
                            <td>Project name</td>
                            <td>{route.projectName}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            {content}
        </div>
    )
}

type ImportDandiAssetIntoProjectComponentProps = {
    dandisetId: string
    dandisetVersion: string
    assetPath: string
    assetUrl: string
}

const ImportDandiAssetIntoProjectComponent: FunctionComponent<ImportDandiAssetIntoProjectComponentProps> = ({dandisetId, dandisetVersion, assetPath, assetUrl}) => {
    const {files, project} = useProject()
    const projectFileName = `imported/${dandisetId}/${assetPath}`
    const file = useMemo(() => {
        if (!files) return undefined
        return files.find(file => file.fileName === projectFileName)
    }, [files, projectFileName])
    const [importStatus, setImportStatus] = useState<string>('')

    const auth = useGithubAuth()

    const {setRoute} = useRoute()

    const handleImport = useCallback(async () => {
        if (!project?.projectId) return
        // example asset url:
        // https://api.dandiarchive.org/api/assets/26e85f09-39b7-480f-b337-278a8f034007/download/
        // https://api-staging.dandiarchive.org/api/assets/...
        let staging: boolean
        if (assetUrl.startsWith('https://api.dandiarchive.org/api/assets/')) {
            staging = false
        }
        else if (assetUrl.startsWith('https://api-staging.dandiarchive.org/api/assets/')) {
            staging = true
        }
        else {
            console.warn(`Not a valid asset URL: ${assetUrl}`)
            return
        }
        setImportStatus('Importing...')
        const aa = assetUrl.split('/')
        const assetId = aa[5]
        const metadata = {
            dandisetId,
            dandisetVersion,
            dandiAssetId: assetId,
            dandiAssetPath: assetPath,
            dandiStaging: staging
        }
        await setUrlFile(
            project?.projectId,
            projectFileName,
            assetUrl,
            metadata,
            auth
        )
        setImportStatus('Adding tag...')
        const newTag = `dandiset${staging ? '-staging' : ''}.${dandisetId}`
        if (!project.tags.includes(newTag)) {
            const newTags = [...project.tags, newTag]
            await setProjectTags(project.projectId, newTags, auth)
        }
        setImportStatus('Done.')
        setRoute({page: 'project', projectId: project.projectId})
    }, [project, projectFileName, assetUrl, dandisetId, dandisetVersion, assetPath, auth, setRoute])

    if (!files) return <div>Loading project files...</div>
    if (!file) {
        return (
            <div style={{paddingTop: 25, paddingBottom: 25}}>
                <div>Do you wish to import {projectFileName} into project {project?.name}?</div>
                <div style={{paddingTop: 20}}>
                    <Button onClick={handleImport} disabled={!!importStatus}>Import</Button>
                </div>
                <div>
                    {importStatus}
                </div>
            </div>
        )
    }
    else {
        return (
            <div style={{paddingTop: 25, paddingBottom: 25}}>
                This file already exists in the project. If you want to re-import, you will need to delete the file first.
                &nbsp;&nbsp;<Hyperlink onClick={() => {
                    if (project?.projectId) {
                        setRoute({page: 'project', projectId: project.projectId})
                    }
                }}>Go to project {project?.name}</Hyperlink>
            </div>
        )
    }
}

type SelectProjectForImportProps = {
    defaultProjectName: string
    onSelectProjectId: (projectId: string) => void
}

const SelectProjectForImport: FunctionComponent<SelectProjectForImportProps> = ({defaultProjectName, onSelectProjectId}) => {
    const projects = useProjectsForUser()

    const defaultProject = projects?.find(project => project.name === defaultProjectName)

    const [mode, setMode] = useState<'use-existing' | 'create-new'>('use-existing')

    useEffect(() => {
        if (defaultProject === undefined) {
            setMode('create-new')
        }
        else {
            setMode('use-existing')
        }
    }, [defaultProject])

    if (!projects) return <div>Loading projects...</div>

    return (
        <div>
            <div style={{paddingTop: 25, paddingBottom: 25}}>
                <label>
                    <input
                        type="radio"
                        name="mode"
                        checked={mode === 'use-existing'}
                        onChange={() => setMode('use-existing')}
                    />
                    Import into existing project
                </label>
                &nbsp;&nbsp;&nbsp;&nbsp;
                <label>
                    <input
                        type="radio"
                        name="mode"
                        checked={mode === 'create-new'}
                        onChange={() => setMode('create-new')}
                    />
                    Create new project
                </label>
            </div>
            {mode === 'use-existing' && projects.length > 0 && (
                <SelectExistingProjectComponent
                    projects={projects}
                    defaultProjectId={defaultProject?.projectId}
                    onSelectProjectId={onSelectProjectId}
                />
            )}
            {mode === 'use-existing' && projects.length === 0 && (
                <div>
                    You do not have any projects yet.
                </div>
            )}
            {mode === 'create-new' && (
                <div>
                    <CreateNewProjectComponent
                        defaultProjectName={defaultProjectName}
                        onSelectProjectId={onSelectProjectId}
                    />
                </div>
            )}
        </div>
    )
}

type CreateNewProjectComponentProps = {
    defaultProjectName: string
    onSelectProjectId: (projectId: string) => void
}

const CreateNewProjectComponent: FunctionComponent<CreateNewProjectComponentProps> = ({defaultProjectName, onSelectProjectId}) => {
    const [projectName, setProjectName] = useState(defaultProjectName)
    const auth = useGithubAuth()
    const [creating, setCreating] = useState(false)
    const handleCreate = useCallback(async () => {
        setCreating(true)
        const newProjectId = await createProject(projectName, auth)
        onSelectProjectId(newProjectId)
    }, [projectName, auth, onSelectProjectId])

    return (
        <div>
            <div>
                <label>
                    New project name:&nbsp;&nbsp;
                    <input
                        type="text"
                        value={projectName}
                        onChange={e => setProjectName(e.target.value)}
                    />
                </label>
            </div>
            <div style={{paddingTop: 25, paddingBottom: 25}}>
                <Button
                    onClick={handleCreate}
                    disabled={creating}
                >
                    Create project
                </Button>
            </div>
        </div>
    )
}

type SelectExistingProjectComponentProps = {
    projects: DendroProject[]
    defaultProjectId?: string
    onSelectProjectId: (projectId: string) => void
}

const SelectExistingProjectComponent: FunctionComponent<SelectExistingProjectComponentProps> = ({projects, defaultProjectId, onSelectProjectId}) => {
    const [internalProjectId, setInternalProjectId] = useState(defaultProjectId)
    return (
        <div>
            Import into project:&nbsp;&nbsp;
            <select
                value={internalProjectId}
                onChange={e => setInternalProjectId(e.target.value)}
            >
                {projects.map(project => (
                    <option
                        key={project.projectId}
                        value={project.projectId}
                    >
                        {project.name} ({project.projectId})
                    </option>
                ))}
            </select>
            &nbsp;&nbsp;
            <Hyperlink onClick={() => {
                if (internalProjectId) {
                    onSelectProjectId(internalProjectId)
                }
            }} disabled={!internalProjectId}>Select this project</Hyperlink>
        </div>
    )
}

export default ImportDandiAssetPage
