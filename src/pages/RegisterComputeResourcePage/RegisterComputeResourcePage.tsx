import { FunctionComponent, useCallback, useMemo, useState } from "react";
import { registerComputeResource } from "../../dbInterface/dbInterface";
import { useGithubAuth } from "../../GithubAuth/useGithubAuth";
import UserIdComponent from "../../UserIdComponent";
import useRoute from "../../useRoute";

type Props = {
    // none
}

const RegisterComputeResourcePage: FunctionComponent<Props> = () => {
    const {route, setRoute} = useRoute()
    const [name, setName] = useState('')

    if (route.page !== 'register-compute-resource') throw Error('Unexpected')

    const {computeResourceId, resourceCode} = route

    const auth = useGithubAuth()

    const handleRegister = useCallback(async () => {
        if (!auth) return
        await registerComputeResource(computeResourceId, resourceCode, name, auth)
        setRoute({page: 'compute-resources'})
    }, [computeResourceId, resourceCode, name, auth, setRoute])

    if (!auth.userId) {
        <p>To register this compute resource, you must first log in.</p>
    }

    return (
        <div>
            <p>You are registering compute resource {computeResourceId} to user <UserIdComponent userId={auth.userId} /></p>
            <div>
                Choose a name for this resource: <input type="text" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <div>
                <button disabled={!name} onClick={handleRegister}>Register</button>
            </div>
        </div>
    )
}

export default RegisterComputeResourcePage;