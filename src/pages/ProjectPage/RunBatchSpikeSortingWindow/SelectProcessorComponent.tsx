import { FunctionComponent } from "react"
import { Hyperlink } from "@hodj/misc";
import { ComputeResourceSpecApp, ComputeResourceSpecProcessor, DendroComputeResourceApp } from "../../../types/dendro-types"

type SelectProcessorComponentProps = {
    processors: {appSpec: ComputeResourceSpecApp, app?: DendroComputeResourceApp, processor: ComputeResourceSpecProcessor}[]
    onSelected: (processorName: string) => void
}

const SelectProcessorComponent: FunctionComponent<SelectProcessorComponentProps> = ({processors, onSelected}) => {
    return (
        <div>
            <h3>Select a spike sorter</h3>
            <table className="table1" style={{maxWidth: 900}}>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>App</th>
                    </tr>
                </thead>
                <tbody>
                {
                    processors.map((processor, i) => (
                        <tr key={i}>
                            <td>
                                <Hyperlink onClick={() => {onSelected(processor.processor.name)}}>
                                    {processor.processor.name}
                                </Hyperlink>
                            </td>
                            <td>
                                {processor.appSpec.name}
                            </td>
                        </tr>
                    ))
                }
                </tbody>
            </table>
        </div>
    )
}

export default SelectProcessorComponent