import { FunctionComponent, useMemo } from "react"
import UserIdComponent from "../../UserIdComponent"
import { Hyperlink } from "@fi-sci/misc";
import { timeAgoString } from "../../timeStrings"
import useRoute from "../../useRoute"
import useProjectsForUser from './useProjectsForUser'

type Props = {
    admin?: boolean
}

const ProjectsTable: FunctionComponent<Props> = ({admin}) => {
    const projects = useProjectsForUser({admin})

    const { setRoute } = useRoute()

    if (!projects) return <div>Retrieving projects...</div>

    return (
        <table className="scientific-table">
            <thead>
                <tr>
                    <th>Project</th>
                    <th>ID</th>
                    <th>Dandisets</th>
                    <th>Description</th>
                    <th>Owner</th>
                    <th>Created</th>
                </tr>
            </thead>
            <tbody>
                {
                    projects.map((pr) => (
                        <tr key={pr.projectId}>
                            <td>
                                <Hyperlink onClick={() => setRoute({page: 'project', projectId: pr.projectId})}>
                                    {pr.name}
                                </Hyperlink>
                            </td>
                            <td>
                                <Hyperlink onClick={() => setRoute({page: 'project', projectId: pr.projectId})}>
                                    {pr.projectId}
                                </Hyperlink>
                            </td>
                            <td>
                                {
                                    dandisetsForProjectTags(pr.tags).map((dandiset) => (
                                        <span key={dandiset.dandisetId}>
                                            <DandisetLink dandisetId={dandiset.dandisetId} staging={dandiset.staging} />
                                            &nbsp;&nbsp;&nbsp;
                                        </span>
                                    ))
                                }
                            </td>
                            <td>
                                {
                                    pr.description
                                }
                            </td>
                            <td><UserIdComponent userId={pr.ownerId} /></td>
                            <td>{timeAgoString(pr.timestampCreated)}</td>
                        </tr>
                    ))
                }
            </tbody>
        </table>
    )
}

const dandisetsForProjectTags = (tags: string[]): {dandisetId: string, staging: boolean}[] => {
    const ret: {dandisetId: string, staging: boolean}[] = []
    for (const tag of tags) {
        if (tag.startsWith('dandiset.')) {
            const dandisetId = tag.slice('dandiset.'.length)
            ret.push({dandisetId, staging: false})
        }
        else if (tag.startsWith('dandiset-staging.')) {
            const dandisetId = tag.slice('dandiset-staging.'.length)
            ret.push({dandisetId, staging: true})
        }
    }
    return ret.sort()
}

type DandisetLinkProps = {
    dandisetId: string
    staging: boolean
}

const DandisetLink: FunctionComponent<DandisetLinkProps> = ({dandisetId, staging}) => {
    const {setRoute} = useRoute()
    return (
        <Hyperlink onClick={() => setRoute({page: 'dandiset', dandisetId}, staging)}>{staging ? `staging-` : ''}{dandisetId}</Hyperlink>
    )
}

export default ProjectsTable