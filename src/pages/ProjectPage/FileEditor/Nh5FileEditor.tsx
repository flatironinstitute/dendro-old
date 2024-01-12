import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react";
import { useModalWindow } from "@fi-sci/modal-window"
import { RemoteH5File, getRemoteH5File } from "../../../RemoteH5File/RemoteH5File";
import { Hyperlink } from "@fi-sci/misc";
import ModalWindow from "@fi-sci/modal-window";
import { Splitter } from "@fi-sci/splitter";
import JobsWindow from "../JobsWindow/JobsWindow";
import LoadNwbInPythonWindow from "../LoadNwbInPythonWindow/LoadNwbInPythonWindow";
import { useProject } from "../ProjectPageContext";
import SpikeSortingOutputSection from "./SpikeSortingOutputSection/SpikeSortingOutputSection";
import { DendroJob } from "../../../types/dendro-types";
import { AssetResponse } from "../../DandiBrowser/types";
import { getDandiApiHeaders } from "../../DandiBrowser/DandiBrowser";
import ElectricalSeriesSection from "./ElectricalSeriesSection/ElectricalSeriesSection";
import { RemoteNH5FileClient, RemoteNH5Group } from "../../../nh5";
import { ElapsedTimeComponent } from "./NwbFileEditor";


type Props = {
    fileName: string
    width: number
    height: number
}

const Nh5FileEditor: FunctionComponent<Props> = ({fileName, width, height}) => {
    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={height * 2 / 3}
            direction="vertical"
        >
            <Nh5FileEditorChild
                width={0}
                height={0}
                fileName={fileName}
            />
            <JobsWindow
                width={0}
                height={0}
                fileName={fileName}
            />
        </Splitter>
    )
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

const Nh5FileEditorChild: FunctionComponent<Props> = ({fileName, width, height}) => {
    const {jobs, filesIncludingPending, openTab} = useProject()

    const {projectId} = useProject()

    const nbFile = useMemo(() => {
        if (!filesIncludingPending) return undefined
        return filesIncludingPending.find(f => (f.fileName === fileName))
    }, [filesIncludingPending, fileName])

    // const metadata = nbFile?.metadata
    const cc = nbFile?.content || ''
    const nh5Url = cc.startsWith('url:') ? cc.slice('url:'.length) : ''

    const nh5FileClient = useNh5FileClient(nh5Url)

    const [rootGroup, setRootGroup] = useState<RemoteNH5Group | undefined>(undefined)
    useEffect(() => {
        console.log('--- 1')
        let canceled = false
        if (!nh5FileClient) return
        console.log('--- 2')
        ; (async () => {
            console.log('--- 3')
            const g = await nh5FileClient.getGroup('/')
            console.log('--- 4', g)
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

    const jobProducingThisFile = useMemo(() => {
        if (!jobs) return undefined
        if (!nbFile) return undefined
        if (!nbFile.jobId) return undefined
        const job = jobs.find(j => (j.jobId === nbFile.jobId))
        if (!job) return
        return job
    }, [jobs, nbFile])

    return (
        <div style={{position: 'absolute', width, height, background: 'white'}}>
            <hr />
            <table className="table1">
                <tbody>
                    <tr>
                        <td>Path:</td>
                        <td>{fileName}</td>
                    </tr>
                    <tr>
                        <td>URL:</td>
                        <td>{nh5Url}</td>
                    </tr>
                    {
                        jobProducingThisFile && (
                            <>
                                <tr>
                                    <td>Job status:</td>
                                    <td>
                                        <Hyperlink onClick={() => {openTab(`job:${jobProducingThisFile.jobId}`)}}>
                                            {jobProducingThisFile.status}
                                        </Hyperlink>
                                    </td>
                                </tr>
                                <tr>
                                    <td>Elapsed time (sec):</td>
                                    <td><ElapsedTimeComponent job={jobProducingThisFile} /></td>
                                </tr>
                            </>
                        )
                    }
                    <tr>
                        <td>File type:</td>
                        <td>{fileType}</td>
                    </tr>
                    <tr>
                        <td>File format version:</td>
                        <td>{fileFormatVersion}</td>
                    </tr>
                </tbody>
            </table>
            <div>&nbsp;</div>
            <div>
                {
                    fileType === 'tuning_curves_2d' && (
                        <Hyperlink onClick={() => {
                            const viewData = encodeURI(JSON.stringify({
                                type: 'tuning_curves_2d_nh5',
                                nh5_file: nh5Url
                            }))
                            const label = encodeURI(projectId + ':' + fileName)
                            const url = `https://figurl.org/f?v=https://figurl-tuning-curves-1.surge.sh&d=${viewData}&label=${label}`
                            window.open(url, '_blank')
                        }}>View 2D tuning curves</Hyperlink>
                    )
                }
            </div>
            <div>&nbsp;</div>
        </div>
    )
}

export default Nh5FileEditor