import { FunctionComponent, useCallback, useEffect, useState } from "react"
import useRoute from "../useRoute"
import { useDendro } from "../DendroContext/DendroContext"
import { DendroProject, isDendroProject } from "../types/dendro-types"
import { Hyperlink } from "@hodj/misc";

type RecentProjectsPanelProps = {
    width: number
    height: number
    expanded: boolean
}

const initialRecentProjects = (): DendroProject[] => {
    try {
        const rp = localStorage.getItem('dendro-recent-projects')
        if (!rp) return []
        const parsed = JSON.parse(rp)
        if (!Array.isArray(parsed)) throw Error('recent projects is not an array')
        if (!parsed.every(isDendroProject)) throw Error('recent projects is not an array of recent projects')
        return parsed
    }
    catch(err) {
        localStorage.removeItem('dendro-recent-projects')
        console.error(err)
        return []
    }
}

const useRecentProjects = () => {
    const [recentProjects, setRecentProjects] = useState<DendroProject[]>(initialRecentProjects())

    const addRecentProject = useCallback((project: DendroProject) => {
        // this is important so we don't get an infinite loop
        if (recentProjects.length > 0 && recentProjects[0].projectId === project.projectId) return
        let newRecentProjects = recentProjects.filter(rp => rp.projectId !== project.projectId)
        newRecentProjects.unshift(project)
        newRecentProjects = newRecentProjects.slice(0, 10)
        localStorage.setItem('dendro-recent-projects', JSON.stringify(newRecentProjects))
        setRecentProjects(newRecentProjects)
    }, [recentProjects])

    return {
        recentProjects,
        addRecentProject
    }
}

const RecentProjectsPanel: FunctionComponent<RecentProjectsPanelProps> = ({width, height, expanded}) => {
    const {recentProjects, addRecentProject} = useRecentProjects()
    const {route, setRoute} = useRoute()

    const {loadedProjects} = useDendro()

    useEffect(() => {
        if (route.page !== 'project') return
        const project = loadedProjects.find(p => p.projectId === route.projectId)
        if (!project) return
        addRecentProject(project)
    }, [route, loadedProjects, addRecentProject])

    // if not expanded, we don't show the content (because it looks bad if only a small portion is showing)
    // but we do render the component so that it can update the recent projects
    if (!expanded) return <div />

    return (
        <div
            style={{
                width,
                height,
                overflowY: 'auto'
            }}
        >
            <div
                style={{
                    padding: 10,
                    fontSize: 20,
                    fontWeight: 'bold'
                }}
            >
                Recent Projects
            </div>
            <div
                style={{
                    padding: 10,
                    fontSize: 14
                }}
            >
                <table className="scientific-table">
                    <thead>
                        <tr>
                            <td>Project</td>
                            <td>Dandisets</td>
                        </tr>
                    </thead>
                    <tbody>
                        {recentProjects.map(rp => (
                            <tr
                                key={rp.projectId}
                                style={{
                                    padding: 5
                                }}
                            >
                                <td>
                                    <Hyperlink
                                        onClick={() => setRoute({page: 'project', projectId: rp.projectId})}
                                    >
                                        {rp.name}
                                    </Hyperlink>
                                </td>
                                <td>{dandisetIdsFromTags(rp.tags).join(', ')}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

const dandisetIdsFromTags = (tags: string[]) => {
    return tags.map(tag => {
        if (tag.startsWith('dandiset.')) {
            return tag.slice('dandiset.'.length)
        }
        else if (tag.startsWith('dandiset-staging.')) {
            return tag.slice('dandiset-staging.'.length)
        }
        else return undefined
    }).filter(tag => tag !== undefined)
}

export default RecentProjectsPanel