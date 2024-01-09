import { SmallIconButton } from "@fi-sci/misc";
import { Add, Edit, Remove } from "@mui/icons-material";
import { FunctionComponent, useCallback, useEffect, useReducer, useState } from "react";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { confirm } from "../../confirm_prompt_alert";
import { setProjectUsers } from "../../dbInterface/dbInterface";
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
            <EditProjectUsersComponent />
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
                <button onClick={() => {setProjectName(editText); setEditing(false)}}>Save</button>
                &nbsp;
                <button onClick={() => setEditing(false)}>Cancel</button>
            </span>
        )
    }
}

export type DendroProjectUser = {
    userId: string
    role: 'admin' | 'editor' | 'viewer'
}

type SelectedUserIds = string[]

const selectedUserIdsReducer = (state: SelectedUserIds, action: {type: 'toggle', userId: string}) => {
    switch (action.type) {
        case 'toggle':
            if (state.includes(action.userId)) {
                return state.filter(id => id !== action.userId)
            }
            else {
                return [...state, action.userId]
            }
    }
}

const EditProjectUsersComponent: FunctionComponent = () => {
    const {project, refreshProject} = useProject()

    const [selectedUserIds, selectedUserIdsDispatch] = useReducer(selectedUserIdsReducer, [])

    useEffect(() => {
        for (const user of selectedUserIds) {
            if (!project?.users.find(u => u.userId === user)) {
                selectedUserIdsDispatch({type: 'toggle', userId: user})
            }
        }
    }, [project, selectedUserIds])


    const users: DendroProjectUser[] | undefined = project?.users

    const auth = useGithubAuth()

    const handleAdd = useCallback(async () => {
        if (!project) return
        const userId = prompt('User ID to add:')
        if (!userId) return
        if (project.users.find(user => user.userId === userId)) {
            alert('User is already in project.')
            return
        }
        const role = prompt('Role (admin, editor, or viewer):')
        if (!role) return
        if (role !== 'admin' && role !== 'editor' && role !== 'viewer') {
            alert('Invalid role.')
            return
        }
        const newUsers: DendroProjectUser[] = [...project.users]
        newUsers.push({userId, role: role as DendroProjectUser['role']})
        await setProjectUsers(project.projectId, newUsers, auth)
        refreshProject()
    }, [project, auth, refreshProject])

    const handleRemove = useCallback(async () => {
        if (!project) return
        const newUsers: DendroProjectUser[] = project.users.filter(user => !selectedUserIds.includes(user.userId))
        await setProjectUsers(project.projectId, newUsers, auth)
        refreshProject()
    }, [project, selectedUserIds, auth, refreshProject])

    return (
        <div>
            <h3>Project users</h3>
            <SmallIconButton icon={<Add />} label="Add user" title="Add user" onClick={handleAdd} />
            &nbsp;&nbsp;
            {
                selectedUserIds.length > 0 && (
                    <SmallIconButton icon={<Remove />} label="Remove selected users" title="Remove selected users" disabled={selectedUserIds.length === 0} onClick={handleRemove} />
                )
            }
            <table className="scientific-table">
                <thead>
                    <tr>
                        <th></th>
                        <th>User ID</th>
                        <th>Role</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        users?.map(user => (
                            <tr key={user.userId}>
                                <td><Checkbox selected={selectedUserIds.includes(user.userId)} onClick={() => selectedUserIdsDispatch({type: 'toggle', userId: user.userId})} /></td>
                                <td>{user.userId}</td>
                                <td>{user.role}</td>
                            </tr>
                        ))
                    }
                </tbody>
            </table>
        </div>
    )
}

const Checkbox: FunctionComponent<{selected: boolean, onClick: () => void}> = ({selected, onClick}) => {
    return (
        <input type="checkbox" checked={selected} onChange={onClick} />
    )
}

export default ProjectSettingsWindow;