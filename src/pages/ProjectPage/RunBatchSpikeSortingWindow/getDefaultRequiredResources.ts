import { ComputeResourceSpecProcessor, DendroJobRequiredResources } from "../../../types/dendro-types"


const getDefaultRequiredResources = (processor: ComputeResourceSpecProcessor | undefined): DendroJobRequiredResources | undefined => {
    if (!processor) return undefined
    const tags = processor.tags.map(t => t.tag)
    if ((tags.includes('kilosort2_5') || tags.includes('kilosort3'))) {
        return {
            numCpus: 4,
            numGpus: 1,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
    else if (tags.includes('mountainsort5')) {
        return {
            numCpus: 8,
            numGpus: 0,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
    else {
        return {
            numCpus: 8,
            numGpus: 0,
            memoryGb: 16,
            timeSec: 3600 * 3 // todo: determine this based on the size of the recording!
        }
    }
}

export default getDefaultRequiredResources