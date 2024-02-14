import { Hyperlink } from "@fi-sci/misc";
import { FunctionComponent, useMemo, useReducer } from "react";
import { useGithubAuth } from "../../../GithubAuth/useGithubAuth";
import UserIdComponent from "../../../UserIdComponent";
import { timeAgoString } from "../../../timeStrings";
import { DendroScript } from "../../../types/dendro-types";
import { selectedStringsReducer } from "../FileBrowser/FileBrowser2";
import { Checkbox } from "../FileBrowser/FileBrowserTable";
import ScriptsTableMenuBar from "./ScriptsTableMenuBar";

type Props = {
    width: number
    height: number
    scripts: DendroScript[]
    onScriptClicked: (scriptId: string) => void
    createScriptEnabled?: boolean
    createScriptTitle?: string
}

const menuBarHeight = 30
const hPadding = 20
const vPadding = 5

type RowItem = {
    type: 'script'
    script: DendroScript
    timestampCreated: number
}

const ScriptsTable: FunctionComponent<Props> = ({ width, height, scripts, onScriptClicked, createScriptEnabled, createScriptTitle }) => {
    const sortedScripts: DendroScript[] = useMemo(() => {
        return [...scripts].sort((a, b) => (b.timestampCreated - a.timestampCreated))
    }, [scripts])

    const [selectedScriptIds, selectedScriptIdsDispatch] = useReducer(selectedStringsReducer, new Set<string>())

    const colWidth = 15

    const rowItems: RowItem[] = useMemo(() => (
        sortedScripts.map(script => {
            return {
                type: 'script',
                script,
                timestampCreated: script.timestampCreated
            }
        })
    ), [sortedScripts])

    return (
        <div style={{position: 'relative', width, height}}>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: menuBarHeight - vPadding * 2, paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <ScriptsTableMenuBar
                    width={width - hPadding * 2}
                    height={menuBarHeight - vPadding * 2}
                    selectedScriptIds={Array.from(selectedScriptIds)}
                    onResetSelection={() => selectedScriptIdsDispatch({type: 'set', values: new Set<string>()})}
                    createScriptEnabled={createScriptEnabled}
                    createScriptTitle={createScriptTitle}
                />
            </div>
            <div style={{position: 'absolute', width: width - hPadding * 2, height: height - menuBarHeight - vPadding * 2, top: menuBarHeight, overflowY: 'scroll', paddingLeft: hPadding, paddingRight: hPadding, paddingTop: vPadding, paddingBottom: vPadding}}>
                <table className="scientific-table" style={{fontSize: 12}}>
                    <thead>
                        <tr>
                            <th style={{width: colWidth}} />
                            <th>Script</th>
                            <th>User</th>
                            <th>Created</th>
                            <th>Modified</th>
                        </tr>
                    </thead>
                    <tbody>
                        {
                            rowItems.map((rowItem) => {
                                if (rowItem.type === 'script') {
                                    const ss = rowItem.script
                                    return (
                                        <tr key={ss.scriptId}>
                                            <td style={{width: colWidth}}>
                                                <Checkbox checked={selectedScriptIds.has(ss.scriptId)} onClick={() => selectedScriptIdsDispatch({type: 'toggle', value: ss.scriptId})} />
                                            </td>
                                            <td>
                                                <Hyperlink onClick={() => onScriptClicked(ss.scriptId)}>
                                                    {ss.scriptName}
                                                </Hyperlink>
                                            </td>
                                            <td>
                                                <UserIdComponent userId={ss.userId} />
                                            </td>
                                            <td>{timeAgoString(ss.timestampCreated)}</td>
                                            <td>{timeAgoString(ss.timestampModified)}</td>
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

export default ScriptsTable