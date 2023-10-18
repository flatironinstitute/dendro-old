import { Edit } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { FunctionComponent, useState } from "react";
import ComputeResourceNameDisplay from "../../ComputeResourceNameDisplay";
import { useComputeResources } from "../ComputeResourcesPage/ComputeResourcesContext";
import { useProject } from "./ProjectPageContext";

type Props = {
    // none
}

const ProjectComputeResourceComponent: FunctionComponent<Props> = () => {
    const {project, projectRole, setProjectComputeResourceId} = useProject()
    const [editing, setEditing] = useState(false)

    return (
        <div>
            {
                project && (
                    <table>
                        <tbody>
                            <tr>
                                <td>Using compute resource:</td>
                                <td>{
                                    project.computeResourceId ? (
                                        <ComputeResourceNameDisplay computeResourceId={project.computeResourceId} />
                                    ) : (
                                        <span>DEFAULT</span>
                                    )
                                }</td>
                            </tr>
                        </tbody>
                    </table>
                )
            }
            {
                project && !editing && projectRole === 'admin' && (
                    <IconButton onClick={() => setEditing(true)} title="Select a different compute resource">
                        <Edit />
                    </IconButton>
                )
            }
            {
                project && editing && (
                    <SelectComputeResourceComponent
                        selectedComputeResourceId={project.computeResourceId || undefined}
                        onSelected={(computeResourceId) => {
                            setProjectComputeResourceId(computeResourceId || '')
                            setEditing(false)
                        }}
                    />
                )
            }
        </div>
    )
}

type SelectComputeResourceComponentProps = {
    selectedComputeResourceId?: string
    onSelected: (computeResourceId: string) => void
}

const SelectComputeResourceComponent: FunctionComponent<SelectComputeResourceComponentProps> = ({onSelected, selectedComputeResourceId}) => {
    const {computeResources} = useComputeResources()
    return (
        <div>
            <select onChange={
                e => {
                    const crId = e.target.value
                    if (crId === '<none>') return
                    onSelected(crId)
                }
            } value={selectedComputeResourceId || ''}>
                <option value="<none>">Select a compute resource</option>
                <option value="">DEFAULT</option>
                {
                    computeResources.map(cr => (
                        <option key={cr.computeResourceId} value={cr.computeResourceId}>{cr.name} ({abbreviate(cr.computeResourceId, 10)})</option>
                    ))
                }
            </select>
        </div>
    )
}

function abbreviate(s: string, maxLength: number) {
    if (s.length <= maxLength) return s
    return s.slice(0, maxLength - 3) + '...'
}

export default ProjectComputeResourceComponent;