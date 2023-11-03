import { FunctionComponent } from "react"
import ProjectsTable from "../ProjectsPage/ProjectsTable"

type AdminPageProps = {
    width: number
    height: number
}

const AdminPage: FunctionComponent<AdminPageProps> = ({width, height}) => {
    return (
        <ProjectsTable
            admin={true}
        />
    )
}

export default AdminPage