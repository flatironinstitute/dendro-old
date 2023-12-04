import { PluginAction, PluginContext } from "./DendroFrontendPlugin"
import mearecPlugin from "./mearec/mearecPlugin"

const initializePlugins = () => {
    const actions: PluginAction[] = []
    const pluginContext: PluginContext = {
        registerAction: (action) => {
            actions.push(action)
        }
    }
    mearecPlugin.initialize(pluginContext)

    return {
        actions
    }
}

export default initializePlugins