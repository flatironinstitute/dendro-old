import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react";
import Hyperlink from "../../../components/Hyperlink";
import { ProtocaasProcessingJobDefinition, ProtocaasProcessingJobDefinitionAction } from "../../../dbInterface/dbInterface";
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File";
import { ComputeResourceSpecProcessor, ComputeResourceSpecProcessorParameter } from "../../../types/protocaas-types";
import useRoute from "../../../useRoute";
import { useProject } from "../ProjectPageContext";
import { useElectricalSeriesPaths } from "../FileEditor/NwbFileEditor";



type EditJobDefinitionWindowProps = {
    jobDefinition: ProtocaasProcessingJobDefinition | undefined
    jobDefinitionDispatch?: (action: ProtocaasProcessingJobDefinitionAction) => void
    secretParameterNames?: string[]
    processor: ComputeResourceSpecProcessor
    nwbFile?: RemoteH5File
    setValid?: (valid: boolean) => void
    readOnly?: boolean
    show?: 'inputs' | 'outputs' | 'parameters' | 'all' | 'inputs+outputs'
    fileLinks?: boolean
}

type validParametersState = {
    [key: string]: boolean
}

type validParametersAction = {
    type: 'setValid'
    name: string
    valid: boolean
}

const validParametersReducer = (state: validParametersState, action: validParametersAction) => {
    if (action.type === 'setValid') {
        // check if no change
        if (state[action.name] === action.valid) return state
        return {
            ...state,
            [action.name]: action.valid
        }
    }
    else return state
}

const EditJobDefinitionWindow: FunctionComponent<EditJobDefinitionWindowProps> = ({jobDefinition, jobDefinitionDispatch, secretParameterNames, processor, nwbFile, setValid, readOnly, show='all', fileLinks}) => {
    const setParameterValue = useCallback((name: string, value: any) => {
        jobDefinitionDispatch && jobDefinitionDispatch({
            type: 'setInputParameter',
            name,
            value
        })
    }, [jobDefinitionDispatch])

    const [validParameters, validParametersDispatch] = useReducer(validParametersReducer, {})
    const allParametersAreValid = useMemo(() => {
        const allNames: string[] = [...processor.parameters.map(p => p.name), ...processor.inputs.map(i => i.name), ...processor.outputs.map(o => o.name)]
        for (const name of allNames) {
            if (!validParameters[name]) {
                return false
            }
        }
        return true
    }, [processor, validParameters])
    useEffect(() => {
        setValid && setValid(allParametersAreValid)
    }, [allParametersAreValid, setValid])

    const rows = useMemo(() => {
        const ret: any[] = []
        const showInputs = show === 'all' || show === 'inputs' || show === 'inputs+outputs'
        const showOutputs = show === 'all' || show === 'outputs' || show === 'inputs+outputs'
        const showParameters = show === 'all' || show === 'parameters'
        if (showInputs) {
            processor.inputs.forEach(input => {
                ret.push(
                    <InputRow
                        key={input.name}
                        name={input.name}
                        description={input.help}
                        value={jobDefinition?.inputFiles.find(f => (f.name === input.name))?.fileName}
                        setValid={valid => {
                            validParametersDispatch({
                                type: 'setValid',
                                name: input.name,
                                valid
                            })
                        }}
                        fileLinks={fileLinks}
                    />
                )
            })
        }
        if (showOutputs) {
            processor.outputs.forEach(output => {
                ret.push(
                    <OutputRow
                        key={output.name}
                        name={output.name}
                        description={output.help}
                        value={jobDefinition?.outputFiles.find(f => (f.name === output.name))?.fileName}
                        setValid={valid => {
                            validParametersDispatch({
                                type: 'setValid',
                                name: output.name,
                                valid
                            })
                        }}
                        fileLinks={fileLinks}
                    />
                )
            })
        }
        if (showParameters) {
            processor.parameters.forEach(parameter => {
                ret.push(
                    <ParameterRow
                        key={parameter.name}
                        parameter={parameter}
                        value={jobDefinition?.inputParameters.find(f => (f.name === parameter.name))?.value}
                        nwbFile={nwbFile}
                        secret={secretParameterNames?.includes(parameter.name)}
                        setValue={value => {
                            setParameterValue(parameter.name, value)
                        }}
                        setValid={valid => {
                            validParametersDispatch({
                                type: 'setValid',
                                name: parameter.name,
                                valid
                            })
                        }}
                        readOnly={readOnly}
                    />
                )
            })
        }
        return ret
    }, [jobDefinition, processor, nwbFile, setParameterValue, readOnly, show, secretParameterNames, fileLinks])
    return (
        <div>
            <table className="table1">
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    )
}

type InputRowProps = {
    name: string
    description: string
    value?: string
    setValid?: (valid: boolean) => void
    fileLinks?: boolean
}

const InputRow: FunctionComponent<InputRowProps> = ({name, description, value, setValid, fileLinks}) => {
    const {projectId, openTab} = useProject()
    const {setRoute} = useRoute()
    useEffect(() => {
        setValid && setValid(!!value)
    }, [value, setValid])
    const handleOpenFile = useCallback((fileName: string) => {
        openTab(`file:${fileName}`)
        setRoute({
            page: 'project',
            projectId,
            tab: `project-files`
        })
    }, [openTab, setRoute, projectId])
    return (
        <tr>
            <td>{name}</td>
            <td>{
                fileLinks && value ? (
                    <Hyperlink
                        onClick={() => {
                            handleOpenFile(value)
                        }}
                    >{value}</Hyperlink>                
                ) : (
                    value
                )
            }</td>
            <td>{description}</td>
        </tr>
    )
}

type OutputRowProps = {
    name: string
    description: string
    value?: string
    setValid?: (valid: boolean) => void
    fileLinks?: boolean
}

const OutputRow: FunctionComponent<OutputRowProps> = ({name, description, value, setValid, fileLinks}) => {
    const {projectId, openTab} = useProject()
    const {setRoute} = useRoute()
    useEffect(() => {
        setValid && setValid(!!value)
    }, [value, setValid])
    const handleOpenFile = useCallback((fileName: string) => {
        openTab(`file:${fileName}`)
        setRoute({
            page: 'project',
            projectId,
            tab: `project-files`
        })
    }, [openTab, setRoute, projectId])
    return (
        <tr>
            <td>{name}</td>
            <td>{
                fileLinks && value ? (
                    <Hyperlink
                        onClick={() => {
                            handleOpenFile(value)
                        }}
                    >{value}</Hyperlink>                
                ) : (
                    value
                )
            }</td>
            <td>{description}</td>
        </tr>
    )
}

type ParameterRowProps = {
    parameter: ComputeResourceSpecProcessorParameter
    value: any
    nwbFile?: RemoteH5File
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
    readOnly?: boolean
    secret?: boolean
}

const ParameterRow: FunctionComponent<ParameterRowProps> = ({parameter, value, nwbFile, setValue, setValid, readOnly, secret}) => {
    const {type, name, help} = parameter
    const [isValid, setIsValid] = useState<boolean>(false)
    return (
        <tr>
            <td title={`${name} (${type})`}>
                <span
                    style={{color: readOnly || isValid ? 'black' : 'red'}}
                >{name}</span>
            </td>
            <td>
                {
                    readOnly ? (
                        <span>
                            <DisplayParameterValue
                                parameter={parameter}
                                value={value}
                            />
                            {
                                // we don't want to rely on the display to hide the secret
                                // if it is a secret the value should be empty
                                // if that's not the case, it's better that we see it here
                                // so we can know there is an issue with secrets being displayed
                                secret && (
                                    <span style={{color: 'darkgreen'}}> (secret)</span>
                                )
                            }
                        </span>
                    ) : (
                        <EditParameterValue
                            parameter={parameter}
                            value={value}
                            nwbFile={nwbFile}
                            setValue={setValue}
                            setValid={valid => {
                                setIsValid(valid)
                                setValid(valid)
                            }}
                        />
                    )
                }
            </td>
            <td>{help}</td>
        </tr>
    )
}

type EditParameterValueProps = {
    parameter: ComputeResourceSpecProcessorParameter
    value: any
    nwbFile?: RemoteH5File
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
}

const EditParameterValue: FunctionComponent<EditParameterValueProps> = ({parameter, value, nwbFile, setValue, setValid}) => {
    const {type, name} = parameter
    if (name === 'electrical_series_path') {
        return <ElectricalSeriesPathSelector value={value} nwbFile={nwbFile} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'str') {
        setValid(true)
        return <input type="text" value={value || ''} onChange={evt => {setValue(evt.target.value)}} />
    }
    else if (type === 'int') {
        return <IntEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'float') {
        return <FloatEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'bool') {
        setValid(true)
        return <input type="checkbox" checked={value || false} onChange={evt => {setValue(evt.target.checked ? true : false)}} />
    }
    else if (type === 'List[float]') {
        return <FloatListEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else {
        return <div>Unsupported type: {type}</div>
    }
}

type FloatEditProps = {
    value: any
    setValue: (value: number) => void
    setValid: (valid: boolean) => void
}

const FloatEdit: FunctionComponent<FloatEditProps> = ({value, setValue, setValid}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (isFloatType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidFloat(old)) && (parseFloat(old) === value)) return old
                return `${value}`
            })
        }
    }, [value])

    useEffect(() => {
        if (internalValue === undefined) return
        if (stringIsValidFloat(internalValue)) {
            setValue(parseFloat(internalValue))
            setValid(true)
        }
        else {
            setValid(false)
        }
    }, [internalValue, setValue, setValid])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidFloat(internalValue)
    }, [internalValue])

    return (
        <span>
            <input type="text" value={internalValue || ''} onChange={evt => {setInternalValue(evt.target.value)}} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
        </span>
    )
}

const isFloatType = (x: any) => {
    return (typeof(x) === 'number') && (!isNaN(x))
}

function stringIsValidFloat(s: string) {
    const floatRegex = /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/;
    return floatRegex.test(s);
}

type IntEditProps = {
    value: any
    setValue: (value: number) => void
    setValid: (valid: boolean) => void
}

const IntEdit: FunctionComponent<IntEditProps> = ({value, setValue, setValid}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (isIntType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidInt(old)) && (parseInt(old) === value)) return old
                return `${value}`
            })
        }
    }, [value])

    useEffect(() => {
        if (internalValue === undefined) return
        if (stringIsValidInt(internalValue)) {
            setValue(parseInt(internalValue))
            setValid(true)
        }
        else {
            setValid(false)
        }
    }, [internalValue, setValue, setValid])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidInt(internalValue)
    }, [internalValue])

    return (
        <span>
            <input type="text" value={internalValue || ''} onChange={evt => {setInternalValue(evt.target.value)}} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
        </span>
    )
}

const isIntType = (x: any) => {
    return (typeof(x) === 'number') && (!isNaN(x)) && (Math.floor(x) === x)
}

function stringIsValidInt(s: string) {
    const intRegex = /^[-+]?[0-9]+$/;
    return intRegex.test(s);
}

type ElectricalSeriesPathSelectorProps = {
    value?: string
    nwbFile?: RemoteH5File
    setValue: (value: string) => void
    setValid?: (valid: boolean) => void
}

const ElectricalSeriesPathSelector: FunctionComponent<ElectricalSeriesPathSelectorProps> = ({value, nwbFile, setValue, setValid}) => {
    const electricalSeriesPaths = useElectricalSeriesPaths(nwbFile)

    useEffect(() => {
        if (value) return
        if (!electricalSeriesPaths) return
        if (electricalSeriesPaths.length === 0) return
        setValue(electricalSeriesPaths[0])
    }, [value, electricalSeriesPaths, setValue])

    useEffect(() => {
        if (!setValid) return
        if ((electricalSeriesPaths === undefined) || (electricalSeriesPaths.length === 0)) {
            setValid(false)
            return
        }
        setValid(!!value)
    }, [setValid, value, electricalSeriesPaths])

    if (!electricalSeriesPaths) return <div>Loading...</div>
    if (electricalSeriesPaths.length === 0) return <div>No electrical series found.</div>
    return (
        <select value={value} onChange={evt => {setValue(evt.target.value)}}>
            {
                [...electricalSeriesPaths].map(path => (
                    <option key={path} value={path}>{path}</option>
                ))
            }
        </select>
    )
}

type FloatListEditProps = {
    value: any
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
}

const isFloatListType = (x: any) => {
    if (!Array.isArray(x)) return false
    for (let i=0; i<x.length; i++) {
        if (!isFloatType(x[i])) return false
    }
    return true
}

function floatListToString(x: number[]) {
    return x.join(', ')
}

function stringToFloatList(s: string) {
    return s.split(',').map(x => parseFloat(x.trim()))
}

function stringIsValidFloatList(s: string) {
    const floatListRegex = /^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?(,\s*[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?)*$/;
    return floatListRegex.test(s);
}

const FloatListEdit: FunctionComponent<FloatListEditProps> = ({value, setValue, setValid}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (isFloatListType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidFloatList(old)) && (floatListToString(value) === old)) return old
                return floatListToString(value)
            })
        }
    }, [value])

    useEffect(() => {
        if (internalValue === undefined) return
        if (stringIsValidFloatList(internalValue)) {
            setValue(stringToFloatList(internalValue))
            setValid(true)
        }
        else {
            setValid(false)
        }
    }, [internalValue, setValue, setValid])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidFloatList(internalValue)
    }, [internalValue])

    return (
        <span>
            <input type="text" value={internalValue || ''} onChange={evt => {setInternalValue(evt.target.value)}} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
        </span>
    )
}

type DisplayParameterValueProps = {
    parameter: ComputeResourceSpecProcessorParameter
    value: any
}

const DisplayParameterValue: FunctionComponent<DisplayParameterValueProps> = ({parameter, value}) => {
    const {type} = parameter
    if (type === 'str') {
        return <span>{value}</span>
    }
    else if (type === 'int') {
        return <span>{value}</span>
    }
    else if (type === 'float') {
        return <span>{value}</span>
    }
    else if (type === 'bool') {
        return <span>{value ? 'true' : 'false'}</span>
    }
    else if (type === 'List[float]') {
        return <span>{value.join(', ')}</span>
    }
    else {
        return <div>Unsupported type: {type}</div>
    }
}

export default EditJobDefinitionWindow