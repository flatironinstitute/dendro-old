import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { DendroProject } from "../../../../types/dendro-types"
import Markdown from "../../../../Markdown/Markdown"
import nunjucks from "nunjucks"
import { useScript } from "../ElectricalSeriesSection/LoadElectricalSeriesScriptWindow"

type LoadSpikeSortingInScriptWindowProps = {
    onClose: () => void
    project: DendroProject
    fileName: string
}

const LoadSpikeSortingInScriptWindow: FunctionComponent<LoadSpikeSortingInScriptWindowProps> = ({project, fileName}) => {
    const [copied, setCopied] = useState(false)
    const script = useScript('/scripts/load_spike_sorting.py')
    const processedScript = useMemo(() => {
        return nunjucks.renderString(script, {project, fileName})
    }, [script, project, fileName])
    const markdownSource = `
Use this script to load this spike sorting into a SpikeInterface sorting object. If this is an embargoed dandiset, then be sure to set the DANDI_API_KEY environment variable prior to running the script.

You first need install dendro and spikeinterface via pip: \`pip install --upgrade dendro spikeinterface\`

${copied ? '*Copied to clipboard*' : '[Copy](#copy)'}

\`\`\`python
${processedScript}
\`\`\`
    `
    const processedMarkdownSource = useMemo(() => {
        return nunjucks.renderString(markdownSource, {project, fileName})
    }, [markdownSource, project, fileName])
    const handleLinkClick = useCallback((href: string) => {
        if (href === '#copy') {
            navigator.clipboard.writeText(processedScript)
            setCopied(true)
        }
    }, [processedScript])
    return (
        <Markdown source={processedMarkdownSource} onLinkClick={handleLinkClick} />
    )
}

export default LoadSpikeSortingInScriptWindow