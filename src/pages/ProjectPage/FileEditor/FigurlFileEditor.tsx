import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { useProject } from "../ProjectPageContext"

type FigurlFileEditorProps = {
    fileName: string
    width: number
    height: number
}

const FigurlFileEditor: FunctionComponent<FigurlFileEditorProps> = ({fileName, width, height}) => {
    if (!fileName.endsWith('.figurl')) {
        throw Error('Unexpected file extension: ' + fileName)
    }
    const {files} = useProject()
    const file = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])

    const [url, setUrl] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (!file) return
        if (!file.content.startsWith('url:')) {
            console.warn('Unexpected file content: ' + file.content)
            return
        }
        let canceled = false
        ; (async () => {
            const u = await fetchTextFile(file.content.slice('url:'.length))
            if (canceled) return
            setUrl(u)
        })()
        return () => {canceled = true}
    }, [file])

    if (!files) return <div>Loading...</div>
    if (!file) return <div>File not found: {fileName}</div>
    if (!url) return <div>Loading file content...</div>

    return (
        <div>
            <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
        </div>
    )
}

const fetchTextFile = async (url: string) => {
    const response = await fetch(url)
    if (!response.ok) {
        throw Error(`Unexpected response for ${url}: ${response.status}`)
    }
    return await response.text()
}

export default FigurlFileEditor