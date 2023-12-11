import { Edit } from "@mui/icons-material";
import { FunctionComponent, useCallback, useEffect, useState } from "react";
import { SmallIconButton } from "@fi-sci/misc";
import { confirm } from "../../confirm_prompt_alert";
import useRoute from "../../useRoute";
import { useProject } from "./ProjectPageContext";

type Props = {
    // none
}

const ProjectSettingsWindow: FunctionComponent<Props> = () => {
    const {project, setProjectName, projectRole} = useProject()

    return (
        <div>
            <h3>Settings for project: {project?.name}</h3>
            <table>
                <tbody>
                    <tr>
                        <td>
                            Project name:
                        </td>
                        <td>
                            <EditProjectNameComponent projectName={project?.name} setProjectName={setProjectName} />
                        </td>
                    </tr>
                    <tr>
                        <td>Project ID:</td>
                        <td style={{whiteSpace: 'nowrap'}}>{project?.projectId}</td>
                    </tr>
                </tbody>
            </table>
            <hr />
            In the future, this page will allow you to change the users for the project.
            <hr />
            {
                (projectRole === 'admin') ? (
                    <DeleteProjectButton />
                ) : (
                    <div>You do not have permission to edit this project.</div>
                )
            }
        </div>
    )
}

const DeleteProjectButton: FunctionComponent = () => {
    const {deleteProject} = useProject()
    const {setRoute} = useRoute()
    const handleDeleteProject = useCallback(async () => {
        const okay = await confirm('Are you sure you want to delete this project?')
        if (!okay) return
        await deleteProject()
        setRoute({page: 'dandisets'})
    }, [deleteProject, setRoute])

    return (
        <button onClick={handleDeleteProject}>Delete project</button>
    )
}

const EditProjectNameComponent: FunctionComponent<{projectName: string | undefined, setProjectName: (name: string) => void}> = ({projectName, setProjectName}) => {
    const [editing, setEditing] = useState(false)
    const [editText, setEditText] = useState(projectName || '')
    useEffect(() => {
        setEditText(projectName || '')
    }, [projectName])
    if (!editing) {
        return (
            <span>
                {projectName}
                &nbsp;
                <SmallIconButton
                    icon={<Edit />}
                    onClick={() => setEditing(true)}
                    title="Edit project name"
                />
            </span>
        )
    }
    else {
        return (
            <span>
                <input type="text" value={editText} onChange={e => setEditText(e.target.value)} />
                &nbsp;
                <button onClick={() => setEditing(false)}>Cancel</button>
                &nbsp;
                <button onClick={() => {setProjectName(editText); setEditing(false)}}>Save</button>
            </span>
        )
    }
}

export default ProjectSettingsWindow;