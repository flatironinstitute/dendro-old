import { FunctionComponent } from "react"

type RunMethodSelectorProps = {
    runMethod: 'local' | 'aws_batch' | 'slurm'
    setRunMethod: (method: 'local' | 'aws_batch' | 'slurm') => void
    availableRunMethods: ('local' | 'aws_batch' | 'slurm')[]
}

const RunMethodSelector: FunctionComponent<RunMethodSelectorProps> = ({ runMethod, setRunMethod, availableRunMethods }) => {
    return (
        <div>
            <select value={runMethod} onChange={e => setRunMethod(e.target.value as any)}>
                {
                    availableRunMethods.map(method => (
                        <option key={method} value={method}>{method}</option>
                    ))
                }
            </select>
        </div>
    )
}

export default RunMethodSelector