import { useEffect, useState } from "react";
import { ProtocaasProject, isProtocaasProject } from "../../types/protocaas-types";

const useProjectsForTag = (tag: string | undefined): ProtocaasProject[] | undefined => {
    const [projects, setProjects] = useState<ProtocaasProject[] | undefined>(undefined)
    useEffect(() => {
        let canceled = false

        if (!tag) {
            setProjects([])
            return
        }

        setProjects(undefined)

        ; (async () => {
            const url = `/api/gui/projects?tag=${tag}`
            const res = await fetch(url)
            const json = await res.json()
            if (canceled) return
            if (!json.success) {
                console.error(json.error)
                return
            }
            const projects = json.projects
            for (const p of projects) {
                if (!isProtocaasProject(p)) {
                    console.error('Invalid project:', p)
                    return
                }
            }
            setProjects(projects)
        })()
        return () => {
            canceled = true
        }
    }, [tag])
    return projects
}

export default useProjectsForTag