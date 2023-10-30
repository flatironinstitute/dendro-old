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
                <p>
                    <a href="https://github.com/scratchrealm/dendro/blob/main/doc/host_compute_resource.md" target="_blank" rel="noreferrer">
                        Add a compute resource
                    </a>
                </p>
            </div>
        </SetupComputeResources>
    )
}

export default ComputeResourcesPage