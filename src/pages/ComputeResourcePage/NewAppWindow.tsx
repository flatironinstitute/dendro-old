import { FunctionComponent, useEffect, useMemo, useState } from "react"
import { App } from "../../dbInterface/dbInterface"
import { ComputeResourceAwsBatchOpts, ComputeResourceSlurmOpts, DendroComputeResource } from "../../types/dendro-types"

type Props = {
    computeResource: DendroComputeResource
    onNewApp: (name: string, specUri: string, awsBatch?: ComputeResourceAwsBatchOpts, slurm?: ComputeResourceSlurmOpts) => void
    appBeingEdited?: App
}

const NewAppWindow: FunctionComponent<Props> = ({computeResource, onNewApp, appBeingEdited}) => {
    const [newAppName, setNewAppName] = useState('')
    const [newSpecUri, setNewSpecUri] = useState('')
    const [newAwsBatchOpts, setNewAwsBatchOpts] = useState<ComputeResourceAwsBatchOpts | undefined>(undefined)
    const [newSlurmOpts, setNewSlurmOpts] = useState<ComputeResourceSlurmOpts | undefined>(undefined)

    const [newAwsBatchOptsValid, setNewAwsBatchOptsValid] = useState(false)
    const [newSlurmOptsValid, setNewSlurmOptsValid] = useState(false)

    useEffect(() => {
        if (!appBeingEdited) return
        setNewAppName(appBeingEdited.name)
        setNewSpecUri(appBeingEdited.specUri || '')
        if ((appBeingEdited.awsBatch) && (appBeingEdited.awsBatch.useAwsBatch)) {
            setNewAwsBatchOpts(appBeingEdited.awsBatch)
        }
        else {
            setNewAwsBatchOpts(undefined)
        }
        setNewSlurmOpts(appBeingEdited.slurm)
    }, [appBeingEdited])
    
    const isValidAppName = useMemo(() => ((appName: string) => {
        if (!appName) return false
        if (!appBeingEdited) {
            if (computeResource.apps.find(a => a.name === appName)) return false
        }
        return true
    }), [computeResource, appBeingEdited])

    const isValid = useMemo(() => {
        if (!isValidAppName(newAppName)) return false
        if (!isValidSpecUri(newSpecUri)) return false
        if (!newAwsBatchOptsValid) return false
        if (!newSlurmOptsValid) return false
        if (newAwsBatchOpts && newSlurmOpts) return false
        return true
    }, [newAppName, newSpecUri, newAwsBatchOpts, newSlurmOpts, isValidAppName, newAwsBatchOptsValid, newSlurmOptsValid])

    return (
        <div style={{fontSize: 11}}>
            <h3>
                {
                    appBeingEdited ? (
                        <span>Edit app</span>
                    ) : (
                        <span>Add new app</span>
                    )
                }
            </h3>
            <hr />
            {/* Input field for the app name */}
            <div>
                <table>
                    <tbody>
                        <tr>
                            <td>App name</td>
                            <td>
                                {
                                    !appBeingEdited ? (
                                        <input type="text" id="new-app-name" value={newAppName} onChange={e => setNewAppName(e.target.value)} />
                                    ) : (
                                        <span>{newAppName}</span>
                                    )
                                }          
                                {/* Indicator on whether the app name is valid */}
                                &nbsp;&nbsp;
                                {
                                    isValidAppName(newAppName) ? (
                                        <span style={{color: 'green'}}>
                                            {/* Checkmark character */}
                                            &#10004;
                                        </span>
                                    ) : (
                                        <span style={{color: 'red'}}>
                                            {/* Cross character */}
                                            &#10008;
                                        </span>
                                    )
                                }
                            </td>
                        </tr>
                        <tr>
                            <td>Spec URI</td>
                            <td>
                                <input type="text" id="new-spec-uri" value={newSpecUri} onChange={e => setNewSpecUri(e.target.value)} />                
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <br />
            <hr />
            <EditAwsBatchOpts
                value={newAwsBatchOpts}
                onChange={setNewAwsBatchOpts}
                setValid={setNewAwsBatchOptsValid}
            />
            <br />
            <hr />
            <EditSlurmOpts
                value={newSlurmOpts}
                onChange={setNewSlurmOpts}
                setValid={setNewSlurmOptsValid}
            />
            <br />
            <hr />
            {/* Indicator on whether the app is valid */}
            {
                isValid ? (
                    <span style={{color: 'green'}}>
                        {/* Checkmark character */}
                        &#10004;
                    </span>
                ) : (
                    <span style={{color: 'red'}}>
                        {/* Cross character */}
                        &#10008;
                    </span>
                )
            }
            <hr />
            <p style={{fontWeight: 'bold'}}>
                Important: for any changes to take effect, you must reload this page after saving the changes.
            </p>
            <div>&nbsp;</div>
            {/* Button to create the app */}
            <button disabled={!isValid} onClick={() => onNewApp(newAppName, newSpecUri, newAwsBatchOpts, newSlurmOpts)}>
                {
                    !appBeingEdited ? (
                        <span>Add new app</span>
                    ) : (
                        <span>Save changes</span>
                    )
                }
            </button>
        </div>
    )
}

const isValidSpecUri = (specUri: string) => {
    if (!specUri) return false
    if (!specUri.startsWith('http')) return false
    return true
}

type EditAwsBatchOptsProps = {
    value: ComputeResourceAwsBatchOpts | undefined
    onChange: (value: ComputeResourceAwsBatchOpts | undefined) => void
    setValid: (valid: boolean) => void
}

const EditAwsBatchOpts: FunctionComponent<EditAwsBatchOptsProps> = ({value, onChange, setValid}) => {
    const [internalUseAwsBatch, setInternalUseAwsBatch] = useState(false)

    useEffect(() => {
        if (!value) {
            setInternalUseAwsBatch(false)
            return
        }
        setInternalUseAwsBatch(!!value.useAwsBatch)
    }, [value])

    useEffect(() => {
        // if (!internalJobQueue && !internalJobDefinition) {
        //     onChange(undefined)
        //     setValid(true)
        //     return
        // }
        // if (!internalJobQueue || !internalJobDefinition) {
        //     setValid(false)
        //     return
        // }
        // onChange({
        //     jobQueue: internalJobQueue,
        //     jobDefinition: internalJobDefinition
        // })
        onChange({
            useAwsBatch: internalUseAwsBatch
        })
        setValid(true)
    }, [setValid, onChange, internalUseAwsBatch])

    return (
        <div>
            <h4>AWS Batch</h4>
            <div>
                <table>
                    <tbody>
                        {/* <tr>
                            <td>Job queue</td>
                            <td>
                                <input type="text" id="new-aws-batch-job-queue" value={internalJobQueue} onChange={e => setInternalJobQueue(e.target.value)} />                
                            </td>
                        </tr>
                        <tr>
                            <td>Job definition</td>
                            <td>
                                <input type="text" id="new-aws-batch-job-definition" value={internalJobDefinition} onChange={e => setInternalJobDefinition(e.target.value)} />
                            </td>
                        </tr> */}
                        <tr>
                            <td>Use AWS Batch</td>
                            <td>
                                <input type="checkbox" id="new-aws-batch-use-aws-batch" checked={internalUseAwsBatch} onChange={e => setInternalUseAwsBatch(e.target.checked)} />
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    )
}

type EditSlurmOptsProps = {
    value: ComputeResourceSlurmOpts | undefined
    onChange: (value: ComputeResourceSlurmOpts | undefined) => void
    setValid: (valid: boolean) => void
}

const EditSlurmOpts: FunctionComponent<EditSlurmOptsProps> = ({value, onChange, setValid}) => {
    const [internalCpusPerTask, setInternalCpusPerTask] = useState('')
    const [internalPartition, setInternalPartition] = useState('')
    const [internalTime, setInternalTime] = useState('')
    const [internalOtherOpts, setInternalOtherOpts] = useState('')

    useEffect(() => {
        if (!value) {
            setInternalCpusPerTask('')
            setInternalPartition('')
            setInternalTime('')
            setInternalOtherOpts('')
            return
        }
        setInternalCpusPerTask(value.cpusPerTask !== undefined ? value.cpusPerTask + '' : '')
        setInternalPartition(value.partition || '')
        setInternalTime(value.time || '')
        setInternalOtherOpts(value.otherOpts || '')
    }, [value])

    useEffect(() => {
        if (!internalCpusPerTask && !internalPartition && !internalTime && !internalOtherOpts) {
            onChange(undefined)
            setValid(true)
            return
        }
        if ((internalCpusPerTask) && (!isValidInteger(internalCpusPerTask))) {
            setValid(false)
            return
        }
        onChange({
            cpusPerTask: internalCpusPerTask ? parseInt(internalCpusPerTask) : undefined,
            partition: internalPartition || undefined,
            time: internalTime || undefined,
            otherOpts: internalOtherOpts || undefined
        })
        setValid(true)
    }, [internalCpusPerTask, internalPartition, internalTime, internalOtherOpts, onChange, setValid])

    return (
        <div>
            <h4>Slurm</h4>
            <table>
                <tbody>
                    <tr>
                        <td>CPUs per task</td>
                        <td>
                            <input type="text" id="new-slurm-cpus-per-task" value={internalCpusPerTask} onChange={e => setInternalCpusPerTask(e.target.value)} />
                        </td>
                    </tr>
                    <tr>
                        <td>Partition</td>
                        <td>
                            <input type="text" id="new-slurm-partition" value={internalPartition} onChange={e => setInternalPartition(e.target.value)} />
                        </td>
                    </tr>
                    <tr>
                        <td>Time</td>
                        <td>
                            <input type="text" id="new-slurm-time" value={internalTime} onChange={e => setInternalTime(e.target.value)} />
                        </td>
                    </tr>
                    <tr>
                        <td>Other options</td>
                        <td>
                            <input type="text" id="new-slurm-other-opts" value={internalOtherOpts} onChange={e => setInternalOtherOpts(e.target.value)} />
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    )
}

const isValidInteger = (value: string) => {
    const regex = /^\d+$/
    return value.match(regex)
}

export default NewAppWindow