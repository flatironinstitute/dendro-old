import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { DendroJob } from "../../../types/dendro-types"

type ResourceUtilizationViewProps = {
    job: DendroJob
}

type ResourceUtilizationLogLine = {
    timestamp: number,
    cpu: {
        percent: number
    },
    virtual_memory: {
        total: number,
        available: number,
        percent: number,
        used: number,
        free: number,
        active: number,
        inactive: number,
        buffers: number,
        cached: number,
        shared: number,
        slab: number
    },
    disk_io_counters: {
        read_count: number,
        write_count: number,
        read_bytes: number,
        write_bytes: number,
        read_time: number,
        write_time: number
    } | null,
    net_io_counters: {
        bytes_sent: number,
        bytes_recv: number,
        packets_sent: number,
        packets_recv: number,
        errin: number,
        errout: number,
        dropin: number,
        dropout: number
    },
    gpu: {
        loads: number[]
    } | null
}

const useResourceUtilizationLog = (job: DendroJob) => {
    const [resourceUtilizationLogText, setResourceUtilizationLogText] = useState<string | undefined>()

    useEffect(() => {
        let canceled = false
        ;(async () => {
            if (job?.resourceUtilizationLogUrl) {
                // fetch resource utilization log
                const resp = await fetch(job.resourceUtilizationLogUrl)
                if (resp.ok) {
                    const text = await resp.text()
                    if (canceled) return
                    setResourceUtilizationLogText(text)
                }
            }
        })()
        return () => {
            canceled = true
        }
    }, [job])

    const resourceUtilizationLog = useMemo(() => {
        const lines = resourceUtilizationLogText?.split("\n") || []
        const ret: ResourceUtilizationLogLine[] = []
        for (const line of lines) {
            try {
                ret.push(JSON.parse(line))
            }
            catch (e) {
                // ignore
            }
        }
        return ret
    }, [resourceUtilizationLogText])

    return {resourceUtilizationLog}
}

const ResourceUtilizationView: FunctionComponent<ResourceUtilizationViewProps> = ({job}) => {
    const {resourceUtilizationLog} = useResourceUtilizationLog(job)

    return (
        <div>
            <table className="scientific-table">
                <thead>
                    <tr>
                        <th>Timestamp</th>
                        <th>CPU</th>
                        <th>Memory</th>
                        <th>Disk</th>
                        <th>Network</th>
                        <th>GPU</th>
                    </tr>
                </thead>
                <tbody>
                    {
                        resourceUtilizationLog.map((line, i) => (
                            <tr key={i}>
                                <td>{line.timestamp}</td>
                                <td>{line.cpu.percent.toFixed(2)}%</td>
                                <td>{(line.virtual_memory.used / 1024 / 1024).toFixed(2)} MB</td>
                                <td>{line.disk_io_counters?.read_bytes} / {line.disk_io_counters?.write_bytes}</td>
                                <td>{line.net_io_counters.bytes_sent} / {line.net_io_counters.bytes_recv}</td>
                                <td>{line.gpu?.loads.map(l => l.toFixed(2)).join(', ')}</td>
                            </tr>
                        ))
                    }
                </tbody>
            </table>
        </div>
    )
}

export default ResourceUtilizationView