import { Splitter } from "@fi-sci/splitter";
import { FunctionComponent, useState } from "react";
import { useProject } from "./ProjectPageContext";
import ScriptsTable from "./scripts/ScriptsTable";
import ScriptView from "./scripts/ScriptView";

const ProjectScripts: FunctionComponent<{width: number, height: number}> = ({width, height}) => {
    const {scripts, projectRole} = useProject()
    const [selectedScriptId, setSelectedScriptId] = useState<string | undefined>(undefined)

    const createScriptEnabled = projectRole === 'admin' || projectRole === 'editor'

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
                scriptId={selectedScriptId || ''}
            />
        </Splitter>
    )
}

export default ProjectScripts