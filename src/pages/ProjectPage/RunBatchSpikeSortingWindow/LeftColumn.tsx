import { FunctionComponent } from "react"
import { ComputeResourceSpecApp, DendroComputeResourceApp, DendroJobRequiredResources } from "../../../types/dendro-types"
import RequiredResourcesEditor from "./RequiredResourcesEditor"
import ElectrodeGeometryView from "./ElectrodeGeometryView"
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File"


type LeftColumnProps = {
    width: number
    height: number
    overwriteExistingOutputs: boolean
    setOverwriteExistingOutputs: (val: boolean) => void
    descriptionString: string
    setDescriptionString: (val: string) => void
    descriptionStringIsValid: boolean
    filePaths: string[]
    selectedSpikeSortingProcessor: string
    valid: boolean
    setValid: (val: boolean) => void
    okayToSubmit: boolean
    handleSubmit: () => void
    operating: boolean
    operatingMessage?: string
    requiredResources?: DendroJobRequiredResources
    setRequiredResources: (val: DendroJobRequiredResources) => void
    appSpec?: ComputeResourceSpecApp
    app?: DendroComputeResourceApp
    onClose: () => void
    runMethod: 'local' | 'aws_batch' | 'slurm'
    setRunMethod: (val: 'local' | 'aws_batch' | 'slurm') => void
    availableRunMethods: ('local' | 'aws_batch' | 'slurm')[]
    representativeNwbFile?: RemoteH5File
}

const LeftColumn: FunctionComponent<LeftColumnProps> = ({
    width, height,
    overwriteExistingOutputs, setOverwriteExistingOutputs,
    descriptionString, setDescriptionString, descriptionStringIsValid,
    filePaths, selectedSpikeSortingProcessor,
    valid,
    okayToSubmit, handleSubmit,
    operatingMessage,
    requiredResources, setRequiredResources,
    app,
    onClose,
    runMethod, setRunMethod,
    availableRunMethods,
    representativeNwbFile
}) => {
    return (
        <div className="leftColumn" style={{position: 'absolute', width, height, overflowY: 'auto', overflowX: 'hidden'}}>
            <h3>Batch spike sorting of {filePaths.length === 1 ? `1 file` : `${filePaths.length} files`} using {selectedSpikeSortingProcessor}</h3>
            <div>&nbsp;</div>
            <div>
                <table className="table1" style={{maxWidth: 500}}>
                    <tbody>
                        <tr>
                            <td>Overwrite existing outputs</td>
                            <td>
                                <input type="checkbox" checked={overwriteExistingOutputs} onChange={evt => setOverwriteExistingOutputs(evt.target.checked)} />
                            </td>
                        </tr>
                        <tr>
                            <td>Description string in output file name</td>
                            <td>
                                <input type="text" value={descriptionString} onChange={evt => setDescriptionString(evt.target.value)} />
                                {
                                    !descriptionStringIsValid && (
                                        <span style={{color: 'red'}}>Invalid description string</span>
                                    )
                                }
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div>&nbsp;</div>
            {requiredResources && <RequiredResourcesEditor
                requiredResources={requiredResources}
                setRequiredResources={setRequiredResources}
                runMethod={runMethod}
                setRunMethod={setRunMethod}
                availableRunMethods={availableRunMethods}
            />}
            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            <div>
                {/* Large submit button */}
                <button
                    disabled={!okayToSubmit}
                    onClick={handleSubmit}
                    style={{
                        fontSize: 16,
                        padding: 10,
                        color: 'white',
                        background: okayToSubmit ? '#080' : '#ccc',
                        border: 'none',
                        borderRadius: 5,
                        cursor: okayToSubmit ? 'pointer' : 'default'
                    }}
                >
                    Submit spike sorting job(s)
                </button>
                &nbsp;
                {/* Large cancel button */}
                <button
                    onClick={onClose}
                    style={{
                        fontSize: 16,
                        padding: 10,
                        color: 'white',
                        background: '#444',
                        border: 'none',
                        borderRadius: 5,
                        cursor: 'pointer'
                    }}
                >
                    Cancel
                </button>
            </div>
            <div>
                {
                    operatingMessage && (
                        <span>{operatingMessage}</span>
                    )
                }
            </div>
            {
                !valid ? (
                    <div>
                        <div>&nbsp;</div>
                        <span style={{color: 'red'}}>There are errors in the job definition.</span>
                    </div>
                ) : <span />
            }
            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            {
                app && (
                    <>
                        <div>Dendro app: {app.name}</div>
                    </>
                )
            }
            <div>&nbsp;</div><hr /><div>&nbsp;</div>
            {representativeNwbFile && <ElectrodeGeometryView
                width={width - 15} // make room for possible scroll bar
                height={200}
                nwbFile={representativeNwbFile}
            />}
        </div>
    )

}

export default LeftColumn