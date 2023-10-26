import { useEffect, useState } from "react";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { fetchProjectsForUser } from "../../dbInterface/dbInterface";
import { ProtocaasProject } from "../../types/protocaas-types";

const useProjectsForUser = (): ProtocaasProject[] | undefined => {
    const [projects, setProjects] = useState<ProtocaasProject[] | undefined>(undefined)
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