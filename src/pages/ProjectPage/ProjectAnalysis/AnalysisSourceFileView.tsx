import { FunctionComponent, useEffect, useMemo, useState } from "react"
import AnalysisSourceClient from "./AnalysisSourceClient"
import ReactSyntaxHighlighter from "react-syntax-highlighter"
import { IpynbRenderer } from "react-ipynb-renderer"

// select jupyter theme
import "react-ipynb-renderer/dist/styles/default.css";
//import "react-ipynb-renderer/dist/styles/dark.css";
//import "react-ipynb-renderer/dist/styles/darkbronco.css";
//import "react-ipynb-renderer/dist/styles/dorkula.css";
//import "react-ipynb-renderer/dist/styles/chesterish.css";
//import "react-ipynb-renderer/dist/styles/grade3.css";
//import "react-ipynb-renderer/dist/styles/gruvboxd.css";
//import "react-ipynb-renderer/dist/styles/gruvboxl.css";
//import "react-ipynb-renderer/dist/styles/monokai.css";
//import "react-ipynb-renderer/dist/styles/oceans16.css";
//import "react-ipynb-renderer/dist/styles/onedork.css";
//import "react-ipynb-renderer/dist/styles/solarizedd.css";
//import "react-ipynb-renderer/dist/styles/solarizedl.css";

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

    const language = useMemo(() => {
        if (!fileName) return 'text'
        return determineLanguageFromFileName(fileName)
    }, [fileName])

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
        if (fileName.endsWith('.ipynb')) {
            let obj
            try {
                obj = JSON.parse(text)
            }
            catch (err) {
                content = <div>Error parsing ipynb file</div>
                obj = undefined
            }
            content = (
                <div style={{position: 'absolute', width, top: topBarHeight, height: height - topBarHeight, overflowY: 'auto'}}>
                    <IpynbRenderer
                        ipynb={obj ? obj : {}}
                        syntaxTheme="darcula"
                    />
                </div>
            )
        }
        else {
            content = (
                <div style={{position: 'absolute', width, top: topBarHeight, height: height - topBarHeight, overflowY: 'auto'}}>
                    <ReactSyntaxHighlighter language={language}>
                        {text}
                    </ReactSyntaxHighlighter>
                </div>
            )
        }
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

const determineLanguageFromFileName = (fileName: string) => {
    const ext = fileName.split('.').slice(-1)[0].toLowerCase()
    if (ext === 'md') return 'markdown'
    if (ext === 'py') return 'python'
    if (ext === 'ipynb') return 'python'
    if (ext === 'json') return 'json'
    if (ext === 'yaml') return 'yaml'
    if (ext === 'yml') return 'yaml'
    if (ext === 'sh') return 'bash'
    if (ext === 'bash') return 'shell'
    if (ext === 'c') return 'c'
    if (ext === 'cpp') return 'cpp'
    if (ext === 'h') return 'cpp'
    if (ext === 'hpp') return 'cpp'
    if (ext === 'java') return 'java'
    if (ext === 'js') return 'javascript'
    if (ext === 'ts') return 'typescript'
    if (ext === 'tsx') return 'typescript'
    if (ext === 'css') return 'css'
    if (ext === 'xml') return 'xml'
    if (ext === 'svg') return 'xml'
    return 'text'
}

export default AnalysisSourceFileView