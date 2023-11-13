import { useEffect, useState } from "react";
import { DendroProject } from "../../types/dendro-types";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { fetchProjectsForTag } from "../../dbInterface/dbInterface";

const useProjectsForTag = (tag: string | undefined): DendroProject[] | undefined => {
    const [projects, setProjects] = useState<DendroProject[] | undefined>(undefined)
    const auth = useGithubAuth()
    useEffect(() => {
        let canceled = false

        if (!tag) {
            setProjects([])
            return
        }

        setProjects(undefined)

        ; (async () => {
            const projects = await fetchProjectsForTag(tag, auth)
            if (canceled) return
            setProjects(projects)
        })()
        return () => {
            canceled = true
        }
    }, [tag, auth])
    return projects
}

export default useProjectsForTag