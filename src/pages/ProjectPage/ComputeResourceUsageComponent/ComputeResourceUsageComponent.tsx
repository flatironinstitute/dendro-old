import { FunctionComponent, useEffect, useState } from "react"
import { ComputeResourceUserUsage, isComputeResourceUserUsage } from "../../../types/dendro-types"
import { apiBase, getRequest } from "../../../dbInterface/dbInterface"
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth"
import { GithubAuthData } from "../../../GithubAuth/GithubAuthContext"

type ComputeResourceUsageComponentProps = {
    computeResourceId: string
}

const useComputeResourceUserUsage = (computeResourceId: string, userId: string | undefined, auth: GithubAuthData) => {
    const [usage, setUsage] = useState<ComputeResourceUserUsage | undefined>(undefined)

    useEffect(() => {
        if (!userId) return
        let canceled = false
        const fetchUsage = async () => {
            const url = `${apiBase}/api/gui/usage/compute_resource/${computeResourceId}/user/${userId}`
            const response = await getRequest(url, auth)
            if (canceled) return
            if (!response.success) {
                console.error("Error fetching usage", response)
                return
            }
            const u = response.usage
            if (!isComputeResourceUserUsage(u)) {
                console.error("Invalid usage", u)
                return
            }
            setUsage(u)
        }
        fetchUsage()
        return () => { canceled = true }
    }, [computeResourceId, userId, auth])

    return usage
}

const ComputeResourceUsageComponent: FunctionComponent<ComputeResourceUsageComponentProps> = ({computeResourceId}) => {
    const auth = useGithubAuth()
    const usage = useComputeResourceUserUsage(computeResourceId, auth.userId, auth)
    if (!auth.userId) return <div>Not logged in</div>
    if (!usage) return <div>Loading...</div>
    const numJobsIncludingDeleted = usage.jobsIncludingDeleted.length
    const numJobs = usage.jobsIncludingDeleted.filter(j => (!j.deleted)).length
    return (
        <div>
            <table className="scientific-table">
                <body>
                    <tr>
                        <td>Num. jobs</td>
                        <td>{numJobs}</td>
                    </tr>
                    <tr>
                        <td>Num. jobs including deleted</td>
                        <td>{numJobsIncludingDeleted}</td>
                    </tr>
                </body>
            </table>
        </div>
    )
}

export default ComputeResourceUsageComponent