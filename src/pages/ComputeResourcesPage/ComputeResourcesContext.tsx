import React, { FunctionComponent, PropsWithChildren, useCallback, useEffect, useMemo, useState } from 'react';
import { deleteComputeResource, fetchComputeResources } from '../../dbInterface/dbInterface';
import { useGithubAuth } from '../../GithubAuth/useGithubAuth';
import { DendroComputeResource } from '../../types/dendro-types';

type Props = {
    // none
}

type ComputeResourcesContextType = {
    computeResources: DendroComputeResource[]
    refreshComputeResources: () => void
    deleteComputeResource: (computeResourceId: string) => void
}

const ComputeResourcesContext = React.createContext<ComputeResourcesContextType>({
    computeResources: [],
    refreshComputeResources: () => {},
    deleteComputeResource: () => {}
})

export const SetupComputeResources: FunctionComponent<PropsWithChildren<Props>> = ({children}) => {
    const [computeResources, setComputeResources] = useState<DendroComputeResource[]>([])
    const [refreshComputeResourcesCode, setRefreshComputeResourcesCode] = useState(0)
    const refreshComputeResources = useCallback(() => setRefreshComputeResourcesCode(rc => rc + 1), [])

    const auth = useGithubAuth()

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