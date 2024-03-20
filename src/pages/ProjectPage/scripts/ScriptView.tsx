import { SmallIconButton } from "@fi-sci/misc"
import { Splitter } from "@fi-sci/splitter"
import { Save } from "@mui/icons-material"
import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { DendroScript } from "../../../types/dendro-types"
import CodeEditor from "./CodeEditor"
import RunScriptWindow from "./RunScript/RunScriptWindow"

type ScriptViewProps = {
    width: number
    height: number
    script?: DendroScript
    onSetContent?: (content: string) => void
}

const ScriptView: FunctionComponent<ScriptViewProps> = ({ width, height, script, onSetContent }) => {
    // const script = useScript(scriptId)
    const [internalContent, setInternalContent] = useState<string | undefined>()
    useEffect(() => {
        setInternalContent(script?.content)
    }, [script])

    const modified = useMemo(() => {
        if (!script) return false
        return internalContent !== script.content
    }, [script, internalContent])

    const topBarHeight = 25
    if (!script) return <span />
    if (internalContent === undefined) return <span />
    return (
        <div style={{position: 'absolute', width, height}}>
            <div style={{position: 'absolute', width, height: topBarHeight, display: 'flex'}}>
                <div style={{fontSize: 14, fontWeight: 'bold'}}>
                    {script.scriptName}
                </div>
                <div style={{visibility: modified ? undefined : 'hidden'}}>
                    *&nbsp;&nbsp;&nbsp;
                    <SmallIconButton
                        icon={<Save />}
                        title='Save this script'
                        onClick={() => {
                            onSetContent && onSetContent(internalContent)
                        }}
                        disabled={!modified}
                    />
                </div>
            </div>
            <div style={{position: 'absolute', width, height: height - topBarHeight, top: topBarHeight, overflow: 'hidden'}}>
                <Splitter
                    width={width}
                    height={height - topBarHeight}
                    initialPosition={height * 2 / 3}
                    direction="vertical"
                >
                    <CodeEditor
                        width={0}
                        height={0}
                        content={internalContent}
                        onContentChanged={setInternalContent}
                        readOnly={false}
                        onSave={() => {
                            onSetContent && onSetContent(internalContent)
                        }}
                    />
                    <RunScriptWindow
                        width={0}
                        height={0}
                        scriptContent={internalContent}
                        saved={!modified}
                    />
                </Splitter>
            </div>
        </div>
    )
}

export default ScriptView