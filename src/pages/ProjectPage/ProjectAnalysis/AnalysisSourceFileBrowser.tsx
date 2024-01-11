import { FunctionComponent, useMemo, useReducer } from "react"
import { selectedStringsReducer } from "../FileBrowser/FileBrowser2"
import FileBrowserTable, { FileBrowserTableFile } from "../FileBrowser/FileBrowserTable"
import AnalysisSourceClient from "./AnalysisSourceClient"

type AnalysisSourceFileBrowserProps = {
    width: number
    height: number
    analysisSourceClient: AnalysisSourceClient
    onOpenFile: (path: string) => void
    allFiles?: AnalysisSourceFile[]
}

export type AnalysisSourceFile = {
    path: string
}

const AnalysisSourceFileBrowser: FunctionComponent<AnalysisSourceFileBrowserProps> = ({width, height, analysisSourceClient, onOpenFile, allFiles}) => {
    const [selectedFileNames, selectedFileNamesDispatch] = useReducer(selectedStringsReducer, new Set<string>())

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