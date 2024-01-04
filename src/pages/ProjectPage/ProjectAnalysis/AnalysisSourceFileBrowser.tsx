import { FunctionComponent, useEffect, useMemo, useReducer, useState } from "react"
import AnalysisSourceClient from "./AnalysisSourceClient"
import { joinPaths } from "./ClonedRepo"
import FileBrowserTable, { FileBrowserTableFile } from "../FileBrowser/FileBrowserTable"
import { selectedStringsReducer } from "../FileBrowser/FileBrowser2"

type AnalysisSourceFileBrowserProps = {
    width: number
    height: number
    analysisSourceClient: AnalysisSourceClient
    onOpenFile: (path: string) => void
}

type AnalysisSourceFile = {
    path: string
}

const AnalysisSourceFileBrowser: FunctionComponent<AnalysisSourceFileBrowserProps> = ({width, height, analysisSourceClient, onOpenFile}) => {
    const [allFiles, setAllFiles] = useState<AnalysisSourceFile[] | undefined>(undefined)

    const [selectedFileNames, selectedFileNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

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

    const files2: FileBrowserTableFile[] | undefined = useMemo(() => {
        if (!allFiles) return undefined
        return allFiles.map(f => ({
            fileName: f.path,
            size: 0,
            timestampCreated: 0,
            content: undefined
        }))
    }, [allFiles])

    if (!allFiles) {
        return <div>Loading files...</div>
    }

    return (
        <div style={{width, height, overflowY: 'auto'}}>
            <FileBrowserTable
                hideSizeColumn={true}
                hideModifiedColumn={true}
                files={files2}
                selectedFileNames={selectedFileNames}
                selectedFileNamesDispatch={selectedFileNamesDispatch}
                currentTabName={undefined}
                onOpenFile={onOpenFile}
                multiSelect={false}
            />
        </div>
    )
}

export default AnalysisSourceFileBrowser