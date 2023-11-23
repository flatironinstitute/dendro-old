import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { DendroProject } from "../../../../types/dendro-types"
import Markdown from "../../../../Markdown/Markdown"
import nunjucks from "nunjucks"

type LoadElectricalSeriesScriptWindowProps = {
    onClose: () => void
    project: DendroProject
    fileName: string
    electricalSeriesPath: string
}

export const useScript = (url: string) => {
    const [script, setScript] = useState(`# Loading script from ${url}...`)
    useEffect(() => {
        let canceled = false
        ;(async () => {
            const resp = await fetch(url)
            const text = await resp.text()
            if (canceled) return
            setScript(text)
        })()
        return () => {canceled = true}
    }, [url])
    return script
}

const LoadElectricalSeriesScriptWindow: FunctionComponent<LoadElectricalSeriesScriptWindowProps> = ({project, fileName, electricalSeriesPath}) => {
    const [copied, setCopied] = useState(false)
    const script = useScript('/scripts/load_electrical_series.py')
    const processedScript = useMemo(() => {
        return nunjucks.renderString(script, {project, fileName, electricalSeriesPath})
    }, [script, project, fileName, electricalSeriesPath])
    const markdownSource = `
Use this script to load this electrical series into a SpikeInterface recording object. If this is an embargoed dandiset, then be sure to set the DANDI_API_KEY environment variable prior to running the script.

You first need install dendro and spikeinterface via pip: \`pip install --upgrade dendro spikeinterface\`

${copied ? '*Copied to clipboard*' : '[Copy](#copy)'}

\`\`\`python
${processedScript}
\`\`\`
    `
    const processedMarkdownSource = useMemo(() => {
        return nunjucks.renderString(markdownSource, {project, fileName, electricalSeriesPath})
    }, [markdownSource, project, fileName, electricalSeriesPath])
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

export default LoadElectricalSeriesScriptWindow