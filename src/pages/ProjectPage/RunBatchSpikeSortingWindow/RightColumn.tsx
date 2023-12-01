import { FunctionComponent } from "react"
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File"
import { DendroProcessingJobDefinition, DendroProcessingJobDefinitionAction } from "../../../dbInterface/dbInterface"
import { ComputeResourceSpecProcessor } from "../../../types/dendro-types"
import EditJobDefinitionWindow from "../EditJobDefinitionWindow/EditJobDefinitionWindow"


type RightColumnProps = {
    width: number
    height: number
    processor?: ComputeResourceSpecProcessor
    operating: boolean
    valid: boolean
    setValid: (val: boolean) => void
    jobDefinition: DendroProcessingJobDefinition
    jobDefinitionDispatch: React.Dispatch<DendroProcessingJobDefinitionAction>
    representativeNwbFile?: RemoteH5File
    processorName: string
}

const RightColumn: FunctionComponent<RightColumnProps> = ({
    width, height,
    operating, processor, setValid,
    jobDefinition,
    jobDefinitionDispatch,
    representativeNwbFile,
    processorName
}) => {
    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Sorting parameters for {processorName}</h3>
            {processor && (
                <EditJobDefinitionWindow
                    jobDefinition={jobDefinition}
                    jobDefinitionDispatch={jobDefinitionDispatch}
                    processor={processor}
                    nwbFile={representativeNwbFile}
                    setValid={setValid}
                    readOnly={operating}
                />
            )}
        </div>
    )
}

export default RightColumn