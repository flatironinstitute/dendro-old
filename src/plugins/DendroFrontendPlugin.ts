import { DendroJobRequiredResources } from "../types/dendro-types"

export type PluginAction = {
    type: 'processor-that-generates-a-single-output',
    name: string,
    label: string,
    defaultOutputFileName: string,
    processorTag: string,
    defaultRequiredResources: DendroJobRequiredResources
}

export type PluginContext = {
    registerAction: (action: PluginAction) => void
}

export type DendroFrontendPlugin = {
    pluginName: string
    initialize: (context: PluginContext) => void
}