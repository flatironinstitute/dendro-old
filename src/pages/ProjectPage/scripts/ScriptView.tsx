import { FunctionComponent } from "react"

type ScriptViewProps = {
    width: number
    height: number
    scriptId: string
}

const ScriptView: FunctionComponent<ScriptViewProps> = ({ width, height, scriptId }) => {
    return (
        <div style={{width, height, padding: 10}}>
            <div>Script {scriptId}</div>
        </div>
    )
}

export default ScriptView