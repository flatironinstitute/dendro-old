import { FunctionComponent } from "react";
import { SetupComputeResources } from "./ComputeResourcesContext";
import ComputeResourcesTable from "./ComputeResourcesTable";
import './ComputeResourcesPage.css'

type Props = {
    width: number
    height: number
}

const ComputeResourcesPage: FunctionComponent<Props> = ({width, height}) => {
    return (
        <SetupComputeResources>
            <div className="compute-resources-page">
                <h3>Your compute resources</h3>
                <ComputeResourcesTable />
                <hr />
                <p>To register a compute resource, run the following from your computer</p>
                <code>
                    cd /path/to/compute/resource/directory
                </code><br />
                <code>
                    protocaas register-compute-resource
                </code>
            </div>
        </SetupComputeResources>
    )
}

export default ComputeResourcesPage