import { useEffect, useState } from "react";
import { ProtocaasProject } from "../../types/protocaas-types";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import { fetchProjectsForTag } from "../../dbInterface/dbInterface";

const useProjectsForTag = (tag: string | undefined): ProtocaasProject[] | undefined => {
    const [projects, setProjects] = useState<ProtocaasProject[] | undefined>(undefined)
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