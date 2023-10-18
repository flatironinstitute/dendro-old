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
        try {
            await registerComputeResource(computeResourceId, resourceCode, name, auth)
        }
        catch(e) {
            alert(`Error registering compute resource: ${e}`)
            return
        }
        setRoute({page: 'compute-resources'})
    }, [computeResourceId, resourceCode, name, auth, setRoute])

    if (!auth.userId) {
        return <p style={{padding: 30, fontSize: 30}}>To register this compute resource, you must first log in. Click the &quot;Log in&quot; button in the upper right corner.</p>
    }

    return (
        <div style={{fontSize: 20, padding: 20}}>
            <p>You are registering compute resource {abbreviate(computeResourceId, 12)} to user <UserIdComponent userId={auth.userId} /></p>
            <div>
                Choose a name for this resource: <input style={{height: 24}} type="text" value={name} onChange={e => setName(e.target.value)} />
            </div>
            <br />
            <div>
                <button disabled={!name} onClick={handleRegister}>Register</button>
            </div>
        </div>
    )
}

const abbreviate = (s: string, maxLength: number) => {
    if (s.length <= maxLength) return s
    return s.slice(0, maxLength - 3) + '...'
}

export default RegisterComputeResourcePage;