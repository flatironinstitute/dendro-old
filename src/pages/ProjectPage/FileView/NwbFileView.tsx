import { Hyperlink } from "@fi-sci/misc";
import ModalWindow, { useModalWindow } from "@fi-sci/modal-window";
import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react";
import { RemoteH5File, getRemoteH5File } from "../../../RemoteH5File/RemoteH5File";
import { getDandiApiHeaders } from "../../DandiBrowser/DandiBrowser";
import { AssetResponse } from "../../DandiBrowser/types";
import LoadNwbInPythonWindow from "../LoadNwbInPythonWindow/LoadNwbInPythonWindow";
import { useProject } from "../ProjectPageContext";
import ElectricalSeriesSection from "./ElectricalSeriesSection/ElectricalSeriesSection";
import { ElapsedTimeComponent } from "./FileViewTable";
import SpikeSortingOutputSection from "./SpikeSortingOutputSection/SpikeSortingOutputSection";


type Props = {
    fileName: string
    width: number
    height: number
}

export const useNwbFile = (nwbUrl?: string) => {
    const [nwbFile, setNwbFile] = useState<RemoteH5File | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        if (!nwbUrl) return
        ; (async () => {
            const resolvedNwbUrl = await getResolvedUrl(nwbUrl)
            const f = await getRemoteH5File(resolvedNwbUrl, undefined)
            if (canceled) return
            setNwbFile(f)
        })()
        return () => {canceled = true}
    }, [nwbUrl])
    return nwbFile
}

export const useElectricalSeriesPaths = (nwbFile: RemoteH5File | undefined) => {
    const [electricalSeriesPaths, setElectricalSeriesPaths] = useState<string[] | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        setElectricalSeriesPaths(undefined)
        ; (async () => {
            if (!nwbFile) return
            const grp = await nwbFile.getGroup('acquisition')
            if (canceled) return
            if (!grp) return
            const pp: string[] = []
            for (const sg of grp.subgroups) {
                if (sg.attrs['neurodata_type'] === 'ElectricalSeries') {
                    pp.push(sg.path)
                }
            }
            setElectricalSeriesPaths(pp)
        })()
        return () => {canceled = true}
    }, [nwbFile])
    return electricalSeriesPaths
}

export const useUnitsPaths = (nwbFile: RemoteH5File | undefined) => {
    const [unitsPaths, setUnitsPaths] = useState<string[] | undefined>(undefined)
    useEffect(() => {
        let canceled = false
        setUnitsPaths(undefined)
        ; (async () => {
            const foundPaths: string[] = []
            if (!nwbFile) return
            const grp = await tryGetGroup(nwbFile, '/units')
            if (canceled) return
            if (grp) {
                foundPaths.push('/units')
            }
            const processingEcephysGroup = await tryGetGroup(nwbFile, '/processing/ecephys')
            if (canceled) return
            if (processingEcephysGroup) {
                for (const sg of processingEcephysGroup.subgroups) {
                    if (sg.attrs['neurodata_type'] === 'Units') {
                        foundPaths.push(sg.path)
                    }
                }
            }
            setUnitsPaths(foundPaths)
        })()
        return () => {canceled = true}
    }, [nwbFile])
    return unitsPaths
}

type FileViewTableProps = {
    fileName: string
    additionalRows: {
        label: string
        value: any
    }[]
}

const FileViewTable: FunctionComponent<FileViewTableProps> = ({fileName, additionalRows}) => {
    const {files, jobs, openTab} = useProject()
    const theFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])

    const cc = theFile?.content || ''
    const theUrl = cc.startsWith('url:') ? cc.slice('url:'.length) : cc
    const theUri = theFile ? `dendro:?file_id=${theFile.fileId}&project=${theFile.projectId}&label=${theFile.fileName}` : ''

    const jobProducingThisFile = useMemo(() => {
        if (!jobs) return undefined
        if (!theFile) return undefined
        if (!theFile.jobId) return undefined
        const job = jobs.find(j => (j.jobId === theFile.jobId))
        if (!job) return
        return job
    }, [jobs, theFile])

    return (
        <table className="table1">
            <tbody>
                <tr>
                    <td>Path:</td>
                    <td>{fileName}</td>
                </tr>
                <tr>
                    <td>URL:</td>
                    <td>{theUrl}</td>
                </tr>
                <tr>
                    <td>URI:</td>
                    <td>{theUri}</td>
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
                {
                    additionalRows.map(row => (
                        <tr key={row.label}>
                            <td>{row.label}</td>
                            <td>{row.value}</td>
                        </tr>
                    ))
                }
                <tr>
                </tr>
            </tbody>
        </table>
    )
}

const NwbFileView: FunctionComponent<Props> = ({fileName, width, height}) => {
    const [assetResponse, setAssetResponse] = useState<AssetResponse | null>(null)

    const {project, jobs, files} = useProject()

    const nbFile = useMemo(() => {
        if (!files) return undefined
        return files.find(f => (f.fileName === fileName))
    }, [files, fileName])

    const metadata = nbFile?.metadata
    const cc = nbFile?.content || ''
    const nwbUrl = cc.startsWith('url:') ? cc.slice('url:'.length) : cc
    // const nwbFile = useNwbFile(nwbUrl)
    // const electricalSeriesPaths = useElectricalSeriesPaths(nwbFile)

    const dandisetId = metadata?.dandisetId || ''
    const dandisetVersion = metadata?.dandisetVersion || ''
    const dandiAssetId = metadata?.dandiAssetId || ''
    const dandiAssetPath = metadata?.dandiAssetPath || ''
    const dandiStaging = metadata?.dandiStaging || false

    const stagingStr = dandiStaging ? '-staging' : ''
    const stagingStr2 = dandiStaging ? 'gui-staging.' : ''

    const handleOpenInNeurosift = useCallback(() => {
        let additionalQueryParams = ''
        if (metadata.dandisetId) {
            additionalQueryParams += `&dandisetId=${metadata.dandisetId}`
        }
        if (metadata.dandisetVersion) {
            additionalQueryParams += `&dandisetVersion=${metadata.dandisetVersion}`
        }
        if (metadata.dandiAssetPath) {
            const dandiAssetPathEncoded = encodeURIComponent(metadata.dandiAssetPath)
            additionalQueryParams += `&dandiAssetPath=${dandiAssetPathEncoded}`
        }
        const u = `https://flatironinstitute.github.io/neurosift/?p=/nwb&url=${nwbUrl}${additionalQueryParams}`
        window.open(u, '_blank')
    }, [nwbUrl, metadata])

    useEffect(() => {
        if (!dandisetId) return
        if (!dandiAssetId) return
        ; (async () => {
            const {headers} = getDandiApiHeaders(dandiStaging)
            const response = await fetch(
                `https://api${stagingStr}.dandiarchive.org/api/dandisets/${dandisetId}/versions/${dandisetVersion}/assets/${dandiAssetId}/`,
                {
                    headers
                }
            )
            if (response.status === 200) {
                const json = await response.json()
                const assetResponse: AssetResponse = json
                setAssetResponse(assetResponse)
            }
        })()
    }, [dandisetId, dandiAssetId, dandisetVersion, stagingStr, dandiStaging])

    if ((assetResponse) && (dandiAssetPath !== assetResponse.path)) {
        console.warn(`Mismatch between dandiAssetPath (${dandiAssetPath}) and assetResponse.path (${assetResponse.path})`)
    }

    const {visible: loadNwbInPythonWindowVisible, handleOpen: openLoadNwbInPythonWindow, handleClose: closeLoadNwbInPythonWindow} = useModalWindow()

    const spikeSortingJob = useMemo(() => {
        if (!jobs) return undefined
        if (!nbFile) return undefined
        if (!nbFile.jobId) return undefined
        const job = jobs.find(j => (j.jobId === nbFile.jobId))
        if (!job) return
        if (job.processorSpec.tags.map(t => t.tag).includes('spike_sorter')) {
            return job
        }
        return undefined
    }, [jobs, nbFile])


    return (
        <div style={{position: 'absolute', width, height, background: 'white'}}>
            <hr />
            <FileViewTable
                fileName={fileName}
                additionalRows={[
                    {label: 'Dandiset', value: <>{
                        dandisetId && <a href={`https://${stagingStr2}dandiarchive.org/dandiset/${dandisetId}/${dandisetVersion}`} target="_blank" rel="noreferrer">
                            {dandisetId} ({dandisetVersion || ''})
                        </a>
                    }</>},
                    {label: 'DANDI Path', value: assetResponse?.path},
                ]}
            />
            <div>&nbsp;</div>
            <ul>
            {
                nwbUrl && (
                    <li>
                        <Hyperlink onClick={handleOpenInNeurosift}>Open NWB file in Neurosift</Hyperlink>
                    </li>
                )
            }
            {
                nwbUrl && (
                    <li>
                        <Hyperlink onClick={openLoadNwbInPythonWindow}>Load NWB file in Python</Hyperlink>
                    </li>
                )
            }
            </ul>
            {
                <ElectricalSeriesSection
                    fileName={fileName}
                    nwbUrl={nwbUrl}
                />
            }
            {
                spikeSortingJob && (
                    <SpikeSortingOutputSection
                        fileName={fileName}
                        spikeSortingJob={spikeSortingJob}
                    />
                )
            }
            <div>&nbsp;</div>
            <hr />
            <ModalWindow
                visible={loadNwbInPythonWindowVisible}
                onClose={closeLoadNwbInPythonWindow}
            >
                {project && <LoadNwbInPythonWindow
                    onClose={closeLoadNwbInPythonWindow}
                    project={project}
                    fileName={fileName}
                />}
            </ModalWindow>
        </div>
    )
}

export const getAuthorizationHeaderForUrl = (url?: string) => {
    if (!url) return ''
    let key = ''
    if (url.startsWith('https://api-staging.dandiarchive.org/')) {
      key = localStorage.getItem('dandiStagingApiKey') || ''
    }
    else if (url.startsWith('https://api.dandiarchive.org/')) {
      key = localStorage.getItem('dandiApiKey') || ''
    }
    if (key) return 'token ' + key
    else return ''
}

const getResolvedUrl = async (url: string) => {
    if (isDandiAssetUrl(url)) {
        const authorizationHeader = getAuthorizationHeaderForUrl(url)
        const headers = authorizationHeader ? {Authorization: authorizationHeader} : undefined
        const redirectUrl = await getRedirectUrl(url, headers)
        if (redirectUrl) {
            return redirectUrl
        }
    }
    return url
}

const headRequest = async (url: string, headers?: any) => {
    // Cannot use HEAD, because it is not allowed by CORS on DANDI AWS bucket
    // let headResponse
    // try {
    //     headResponse = await fetch(url, {method: 'HEAD'})
    //     if (headResponse.status !== 200) {
    //         return undefined
    //     }
    // }
    // catch(err: any) {
    //     console.warn(`Unable to HEAD ${url}: ${err.message}`)
    //     return undefined
    // }
    // return headResponse

    // Instead, use aborted GET.
    const controller = new AbortController();
    const signal = controller.signal;
    const response = await fetch(url, {
        signal,
        headers
    })
    controller.abort();
    return response
}

const getRedirectUrl = async (url: string, headers: any) => {
    // This is tricky. Normally we would do a HEAD request with a redirect: 'manual' option.
    // and then look at the Location response header.
    // However, we run into mysterious cors problems
    // So instead, we do a HEAD request with no redirect option, and then look at the response.url
    const response = await headRequest(url, headers)
    if (response.url) return response.url
  
    // if (response.type === 'opaqueredirect' || (response.status >= 300 && response.status < 400)) {
    //     return response.headers.get('Location')
    // }

    return null // No redirect
  }

const isDandiAssetUrl = (url: string) => {
    if (url.startsWith('https://api-staging.dandiarchive.org/api/')) {
      return true
    }
    if (url.startsWith('https://api.dandiarchive.org/api/')) {
      return true
    }
}

const tryGetGroup = async (nwbFile: RemoteH5File | undefined, path: string) => {
    if (!nwbFile) return undefined
    if (!path) return
    try {
        return await nwbFile.getGroup(path)
    }
    catch(err: any) {
        return undefined
    }
}

export default NwbFileView