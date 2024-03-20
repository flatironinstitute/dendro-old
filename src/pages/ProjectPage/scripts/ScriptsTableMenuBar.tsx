import { SmallIconButton } from "@fi-sci/misc";
import { Add, Delete, Edit, Refresh } from "@mui/icons-material";
import { FunctionComponent, useCallback, useState } from "react";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";
import { confirm } from "../../../confirm_prompt_alert";
import { addScript, renameScript } from "../../../dbInterface/dbInterface";
import { useProject } from "../ProjectPageContext";

type ScriptsTableMenuBarProps = {
    width: number
    height: number
    selectedScriptIds: string[]
    onResetSelection: () => void
    createScriptEnabled?: boolean
    createScriptTitle?: string
}

const ScriptsTableMenuBar: FunctionComponent<ScriptsTableMenuBarProps> = ({width, height, selectedScriptIds, onResetSelection, createScriptEnabled, createScriptTitle}) => {
    const {deleteScript, refreshScripts, refreshFiles, projectRole, projectId, scripts} = useProject()
    const [operating, setOperating] = useState(false)
    const auth = useGithubAuth()
    const handleDelete = useCallback(async () => {
        if (!['admin', 'editor'].includes(projectRole || '')) {
            alert('You are not authorized to delete scripts in this project.')
            return
        }
        const okay = await confirm(`Are you sure you want to delete these ${selectedScriptIds.length} scripts?`)
        if (!okay) return
        try {
            setOperating(true)
            for (const scriptId of selectedScriptIds) {
                await deleteScript(scriptId)
            }
        }
        finally {
            setOperating(false)
            refreshScripts()
            refreshFiles
            onResetSelection()
        }
    }, [selectedScriptIds, deleteScript, refreshScripts, refreshFiles, onResetSelection, projectRole])

    const handleRename = useCallback(async () => {
        if (!['admin', 'editor'].includes(projectRole || '')) {
            alert('You are not authorized to rename scripts in this project.')
            return
        }
        if (selectedScriptIds.length !== 1) return
        const scriptId = selectedScriptIds[0]
        const script = scripts?.find(s => s.scriptId === scriptId)
        if (!script) return
        let scriptName: string | null
        // eslint-disable-next-line no-constant-condition
        while (true) {
            scriptName = prompt('Enter a new name for the script', script.scriptName)
            if (!scriptName) return
            if (scripts?.find(s => s.scriptName === scriptName)) {
                alert('A script with that name already exists. Please choose a different name.')
            }
            else {
                break
            }
        }
        if (!scriptName) return
        setOperating(true)
        await renameScript(scriptId, scriptName, auth)
        setOperating(false)
        refreshScripts()
    }, [selectedScriptIds, scripts, refreshScripts, projectRole, auth])

    const handleCreateScript = useCallback(async () => {
        if (!auth.signedIn) return
        let scriptName: string | null
        // eslint-disable-next-line no-constant-condition
        while (true) {
            scriptName = prompt('Enter a name for the new script', 'untitled.js')
            if (!scriptName) return
            if (scripts?.find(s => s.scriptName === scriptName)) {
                alert('A script with that name already exists. Please choose a different name.')
            }
            else {
                break
            }
        }
        if (!scriptName) return
        setOperating(true)
        await addScript(projectId, scriptName, auth)
        setOperating(false)
        refreshScripts()
    }, [refreshScripts, projectId, auth, scripts])

    return (
        <div>
            <SmallIconButton
                icon={<Refresh />}
                disabled={operating}
                title='Refresh'
                onClick={refreshScripts}
            />
            <span style={{visibility: selectedScriptIds.length > 0 ? undefined : 'hidden'}}>
                <SmallIconButton
                    icon={<Delete />}
                    disabled={(selectedScriptIds.length === 0) || operating}
                    title={selectedScriptIds.length > 1 ? `Delete these ${selectedScriptIds.length} scripts` : 'Delete this script'}
                    onClick={handleDelete}
                />
            </span>
            <span style={{visibility: selectedScriptIds.length === 1 ? undefined : 'hidden'}}>
                <SmallIconButton
                    icon={<Edit />}
                    disabled={selectedScriptIds.length !== 1 || operating}
                    title='Rename this script'
                    onClick={handleRename}
                />
            </span>
            {createScriptEnabled && <SmallIconButton
                icon={<Add />}
                disabled={operating || !auth.signedIn}
                title={createScriptTitle || 'Create a new script'}
                label="New script"
                onClick={handleCreateScript}
            />}
        </div>
    )
}

export default ScriptsTableMenuBar