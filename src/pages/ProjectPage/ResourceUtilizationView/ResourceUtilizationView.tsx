import { FunctionComponent, useCallback, useEffect, useMemo, useState } from "react"
import { DendroJob } from "../../../types/dendro-types"
import LogPlot from "./LogPlot"
import Hyperlink from "../../../components/Hyperlink"

type ResourceUtilizationViewProps = {
    job: DendroJob
}

type ResourceUtilizationLog = ResourceUtilizationLogLine[]

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
    const [refreshCode, setRefreshCode] = useState(0)
    const refreshResourceUtilizationLog = useCallback(() => {
        setRefreshCode(rc => rc + 1)
    }, [])

    useEffect(() => {
        let canceled = false
        ;(async () => {
            setResourceUtilizationLogText(undefined)
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
    }, [job, refreshCode])

    const resourceUtilizationLog: ResourceUtilizationLog = useMemo(() => {
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

    return {resourceUtilizationLog, refreshResourceUtilizationLog}
}

const ResourceUtilizationView: FunctionComponent<ResourceUtilizationViewProps> = ({job}) => {
    const {resourceUtilizationLog, refreshResourceUtilizationLog} = useResourceUtilizationLog(job)
    const referenceTime = resourceUtilizationLog && resourceUtilizationLog.length > 0 ? resourceUtilizationLog[0].timestamp : 0

    const handleDownloadCsv = useCallback(() => {
        const headerLine = "timestamp,cpu_percent,memory_used,memory_total,network_sent,network_received,disk_read,disk_write"
        const lines = resourceUtilizationLog.map(l => {
            const cpuPercent = l.cpu.percent
            const memoryUsed = l.virtual_memory.used / 1024 / 1024 / 1024
            const memoryTotal = l.virtual_memory.total / 1024 / 1024 / 1024
            const networkSent = (l.net_io_counters?.bytes_sent || 0) / 1024 / 1024 / 1024
            const networkReceived = (l.net_io_counters?.bytes_recv || 0) / 1024 / 1024 / 1024
            const diskRead = (l.disk_io_counters?.read_bytes || 0) / 1024 / 1024 / 1024
            const diskWrite = (l.disk_io_counters?.write_bytes || 0) / 1024 / 1024 / 1024
            return `${l.timestamp},${cpuPercent},${memoryUsed},${memoryTotal},${networkSent},${networkReceived},${diskRead},${diskWrite}`
        })
        const csv = lines.join("\n")
        const csv2 = headerLine + "\n" + csv
        const blob = new Blob([csv2], {type: 'text/csv'})
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `resource_utilization_${job.jobId}.csv`
        a.click()
    }, [resourceUtilizationLog, job])

    const handleDownloadJsonl = useCallback(() => {
        const lines = resourceUtilizationLog.map(l => JSON.stringify(l))
        const jsonl = lines.join("\n")
        const blob = new Blob([jsonl], {type: 'application/json'})
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `resource_utilization_${job.jobId}.jsonl`
        a.click()
    }, [resourceUtilizationLog, job])

    return (
        <div>
            <div>
                <Hyperlink onClick={refreshResourceUtilizationLog}>Refresh resource utilization for job {job.jobId} ({job.processorName})</Hyperlink>
            </div>
            <hr />
            {/* CPU Percent */}
            <LogPlot
                series={[
                    {
                        label: 'CPU percent',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: l.cpu.percent
                        })),
                        color: 'black'
                    }
                ]}
                referenceTime={referenceTime}
                yAxisLabel="CPU percent"
            />
            {/* Memory */}
            <LogPlot
                series={[
                    {
                        label: 'Memory used',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: l.virtual_memory.used / 1024 / 1024 / 1024
                        })),
                        color: 'red'
                    },
                    {
                        label: 'Total memory',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: l.virtual_memory.total / 1024 / 1024 / 1024
                        })),
                        color: 'black'
                    }
                ]}
                referenceTime={referenceTime}
                yAxisLabel="Memory (GB)"
            />
            {/* GPU */}
            <LogPlot
                series={[
                    {
                        label: 'GPU load',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: l.gpu ? l.gpu.loads.reduce((a, b) => a + b, 0) : 0
                        })),
                        color: 'magenta'
                    }
                ]}
                referenceTime={referenceTime}
                yAxisLabel="GPU load"
            />
            {/* Network IO */}
            <LogPlot
                series={[
                    {
                        label: 'Network sent',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: (l.net_io_counters?.bytes_sent || 0) / 1024 / 1024 / 1024
                        })),
                        color: 'blue'
                    },
                    {
                        label: 'Network received',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: (l.net_io_counters?.bytes_recv || 0) / 1024 / 1024 / 1024
                        })),
                        color: 'darkgreen'
                    }
                ]}
                referenceTime={referenceTime}
                yAxisLabel="Network IO (GB)"
            />
            {/* Disk IO */}
            <LogPlot
                series={[
                    {
                        label: 'Disk read',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: (l.disk_io_counters?.read_bytes || 0) / 1024 / 1024 / 1024
                        })),
                        color: 'darkgreen'
                    },
                    {
                        label: 'Disk write',
                        data: resourceUtilizationLog.map(l => ({
                            x: l.timestamp,
                            y: (l.disk_io_counters?.write_bytes || 0) / 1024 / 1024 / 1024
                        })),
                        color: 'blue'
                    }
                ]}
                referenceTime={referenceTime}
                yAxisLabel="Disk IO (GB)"
            />
            <hr />
            <button onClick={handleDownloadCsv}>Download .csv</button>
            &nbsp;
            <button onClick={handleDownloadJsonl}>Download .jsonl</button>
        </div>
    )
}


export default ResourceUtilizationView