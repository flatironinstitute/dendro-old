import { useEffect, useState } from "react";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { fetchAdminAllProjects, fetchProjectsForUser } from "../../dbInterface/dbInterface";
import { DendroProject } from "../../types/dendro-types";

const useProjectsForUser = (o: {admin?: boolean} = {}): DendroProject[] | undefined => {
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
            let projects
            if (!o.admin) {
                projects = await fetchProjectsForUser(auth)
            }
            else {
                projects = await fetchAdminAllProjects(auth)
            }
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