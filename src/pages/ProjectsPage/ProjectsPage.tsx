import { Hyperlink, SmallIconButton } from "@fi-sci/misc";
import { Add, ImportExport } from "@mui/icons-material";
import { FunctionComponent, useCallback } from "react";
import useRoute from "../../useRoute";
import './ProjectsPage.css';
import ProjectsTable from "./ProjectsTable";
import { createProject } from "../../dbInterface/dbInterface";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";

type Props = {
    width: number
    height: number
}

const ProjectsPage: FunctionComponent<Props> = ({width, height}) => {
    const {setRoute} = useRoute()

    const auth = useGithubAuth()

    const handleAdd = useCallback(async () => {
        if (!auth.signedIn) {
            alert('You must be signed in to create a project')
            return
        }
        const projectName = prompt('Enter a name for your project', 'untitled')
        if (!projectName) return
        const newProjectId = await createProject(projectName, auth)
        setRoute({page: 'project', projectId: newProjectId})
    }, [setRoute, auth])

    return (
        <div className="projects-page" style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Your projects</h3>
            <div>
                <SmallIconButton icon={<Add />} onClick={handleAdd} label="Create a new project" />
                &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <SmallIconButton icon={<ImportExport />} onClick={() => setRoute({page: 'dandisets'})} label="Import data from DANDI" />
            </div>
            <br />
            <ProjectsTable />
        </div>
    )
}

export default ProjectsPage