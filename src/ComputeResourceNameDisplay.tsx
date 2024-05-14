import { Hyperlink } from "@fi-sci/misc";
import { FunctionComponent, useMemo } from "react";
import { useComputeResources } from "./pages/ComputeResourcesPage/ComputeResourcesContext";
import useRoute from "./useRoute";

type Props = {
    computeResourceId: string | undefined
    link?: boolean
}

const ComputeResourceNameDisplay: FunctionComponent<Props> = ({ computeResourceId, link }) => {
    const {computeResources} = useComputeResources()
    const displayString = useMemo(() => {
        if (!computeResourceId) return 'DEFAULT'
        const cr = computeResources.find(cr => cr.computeResourceId === computeResourceId)
        return (cr ? cr.name + ` (${abbreviate(computeResourceId, 9)})` : undefined) || abbreviate(computeResourceId, 16)
    }, [computeResources, computeResourceId])
    const {setRoute} = useRoute()
    const a = <span style={{color: '#345', fontStyle: 'italic'}}>{displayString || ''}</span>
    const crId = computeResourceId || import.meta.env.VITE_DEFAULT_COMPUTE_RESOURCE_ID
    if (link) {
        return <Hyperlink onClick={() => setRoute({page: 'compute-resource', computeResourceId: crId})}>{a}</Hyperlink>
    }
    else {
        return a
    }
}

function abbreviate(s: string, maxLength: number) {
    if (s.length <= maxLength) return s
    return s.slice(0, maxLength - 3) + '...'
}

export default ComputeResourceNameDisplay