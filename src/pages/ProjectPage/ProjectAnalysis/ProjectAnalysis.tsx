import { FunctionComponent, useEffect, useState } from "react"
import { useProject } from "../ProjectPageContext"
import AnalysisSourceClient from "./AnalysisSourceClient"
import { Splitter } from "@fi-sci/splitter"
import AnalysisSourceFileBrowser, { AnalysisSourceFile } from "./AnalysisSourceFileBrowser"
import AnalysisSourceFileView from "./AnalysisSourceFileView"
import { joinPaths } from "./ClonedRepo"

type ProjectAnalysisProps = {
    width: number
    height: number
}

const ProjectAnalysis: FunctionComponent<ProjectAnalysisProps> = ({width, height}) => {
    const {project} = useProject()
    const analysisSourceUrl = project?.analysisSourceUrl

    const {analysisSourceClient, status} = useAnalysisSourceClient(analysisSourceUrl)

    if (!project) {
        return (
            <div style={{width, height, padding: 20}}>
                <span style={{fontSize: 20}}>Loading project...</span>
            </div>
        )
    }

    if (!analysisSourceUrl) {
        return (
            <div style={{width, height, padding: 20}}>
                <span style={{fontSize: 20}}>This project does not have a linked analysis source URL.</span>
            </div>
        )
    }

    if (!analysisSourceClient) {
        return (
            <div style={{width, height, padding: 20}}>
                <span style={{fontSize: 20}}>Loading analysis source: {status}</span>
            </div>
        )
    }

    return (
        <ProjectAnalysisChild
            width={width}
            height={height}
            analysisSourceClient={analysisSourceClient}
        />
    )
}

const useAnalysisSourceClient = (analysisSourceUrl: string | undefined) => {
    const [status, setStatus] = useState<string | undefined>('')
    const [analysisSourceClient, setAnalysisSourceClient] = useState<AnalysisSourceClient | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        ; (async () => {
            if (!analysisSourceUrl) return
            setStatus('loading')
            const client = await AnalysisSourceClient.create(analysisSourceUrl, setStatus)
            if (canceled) return
            setAnalysisSourceClient(client)
        })()
        return () => {canceled = true}
    }, [analysisSourceUrl])
    return {analysisSourceClient, status}
}

type ProjectAnalysisChildProps = {
    width: number
    height: number
    analysisSourceClient: AnalysisSourceClient
}

const ProjectAnalysisChild: FunctionComponent<ProjectAnalysisChildProps> = ({width, height, analysisSourceClient}) => {
    const initialSplitterPosition = 250
    const [currentFileName, setCurrentFileName] = useState<string | undefined>(undefined)
    const [allFiles, setAllFiles] = useState<AnalysisSourceFile[] | undefined>(undefined)

    useEffect(() => {
        let canceled = false
        ; (async () => {
            const ret: AnalysisSourceFile[] = []
            const load = async (path: string) => {
                const ff = await analysisSourceClient.readDirectory(path)
                for (const f of ff.files) {
                    ret.push({path: joinPaths(path, f)})
                }
                for (const d of ff.subdirectories) {
                    await load(joinPaths(path, d))
                }
                if (canceled) return
            }
            await load('')
            if (canceled) return
            setAllFiles(ret)
        })()
        return () => {canceled = true}
    }, [analysisSourceClient])

    // if there is just one .ipynb file, open it by default
    // or if there is just one main.ipynb file, open it by default
    // of if there is just one index.ipynb file, open it by default
    useEffect(() => {
        if (currentFileName) return
        if (!allFiles) return
        const ipynbFiles = allFiles.filter(f => f.path.endsWith('.ipynb'))
        if (ipynbFiles.length === 1) {
            setCurrentFileName(ipynbFiles[0].path)
            return
        }
        const mainIpynbFiles = allFiles.filter(f => f.path.endsWith('main.ipynb'))
        if (mainIpynbFiles.length === 1) {
            setCurrentFileName(mainIpynbFiles[0].path)
            return
        }
        const indexIpynbFiles = allFiles.filter(f => f.path.endsWith('index.ipynb'))
        if (indexIpynbFiles.length === 1) {
            setCurrentFileName(indexIpynbFiles[0].path)
            return
        }
    }, [allFiles, currentFileName])

    return (
        <Splitter
            width={width}
            height={height}
            direction="horizontal"
            initialPosition={initialSplitterPosition}
        >
            <AnalysisSourceFileBrowser
                width={0}
                height={0}
                analysisSourceClient={analysisSourceClient}
                onOpenFile={setCurrentFileName}
                allFiles={allFiles}
            />
            <AnalysisSourceFileView
                width={0}
                height={0}
                analysisSourceClient={analysisSourceClient}
                fileName={currentFileName}
            />
        </Splitter>
    )
}

export default ProjectAnalysis