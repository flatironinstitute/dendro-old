import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react";
import { useModalWindow } from "@hodj/modal-window"
import { RemoteH5File, getRemoteH5File } from "../../../RemoteH5File/RemoteH5File";
import { Hyperlink } from "@hodj/misc";
import ModalWindow from "@hodj/modal-window";
import { Splitter } from "@hodj/splitter";
import JobsWindow from "../JobsWindow/JobsWindow";
import LoadNwbInPythonWindow from "../LoadNwbInPythonWindow/LoadNwbInPythonWindow";
import { useProject } from "../ProjectPageContext";
import SpikeSortingOutputSection from "./SpikeSortingOutputSection/SpikeSortingOutputSection";
import { DendroJob } from "../../../types/dendro-types";
import { AssetResponse } from "../../DandiBrowser/types";
import { getDandiApiHeaders } from "../../DandiBrowser/DandiBrowser";
import ElectricalSeriesSection from "./ElectricalSeriesSection/ElectricalSeriesSection";


type Props = {
    fileName: string
    width: number
    height: number
}

const NwbFileEditor: FunctionComponent<Props> = ({fileName, width, height}) => {
    return (
        <Splitter
            width={width}
            height={height}
            initialPosition={height * 2 / 3}
            direction="vertical"
        >
            <NwbFileEditorChild
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

const NwbFileEditorChild: FunctionComponent<Props> = ({fileName, width, height}) => {
    const [assetResponse, setAssetResponse] = useState<AssetResponse | null>(null)

    const {project, jobs, filesIncludingPending, openTab} = useProject()

    const nbFile = useMemo(() => {
        if (!filesIncludingPending) return undefined
        return filesIncludingPending.find(f => (f.fileName === fileName))
    }, [filesIncludingPending, fileName])

    const metadata = nbFile?.metadata
    const cc = nbFile?.content || ''
    const nwbUrl = cc.startsWith('url:') ? cc.slice('url:'.length) : ''
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
        const u = `https://flatironinstitute.github.io/neurosift/?p=/nwb&url=${nwbUrl}`
        window.open(u, '_blank')
    }, [nwbUrl])

    useEffect(() => {
        if (!dandisetId) return
        if (!dandiAssetId) return
        ; (async () => {
            const headers = getDandiApiHeaders(dandiStaging)
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
                        <td>{nwbUrl}</td>
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
                        dandisetId && (
                            <tr>
                                <td>Dandiset:</td>
                                <td>
                                    {dandisetId && <a href={`https://${stagingStr2}dandiarchive.org/dandiset/${dandisetId}/${dandisetVersion}`} target="_blank" rel="noreferrer">
                                        {dandisetId} ({dandisetVersion || ''})
                                    </a>}
                                </td>
                            </tr>
                        )
                    }
                    {
                        assetResponse?.path && (
                            <tr>
                                <td>DANDI Path:</td>
                                <td>
                                    {assetResponse?.path || ''}
                                </td>
                            </tr>
                        )
                    }
                    <tr>
                    </tr>
                </tbody>
            </table>
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

type ElapsedTimeComponentProps = {
    job: DendroJob
}

export const ElapsedTimeComponent: FunctionComponent<ElapsedTimeComponentProps> = ({job}) => {

    // if job.status is 'running', then we want to refresh ever 30 seconds
    const [refreshCode, setRefreshCode] = useState(0)
    const refreshInterval = 30000
    useEffect(() => {
        let canceled = false
        if (['running'].includes(job.status)) {
            const timer = setInterval(() => {
                if (canceled) return
                setRefreshCode(rc => rc + 1)
            }, refreshInterval)
            return () => {
                canceled = true
                clearInterval(timer)
            }
        }
    }, [job.status])

    const truncateToThreeDigits = (x: number) => {
        return Math.floor(x * 1000) / 1000
    }
    if (['completed', 'failed'].includes(job.status)) {
        const elapsed = (job.timestampFinished || 0) - (job.timestampStarted || 0)
        return <span>{truncateToThreeDigits(elapsed)}</span>
    }
    else if (['running'].includes(job.status)) {
        const elapsed = (Date.now() / 1000) - (job.timestampStarted || 0)
        return <span>{Math.floor(elapsed)}</span>
    }
    else {
        return <span></span>
    }
}

export default NwbFileEditor