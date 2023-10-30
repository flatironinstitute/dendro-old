import { useEffect, useState } from "react";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { fetchProjectsForUser } from "../../dbInterface/dbInterface";
import { DendroProject } from "../../types/dendro-types";

const useProjectsForUser = (): DendroProject[] | undefined => {
    const [projects, setProjects] = useState<DendroProject[] | undefined>(undefined)
    const auth = useGithubAuth()
    useEffect(() => {
        let canceled = false

        if (!auth) {
            setProjects([])
            return
        }

        setProjects(undefined)

        ; (async () => {
            const projects = await fetchProjectsForUser(auth)
            if (canceled) return
            setProjects(projects)
        })()
        return () => {
            canceled = true
        }
    }, [auth])
    return projects
}

export default useProjectsForUser