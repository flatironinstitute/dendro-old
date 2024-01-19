import { Hyperlink } from "@fi-sci/misc";
import { FunctionComponent, useEffect, useMemo, useState } from "react";
import { useProject } from "../ProjectPageContext";
import { DendroJob } from "../../../types/dendro-types";


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

export default FileViewTable