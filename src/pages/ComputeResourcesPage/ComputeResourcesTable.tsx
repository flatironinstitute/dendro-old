import { Delete } from "@mui/icons-material"
import { FunctionComponent, useCallback } from "react"
import Hyperlink from "../../components/Hyperlink"
import ComputeResourceNameDisplay from "../../ComputeResourceNameDisplay"
import { confirm } from "../../confirm_prompt_alert"
import { timeAgoString } from "../../timeStrings"
import UserIdComponent from "../../UserIdComponent"
import useRoute from "../../useRoute"
import { useComputeResources } from "./ComputeResourcesContext"

type Props = {
    // none
}

const ComputeResourcesTable: FunctionComponent<Props> = () => {
    const {computeResources, deleteComputeResource} = useComputeResources()

    const handleDeleteComputeResource = useCallback(async (computeResourceId: string) => {
        const okay = await confirm('Are you sure you want to delete this compute resource?')
        if (!okay) return
        deleteComputeResource(computeResourceId)
    }, [deleteComputeResource])

    const { setRoute } = useRoute()

    return (
        <table className="scientific-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Compute resource</th>
                    <th>ID</th>
                    <th>Owner</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                {
                    computeResources.map((cr) => (
                        <tr key={cr.computeResourceId}>
                            <td><Delete onClick={() => handleDeleteComputeResource(cr.computeResourceId)} /></td>
                            <td>
                                <Hyperlink onClick={() => setRoute({page: 'compute-resource', computeResourceId: cr.computeResourceId})}>
                                    {cr.name}
                                </Hyperlink>
                            </td>
                            <td>
                                <Hyperlink onClick={() => setRoute({page: 'compute-resource', computeResourceId: cr.computeResourceId})}>
                                    <ComputeResourceNameDisplay computeResourceId={cr.computeResourceId} link={false} />
                                </Hyperlink>
                            </td>
                            <td><UserIdComponent userId={cr.ownerId} /></td>
                            <td>{timeAgoString(cr.timestampCreated)}</td>
                        </tr>
                    ))
                }
            </tbody>
        </table>
    )
}

export default ComputeResourcesTable