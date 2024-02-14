import { Splitter } from "@fi-sci/splitter";
import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { useProject } from "./ProjectPageContext";
import ScriptsTable from "./scripts/ScriptsTable";
import ScriptView from "./scripts/ScriptView";
import { setScriptContent } from "../../dbInterface/dbInterface";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";

const ProjectScripts: FunctionComponent<{width: number, height: number}> = ({width, height}) => {
    const {scripts, projectRole, refreshScripts} = useProject()
    const [selectedScriptId, setSelectedScriptId] = useState<string | undefined>(undefined)

    const createScriptEnabled = projectRole === 'admin' || projectRole === 'editor'

    const selectedScript = useMemo(() => {
        if (!selectedScriptId) return undefined
        return scripts?.find(s => s.scriptId === selectedScriptId)
    }, [selectedScriptId, scripts])

    const auth = useGithubAuth()

    const handleSetScriptContent = useCallback(async (content: string) => {
        if (!selectedScriptId) return
        await setScriptContent(selectedScriptId, content, auth)
        refreshScripts()
    }, [selectedScriptId, auth, refreshScripts])

    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={width / 2}
            direction="horizontal"
            hideSecondChild={selectedScriptId === undefined || (!scripts?.map(s => s.scriptId).includes(selectedScriptId))}
        >
            {scripts ? <ScriptsTable
                width={0}
                height={0}
                scripts={scripts}
                onScriptClicked={scriptId => setSelectedScriptId(scriptId)}
                createScriptEnabled={createScriptEnabled}
                createScriptTitle={createScriptEnabled ? "Create a new script" : ""}
            /> : <div />}
            <ScriptView
                width={0}
                height={0}
                script={selectedScript}
                onSetContent={handleSetScriptContent}
            />
        </Splitter>
    )
}

export default ProjectScripts