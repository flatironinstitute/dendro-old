import { faCaretDown, faCaretRight } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { FunctionComponent, useCallback, useEffect, useMemo, useReducer } from "react";
import Hyperlink from "../../../components/Hyperlink";
import ComputeResourceNameDisplay from "../../../ComputeResourceNameDisplay";
import { timeAgoString } from "../../../timeStrings";
import { ProtocaasJob } from "../../../types/protocaas-types";
import UserIdComponent from "../../../UserIdComponent";
import { Checkbox, selectedStringsReducer } from "../FileBrowser/FileBrowser2";
import JobsTableMenuBar from "./JobsTableMenuBar";

type Props = {
    width: number
    height: number
    fileName: string
    jobs: ProtocaasJob[] | undefined
    onJobClicked: (jobId: string) => void
    createJobEnabled?: boolean
    createJobTitle?: string
}

const menuBarHeight = 30
const hPadding = 20
const vPadding = 5

type RowItem = {
    type: 'job'
    job: ProtocaasJob
    timestampCreated: number
} | {
    type: 'batch'
    batchId: string
    timestampCreated: number
    status: string
    role: string
}

const JobsTable: FunctionComponent<Props> = ({ width, height, fileName, jobs, onJobClicked, createJobEnabled, createJobTitle }) => {
    const sortedJobs = useMemo(() => {
        if (!jobs) return []
        return [...jobs].sort((a, b) => (b.timestampCreated - a.timestampCreated))
    }, [jobs])

    const [selectedJobIds, selectedJobIdsDispatch] = useReducer(selectedStringsReducer, new Set<string>())
    const [expandedBatchIds, expandedBatchIdsDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const colWidth = 15

    const rowItems: RowItem[] = useMemo(() => {
        const allBatchIds: string[] = []
        for (const jj of sortedJobs) {
            if (jj.batchId && !allBatchIds.includes(jj.batchId)) {
                allBatchIds.push(jj.batchId)
            }
        }
        const batchRowItems: RowItem[] = []
        for (const batchId of allBatchIds) {
            const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
            if (batchJobs.length === 0) {
                throw Error('should not happen')
            }
            const timestampCreated = computeMin(batchJobs.map(jj => jj.timestampCreated))
            const statuses = batchJobs.map(jj => jj.status)
            let status = 'pending'
            // all statuses are completed
            if (statuses.every(s => s === 'completed')) {
                status = 'completed'
            }
            // all statuses are pending
            else if (statuses.every(s => s === 'pending')) {
                status = 'pending'
            }
            // all statuses are pending or queued
            else if (statuses.every(s => s === 'pending' || s === 'queued')) {
                status = 'queued'
            }
            // all status are pending or queued or starting
            else if (statuses.every(s => s === 'pending' || s === 'queued' || s === 'starting')) {
                status = 'starting'
            }
            // some status is failed
            else if (statuses.some(s => s === 'failed')) {
                status = 'failed'
            }
            // some status is running
            else if (statuses.some(s => s === 'running')) {
                status = 'running'
            }
            // some status is queued
            else if (statuses.some(s => s === 'pending')) {
                status = 'pending'
            }
            else {
                status = 'unknown' // should not happen
            }
            const batchJobRoles = batchJobs.map(jj => {
                if (jj.inputFiles.map(f => f.fileName).includes(fileName)) {
                    return 'input'
                }
                else if (jj.outputFiles.map(f => f.fileName).includes(fileName)) {
                    return 'output'
                }
                else {
                    return ''
                }
            })
            const role = batchJobRoles.includes('input') ? 'input' : batchJobRoles.includes('output') ? 'output' : ''


            batchRowItems.push({
                type: 'batch',
                batchId,
                timestampCreated,
                status,
                role
            })
        }
        const isolatedJobRowItems: RowItem[] = []
        for (const jj of sortedJobs) {
            if (!jj.batchId) {
                isolatedJobRowItems.push({
                    type: 'job',
                    job: jj,
                    timestampCreated: jj.timestampCreated
                })
            }
        }
        // sort backwards by timestampCreated
        isolatedJobRowItems.sort((a, b) => (b.timestampCreated - a.timestampCreated))
        const allTopLevelRowItems: RowItem[] = [...batchRowItems, ...isolatedJobRowItems]
        const allRowItems: RowItem[] = []
        for (const rowItem of allTopLevelRowItems) {
            allRowItems.push(rowItem)
            if (rowItem.type === 'batch') {
                const batchJobs = sortedJobs.filter(jj => jj.batchId === rowItem.batchId)
                for (const jj of batchJobs) {
                    allRowItems.push({
                        type: 'job',
                        job: jj,
                        timestampCreated: jj.timestampCreated
                    })
                }
            }
        }
        return allRowItems
    }, [sortedJobs, fileName])

    useEffect(() => {
        // default expanded batches
        const batchIdsToExpand: string[] = []
        for (const rowItem of rowItems) {
            if (rowItem.type === 'batch') {
                const jj = sortedJobs.filter(jj => jj.batchId === rowItem.batchId)
                if (jj.length <= 2) {
                    batchIdsToExpand.push(rowItem.batchId)
                }
            }
        }
        expandedBatchIdsDispatch({type: 'set-multiple', paths: batchIdsToExpand, selected: true})
    }, [rowItems, sortedJobs])

    const getBatchCheckedStatus = useMemo(() => ((batchId: string) => {
        const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
        const selectedBatchJobs = batchJobs.filter(jj => selectedJobIds.has(jj.jobId))
        if (selectedBatchJobs.length === 0)  return false
        if (selectedBatchJobs.length === batchJobs.length) return true
        return null // indeterminate
    }), [sortedJobs, selectedJobIds])

    const getProcessorNamesForBatch = useMemo(() => ((batchId: string) => {
        const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
        const processorNames = new Set<string>()
        for (const jj of batchJobs) {
            processorNames.add(jj.processorName)
        }
        return Array.from(processorNames).sort()
    }), [sortedJobs])

    const getUserIdForBatch = useMemo(() => ((batchId: string) => {
        const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
        const userIds = new Set<string>()
        for (const jj of batchJobs) {
            userIds.add(jj.userId)
        }
        if (userIds.size === 0) {
            return ''
        }
        return Array.from(userIds)[0]
    }), [sortedJobs])

    const getComputeResourceIdForBatch = useMemo(() => ((batchId: string) => {
        const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
        const computeResourceIds = new Set<string>()
        for (const jj of batchJobs) {
            computeResourceIds.add(jj.computeResourceId)
        }
        if (computeResourceIds.size === 0) {
            return ''
        }
        return Array.from(computeResourceIds)[0]
    }), [sortedJobs])

    const toggleBatchSelection = useCallback((batchId: string) => {
        const batchJobs = sortedJobs.filter(jj => jj.batchId === batchId)
        const selectedBatchJobs = batchJobs.filter(jj => selectedJobIds.has(jj.jobId))
        if (selectedBatchJobs.length === batchJobs.length) {
            selectedJobIdsDispatch({type: 'set-multiple', paths: batchJobs.map(jj => jj.jobId), selected: false})
        }
        else {
            selectedJobIdsDispatch({type: 'set-multiple', paths: batchJobs.map(jj => jj.jobId), selected: true})
        }
    }, [sortedJobs, selectedJobIds])

    return (
        <div style={{position: 'relative', width, height}}>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: menuBarHeight - vPadding * 2, paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <JobsTableMenuBar
                    width={width - hPadding * 2}
                    height={menuBarHeight - vPadding * 2}
                    selectedJobIds={Array.from(selectedJobIds)}
                    onResetSelection={() => selectedJobIdsDispatch({type: 'set', values: new Set<string>()})}
                    createJobEnabled={createJobEnabled}
                    createJobTitle={createJobTitle}
                />
            </div>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: height - menuBarHeight - vPadding * 2, top: menuBarHeight, overflowY: 'scroll', paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <table className="scientific-table" style={{fontSize: 12}}>
                    <thead>
                        <tr>
                            <th style={{width: colWidth}} />
                            <th style={{width: colWidth}} />
                            <th>Job</th>
                            <th>Processor</th>
                            <th>Status</th>
                            <th>User</th>
                            <th>Created</th>
                            <th>Compute</th>
                            <th>Role</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            rowItems.map((rowItem) => {
                                if (rowItem.type === 'job') {
                                    const jj = rowItem.job
                                    if (jj.batchId && !expandedBatchIds.has(jj.batchId)) {
                                        return null
                                    }
                                    let role = ''
                                    if (jj.inputFiles.map(f => f.fileName).includes(fileName)) {
                                        role = 'input'
                                    }
                                    else if (jj.outputFiles.map(f => f.fileName).includes(fileName)) {
                                        role = 'output'
                                    }
                                    return (
                                        <tr key={jj.jobId}>
                                            <td style={{width: colWidth}}>
                                                <Checkbox checked={selectedJobIds.has(jj.jobId)} onClick={() => selectedJobIdsDispatch({type: 'toggle', value: jj.jobId})} />
                                            </td>
                                            <td style={{width: colWidth}}>
                                                <JobIcon status={jj.status} />
                                            </td>
                                            <td>
                                                <Hyperlink onClick={() => onJobClicked(jj.jobId)}>
                                                    {
                                                        jj.batchId ? (
                                                            <span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span> // indent
                                                        ) : null
                                                    }{jj.jobId}
                                                </Hyperlink>
                                            </td>
                                            <td>{jj.processorName}</td>
                                            <td>{
                                                jj.status !== 'failed' ? (
                                                    <span>{jj.status}</span>
                                                ) : (
                                                    <Hyperlink onClick={() => onJobClicked(jj.jobId)}>
                                                        <span style={{color: 'red'}}>{jj.status}: {jj.error}</span>
                                                    </Hyperlink>
                                                )
                                            }</td>
                                            <td>
                                                <UserIdComponent userId={jj.userId} />
                                            </td>
                                            <td>{timeAgoString(jj.timestampCreated)}</td>
                                            <td><ComputeResourceNameDisplay computeResourceId={jj.computeResourceId} link={true} /></td>
                                            <td>{role}</td>
                                        </tr>
                                    )
                                }
                                else if (rowItem.type === 'batch') {
                                    return (
                                        <tr key={`batch:${rowItem.batchId}`} style={{fontWeight: 'bold'}}>
                                            <td style={{width: colWidth}}>
                                                <Checkbox checked={getBatchCheckedStatus(rowItem.batchId)} onClick={() => toggleBatchSelection(rowItem.batchId)} />
                                            </td>
                                            <td style={{width: colWidth}}>
                                                <JobIcon status={rowItem.status} />
                                            </td>
                                            <td>
                                                <span style={{cursor: 'pointer'}} onClick={() => expandedBatchIdsDispatch({type: 'toggle', value: rowItem.batchId})}>
                                                    {
                                                        expandedBatchIds.has(rowItem.batchId) ? (
                                                            <FontAwesomeIcon icon={faCaretDown} style={{color: 'gray', fontSize: 16}} />
                                                        ) : (
                                                            <FontAwesomeIcon icon={faCaretRight} style={{color: 'gray', fontSize: 16}} />
                                                        )
                                                    }
                                                    &nbsp;&nbsp;Batch {rowItem.batchId}
                                                </span>
                                            </td>
                                            <td>{getProcessorNamesForBatch(rowItem.batchId).join(', ')}</td>
                                            <td>
                                                {rowItem.status}
                                            </td>
                                            <td>
                                                <UserIdComponent userId={getUserIdForBatch(rowItem.batchId)} />
                                            </td>
                                            <td>{timeAgoString(rowItem.timestampCreated)}</td>
                                            <td><ComputeResourceNameDisplay computeResourceId={getComputeResourceIdForBatch(rowItem.batchId)} link={true} /></td>
                                            <td>
                                                {rowItem.role}
                                            </td>
                                        </tr>
                                    )
                                }
                                else {
                                    throw Error('should not happen')
                                }
                            })
                        }
                    </tbody>
                </table>
            </div>
        </div>
    )
}

const JobIcon: FunctionComponent<{status: string}> = ({status}) => {
    // 🔴🟠🟡🟢🔵🟣⚫️⚪️🟤
    switch (status) {
        case 'pending':
            return <span title="Job is pending">⚪️</span>
        case 'queued':
            return <span title="Job is queued">🟣</span>
        case 'running':
            return <span title="Job is running">🟠</span>
        case 'completed':
            return <span title="Job completed">🟢</span>
        case 'failed':
            return <span title="Job failed">🔴</span>
        default:
            return <span title="Job has unknown status">⚫️</span>
    }
}

const computeMin = (values: number[]) => {
    let min = Infinity
    for (const value of values) {
        if (value < min) {
            min = value
        }
    }
    return min
}

export default JobsTable