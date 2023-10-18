import React, { FunctionComponent, PropsWithChildren, useCallback, useEffect, useMemo, useState } from 'react';
import { deleteComputeResource, fetchComputeResources } from '../../dbInterface/dbInterface';
import { useGithubAuth } from '../../GithubAuth/useGithubAuth';
import { ProtocaasComputeResource } from '../../types/protocaas-types';

type Props = {
    // none
}

type ComputeResourcesContextType = {
    computeResources: ProtocaasComputeResource[]
    refreshComputeResources: () => void
    deleteComputeResource: (computeResourceId: string) => void
}

const ComputeResourcesContext = React.createContext<ComputeResourcesContextType>({
    computeResources: [],
    refreshComputeResources: () => {},
    deleteComputeResource: () => {}
})

export const SetupComputeResources: FunctionComponent<PropsWithChildren<Props>> = ({children}) => {
    const [computeResources, setComputeResources] = useState<ProtocaasComputeResource[]>([])
    const [refreshComputeResourcesCode, setRefreshComputeResourcesCode] = useState(0)
    const refreshComputeResources = useCallback(() => setRefreshComputeResourcesCode(rc => rc + 1), [])

    const {accessToken, userId} = useGithubAuth()
    const auth = useMemo(() => (accessToken ? {githubAccessToken: accessToken, userId} : {}), [accessToken, userId])

    useEffect(() => {
        (async () => {
            setComputeResources([])
            if (!auth) return
            const cr = await fetchComputeResources(auth)
            setComputeResources(cr)
        })()
    }, [auth, refreshComputeResourcesCode])

    const deleteComputeResourceHandler = useCallback(async (computeResourceId: string) => {
        if (!auth) return
        await deleteComputeResource(computeResourceId, auth)
        refreshComputeResources()
    }, [auth, refreshComputeResources])

    const value = React.useMemo(() => ({
        computeResources,
        refreshComputeResources,
        deleteComputeResource: deleteComputeResourceHandler
    }), [computeResources, refreshComputeResources, deleteComputeResourceHandler])

    return (
        <ComputeResourcesContext.Provider value={value}>
            {children}
        </ComputeResourcesContext.Provider>
    )
}

export const useComputeResources = () => {
    const context = React.useContext(ComputeResourcesContext)
    return context
}