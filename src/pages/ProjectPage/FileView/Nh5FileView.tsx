import { Hyperlink } from "@fi-sci/misc";
import { FunctionComponent, useEffect, useMemo, useState } from "react";
import { RemoteNH5FileClient, RemoteNH5Group } from "../../../nh5";
import { useProject } from "../ProjectPageContext";
import FileViewTable from "./FileViewTable";


type Props = {
    fileName: string
    width: number
    height: number
}

export const useNh5FileClient = (nh5Url?: string) => {
    const [client, setClient] = useState<RemoteNH5FileClient | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        if (!nh5Url) return
        ; (async () => {
            const c = await RemoteNH5FileClient.create(nh5Url)
            if (canceled) return
            setClient(c)
        })()
        return () => {canceled = true}
    }, [nh5Url])
    return client
}

const Nh5FileView: FunctionComponent<Props> = ({fileName, width, height}) => {
    const {files} = useProject()

    const {projectId} = useProject()

    const nbFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])

    // const metadata = nbFile?.metadata
    const cc = nbFile?.content || ''
    const nh5Url = cc.startsWith('url:') ? cc.slice('url:'.length) : cc

    const nh5FileClient = useNh5FileClient(nh5Url)

    const [rootGroup, setRootGroup] = useState<RemoteNH5Group | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        if (!nh5FileClient) return
        ; (async () => {
            const g = await nh5FileClient.getGroup('/')
            if (canceled) return
            setRootGroup(g)
        })()
        return () => {canceled = true}
    }, [nh5FileClient])

    const {fileType, fileFormatVersion} = useMemo(() => {
        if (!rootGroup) return {fileType: undefined, fileFormatVersion: undefined}
        const attrs = rootGroup.attrs
        if (!attrs) return {fileType: undefined, fileFormatVersion: undefined}
        return {
            fileType: attrs['type'],
            fileFormatVersion: attrs['format_version']
        }
    }, [rootGroup])

    return (
        <div style={{position: 'absolute', width, height, background: 'white'}}>
            <hr />
            <FileViewTable fileName={fileName} additionalRows={[
                {label: 'File type', value: fileType},
                {label: 'File format version', value: fileFormatVersion}
            ]} />
            <div>&nbsp;</div>
            <div>
                {
                    ['tuning_curves_2d', 'spike_sorting_summary'].includes(fileType) && (
                        <Hyperlink onClick={() => {
                            const viewData = encodeURI(JSON.stringify({
                                nh5: nh5Url
                            }))
                            const label = encodeURI(projectId + ':' + fileName)
                            const url = `https://figurl.org/f?v=npm://@fi-sci/figurl-dandi-vis@0.1/dist&d=${viewData}&label=${label}`
                            window.open(url, '_blank')
                        }}>View {fileType}</Hyperlink>
                    )
                }
            </div>
            <div>&nbsp;</div>
        </div>
    )
}

export default Nh5FileView