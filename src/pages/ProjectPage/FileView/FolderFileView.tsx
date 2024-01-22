import { FunctionComponent, useEffect, useMemo, useState } from "react";
import FileViewTable from "./FileViewTable";
import { useProject } from "../ProjectPageContext";
import validateObject, { isArrayOf, isNumber, isString } from "../../../types/validateObject";


type Props = {
    fileName: string
    width: number
    height: number
}

type FileManifest = {
    files: {
        name: string
        size: number
    }[]
}

const isFileManifest = (x: any): x is FileManifest => {
    return validateObject(x, {
        files: isArrayOf(y => validateObject(y, {
            name: isString,
            size: isNumber
        }, {allowAdditionalFields: true}))
    })
}

const useFileManifest = (content: string | undefined) => {
    const [fileManifest, setFileManifest] = useState<FileManifest>()
    useEffect(() => {
        let canceled = false
        if (!content) return
        if (!content.startsWith('url:')) return
        const url = content.slice('url:'.length)
        const fileManifestUrl = url + '/file_manifest.json'
        fetch(fileManifestUrl).then(resp => {
            if (canceled) return
            if (!resp.ok) {
                console.warn(`Unable to fetch file manifest: ${fileManifestUrl}`)
                return
            }
            resp.json().then(json => {
                if (canceled) return
                if (!isFileManifest(json)) {
                    console.warn(`Invalid file manifest: ${fileManifestUrl}`)
                    return
                }
                setFileManifest(json)
            })
        })
        return () => {canceled = true}
    }, [content])
    return fileManifest
}

const FolderFileView: FunctionComponent<Props> = ({fileName, width, height}) => {
    const {files} = useProject()
    const theFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])
    const fileManifest = useFileManifest(theFile?.content)
    if (!files) {
        return <div>Loading...</div>
    }
    if (!theFile) {
        return <div>File not found: {fileName}</div>
    }
    if (!theFile.isFolder) {
        return <div>Not a folder: {fileName}</div>
    }
    return (
        <div style={{position: 'absolute', width, height, background: 'white'}}>
            <hr />
            <FileViewTable fileName={fileName} additionalRows={[]} />
            <div>&nbsp;</div>
            {
                fileManifest && (
                    <table className="table1">
                        <thead>
                            <tr>
                                <th>File</th>
                                <th>Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            {
                                fileManifest.files.map((f, ii) => (
                                    <tr key={ii}>
                                        <td>{f.name}</td>
                                        <td>{f.size}</td>
                                    </tr>
                                ))
                            }
                        </tbody>
                    </table>
                )
            }
            <div>&nbsp;</div>
        </div>
    )
}

export default FolderFileView