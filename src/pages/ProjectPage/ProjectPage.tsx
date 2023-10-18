import { FunctionComponent } from "react"
import useRoute from "../../useRoute"

type ProjectPageProps = {
    width: number
    height: number
}

const ProjectPage: FunctionComponent<ProjectPageProps> = ({width, height}) => {
    const {route} = useRoute()
    if (route.page !== 'project') throw new Error('route.page !== project')
    const projectId = route.projectId
    return (
        <div>Project: {projectId}</div>
    )
}

export default ProjectPage