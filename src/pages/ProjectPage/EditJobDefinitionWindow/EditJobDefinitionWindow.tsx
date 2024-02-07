import { FunctionComponent, useCallback, useEffect, useMemo, useReducer, useState } from "react";
import { Hyperlink } from "@fi-sci/misc";
import { DendroProcessingJobDefinition, DendroProcessingJobDefinitionAction } from "../../../dbInterface/dbInterface";
import { RemoteH5File } from "../../../RemoteH5File/RemoteH5File";
import { ComputeResourceSpecProcessor, ComputeResourceSpecProcessorParameter } from "../../../types/dendro-types";
import useRoute from "../../../useRoute";
import { useProject } from "../ProjectPageContext";
import { useElectricalSeriesPaths, useUnitsPaths } from "../FileView/NwbFileView";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCaretDown, faCaretRight } from "@fortawesome/free-solid-svg-icons";
import { expandedFoldersReducer } from "../FileBrowser/FileBrowser2";


type EditJobDefinitionWindowProps = {
    jobDefinition: DendroProcessingJobDefinition | undefined
    jobDefinitionDispatch?: (action: DendroProcessingJobDefinitionAction) => void
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

type RowNode = {
    type: 'leaf'
    fieldType: 'input' | 'output' | 'parameter'
    isFolder?: boolean
    name: string
    description: string
} | {
    type: 'group'
    name: string
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
        const allNames: string[] = [...processor.parameters.map(p => p.name), ...processor.inputs.map(i => i.name), ...(processor.inputFolders || []).map(i => i.name), ...processor.outputs.map(o => o.name), ...(processor.outputFolders || []).map(o => o.name)]
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

    const nodes: RowNode[] = useMemo(() => {
        const nodes: RowNode[] = []
        const addGroupNodes = (name: string) => {
            const aa = name.split('.')
            if (aa.length > 1) {
                for (let i = 0; i < aa.length - 1; i++) {
                    const group = aa.slice(0, i + 1).join('.')
                    if (!nodes.find(n => (n.type === 'group') && (n.name === group))) {
                        nodes.push({
                            type: 'group',
                            name: group
                        })
                    }
                }
            }
        }
        processor.inputs.forEach(input => {
            addGroupNodes(input.name)
            nodes.push({
                type: 'leaf',
                fieldType: 'input',
                name: input.name,
                description: input.description
            })
        })
        ; (processor.inputFolders || []).forEach(inputFolder => {
            addGroupNodes(inputFolder.name)
            nodes.push({
                type: 'leaf',
                fieldType: 'input',
                isFolder: true,
                name: inputFolder.name,
                description: inputFolder.description
            })
        })
        processor.outputs.forEach(output => {
            addGroupNodes(output.name)
            nodes.push({
                type: 'leaf',
                fieldType: 'output',
                name: output.name,
                description: output.description
            })
        })
        ; (processor.outputFolders || []).forEach(outputFolder => {
            addGroupNodes(outputFolder.name)
            nodes.push({
                type: 'leaf',
                fieldType: 'output',
                isFolder: true,
                name: outputFolder.name,
                description: outputFolder.description
            })
        })
        processor.parameters.forEach(parameter => {
            addGroupNodes(parameter.name)
            nodes.push({
                type: 'leaf',
                fieldType: 'parameter',
                name: parameter.name,
                description: parameter.description
            })
        })
        return nodes
    }, [processor])

    const [expandedGroups, expandedGroupsDispatch] = useReducer(expandedFoldersReducer, new Set<string>())

    useEffect(() => {
        // initialize the expanded groups
        // const numInitialLevelsExpanded = 1
        const numInitialLevelsExpanded = 0
        const groupNames = nodes.filter(n => (n.type === 'group')).map(n => n.name)
        const eg = new Set<string>()
        for (const name of groupNames) {
            const aa = name.split('.')
            if (aa.length <= numInitialLevelsExpanded) {
                eg.add(name)
            }
        }
        expandedGroupsDispatch({
            type: 'set',
            paths: eg
        })
    }, [nodes])

    const rows = useMemo(() => {
        const ret: any[] = []
        const showInputs = show === 'all' || show === 'inputs' || show === 'inputs+outputs'
        const showOutputs = show === 'all' || show === 'outputs' || show === 'inputs+outputs'
        const showParameters = show === 'all' || show === 'parameters'

        nodes.forEach(node => {
            const aa = node.name.split('.')
            let visible = true
            for (let i = 0; i < aa.length - 1; i++) {
                const group = aa.slice(0, i + 1).join('.')
                if (!expandedGroups.has(group)) {
                    visible = false
                }
            }
            if (node.type === 'group') {
                ret.push(
                    <GroupRow
                        key={node.name}
                        name={node.name}
                        expanded={expandedGroups.has(node.name)}
                        toggleExpanded={() => {
                            expandedGroupsDispatch({
                                type: 'toggle',
                                path: node.name
                            })
                        }}
                        visible={visible}
                    />
                )
            }
            else if (node.type === 'leaf') {
                if (node.fieldType === 'input') {
                    if (!showInputs) return
                    const value = jobDefinition?.inputFiles.find(f => (f.name === node.name))?.fileName
                    ret.push(<InputRow
                        key={node.name}
                        name={node.name}
                        description={node.description}
                        value={value}
                        setValid={valid => {
                            validParametersDispatch({
                                type: 'setValid',
                                name: node.name,
                                valid
                            })
                        }}
                        fileLinks={fileLinks}
                        visible={visible}
                    />)
                }
                else if (node.fieldType === 'output') {
                    if (!showOutputs) return
                    const value = jobDefinition?.outputFiles.find(f => (f.name === node.name))?.fileName
                    ret.push(<OutputRow
                        key={node.name}
                        name={node.name}
                        description={node.description}
                        value={value}
                        setValid={valid => {
                            validParametersDispatch({
                                type: 'setValid',
                                name: node.name,
                                valid
                            })
                        }}
                        fileLinks={fileLinks}
                        visible={visible}
                    />)
                }
                else if (node.fieldType === 'parameter') {
                    if (!showParameters) return
                    const value = jobDefinition?.inputParameters.find(f => (f.name === node.name))?.value
                    const parameter = processor.parameters.find(p => (p.name === node.name))
                    if (!parameter) {
                        console.warn(`Unexpected: processor parameter not found: ${node.name}`)
                        return
                    }
                    ret.push(<ParameterRow
                        key={node.name}
                        parameter={parameter}
                        value={value}
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
                        visible={visible}
                    />)
                }
                else {
                    throw Error('Unexpected field type')
                }
                ret.push(
                    
                )
            }
            else {
                throw Error('Unexpected node type')
            }
        })
        return ret
    }, [jobDefinition, processor, nwbFile, setParameterValue, readOnly, show, secretParameterNames, fileLinks, nodes, expandedGroups])
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

// minimum width that fits the content
const nameColumnStyle: React.CSSProperties = {
    width: '1%',
    whiteSpace: 'nowrap'
}

type GroupRowProps = {
    name: string
    expanded: boolean
    toggleExpanded: () => void
    visible?: boolean
}

const GroupRow: FunctionComponent<GroupRowProps> = ({name, expanded, toggleExpanded, visible}) => {
    return (
        <tr style={{display: visible ? undefined : 'none'}}>
            <td colSpan={3} style={{fontWeight: 'bold'}}>
                <span onClick={toggleExpanded} style={{cursor: 'pointer'}}>
                    {indentForName(name)}
                    {
                        expanded ? (
                            <span><FontAwesomeIcon icon={faCaretDown} style={{color: 'gray'}} /> </span>
                        ) : (
                            <span><FontAwesomeIcon icon={faCaretRight} style={{color: 'gray'}} /> </span>
                        )
                    }
                    {baseName(name)}
                </span>
            </td>
        </tr>
    )
}

type InputRowProps = {
    name: string
    description: string
    value?: string
    setValid?: (valid: boolean) => void
    fileLinks?: boolean
    visible?: boolean
}

const InputRow: FunctionComponent<InputRowProps> = ({name, description, value, setValid, fileLinks, visible}) => {
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
        <tr style={{display: visible ? undefined : 'none'}}>
            <td style={nameColumnStyle}>{indentForName(name)}{baseName(name)}</td>
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
    visible?: boolean
}

const OutputRow: FunctionComponent<OutputRowProps> = ({name, description, value, setValid, fileLinks, visible}) => {
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
            <td style={{...nameColumnStyle, display: visible ? undefined : 'none'}}>{indentForName(name)}{baseName(name)}</td>
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
    visible?: boolean
}

const ParameterRow: FunctionComponent<ParameterRowProps> = ({parameter, value, nwbFile, setValue, setValid, readOnly, secret, visible}) => {
    const {type, name, description} = parameter
    const [isValid, setIsValid] = useState<boolean>(false)
    useEffect(() => {
        if (parameter.type === 'bool') {
            setValid(true)
            setIsValid(true)
        }
    }, [parameter, setValid])
    return (
        <tr style={{display: visible ? undefined : 'none'}}>
            <td title={`${name} (${type})`} style={nameColumnStyle}>
                <span
                    style={{color: readOnly || isValid ? 'black' : 'red'}}
                >{indentForName(name)}{baseName(name)}</span>
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
            <td>{description}</td>
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

export const isElectricalSeriesPathParameter = (name: string) => {
    const aa = name.split('.')
    if (aa.length === 0) return false
    const last = aa[aa.length - 1]
    return (last === 'electrical_series_path')
}

export const isUnitsPathParameter = (name: string) => {
    const aa = name.split('.')
    if (aa.length === 0) return false
    const last = aa[aa.length - 1]
    return (last === 'units_path')
}

const EditParameterValue: FunctionComponent<EditParameterValueProps> = ({parameter, value, nwbFile, setValue, setValid}) => {
    const {type, name} = parameter
    if (isElectricalSeriesPathParameter(name)) {
        return <ElectricalSeriesPathSelector value={value} nwbFile={nwbFile} setValue={setValue} setValid={setValid} />
    }
    else if (isUnitsPathParameter(name)) {
        return <UnitsPathSelector value={value} nwbFile={nwbFile} setValue={setValue} setValid={setValid} />
    }
    else if (parameter.options) {
        return <SelectEdit value={value} setValue={setValue} setValid={setValid} options={parameter.options} />
    }
    else if (type === 'str') {
        setValid(true)
        return <input type="text" value={value || ''} onChange={evt => {setValue(evt.target.value)}} style={{width: 250}} />
    }
    else if (type === 'int') {
        return <IntEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'Optional[int]') {
        return <IntEdit value={value} setValue={setValue} setValid={setValid} optional={true} />
    }
    else if (type === 'float') {
        return <FloatEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'Optional[float]') {
        return <FloatEdit value={value} setValue={setValue} setValid={setValid} optional={true} />
    }
    else if (type === 'bool') {
        return <input type="checkbox" checked={value || false} onChange={evt => {setValue(evt.target.checked ? true : false)}} />
    }
    else if (type === 'List[int]') {
        return <IntListEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'List[float]') {
        return <FloatListEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else if (type === 'List[str]') {
        return <StringListEdit value={value} setValue={setValue} setValid={setValid} />
    }
    else {
        return <div>Unsupported type: {type}</div>
    }
}

type SelectEditProps = {
    value: any
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
    options: any[]
}

const SelectEdit: FunctionComponent<SelectEditProps> = ({value, setValue, setValid, options}) => {
    const isValid = useMemo(() => {
        return options.includes(value)
    }, [value, options])
    useEffect(() => {
        setValid(isValid)
    }, [isValid, setValid])
    return (
        <select value={value || ''} onChange={evt => {
            for (const option of options) {
                if (option + '' === evt.target.value) {
                    setValue(option)
                    return
                }
            }
        }}>
            {
                options.map(option => (
                    <option key={option} value={option + ''}>{option}</option>
                ))
            }
        </select>
    
    )
}

type FloatEditProps = {
    value: any
    setValue: (value: number | null) => void
    setValid: (valid: boolean) => void
    optional?: boolean
}

const FloatEdit: FunctionComponent<FloatEditProps> = ({value, setValue, setValid, optional}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined) // value of undefined corresponds to internalValue of ''
    useEffect(() => {
        if ((value === undefined) && (optional)) {
            setInternalValue('')
        }
        else {
            if (isFloatType(value)) {
                setInternalValue(old => {
                    if ((old !== undefined) && (stringIsValidFloat(old)) && (parseFloat(old) === value)) {
                        return old
                    }
                    return `${value}`
                })
            }
        }
    }, [value, optional])

    const handleChange = useCallback((newString: string) => {
        if (stringIsValidFloat(newString)) {
            const newValue = parseFloat(newString)
            if (newValue === value) return
            setValue(newValue)
        }
        setInternalValue(newString)
    }, [setValue, value])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        if ((optional) && (internalValue === '')) return true
        return stringIsValidFloat(internalValue)
    }, [internalValue, optional])

    useEffect(() => {
        setValid(isValid)
    }, [isValid, setValid])

    return (
        <span className="FloatEdit">
            <input type="text" value={internalValue || ''} onChange={evt => {handleChange(evt.target.value)}} style={numInputStyle} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
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
    setValue: (value: number | null) => void
    setValid: (valid: boolean) => void
    optional?: boolean
}

const IntEdit: FunctionComponent<IntEditProps> = ({value, setValue, setValid, optional}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined) // value of undefined corresponds to internalValue of ''
    useEffect(() => {
        if ((value === undefined) && (optional)) {
            setInternalValue('')
        }
        else {
            if (isIntType(value)) {
                setInternalValue(old => {
                    if ((old !== undefined) && (stringIsValidInt(old)) && (parseInt(old) === value)) {
                        return old
                    }
                    return `${value}`
                })
            }
        }
    }, [value, optional])

    const handleChange = useCallback((newString: string) => {
        if (stringIsValidInt(newString)) {
            const newValue = parseInt(newString)
            if (newValue === value) return
            setValue(newValue)
        }
        setInternalValue(newString)
    }, [setValue, value])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        if ((optional) && (internalValue === '')) return true
        return stringIsValidInt(internalValue)
    }, [internalValue, optional])

    useEffect(() => {
        setValid(isValid)
    }, [isValid, setValid])

    return (
        <span className="IntEdit">
            <input type="text" value={internalValue || ''} onChange={evt => {handleChange(evt.target.value)}} style={numInputStyle} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
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
        if (!electricalSeriesPaths) return
        if (electricalSeriesPaths.length === 0) return
        if ((value) && (electricalSeriesPaths.includes(value))) return
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
        <select value={value || ''} onChange={evt => {setValue(evt.target.value)}}>
            {
                [...electricalSeriesPaths].map(path => (
                    <option key={path} value={path}>{path}</option>
                ))
            }
        </select>
    )
}

type UnitsPathSelectorProps = {
    value?: string
    nwbFile?: RemoteH5File
    setValue: (value: string) => void
    setValid?: (valid: boolean) => void
}

const UnitsPathSelector: FunctionComponent<UnitsPathSelectorProps> = ({value, nwbFile, setValue, setValid}) => {
    const unitsPaths = useUnitsPaths(nwbFile)

    useEffect(() => {
        if (!unitsPaths) return
        if (unitsPaths.length === 0) return
        if ((value) && (unitsPaths.includes(value))) return
        setValue(unitsPaths[0])
    }, [value, unitsPaths, setValue])

    useEffect(() => {
        if (!setValid) return
        if ((unitsPaths === undefined) || (unitsPaths.length === 0)) {
            setValid(false)
            return
        }
        setValid(!!value)
    }, [setValid, value, unitsPaths])

    if (!unitsPaths) return <div>Loading...</div>
    if (unitsPaths.length === 0) return <div>No units object found.</div>
    return (
        <select value={value || ''} onChange={evt => {setValue(evt.target.value)}}>
            {
                [...unitsPaths].map(path => (
                    <option key={path} value={path}>{path}</option>
                ))
            }
        </select>
    )
}

const numInputStyle = {
    width: 60
}

type IntListEditProps = {
    value: any
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
}

const isIntListType = (x: any) => {
    if (!Array.isArray(x)) return false
    for (let i=0; i<x.length; i++) {
        if (!isIntType(x[i])) return false
    }
    return true
}

function intListToString(x: number[]) {
    return x.join(', ')
}

function stringToIntList(s: string) {
    return s.split(',').map(x => parseInt(x.trim()))
}

function stringIsValidIntList(s: string) {
    const intListRegex = /^[-+]?[0-9]+(,\s*[-+]?[0-9]+)*$/;
    return intListRegex.test(s);
}

const IntListEdit: FunctionComponent<IntListEditProps> = ({value, setValue, setValid}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined) // value of undefined corresponds to internalValue of ''
    useEffect(() => {
        if (isIntListType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidIntList(old)) && (intListToString(stringToIntList(old)) === intListToString(value))) {
                    return old
                }
                return `${value}`
            })
        }
    }, [value])

    const handleChange = useCallback((newString: string) => {
        if (stringIsValidIntList(newString)) {
            const newValue = stringToIntList(newString)
            if (intListToString(newValue) === intListToString(value)) return
            setValue(newValue)
        }
        setInternalValue(newString)
    }, [setValue, value])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidIntList(internalValue)
    }, [internalValue])

    useEffect(() => {
        setValid(isValid)
    }, [isValid, setValid])

    return (
        <span className="IntListEdit">
            <input type="text" value={internalValue || ''} onChange={evt => {handleChange(evt.target.value)}} style={numInputStyle} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
        </span>
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
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined) // value of undefined corresponds to internalValue of ''
    useEffect(() => {
        if (isFloatListType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidFloatList(old)) && (floatListToString(stringToFloatList(old)) === floatListToString(value))) {
                    return old
                }
                return `${value}`
            })
        }
    }, [value])

    const handleChange = useCallback((newString: string) => {
        if (stringIsValidFloatList(newString)) {
            const newValue = stringToFloatList(newString)
            if (floatListToString(newValue) === floatListToString(value)) return
            setValue(newValue)
        }
        setInternalValue(newString)
    }, [setValue, value])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidFloatList(internalValue)
    }, [internalValue])

    useEffect(() => {
        setValid(isValid)
    }, [isValid, setValid])

    return (
        <span className="FloatListEdit">
            <input type="text" value={internalValue || ''} onChange={evt => {handleChange(evt.target.value)}} style={numInputStyle} />
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
            {
                isValid ? null : <span style={{color: 'red'}}>x</span>
            }
        </span>
    )
}

type StringListEditProps = {
    value: any
    setValue: (value: any) => void
    setValid: (valid: boolean) => void
}

const isStringListType = (x: any) => {
    if (!Array.isArray(x)) return false
    for (let i=0; i<x.length; i++) {
        if (typeof(x[i]) !== 'string') return false
    }
    return true
}

function stringListToString(x: string[]) {
    return x.join(', ')
}

function stringToStringList(s: string) {
    return s.split(',').map(x => x.trim())
}

function stringIsValidStringList(s: string) {
    const stringListRegex = /^([^,]+)(,\s*[^,]+)*$/;
    return stringListRegex.test(s);
}

const StringListEdit: FunctionComponent<StringListEditProps> = ({value, setValue, setValid}) => {
    const [internalValue, setInternalValue] = useState<string | undefined>(undefined)
    useEffect(() => {
        if (isStringListType(value)) {
            setInternalValue(old => {
                if ((old !== undefined) && (stringIsValidStringList(old)) && (stringListToString(value) === old)) return old
                return stringListToString(value)
            })
        }
    }, [value])

    useEffect(() => {
        if (internalValue === undefined) return
        if (stringIsValidStringList(internalValue)) {
            setValue(stringToStringList(internalValue))
            setValid(true)
        }
        else {
            setValid(false)
        }
    }, [internalValue, setValue, setValid])

    const isValid = useMemo(() => {
        if (internalValue === undefined) return false
        return stringIsValidStringList(internalValue)
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

const indentForName = (name: string) => {
    const aa = name.split('.')
    return (
        <span>
            {
                aa.map((part, index) => (
                    <span key={index}>
                        &nbsp;&nbsp;&nbsp;
                    </span>
                ))
            }
        </span>
    )
}

const baseName = (name: string) => {
    const aa = name.split('.')
    return aa[aa.length - 1]
}

export default EditJobDefinitionWindow