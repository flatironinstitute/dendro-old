import { SmallIconButton } from "@fi-sci/misc";
import { Add, Check, Delete, Refresh } from "@mui/icons-material";
import { FunctionComponent, useCallback, useState } from "react";
import { confirm } from "../../../confirm_prompt_alert";
import { useProject } from "../ProjectPageContext";
import { addScript } from "../../../dbInterface/dbInterface";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";

type ScriptsTableMenuBarProps = {
    width: number
    height: number
    selectedScriptIds: string[]
    onResetSelection: () => void
    createScriptEnabled?: boolean
    createScriptTitle?: string
}

const ScriptsTableMenuBar: FunctionComponent<ScriptsTableMenuBarProps> = ({width, height, selectedScriptIds, onResetSelection, createScriptEnabled, createScriptTitle}) => {
    const {deleteScript, refreshScripts, refreshFiles, projectRole, projectId} = useProject()
    const [operating, setOperating] = useState(false)
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
    
    const auth = useGithubAuth()

    const handleCreateScript = useCallback(async () => {
        if (!auth.signedIn) return
        const scriptName = prompt('Enter a name for the new script', 'untitled.js')
        if (!scriptName) return
        setOperating(true)
        await addScript(projectId, scriptName, auth)
        setOperating(false)
        refreshScripts()
    }, [refreshScripts, projectId, auth])

    return (
        <div>
            <SmallIconButton
                icon={<Refresh />}
                disabled={operating}
                title='Refresh'
                onClick={refreshScripts}
            />
            <SmallIconButton
                icon={<Delete />}
                disabled={(selectedScriptIds.length === 0) || operating}
                title={selectedScriptIds.length > 0 ? `Delete these ${selectedScriptIds.length} scripts` : ''}
                onClick={handleDelete}
            />
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