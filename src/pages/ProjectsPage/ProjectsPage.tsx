import { FunctionComponent } from "react";
import ProjectsTable from "./ProjectsTable";
import useRoute from "../../useRoute";
import { Hyperlink } from "@fi-sci/misc";
import './ProjectsPage.css'

type Props = {
    width: number
    height: number
}

const ProjectsPage: FunctionComponent<Props> = ({width, height}) => {
    const {setRoute} = useRoute()
    return (
        <div className="projects-page" style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            <h3>Your projects</h3>
            <ProjectsTable />
            <hr />
            <p>
                To add a project, <Hyperlink onClick={() => setRoute({page: 'dandisets'})}>navigate to a dandiset</Hyperlink> and click the button to add a project associated with that dandiset.
            </p>
        </div>
    )
}

export default ProjectsPage