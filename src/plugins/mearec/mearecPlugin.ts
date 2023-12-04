import { DendroFrontendPlugin, PluginContext } from "../DendroFrontendPlugin"

const mearecPlugin: DendroFrontendPlugin = {
    pluginName: 'mearec',
    initialize: (context: PluginContext) => {
        context.registerAction({
            name: 'mearec-generate-templates',
            type: 'processor-that-generates-a-single-output',
            label: 'MEArec: generate templates',
            defaultOutputFileName: 'generated/mearec/default.templates.h5',
            processorTag: 'mearec_generate_templates',
            defaultRequiredResources: {
                numCpus: 4,
                numGpus: 0,
                memoryGb: 8,
                timeSec: 60 * 60
            }
        })
    }
}

export default mearecPlugin
