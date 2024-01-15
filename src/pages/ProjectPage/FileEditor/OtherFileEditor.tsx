import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { useProject } from "../ProjectPageContext"

type FigurlFileEditorProps = {
    fileName: string
    width: number
    height: number
}

const OtherFileEditor: FunctionComponent<FigurlFileEditorProps> = ({fileName, width, height}) => {
    const {files} = useProject()
    const file = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])

    const [content, setContent] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (!file) return
        if (file.size > 50000) {
            setContent('File is too large to display')
            return
        }
        if (!file.content.startsWith('url:')) {
            console.warn('Unexpected file content: ' + file.content)
            return
        }
        let canceled = false
        ; (async () => {
            const u = await fetchTextFile(file.content.slice('url:'.length))
            if (canceled) return
            setContent(u)
        })()
        return () => {canceled = true}
    }, [file])

    if (!files) return <div>Loading...</div>
    if (!file) return <div>File not found: {fileName}</div>
    if (!content) return <div>Loading file content...</div>

    return (
        <div style={{position: 'absolute', width, height, overflowY: 'auto'}}>
            {
                fileName.endsWith('.json') ? (
                    <pre>
                        {JSON.stringify(JSON.parse(content), null, 4)}
                    </pre>
                ) : (
                    <pre>
                        {content}
                    </pre>
                )
            }
        </div>
    )
}

export const fetchTextFile = async (url: string) => {
    const response = await fetch(url)
    if (!response.ok) {
        throw Error(`Unexpected response for ${url}: ${response.status}`)
    }
    return await response.text()
}

export default OtherFileEditor