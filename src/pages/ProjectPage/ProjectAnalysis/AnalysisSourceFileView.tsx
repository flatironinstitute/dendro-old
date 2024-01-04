import { FunctionComponent, useEffect, useState } from "react"
import AnalysisSourceClient from "./AnalysisSourceClient"
import ReactSyntaxHighlighter from "react-syntax-highlighter"

type AnalysisSourceFileViewProps = {
    width: number
    height: number
    analysisSourceClient: AnalysisSourceClient
    fileName: string | undefined
}

const topBarHeight = 18

const AnalysisSourceFileView: FunctionComponent<AnalysisSourceFileViewProps> = ({width, height, analysisSourceClient, fileName}) => {
    const [text, setText] = useState<string | undefined>(undefined)
    const isTextFileType = checkTextFileType(fileName || '')
    useEffect(() => {
        let canceled = false
        if (!fileName) return
        if (!isTextFileType) return
        analysisSourceClient.readTextFile(fileName).then(txt => {
            if (canceled) return
            setText(txt)
        })
        return () => {canceled = true}
    }, [fileName, analysisSourceClient, isTextFileType])

    let content

    if (!fileName) {
        content = <div>No file selected</div>
    }
    else if (!isTextFileType) {
        content = <div>Not a text file type</div>
    }
    else if (text === undefined) {
        content = <div>Loading...</div>
    }
    else {
        content = (
            <div style={{position: 'absolute', width, top: topBarHeight, height: height - topBarHeight, overflowY: 'auto'}}>
                <ReactSyntaxHighlighter language="python">
                    {text}
                </ReactSyntaxHighlighter>
            </div>
        )
    }
    return (
        <div style={{position: 'absolute', width, height}}>
            <div style={{position: 'absolute', width, height: topBarHeight, backgroundColor: '#555', color: 'white', paddingLeft: 10, paddingTop: 5, fontSize: 12}}>
                {fileName}
            </div>
            {content}
        </div>
    )
}

const checkTextFileType = (fileName: string) => {
    const ext = fileName.split('.').slice(-1)[0].toLowerCase()
    const candidates = [
        'txt', 'md', 'rst', 'py', 'ipynb', 'json', 'yaml', 'yml', 'sh', 'bash', 'c', 'cpp', 'h', 'hpp', 'java', 'js', 'ts', 'tsx', 'html', 'css', 'xml', 'svg', 'csv', 'tsv',
    ]
    return candidates.includes(ext)
}

export default AnalysisSourceFileView