import { FunctionComponent } from "react"
import { DendroJobRequiredResources } from "../../../types/dendro-types"

type RequiredResourcesEditorProps = {
    runMethod: 'local' | 'aws_batch' | 'slurm'
    setRunMethod: (method: 'local' | 'aws_batch' | 'slurm') => void
    availableRunMethods: ('local' | 'aws_batch' | 'slurm')[]
    requiredResources: DendroJobRequiredResources
    setRequiredResources: (val: DendroJobRequiredResources) => void
}
const numCpusChoices = [1, 2, 4, 6, 8, 12, 16, 20, 24, 28, 32, 48, 64, 96, 128, 256, 512, 1024, 2048]
const numGpusChoices = [0, 1, 2]
const memoryGbChoices = [1, 2, 4, 6, 8, 12, 16, 20, 24, 28, 32, 48, 64, 96, 128, 256, 512, 1024, 2048]
const timeMinChoices = [1, 5, 10, 30, 60, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 1440, 1440 * 2, 1440 * 3, 1440 * 4, 1440 * 5, 1440 * 6, 1440 * 7]

const RequiredResourcesEditor: FunctionComponent<RequiredResourcesEditorProps> = ({requiredResources, setRequiredResources, runMethod, setRunMethod, availableRunMethods}) => {
    const {numCpus, numGpus, memoryGb, timeSec} = requiredResources
    const WW = 70
    return (
        <div>
            <h3>Resources</h3>
            <table className="table1" style={{maxWidth: 500}}>
                <tbody>
                    <tr>
                        <td>Run method</td>
                        <td>
                            <select value={runMethod} onChange={evt => setRunMethod(evt.target.value as any)}>
                                {
                                    availableRunMethods.map(method => (
                                        <option key={method} value={method}>{method}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Number of CPUs</td>
                        <td>
                            <select style={{width: WW}} value={numCpus} onChange={evt => setRequiredResources({...requiredResources, numCpus: Number(evt.target.value)})}>
                                {
                                    numCpusChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>                            
                        </td>
                    </tr>
                    <tr>
                        <td>Number of GPUs</td>
                        <td>
                            <select style={{width: WW}} value={numGpus} onChange={evt => setRequiredResources({...requiredResources, numGpus: Number(evt.target.value)})}>
                                {
                                    numGpusChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Memory (GB)</td>
                        <td>
                            <select style={{width: WW}} value={memoryGb} onChange={evt => setRequiredResources({...requiredResources, memoryGb: Number(evt.target.value)})}>
                                {
                                    memoryGbChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                    <tr>
                        <td>Time (minutes)</td>
                        <td>
                            <select style={{width: WW}} value={Math.floor(timeSec / 60)} onChange={evt => setRequiredResources({...requiredResources, timeSec: Number(evt.target.value) * 60})}>
                                {
                                    timeMinChoices.map(x => (
                                        <option key={x} value={x}>{x}</option>
                                    ))
                                }
                            </select>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    )
}

export default RequiredResourcesEditor